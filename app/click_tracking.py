import reflex as rx
import logging
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.routing import Route
from reflex.vars.base import VarData
from reflex.utils.imports import ImportVar
import re
from sqlalchemy import text
from app.models import ProductLinkClick
from app.public_catalog import PUBLIC_CTE
from app.discovery import safe_https


def tracking_url(product_id: rx.Var[int]) -> rx.Var[str]:
    return rx.Var(
        _js_expr=f"`${{String(getBackendURL(env.UPLOAD)).replace(/\\/_upload\\/?$/, '')}}/api/product-click/${{{product_id}}}`",
        _var_type=str,
        _var_data=VarData(
            imports={
                "$/utils/state": ["getBackendURL"],
                "$/env.json": [ImportVar(tag="env", is_default=True)],
            }
        ),
    )


def offer_tracking_url(offer_id: rx.Var[int]) -> rx.Var[str]:
    return rx.Var(
        _js_expr=f"`${{String(getBackendURL(env.UPLOAD)).replace(/\\/_upload\\/?$/, '')}}/api/offer-click/${{{offer_id}}}`",
        _var_type=str,
        _var_data=VarData(
            imports={
                "$/utils/state": ["getBackendURL"],
                "$/env.json": [ImportVar(tag="env", is_default=True)],
            }
        ),
    )


def frontend_destination(destination: str, request: Request) -> str:
    if not destination.startswith("/"):
        return destination
    config = rx.config.get_config()
    base = config.deploy_url or f"http://localhost:{config.frontend_port}"
    return f"{base.rstrip('/')}{destination}"


async def _redirect_click(
    request: Request, offer_specific: bool
) -> RedirectResponse:
    destination = "/#catalogo"
    raw_id = request.path_params.get(
        "offer_id" if offer_specific else "product_id", ""
    )
    try:
        if (
            isinstance(raw_id, str)
            and re.fullmatch(r"[0-9]{1,10}", raw_id)
            and 0 < int(raw_id) <= 2147483647
        ):
            async with rx.asession() as session:
                async with session.begin():
                    await session.execute(
                        text("SELECT pg_advisory_xact_lock(71420932)")
                    )
                    column = "offer_id" if offer_specific else "product_id"
                    row = (
                        (
                            await session.execute(
                                text(
                                    f"{PUBLIC_CTE} SELECT e.*, p.sku FROM eligible e JOIN products p ON p.id = e.product_id WHERE e.{column} = :id ORDER BY e.offer_id LIMIT 1 FOR SHARE OF p"
                                ),
                                {"id": int(raw_id)},
                            )
                        )
                        .mappings()
                        .first()
                    )
                    if row:
                        await session.execute(
                            text(
                                "SELECT id FROM offers WHERE id = :id FOR SHARE"
                            ),
                            {"id": row["offer_id"]},
                        )
                        await session.execute(
                            text(
                                "SELECT id FROM merchants WHERE id = :id FOR SHARE"
                            ),
                            {"id": row["merchant_id"]},
                        )
                        await session.execute(
                            text(
                                "SELECT id FROM affiliate_links WHERE offer_id = :id FOR SHARE"
                            ),
                            {"id": row["offer_id"]},
                        )
                        checked = (
                            (
                                await session.execute(
                                    text(
                                        f"{PUBLIC_CTE} SELECT * FROM eligible WHERE offer_id = :id"
                                    ),
                                    {"id": row["offer_id"]},
                                )
                            )
                            .mappings()
                            .first()
                        )
                        if (
                            checked
                            and safe_https(
                                checked["affiliate_url"],
                                [
                                    *(checked["allowed_domains"] or []),
                                    *(checked["tracking_domains"] or []),
                                ],
                            )
                            and safe_https(
                                checked["destination_url"],
                                checked["allowed_domains"] or [],
                            )
                        ):
                            session.add(
                                ProductLinkClick(
                                    offer_id=row["offer_id"],
                                    product_id=row["product_id"],
                                    title=row["title"],
                                    sku=row["sku"],
                                    marketplace=row["merchant"],
                                )
                            )
                            destination = checked["affiliate_url"]
    except Exception as e:
        logging.exception(f"Error: {e}")
        destination = "/#catalogo"
    return RedirectResponse(
        frontend_destination(destination, request),
        status_code=302,
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
    )


async def track_product_click(request: Request) -> RedirectResponse:
    return await _redirect_click(request, False)


async def track_offer_click(request: Request) -> RedirectResponse:
    return await _redirect_click(request, True)


click_api = Starlette(
    routes=[
        Route(
            "/api/offer-click/{offer_id}", track_offer_click, methods=["GET"]
        ),
        Route(
            "/api/product-click/{product_id}",
            track_product_click,
            methods=["GET"],
        ),
    ]
)
