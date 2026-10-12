import reflex as rx
from app.components.header import header
from app.components.hero import footer
from app.components.catalog import catalog
from app.states.storefront_state import StorefrontState
from app.states.cart_state import CartState


def marketplace_tabs(active: str) -> rx.Component:
    return rx.el.nav(
        rx.foreach(
            [
                {"name": "Amazon", "route": "/lojas/amazon"},
                {"name": "Shopee", "route": "/lojas/shopee"},
                {"name": "Mercado Livre", "route": "/lojas/mercado-livre"},
            ],
            lambda store: rx.el.a(
                store["name"],
                rx.icon(
                    "arrow-right",
                    aria_hidden=True,
                    class_name="h-4 w-4 shrink-0",
                ),
                href=store["route"],
                aria_current=rx.cond(active == store["name"], "page", "false"),
                key=store["route"],
                class_name=rx.cond(
                    active == store["name"],
                    "flex min-h-12 items-center justify-between gap-3 border-b-2 border-[#d4af37] bg-[#0B4146] px-5 py-4 text-sm font-medium text-[#faf9f4] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#8b7846]",
                    "flex min-h-12 items-center justify-between gap-3 border-b-2 border-transparent bg-[#f0ece1] px-5 py-4 text-sm font-medium text-[#0B4146] transition-colors hover:border-[#d4af37] hover:bg-[#e9e3d3] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#8b7846]",
                ),
            ),
        ),
        aria_label="Explorar páginas editoriais de lojas",
        class_name="mx-auto grid w-full max-w-[1440px] grid-cols-1 gap-2 px-6 py-6 sm:grid-cols-3 lg:px-12",
    )


def curated_category(item: dict[str, str]) -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.el.span(
                item["number"],
                class_name="font-['Cormorant_Garamond'] text-3xl text-[#8b7846]",
            ),
            rx.icon(
                "arrow-up-right",
                aria_hidden=True,
                class_name="h-5 w-5 text-[#0B4146] transition-transform group-hover:translate-x-1",
            ),
            class_name="flex items-center justify-between",
        ),
        rx.el.p(
            item["category"],
            class_name="mt-7 text-[10px] uppercase tracking-[0.18em] text-[#8b7846]",
        ),
        rx.el.h3(
            item["title"],
            class_name="mt-2 font-['Cormorant_Garamond'] text-3xl leading-tight text-[#073238]",
        ),
        rx.el.p(
            item["body"],
            class_name="mt-4 flex-1 text-sm leading-7 text-[#536059]",
        ),
        rx.el.span(
            f"Explorar {item['category']}",
            class_name="mt-7 w-fit border-b border-[#8b7846] pb-1 text-xs font-medium text-[#0B4146]",
        ),
        href="/#catalogo",
        on_click=[
            StorefrontState.clear_filters,
            StorefrontState.choose_category(item["category"]),
        ],
        key=item["category"],
        class_name="group flex h-full flex-col border border-[#ded9cb] bg-[#faf9f4] p-6 transition-colors hover:bg-[#f0ece1] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#8b7846] lg:p-8",
    )


def editorial_guide(
    title: str, body: str, tips: list[dict[str, str]]
) -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.p(
                "CADERNO DE ESTILO",
                class_name="text-[10px] tracking-[0.22em] text-[#8b7846]",
            ),
            rx.el.h2(
                title,
                class_name="mt-4 font-['Cormorant_Garamond'] text-4xl leading-tight text-[#073238] md:text-5xl",
            ),
            rx.el.p(body, class_name="mt-5 text-sm leading-7 text-[#536059]"),
            rx.el.a(
                "Ver toda a coleção demonstrativa",
                rx.icon("arrow-right", aria_hidden=True, class_name="h-4 w-4"),
                href="/#catalogo",
                on_click=StorefrontState.clear_filters,
                class_name="mt-7 flex w-fit items-center gap-3 border-b border-[#8b7846] pb-2 text-xs font-medium text-[#0B4146] hover:text-[#8b7846] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#8b7846]",
            ),
        ),
        rx.el.ol(
            rx.foreach(
                tips,
                lambda tip: rx.el.li(
                    rx.icon(
                        "check",
                        aria_hidden=True,
                        class_name="mt-1 h-4 w-4 shrink-0 text-[#8b7846]",
                    ),
                    rx.el.div(
                        rx.el.h3(
                            tip["title"],
                            class_name="text-sm font-semibold text-[#073238]",
                        ),
                        rx.el.p(
                            tip["body"],
                            class_name="mt-2 text-sm leading-7 text-[#536059]",
                        ),
                    ),
                    key=tip["title"],
                    class_name="flex gap-4 border-b border-[#ded9cb] py-5 first:pt-0 last:border-0 last:pb-0",
                ),
            ),
            class_name="flex flex-col",
        ),
        aria_label="Guia editorial de escolha",
        class_name="grid gap-10 border border-[#ded9cb] bg-[#f0ece1] p-6 md:grid-cols-2 lg:gap-16 lg:p-10",
    )


