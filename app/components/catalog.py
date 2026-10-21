import reflex as rx
from app.states.storefront_state import StorefrontState, ProductView
from app.components.offer_comparison import offer_row
from app.components.catalog_filters import discovery_filters
from app.components.saved_lists import list_add_control
from app.components.favorites import favorite_control, favorite_feedback


def category_pill(label: str) -> rx.Component:
    return rx.el.button(
        label,
        on_click=StorefrontState.choose_category(label),
        aria_pressed=StorefrontState.category == label,
        class_name=rx.cond(
            StorefrontState.category == label,
            "shrink-0 rounded-full border border-[#0d231d] bg-[#0d231d] px-5 py-2.5 text-xs text-[#f5f1e8]",
            "shrink-0 rounded-full border border-[#d8d7cc] bg-transparent px-5 py-2.5 text-xs text-[#536059] hover:border-[#0d231d] hover:text-[#0d231d]",
        ),
    )


def sort_option(label: str) -> rx.Component:
    return rx.el.button(
        label,
        on_click=StorefrontState.choose_sort(label),
        class_name=rx.cond(
            StorefrontState.sort == label,
            "w-full bg-[#edece3] px-4 py-2.5 text-left text-xs font-semibold text-[#0d231d]",
            "w-full bg-[#faf9f4] px-4 py-2.5 text-left text-xs text-[#536059] hover:bg-[#edece3]",
        ),
    )


def product_card(product: ProductView) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.a(
                rx.el.img(
                    src=product["image_url"],
                    alt=product["title"],
                    loading="lazy",
                    class_name="aspect-[4/3] w-full bg-[#efede4] object-contain",
                ),
                href=f"/produto/{product['id']}",
                class_name="block focus-visible:outline-2 focus-visible:outline-[#d4af37]",
            ),
            rx.el.div(
                favorite_control(product["id"], product["title"]),
                class_name="absolute right-3 top-3",
            ),
            class_name="relative",
        ),
        rx.el.div(
            rx.el.p(product["category"], class_name="text-xs text-gray-600"),
            rx.el.h3(
                rx.el.a(
                    product["title"],
                    href=f"/produto/{product['id']}",
                    class_name="hover:underline focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
                class_name="mt-3 font-['Cormorant_Garamond'] text-3xl text-[#073238]",
            ),
            rx.el.p(
                product["brand_model"], class_name="mt-2 text-xs text-gray-600"
            ),
            rx.el.p(
                f"{product['variant']} · {product['currency']}",
                class_name="mt-3 text-xs font-medium text-[#073238]",
            ),
            rx.el.p(
                product["description"],
                class_name="mt-3 whitespace-pre-wrap text-sm leading-6 text-gray-600",
            ),
            rx.el.div(
                rx.foreach(product["offers"], offer_row), class_name="mt-4"
            ),
            rx.el.a(
                "Detalhes, fontes e histórico",
                href=f"/produto/{product['id']}",
                class_name="block min-h-11 py-3 text-xs text-[#073238] underline focus-visible:outline-2 focus-visible:outline-[#d4af37]",
            ),
            list_add_control(product["id"]),
            class_name="p-5",
        ),
        key=product["key"],
        class_name="min-w-0 border border-[#dedfd5] bg-white text-[#073238]",
    )


