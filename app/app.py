import reflex as rx
import reflex_enterprise as rxe
from app.components.header import header
from app.components.hero import hero, history_section, footer
from app.components.catalog import catalog
from app.states.storefront_state import StorefrontState
from app.pages.privacy import privacy_content
from app.states.legacy_navigation_state import LegacyNavigationState
from app.components.account import account_content
from app.states.account_state import AccountState
from app.states.favorite_state import FavoriteState
from app.pages import marketplaces
from app.components.admin import admin_content
from app.states.admin_state import AdminState
from app.click_tracking import click_api
from app.pages.product import product_page
from app.states.product_detail_state import ProductDetailState


@rxe.page(
    route="/",
    auth=False,
    title="Viktrine | Descubra e compare ofertas",
    description="Descubra produtos editoriais e compare ofertas com fontes registradas. Compras nas lojas externas.",
)
def index() -> rx.Component:
    return rx.el.div(
        rx.el.a(
            "Ir para o catálogo",
            href="#catalogo",
            class_name="sr-only bg-[#d4af37] text-[#05120e] focus:not-sr-only focus:block focus:p-3",
        ),
        header(),
        rx.el.main(
            hero(),
            catalog(),
            history_section(),
            class_name="min-w-0 w-full max-w-[100vw] overflow-x-hidden bg-[#faf9f4] text-[#0d231d]",
        ),
        footer(),
        class_name="min-h-dvh w-full max-w-[100vw] overflow-x-hidden bg-[#faf9f4] font-['Inter'] text-[#0d231d]",
    )


@rxe.page(
    route="/carrinho",
    auth=False,
    title="Descoberta de ofertas | Viktrine",
    description="A Viktrine não possui sacola ou checkout. Compras nas lojas externas.",
)
def legacy_cart_redirect_page() -> rx.Component:
    return rx.el.div(
        header(),
        rx.el.main(
            rx.el.p(
                "A Viktrine não possui sacola ou checkout de produtos. Você será encaminhado à descoberta de ofertas.",
                on_mount=LegacyNavigationState.redirect_to_discovery,
                role="status",
                class_name="px-6 py-16 text-sm leading-7 text-[#073238]",
            ),
            class_name="min-w-0 w-full max-w-[100vw] overflow-x-hidden bg-[#faf9f4] text-[#0d231d]",
        ),
        footer(),
        class_name="min-h-dvh w-full max-w-[100vw] overflow-x-hidden bg-[#faf9f4] font-['Inter'] text-[#0d231d]",
    )


@rxe.page(
    route="/minha-conta",
    auth=True,
    title="Minha conta | Viktrine",
    description="Favoritos, listas privadas e arquivo demonstrativo de pedidos anteriores, somente leitura.",
)
def account_page() -> rx.Component:
    return rx.el.div(
        header(),
        rx.el.main(
            account_content(),
            class_name="min-w-0 w-full max-w-[100vw] overflow-x-hidden bg-[#faf9f4] text-[#0d231d]",
        ),
        footer(),
        on_mount=[
            AccountState.load_orders,
            FavoriteState.sync_auth,
        ],
        class_name="min-h-dvh w-full max-w-[100vw] overflow-x-hidden bg-[#faf9f4] font-['Inter'] text-[#0d231d]",
    )


@rxe.page(
    route="/admin",
    auth=True,
    title="Curadoria editorial | Viktrine",
    description="Produtos editoriais, ofertas e evidências da Viktrine.",
)
def admin_page() -> rx.Component:
    return rx.el.div(
        header(),
        rx.el.main(
            admin_content(),
            class_name="min-w-0 w-full flex-1 bg-[#faf9f4] text-[#0d231d]",
        ),
        footer(),
        on_mount=AdminState.load_dashboard,
        class_name="flex min-h-dvh w-full flex-col bg-[#faf9f4] font-['Inter'] text-[#0d231d]",
    )


@rxe.page(
    route="/produto/[product_id]",
    auth=False,
    title="Produto e ofertas | Viktrine",
    description="Compare ofertas da mesma variante e moeda e consulte suas fontes e observações reais.",
)
def product_detail_page() -> rx.Component:
    return product_page()


@rxe.page(
    route="/privacidade",
    auth=False,
    title="Privacidade e LGPD | Viktrine",
    description="Práticas atuais de dados, identidade, favoritos, listas, cliques e arquivo demonstrativo da Viktrine.",
)
def privacy_page() -> rx.Component:
    return privacy_content()


app = rxe.App(
    api_transformer=click_api,
    theme=rx.theme(appearance="light"),
    stylesheets=["/brand.css"],
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            cross_origin="",
        ),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Inter:wght@400;500;600&display=swap",
            rel="stylesheet",
        ),
    ],
)