def marketplace_content(
    name: str,
    headline: str,
    intro: str,
    categories: list[dict[str, str]],
    guide_title: str,
    guide_body: str,
    tips: list[dict[str, str]],
) -> rx.Component:
    return rx.el.div(
        rx.el.a(
            "Ir para o conteúdo",
            href="#conteudo-loja",
            class_name="sr-only bg-[#d4af37] text-[#073238] focus:not-sr-only focus:block focus:p-3",
        ),
        header(),
        rx.el.main(
            rx.el.section(
                rx.el.div(
                    rx.el.nav(
                        rx.el.a(
                            "Início",
                            href="/",
                            class_name="text-[#e7dfcb] hover:text-[#d4af37]",
                        ),
                        rx.icon(
                            "chevron-right",
                            aria_hidden=True,
                            class_name="h-3 w-3 text-[#d4af37]",
                        ),
                        rx.el.span("Lojas", class_name="text-[#e7dfcb]"),
                        rx.icon(
                            "chevron-right",
                            aria_hidden=True,
                            class_name="h-3 w-3 text-[#d4af37]",
                        ),
                        rx.el.span(
                            name,
                            aria_current="page",
                            class_name="text-[#faf9f4]",
                        ),
                        aria_label="Caminho de navegação",
                        class_name="mb-10 flex flex-wrap items-center gap-2 text-xs",
                    ),
                    rx.el.p(
                        "VIKTRINE SHOP · PÁGINA EDITORIAL INDEPENDENTE",
                        class_name="text-[10px] leading-5 tracking-[0.2em] text-[#d4af37]",
                    ),
                    rx.el.div(
                        rx.el.div(
                            rx.el.h1(
                                name,
                                class_name="mt-4 font-['Cormorant_Garamond'] text-5xl font-medium leading-tight text-[#faf9f4] sm:text-6xl lg:text-7xl",
                            ),
                            rx.el.p(
                                headline,
                                class_name="mt-3 font-['Cormorant_Garamond'] text-3xl italic leading-tight text-[#e7dfcb] sm:text-4xl",
                            ),
                        ),
                        rx.el.div(
                            rx.el.p(
                                intro,
                                class_name="text-sm leading-7 text-[#e7dfcb]",
                            ),
                            rx.el.a(
                                "Explorar esta curadoria",
                                rx.icon(
                                    "arrow-down",
                                    aria_hidden=True,
                                    class_name="h-4 w-4",
                                ),
                                href="#curadoria",
                                class_name="mt-6 flex w-fit items-center gap-4 border border-[#d4af37] bg-[#d4af37] px-6 py-3 text-xs font-medium text-[#073238] hover:bg-[#e1c25c] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#d4af37]",
                            ),
                        ),
                        class_name="grid items-end gap-7 md:grid-cols-2 lg:gap-16",
                    ),
                    rx.el.p(
                        f"Este é um espaço interno da VIKTRINE SHOP dedicado ao tema {name}. Não é uma loja oficial, parceria ou integração com o marketplace.",
                        class_name="mt-9 border-t border-white/15 pt-5 text-xs leading-6 text-[#e7dfcb]",
                    ),
                    class_name="mx-auto w-full max-w-[1440px] px-6 py-10 lg:px-12 lg:py-14",
                ),
                id="conteudo-loja",
                class_name="w-full scroll-mt-6 bg-[#0B4146] text-[#faf9f4]",
            ),
            marketplace_tabs(name),
            rx.el.div(
                rx.el.aside(
                    rx.icon(
                        "info",
                        aria_hidden=True,
                        class_name="mt-0.5 h-4 w-4 shrink-0 text-[#8b7846]",
                    ),
                    rx.el.p(
                        f"Links e anúncios do {name} ainda não foram configurados. As categorias e os produtos abaixo pertencem apenas ao catálogo demonstrativo da VIKTRINE SHOP; a sacola não envia pedidos ao marketplace.",
                        class_name="text-xs leading-6 text-[#536059]",
                    ),
                    class_name="mb-12 flex gap-3 border border-[#ded9cb] bg-[#f0ece1] px-5 py-4",
                ),
                rx.el.section(
                    rx.el.p(
                        "ESCOLHA O SEU PONTO DE PARTIDA",
                        class_name="text-[10px] tracking-[0.22em] text-[#8b7846]",
                    ),
                    rx.el.h2(
                        "Uma curadoria, várias possibilidades",
                        class_name="mt-3 font-['Cormorant_Garamond'] text-4xl text-[#073238] md:text-5xl",
                    ),
                    rx.el.p(
                        "Atalhos para as categorias da nossa vitrine. Cada escolha abre o catálogo interno com o filtro correspondente.",
                        class_name="mt-4 text-sm leading-7 text-[#536059]",
                    ),
                    rx.el.div(
                        rx.foreach(categories, curated_category),
                        class_name="mt-8 grid grid-cols-1 gap-5 md:grid-cols-3",
                    ),
                    id="curadoria",
                    class_name="mb-12 scroll-mt-6",
                ),
                editorial_guide(guide_title, guide_body, tips),
                class_name="mx-auto w-full max-w-[1440px] px-6 pt-4 lg:px-12",
            ),
            catalog(),
            class_name="min-w-0 w-full max-w-[100vw] overflow-x-hidden bg-[#faf9f4] text-[#073238]",
        ),
        footer(),
        on_mount=[StorefrontState.load_catalog, CartState.load_cart],
        class_name="min-h-dvh w-full max-w-[100vw] overflow-x-hidden bg-[#faf9f4] font-['Inter'] text-[#073238]",
    )
