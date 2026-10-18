import reflex as rx
import logging
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.routing import Route
from reflex.vars.base import VarData
from reflex.utils.imports import ImportVar
from app.affiliate import effective_destination
from app.models import Product, ProductLinkClick


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


def frontend_destination(destination: str, request: Request) -> str:
    if not destination.startswith("/"):
        return destination
    config = rx.config.get_config()
    base = config.deploy_url or f"http://localhost:{config.frontend_port}"
    return f"{base.rstrip('/')}{destination}"


async def track_product_click(request: Request) -> RedirectResponse:
    destination = "/#catalogo"
    raw_id = request.path_params["product_id"]
    try:
        product_id = int(raw_id)
        if product_id <= 0 or product_id > 2147483647:
            return RedirectResponse(
                frontend_destination(destination, request),
                status_code=302,
                headers={"Cache-Control": "no-store"},
            )
    except (ValueError, TypeError):
        return RedirectResponse(
            frontend_destination(destination, request),
            status_code=302,
            headers={"Cache-Control": "no-store"},
        )
    try:
        async with rx.asession() as session:
            product = await session.get(Product, product_id)
            if product is not None:
                destination = effective_destination(
                    product.partner_name, product.affiliate_url
                )
                session.add(
                    ProductLinkClick(
                        product_id=product.id,
                        title=product.title,
                        sku=product.sku,
                        marketplace=product.partner_name,
                    )
                )
                await session.commit()
    except Exception as e:
        logging.exception(f"Error: {e}")
    return RedirectResponse(
        frontend_destination(destination, request),
        status_code=302,
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"},
    )


click_api = Starlette(
    routes=[
        Route(
            "/api/product-click/{product_id}",
            track_product_click,
            methods=["GET"],
        ),
    ]
)
