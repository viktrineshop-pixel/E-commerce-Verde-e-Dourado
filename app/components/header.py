import reflex as rx
from app.states.storefront_state import StorefrontState
from app.states.cart_state import CartState


def category_link(label: str) -> rx.Component:
    return rx.el.a(
        label,
        href="/#catalogo",
        on_click=StorefrontState.choose_category(label),
        class_name="block whitespace-nowrap px-4 py-3 text-sm text-[#f5f1e8] transition-colors hover:text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
    )


def pending_social(label: str, icon: str) -> rx.Component:
    return rx.el.span(
        rx.icon(
            icon,
            aria_hidden=True,
            class_name="h-3.5 w-3.5 shrink-0 text-[#d4af37]",
        ),
        label,
        aria_disabled=True,
        aria_label=f"{label}: em breve, aguardando link oficial",
        title="Em breve · aguardando link oficial",
        class_name="inline-flex cursor-default items-center gap-1.5 whitespace-nowrap text-[#f5f1e8]",
    )


def utility_bar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                pending_social("Facebook", "share"),
                pending_social("Instagram", "camera"),
                pending_social("YouTube", "play"),
                rx.el.span("Em breve", class_name="text-[9px] text-[#d6cda9]"),
                aria_label="Redes sociais · links oficiais em breve",
                class_name="flex flex-wrap items-center justify-center gap-x-4 gap-y-2",
            ),
            rx.el.div(
                rx.el.span(
                    rx.icon(
                        "info",
                        aria_hidden=True,
                        class_name="h-3.5 w-3.5 shrink-0 text-[#d4af37]",
                    ),
                    rx.el.span(
                        rx.el.strong(
                            "Compra Segura",
                            class_name="font-medium text-[#f5f1e8]",
                        ),
                        " · demonstração, sem pagamentos",
                    ),
                    class_name="flex items-center gap-1.5 text-[#d6cda9]",
                ),
                rx.el.span(
                    rx.icon(
                        "truck",
                        aria_hidden=True,
                        class_name="h-3.5 w-3.5 shrink-0 text-[#d4af37]",
                    ),
                    "Entrega · não realizada nesta demonstração",
                    class_name="flex items-center gap-1.5 text-[#d6cda9]",
                ),
                rx.el.span(
                    rx.icon(
                        "message-circle",
                        aria_hidden=True,
                        class_name="h-3.5 w-3.5 shrink-0 text-[#d4af37]",
                    ),
                    "Grupo do WhatsApp · em breve",
                    aria_disabled=True,
                    title="Aguardando link oficial do grupo",
                    class_name="flex cursor-default items-center gap-1.5 text-[#f5f1e8]",
                ),
                class_name="flex flex-wrap items-center justify-center gap-x-5 gap-y-2",
            ),
            class_name="mx-auto flex w-full max-w-[1440px] flex-col items-center justify-between gap-2 px-4 py-2.5 text-center text-[10px] leading-relaxed tracking-wide lg:px-12 xl:flex-row xl:text-left",
        ),
        class_name="w-full border-b border-[#d4af37]/20 bg-[var(--brand-petroleum-deep)] text-[#f5f1e8]",
    )