def catalog() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "CURADORIA PARA O SEU DIA A DIA",
                    class_name="mb-3 text-[10px] tracking-[0.22em] text-[#8b7846]",
                ),
                rx.el.h2(
                    "Encontre o seu próximo favorito",
                    class_name="font-['Cormorant_Garamond'] text-4xl font-medium leading-tight text-[#0d231d] md:text-5xl",
                ),
            ),
            rx.el.p(
                "Viktrine · Ofertas publicadas com fonte e revisão manual. Compras nas lojas externas.",
                class_name="mt-4 text-xs leading-relaxed text-[#687268] md:mt-0",
            ),
            class_name="flex flex-col justify-between gap-3 md:flex-row md:items-end",
        ),
        rx.el.div(
            rx.el.div(
                rx.foreach(
                    StorefrontState.categories,
                    category_pill,
                ),
                class_name="flex flex-1 gap-2 overflow-x-auto py-2",
            ),
            rx.el.details(
                rx.el.summary(
                    rx.icon("arrow-down-up", class_name="h-3.5 w-3.5"),
                    StorefrontState.sort,
                    rx.icon("chevron-down", class_name="h-3.5 w-3.5"),
                    class_name="flex cursor-pointer list-none items-center gap-3 whitespace-nowrap py-3 text-xs text-[#536059]",
                ),
                rx.el.div(
                    rx.foreach(
                        [
                            "Menor preço",
                            "Maior preço",
                            "Mais recentes",
                        ],
                        sort_option,
                    ),
                    class_name="absolute right-0 top-full z-10 w-44 overflow-hidden border border-[#d8d7cc] bg-[#faf9f4]",
                ),
                class_name="relative shrink-0",
            ),
            class_name="mt-8 flex flex-col justify-between gap-3 border-b border-[#deded3] pb-5 md:flex-row md:items-center md:gap-8",
        ),
        discovery_filters(),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    f"{StorefrontState.total} grupos de produto, variante e moeda",
                    class_name="text-xs text-[#687268]",
                ),
                rx.el.button(
                    "Limpar filtros",
                    on_click=StorefrontState.clear_filters,
                    class_name="text-xs text-[#0d231d] underline underline-offset-4 hover:text-[#8b7846]",
                ),
                class_name="flex items-center gap-5",
            ),
            class_name="flex flex-wrap items-start justify-between gap-4 py-6",
        ),
        rx.el.div(favorite_feedback(), class_name="mb-5"),
        rx.cond(
            StorefrontState.loading,
            rx.el.div(
                rx.foreach(
                    [0, 1, 2, 3],
                    lambda index: rx.el.div(
                        rx.el.div(class_name="aspect-[4/5] bg-[#e9e6df]"),
                        rx.el.div(class_name="mt-5 h-4 w-3/4 bg-[#e9e6df]"),
                        rx.el.div(class_name="mt-3 h-3 w-1/3 bg-[#e9e6df]"),
                        key=index,
                        class_name="animate-pulse",
                    ),
                ),
                role="status",
                aria_label="Carregando produtos",
                class_name="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3",
            ),
            rx.cond(
                StorefrontState.error != "",
                rx.el.div(
                    rx.icon(
                        "circle-alert",
                        class_name="mx-auto mb-4 h-8 w-8 text-[#8b7846]",
                    ),
                    rx.el.p(
                        StorefrontState.error,
                        class_name="text-sm text-[#536059]",
                    ),
                    rx.el.button(
                        "Tentar novamente",
                        on_click=StorefrontState.load_catalog,
                        class_name="mt-5 border border-[#0d231d] bg-[#0d231d] px-5 py-3 text-xs text-white",
                    ),
                    role="alert",
                    class_name="border border-[#deded3] py-16 text-center",
                ),
                rx.cond(
                    StorefrontState.total == 0,
                    rx.el.div(
                        rx.icon(
                            "search",
                            class_name="mx-auto mb-5 h-8 w-8 text-[#8b7846]",
                        ),
                        rx.el.h3(
                            "Nenhuma oferta elegível encontrada",
                            class_name="font-['Cormorant_Garamond'] text-3xl text-[#0d231d]",
                        ),
                        rx.el.p(
                            "Ajuste a busca ou os filtros. Produtos demonstrativos, ofertas sem evidência e links não revisados não aparecem aqui.",
                            class_name="mt-3 text-sm text-[#687268]",
                        ),
                        rx.el.button(
                            "Ver todos os produtos",
                            on_click=StorefrontState.clear_filters,
                            class_name="mt-6 border-b border-[#0d231d] pb-1 text-xs text-[#0d231d]",
                        ),
                        class_name="border border-[#deded3] py-20 text-center",
                    ),
                    rx.el.div(
                        rx.foreach(StorefrontState.products, product_card),
                        class_name="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3",
                    ),
                ),
            ),
        ),
        rx.cond(
            StorefrontState.page_count > 1,
            rx.el.div(
                rx.el.button(
                    "Anterior",
                    on_click=StorefrontState.change_page(-1),
                    disabled=(StorefrontState.page_number == 1)
                    | StorefrontState.loading,
                    class_name="border border-[#deded3] px-4 py-2 text-xs text-[#0d231d] disabled:opacity-40",
                ),
                rx.el.span(
                    f"Página {StorefrontState.page_number} de {StorefrontState.page_count}",
                    class_name="text-xs text-[#687268]",
                ),
                rx.el.button(
                    "Próxima",
                    on_click=StorefrontState.change_page(1),
                    disabled=(
                        StorefrontState.page_number
                        == StorefrontState.page_count
                    )
                    | StorefrontState.loading,
                    class_name="border border-[#deded3] px-4 py-2 text-xs text-[#0d231d] disabled:opacity-40",
                ),
                class_name="mt-10 flex items-center justify-center gap-5",
            ),
        ),
        id="catalogo",
        class_name="mx-auto w-full max-w-[1440px] scroll-mt-6 px-6 py-16 lg:px-12 lg:py-20",
    )
