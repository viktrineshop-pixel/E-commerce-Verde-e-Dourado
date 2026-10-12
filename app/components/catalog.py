import reflex as rx
from app.states.storefront_state import StorefrontState, ProductView
from app.states.cart_state import CartState


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


def price_option(label: str) -> rx.Component:
    return rx.el.button(
        label,
        on_click=StorefrontState.choose_price(label),
        aria_pressed=StorefrontState.price_filter == label,
        class_name=rx.cond(
            StorefrontState.price_filter == label,
            "rounded-sm border border-[#0d231d] bg-[#0d231d] px-4 py-2 text-xs text-white",
            "rounded-sm border border-[#d8d7cc] bg-[#faf9f4] px-4 py-2 text-xs text-[#536059] hover:border-[#0d231d]",
        ),
    )


def product_card(product: ProductView) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.img(
                src=product["image_url"],
                alt=product["title"],
                loading="lazy",
                class_name="aspect-[4/5] w-full object-cover transition-transform duration-700 group-hover:scale-105",
            ),
            rx.cond(
                product["badge"] != "",
                rx.el.span(
                    product["badge"],
                    class_name="absolute left-4 top-4 w-fit bg-[#faf9f4]/95 px-3 py-1.5 text-[10px] font-medium tracking-wide text-[#0d231d]",
                ),
            ),
            rx.cond(
                product["stock"] == 0,
                rx.el.span(
                    "Indisponível",
                    class_name="absolute bottom-4 left-4 w-fit bg-[#0d231d] px-3 py-1.5 text-[10px] text-[#f5f1e8]",
                ),
            ),
            class_name="relative overflow-hidden bg-[#e9e6df]",
        ),
        rx.el.div(
            rx.el.p(
                product["category"],
                class_name="mb-2 text-[10px] uppercase tracking-[0.16em] text-[#738077]",
            ),
            rx.el.h3(
                product["title"],
                class_name="text-sm font-medium text-[#0d231d] md:text-base",
            ),
            rx.el.div(
                rx.el.span(
                    product["price"],
                    class_name="text-sm font-semibold text-[#0d231d]",
                ),
                rx.cond(
                    product["compare_price"] != "",
                    rx.el.s(
                        product["compare_price"],
                        class_name="text-xs text-[#7b827a]",
                    ),
                ),
                class_name="mt-2 flex flex-wrap items-center gap-3",
            ),
            rx.el.details(
                rx.el.summary(
                    "Sobre a peça",
                    rx.icon("plus", class_name="h-3 w-3"),
                    class_name="mt-4 flex cursor-pointer list-none items-center justify-between border-t border-[#deded3] pt-3 text-[11px] text-[#536059] hover:text-[#0d231d]",
                ),
                rx.el.p(
                    product["description"],
                    class_name="pt-3 text-xs leading-relaxed text-[#536059]",
                ),
            ),
            rx.el.button(
                rx.icon("shopping-bag", class_name="h-4 w-4 shrink-0"),
                rx.cond(
                    product["stock"] > 0, "Adicionar à sacola", "Indisponível"
                ),
                type="button",
                on_click=CartState.add_product(product["id"]),
                disabled=(product["stock"] <= 0)
                | CartState.busy
                | CartState.submitting,
                aria_label=f"Adicionar {product['title']} à sacola",
                class_name="mt-4 flex min-h-11 w-full items-center justify-center gap-2 border border-[#0d231d] bg-[#0d231d] px-2 py-3 text-[11px] font-medium text-[#f5f1e8] hover:bg-[#05120e] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#8b7846] disabled:cursor-not-allowed disabled:opacity-40 sm:text-xs",
            ),
            class_name="px-1 pb-3 pt-5",
        ),
        key=product["id"],
        class_name="group min-w-0 bg-transparent",
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
                "Peças versáteis. Detalhes que fazem a diferença.",
                class_name="mt-4 text-xs leading-relaxed text-[#687268] md:mt-0",
            ),
            class_name="flex flex-col justify-between gap-3 md:flex-row md:items-end",
        ),
        rx.el.div(
            rx.el.div(
                rx.foreach(
                    [
                        "Todos",
                        "Feminino",
                        "Masculino",
                        "Acessórios",
                        "Novidades",
                        "Promoções",
                    ],
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
                            "Destaques",
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
        rx.el.div(
            rx.el.details(
                rx.el.summary(
                    rx.icon("sliders-horizontal", class_name="h-3.5 w-3.5"),
                    "Filtrar por preço e disponibilidade",
                    rx.icon("chevron-down", class_name="h-3 w-3"),
                    class_name="flex cursor-pointer list-none items-center gap-2 text-xs text-[#536059]",
                ),
                rx.el.div(
                    rx.foreach(
                        [
                            "Todos os preços",
                            "Até R$ 200",
                            "R$ 200 a R$ 400",
                            "Acima de R$ 400",
                        ],
                        price_option,
                    ),
                    rx.el.button(
                        rx.icon(
                            "check",
                            class_name=rx.cond(
                                StorefrontState.available_only,
                                "h-4 w-4 text-[#0d231d]",
                                "h-4 w-4 text-[#c4c8bd]",
                            ),
                        ),
                        "Somente disponíveis",
                        aria_pressed=StorefrontState.available_only,
                        on_click=StorefrontState.toggle_available,
                        class_name="flex items-center gap-2 px-3 py-2 text-xs text-[#536059]",
                    ),
                    class_name="mt-4 flex flex-wrap gap-2",
                ),
            ),
            rx.el.div(
                rx.el.span(
                    f"{StorefrontState.total} produtos",
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
                class_name="grid grid-cols-2 gap-x-5 gap-y-10 lg:grid-cols-4 lg:gap-x-7",
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
                            "Nenhuma peça encontrada",
                            class_name="font-['Cormorant_Garamond'] text-3xl text-[#0d231d]",
                        ),
                        rx.el.p(
                            "Experimente outra busca ou ajuste os filtros.",
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
                        class_name="grid grid-cols-2 gap-x-5 gap-y-10 lg:grid-cols-4 lg:gap-x-7",
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
        rx.el.p(
            "Catálogo demonstrativo · Fotos ilustrativas. Os produtos e valores apresentados não representam estoque real de um lojista.",
            class_name="mt-10 border-t border-[#deded3] pt-5 text-[11px] leading-relaxed text-[#7b827a]",
        ),
        id="catalogo",
        class_name="mx-auto w-full max-w-[1440px] scroll-mt-6 px-6 py-16 lg:px-12 lg:py-20",
    )