def stores_menu() -> rx.Component:
    return rx.el.details(
        rx.el.summary(
            "Lojas",
            rx.icon(
                "chevron-down",
                aria_hidden=True,
                class_name="h-3.5 w-3.5 transition-transform group-open:rotate-180",
            ),
            class_name="flex cursor-pointer list-none items-center gap-2 px-4 py-3 text-sm text-[#f5f1e8] hover:text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37] [&::-webkit-details-marker]:hidden",
        ),
        rx.el.div(
            rx.el.p(
                "NOSSAS LOJAS",
                class_name="px-4 pt-2 pb-1 text-[9px] tracking-[0.18em] text-[#d4af37]",
            ),
            rx.foreach(
                [
                    {"label": "Amazon", "href": "/lojas/amazon"},
                    {"label": "Shopee", "href": "/lojas/shopee"},
                    {"label": "Mercado Livre", "href": "/lojas/mercado-livre"},
                ],
                lambda store: rx.el.a(
                    store["label"],
                    rx.icon(
                        "arrow-up-right",
                        aria_hidden=True,
                        class_name="h-3.5 w-3.5",
                    ),
                    href=store["href"],
                    key=store["href"],
                    class_name="flex items-center justify-between gap-4 whitespace-nowrap px-4 py-3 text-sm text-[#f5f1e8] hover:bg-white/5 hover:text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
            ),
            class_name="z-30 w-full border border-[#d4af37]/25 bg-[var(--brand-petroleum)] p-2 md:absolute md:left-0 md:top-full md:w-56",
        ),
        class_name="group relative",
    )


def header() -> rx.Component:
    return rx.el.header(
        utility_bar(),
        rx.el.div(
            rx.el.a(
                "VIKTRINE SHOP",
                href="/",
                class_name="shrink-0 whitespace-nowrap font-['Cormorant_Garamond'] text-xl font-semibold tracking-[0.1em] text-[#d4af37] sm:text-3xl md:text-4xl focus-visible:outline-2 focus-visible:outline-[#d4af37]",
            ),
            rx.el.div(
                rx.icon(
                    "search",
                    class_name="pointer-events-none absolute left-4 top-3.5 h-4 w-4 text-[#c9c9bb]",
                ),
                rx.el.input(
                    placeholder="O que você está procurando?",
                    aria_label="Buscar produtos",
                    default_value=StorefrontState.search,
                    on_change=StorefrontState.set_search.debounce(500),
                    class_name="w-full rounded-sm border border-white/20 bg-white/5 py-3 pr-4 pl-11 text-sm text-[#f5f1e8] placeholder:text-[#c9c9bb] focus:border-[#d4af37] focus:outline-hidden",
                ),
                class_name="relative order-3 w-full md:order-none md:min-w-0 md:flex-1 md:max-w-lg",
            ),
            rx.el.div(
                rx.el.a(
                    rx.icon("user-round", class_name="h-5 w-5"),
                    rx.el.span("Minha conta", class_name="hidden lg:inline"),
                    href="/minha-conta",
                    aria_label="Minha conta",
                    class_name="flex items-center gap-2 text-sm text-[#f5f1e8] hover:text-[#d4af37]",
                ),
                rx.el.a(
                    rx.icon("shopping-bag", class_name="h-5 w-5"),
                    rx.el.span("Sacola", class_name="hidden lg:inline"),
                    rx.el.span(
                        CartState.count,
                        aria_live="polite",
                        class_name="flex h-5 min-w-5 items-center justify-center rounded-full bg-[#d4af37] px-1 text-[10px] font-semibold text-[#05120e]",
                    ),
                    href="/carrinho",
                    aria_label=f"Abrir carrinho com {CartState.count} unidades",
                    class_name="flex items-center gap-2 text-sm text-[#f5f1e8] hover:text-[#d4af37]",
                ),
                rx.el.button(
                    rx.icon("menu", class_name="h-5 w-5"),
                    on_click=StorefrontState.toggle_menu,
                    aria_label="Abrir ou fechar menu",
                    aria_expanded=StorefrontState.mobile_menu,
                    aria_controls="mobile-navigation",
                    type="button",
                    class_name="p-2 text-[#f5f1e8] hover:text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37] md:hidden",
                ),
                class_name="ml-auto flex items-center gap-2 sm:gap-5",
            ),
            class_name="mx-auto flex w-full max-w-[1440px] flex-wrap items-center justify-between gap-3 px-4 py-6 sm:gap-6 sm:px-6 lg:px-12",
        ),
        rx.el.nav(
            stores_menu(),
            rx.el.details(
                rx.el.summary(
                    "Categorias",
                    rx.icon("chevron-down", class_name="h-3.5 w-3.5"),
                    class_name="flex cursor-pointer list-none items-center gap-2 px-4 py-3 text-sm text-[#f5f1e8] hover:text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37] [&::-webkit-details-marker]:hidden",
                ),
                rx.el.div(
                    rx.foreach(
                        [
                            "Feminino",
                            "Masculino",
                            "Acessórios",
                            "Novidades",
                            "Promoções",
                        ],
                        category_link,
                    ),
                    class_name="absolute left-0 top-full z-30 w-52 border border-[#d4af37]/25 bg-[var(--brand-petroleum)] p-2",
                ),
                class_name="relative",
            ),
            rx.foreach(
                [
                    "Feminino",
                    "Masculino",
                    "Acessórios",
                    "Novidades",
                    "Promoções",
                ],
                category_link,
            ),
            class_name="hidden justify-center gap-0 border-t border-white/10 bg-[var(--brand-petroleum)] md:flex lg:gap-6",
            aria_label="Lojas e categorias",
        ),
        rx.cond(
            StorefrontState.mobile_menu,
            rx.el.nav(
                stores_menu(),
                rx.foreach(
                    [
                        "Feminino",
                        "Masculino",
                        "Acessórios",
                        "Novidades",
                        "Promoções",
                    ],
                    category_link,
                ),
                class_name="flex flex-col border-t border-white/10 bg-[var(--brand-petroleum)] px-3 pb-3 md:hidden",
                id="mobile-navigation",
                aria_label="Menu móvel",
            ),
        ),
        class_name="relative z-20 w-full bg-[var(--brand-petroleum)] text-[#f5f1e8]",
    )
