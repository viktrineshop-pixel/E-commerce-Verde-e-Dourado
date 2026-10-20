import reflex as rx
from app.states.product_detail_state import ProductDetailState
from app.public_catalog import ProductView
from app.components.header import header
from app.components.hero import footer
from app.components.offer_comparison import offer_evidence
from app.components.favorites import favorite_control, favorite_feedback
from app.components.saved_lists import list_add_control


def detail_group(product: ProductView) -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.img(
                src=product["image_url"],
                alt=product["title"],
                class_name="aspect-square w-full bg-[#efede4] object-contain",
            ),
            rx.el.div(
                rx.el.p(
                    product["category"], class_name="text-xs text-gray-600"
                ),
                rx.el.h1(
                    product["title"],
                    class_name="mt-4 font-['Cormorant_Garamond'] text-4xl text-[#073238] md:text-5xl",
                ),
                rx.el.p(
                    product["brand_model"],
                    class_name="mt-3 text-sm text-gray-600",
                ),
                rx.el.p(
                    f"{product['variant']} · {product['currency']}",
                    class_name="mt-3 text-sm font-medium text-[#073238]",
                ),
                rx.el.p(
                    product["description"],
                    class_name="mt-5 whitespace-pre-wrap text-sm leading-7 text-gray-600",
                ),
                rx.el.p(
                    f"Revisão editorial atualizada: {product['updated']}",
                    class_name="mt-5 text-xs text-gray-600",
                ),
                rx.el.div(
                    favorite_control(product["id"], product["title"]),
                    list_add_control(product["id"]),
                    class_name="mt-5 flex flex-wrap items-center gap-4",
                ),
                class_name="min-w-0",
            ),
            class_name="grid grid-cols-1 gap-8 md:grid-cols-2",
        ),
        rx.el.h2(
            "Ofertas da mesma variante e moeda",
            class_name="mt-10 font-['Cormorant_Garamond'] text-3xl text-[#073238]",
        ),
        rx.el.p(
            "Comparação dos preços registrados, sem incluir frete ou cupons. Nenhuma reserva, estoque ou compra é processada pela Viktrine.",
            class_name="mt-3 text-sm leading-6 text-gray-600",
        ),
        rx.el.div(
            rx.foreach(product["offers"], offer_evidence),
            class_name="mt-6 grid gap-5 lg:grid-cols-2",
        ),
        key=product["key"],
        class_name="mb-12 text-[#073238]",
    )


def product_page() -> rx.Component:
    return rx.el.div(
        header(),
        rx.el.main(
            rx.el.a(
                "Voltar à descoberta",
                href="/#catalogo",
                class_name="mb-8 inline-block text-sm text-[#073238] underline focus-visible:outline-2 focus-visible:outline-[#d4af37]",
            ),
            favorite_feedback(),
            rx.cond(
                ProductDetailState.loading,
                rx.el.div(
                    "Carregando ofertas e evidências…",
                    role="status",
                    class_name="min-h-72 animate-pulse bg-[#efede4] p-8 text-[#073238]",
                ),
                rx.cond(
                    ProductDetailState.error != "",
                    rx.el.div(
                        rx.el.p(ProductDetailState.error),
                        rx.el.button(
                            "Tentar novamente",
                            on_click=ProductDetailState.load_detail,
                            class_name="mt-4 border border-[#073238] px-4 py-3 text-[#073238]",
                        ),
                        role="alert",
                        class_name="p-8 text-[#073238]",
                    ),
                    rx.cond(
                        ProductDetailState.groups.length() == 0,
                        rx.el.div(
                            rx.el.h1(
                                "Produto não disponível na descoberta",
                                class_name="font-['Cormorant_Garamond'] text-4xl text-[#073238]",
                            ),
                            rx.el.p(
                                "Não há oferta publicada com evidência e link elegível para este produto. Nenhum encaminhamento está disponível.",
                                class_name="mt-4 text-sm text-gray-600",
                            ),
                            class_name="border border-[#dedfd5] p-8",
                        ),
                        rx.foreach(ProductDetailState.groups, detail_group),
                    ),
                ),
            ),
            rx.el.p(
                "Cupons locais de demonstração não são condições das lojas. Somente termos expressamente vinculados à loja podem ser apresentados; aplicação e validade devem ser confirmadas no destino.",
                class_name="mt-8 text-xs leading-6 text-gray-600",
            ),
            class_name="mx-auto w-full max-w-[1440px] px-6 py-12 lg:px-12",
        ),
        footer(),
        class_name="min-h-dvh bg-[#faf9f4] font-['Inter'] text-[#073238]",
    )
