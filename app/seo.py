import reflex as rx

import logging
from urllib.parse import urlsplit
from xml.sax.saxutils import escape
from starlette.responses import Response
from sqlalchemy import text
from app.public_catalog import PUBLIC_CTE
from reflex.vars.base import VarData
from reflex.utils.imports import ImportVar

PUBLIC_ROUTES = (
    "/",
    "/privacidade",
    "/lojas/amazon",
    "/lojas/shopee",
    "/lojas/mercado-livre",
)
PRIVATE_META = [{"name": "robots", "content": "noindex, nofollow, noarchive"}]


def sitemap_href() -> rx.Var[str]:
    return rx.Var(
        _js_expr="`${String(getBackendURL(env.UPLOAD)).replace(/\\/_upload\\/?$/, '')}/sitemap.xml`",
        _var_type=str,
        _var_data=VarData(
            imports={
                "$/utils/state": ["getBackendURL"],
                "$/env.json": [ImportVar(tag="env", is_default=True)],
            }
        ),
    )


def public_origin() -> str:
    value = rx.config.get_config().deploy_url or ""
    parts = urlsplit(value)
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username
        or parts.password
        or parts.query
        or parts.fragment
        or parts.path not in ("", "/")
    ):
        raise ValueError("Origem pública canônica indisponível.")
    return value.rstrip("/")


async def sitemap(request) -> Response:
    try:
        origin = public_origin()
        async with rx.asession() as session:
            rows = (
                (
                    await session.execute(
                        text(
                            f"{PUBLIC_CTE} SELECT DISTINCT product_id FROM eligible ORDER BY product_id LIMIT 50000"
                        )
                    )
                )
                .scalars()
                .all()
            )
        paths = [
            *PUBLIC_ROUTES,
            *(f"/produto/{value}" for value in rows[:49995]),
        ]
        entries = "".join(
            f"<url><loc>{escape(f'{origin}{path}')}</loc></url>"
            for path in paths
        )
        xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{entries}</urlset>'
        return Response(
            xml,
            media_type="application/xml",
            headers={"Cache-Control": "public, max-age=300"},
        )
    except Exception as e:
        logging.exception(f"Error: {e}")
        return Response(
            "Sitemap temporariamente indisponível.",
            status_code=503,
            media_type="text/plain",
        )


async def robots(request) -> Response:
    return Response(
        "User-agent: *\nDisallow: /admin\nDisallow: /minha-conta\nDisallow: /login\nDisallow: /carrinho\nDisallow: /api/\n",
        media_type="text/plain",
    )
