import reflex as rx
from app.components.header import header
from app.components.hero import hero, footer
from app.components.catalog import catalog
from app.states.storefront_state import StorefrontState
from app.components.cart import cart_content
from app.states.cart_state import CartState
from app.components.account import account_content
from app.states.account_state import AccountState
from app.pages import marketplaces


@rx.page(
    route="/",
    auth=False,
    title="VIKTRINE SHOP | Estilo em cada detalhe",
    description="Explore nossa vitrine demonstrativa de moda e acessórios.",
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
            hero(), catalog(), class_name="w-full bg-[#faf9f4] text-[#0d231d]"
        ),
        footer(),
        on_mount=[StorefrontState.load_catalog, CartState.load_cart],
        class_name="min-h-dvh w-full bg-[#faf9f4] font-['Inter'] text-[#0d231d]",
    )


@rxe.page(
    route="/carrinho",
    auth=False,
    title="Sua sacola | VIKTRINE SHOP",
    description="Revise sua sacola e registre um pedido sem cobrança de pagamento.",
)
def cart_page() -> rx.Component:
    return rx.el.div(
        header(),
        rx.el.main(
            cart_content(), class_name="w-full bg-[#faf9f4] text-[#0d231d]"
        ),
        footer(),
        on_mount=CartState.load_cart,
        class_name="min-h-dvh w-full bg-[#faf9f4] font-['Inter'] text-[#0d231d]",
    )


@rxe.page(
    route="/minha-conta",
    auth=True,
    title="Minha conta | VIKTRINE SHOP",
    description="Seu espaço pessoal para acompanhar pedidos e detalhes de entrega.",
)
def account_page() -> rx.Component:
    return rx.el.div(
        header(),
        rx.el.main(
            account_content(), class_name="w-full bg-[#faf9f4] text-[#0d231d]"
        ),
        footer(),
        on_mount=[AccountState.load_orders, CartState.load_cart],
        class_name="min-h-dvh w-full bg-[#faf9f4] font-['Inter'] text-[#0d231d]",
    )


app = rxe.App(
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
            href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:wght@400;500;600&display=swap",
            rel="stylesheet",
        ),
    ],
)
