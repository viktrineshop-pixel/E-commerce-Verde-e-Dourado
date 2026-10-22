import reflex as rx
import logging
from sqlalchemy import text
from app.landing_products import LandingView, landing_is_public


class LandingCatalogState(rx.State):
    products: list[LandingView] = []
    error: str = ""

    @rx.event(background=True)
    async def load_products(self):
        async with self:
            self.products = []
            self.error = ""
        try:
            async with rx.asession() as session:
                rows = (
                    (
                        await session.execute(
                            text(
                                "SELECT id, nome, descricao, slug, link_afiliado_original FROM produtos WHERE published = true ORDER BY created_at DESC, id DESC LIMIT 12"
                            )
                        )
                    )
                    .mappings()
                    .all()
                )
            products = [
                LandingView(
                    id=p["id"],
                    nome=p["nome"],
                    descricao=p["descricao"],
                    slug=p["slug"],
                    url=p["link_afiliado_original"],
                    published=True,
                    media=[],
                )
                for p in rows
                if landing_is_public(
                    True, p["link_afiliado_original"], p["slug"]
                )
            ]
            async with self:
                self.products = products
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    "As páginas de produtos não puderam ser carregadas."
                )
