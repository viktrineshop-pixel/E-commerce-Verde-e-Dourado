import reflex as rx
from app.states.storefront_state import StorefrontState
from app.states.hero_state import HeroState
from app.states.admin_state import AdminState
from app.states.favorite_state import FavoriteState


def category_link(label: str) -> rx.Component:
    return rx.el.a(
        label,
        href="/#catalogo",
        on_click=StorefrontState.choose_category(label),
        class_name="block whitespace-nowrap px-4 py-2 text-sm text-[#f5f1e8] transition-colors hover:text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
    )


def pending_social(label: str, icon: str) -> rx.Component:
    return rx.el.span(
        rx.icon(
            icon,
            aria_hidden=True,
            class_name="h-[9.1px] w-[9.1px] shrink-0 text-[#d4af37]",
        ),
        label,
        aria_disabled=True,
        aria_label=f"{label}: aguardando link oficial",
        title="Aguardando link oficial",
        class_name="inline-flex cursor-default items-center gap-[5.2px] whitespace-nowrap text-[#f5f1e8]",
    )


def utility_bar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                pending_social("Facebook", "share"),
                pending_social("Instagram", "camera"),
                pending_social("YouTube", "play"),
                aria_label="Redes sociais · aguardando link oficial",
                class_name="flex flex-wrap items-center justify-center gap-x-[15.6px] gap-y-[2.6px]",
            ),
            rx.el.div(
                rx.el.span(
                    rx.icon(
                        "info",
                        aria_hidden=True,
                        class_name="h-[9.1px] w-[9.1px] shrink-0 text-[#d4af37]",
                    ),
                    rx.el.span(
                        rx.el.strong(
                            "Descoberta de ofertas",
                            class_name="font-medium text-[#f5f1e8]",
                        ),
                        " · compras nas lojas externas",
                    ),
                    class_name="flex items-center gap-[5.2px] text-[#d6cda9]",
                ),
                rx.el.span(
                    rx.icon(
                        "external-link",
                        aria_hidden=True,
                        class_name="h-[9.1px] w-[9.1px] shrink-0 text-[#d4af37]",
                    ),
                    "Preços observados · sem integração ao vivo",
                    class_name="flex items-center gap-[5.2px] text-[#d6cda9]",
                ),
                rx.el.span(
                    rx.icon(
                        "message-circle",
                        aria_hidden=True,
                        class_name="h-[9.1px] w-[9.1px] shrink-0 text-[#d4af37]",
                    ),
                    "Grupo do WhatsApp",
                    aria_disabled=True,
                    aria_label="Grupo do WhatsApp: aguardando link oficial",
                    title="Aguardando link oficial do grupo",
                    class_name="flex cursor-default items-center gap-[5.2px] text-[#f5f1e8]",
                ),
                class_name="flex flex-wrap items-center justify-center gap-x-[20.8px] gap-y-[2.6px]",
            ),
            class_name="mx-auto flex w-full max-w-[1440px] flex-col items-center justify-between gap-[5.2px] px-3 py-[5.2px] text-center text-[6.5px] leading-tight tracking-wide lg:px-12 xl:flex-row xl:text-left",
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
            class_name="flex cursor-pointer list-none items-center gap-2 px-4 py-2 text-sm text-[#f5f1e8] hover:text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37] [&::-webkit-details-marker]:hidden",
        ),
        rx.el.div(
            rx.el.p(
                "PÁGINAS EDITORIAIS INDEPENDENTES",
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
                    class_name="flex items-center justify-between gap-4 whitespace-nowrap px-4 py-2 text-sm text-[#f5f1e8] hover:bg-white/5 hover:text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
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
            rx.el.div(
                rx.el.a(
                    rx.el.span(
                        "Viktrine",
                        class_name="block text-center leading-[0.82]",
                    ),
                    href="/",
                    aria_label="Viktrine — página inicial",
                    class_name="shrink-0 font-['Cormorant_Garamond'] text-xl font-medium tracking-[0.1em] text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37] sm:text-2xl md:text-3xl",
                ),
                rx.el.a(
                    rx.icon(
                        "house",
                        class_name="h-[18.4px] w-[18.4px] text-[#d4af37]",
                    ),
                    href="/",
                    aria_label="Página inicial",
                    class_name="flex min-h-9 min-w-7 items-center justify-center text-[#d4af37] hover:text-[#e1c25c] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
                class_name="col-start-2 row-start-1 flex shrink-0 items-center justify-center gap-1 justify-self-center md:col-start-1 md:justify-self-start",
            ),
            rx.el.div(
                rx.icon(
                    "search",
                    class_name="pointer-events-none absolute left-4 top-3.5 h-4 w-4 text-[#c9c9bb]",
                ),
                rx.el.input(
                    placeholder="Qual achadinho você está procurando?",
                    aria_label="Buscar produtos",
                    default_value=StorefrontState.search,
                    on_change=StorefrontState.set_search.debounce(500),
                    class_name="min-w-0 w-full max-w-full rounded-sm border border-white/20 bg-white/5 py-2 pr-4 pl-11 text-sm text-[#f5f1e8] placeholder:text-[#c9c9bb] focus:border-[#d4af37] focus:outline-hidden",
                ),
                class_name="relative col-span-3 row-start-2 min-w-0 w-full max-w-full md:col-span-1 md:col-start-2 md:row-start-1 md:justify-self-center",
            ),
            rx.el.div(
                rx.el.a(
                    rx.icon("user-round", class_name="h-5 w-5 text-[#d4af37]"),
                    rx.el.span("Minha conta", class_name="hidden lg:inline"),
                    href="/minha-conta",
                    aria_label="Minha conta",
                    class_name="flex items-center gap-2 text-sm text-[#f5f1e8] hover:text-[#d4af37]",
                ),
                rx.cond(
                    AdminState.can_manage,
                    rx.el.a(
                        rx.icon("package", class_name="h-5 w-5 text-[#d4af37]"),
                        rx.el.span("Admin", class_name="hidden lg:inline"),
                        href="/admin",
                        aria_label="Administrar produtos",
                        class_name="flex min-h-9 items-center gap-2 text-sm text-[#f5f1e8] hover:text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                    ),
                ),
                rx.el.a(
                    rx.icon("search", class_name="h-5 w-5 text-[#d4af37]"),
                    rx.el.span("Descobrir", class_name="hidden lg:inline"),
                    href="/#vk-home-carousel",
                    on_click=HeroState.select_slide(2),
                    aria_label="Como comparar ofertas no terceiro banner",
                    class_name="flex min-h-9 items-center gap-2 text-sm text-[#f5f1e8] hover:text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
                rx.el.button(
                    rx.icon("menu", class_name="h-5 w-5"),
                    on_click=StorefrontState.toggle_menu,
                    aria_label="Abrir ou fechar menu",
                    aria_expanded=StorefrontState.mobile_menu,
                    aria_controls="mobile-navigation",
                    type="button",
                    class_name="p-1.5 text-[#f5f1e8] hover:text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37] md:hidden",
                ),
                class_name="col-start-3 row-start-1 ml-auto flex items-center gap-1.5 justify-self-end sm:gap-3 md:col-start-3 md:gap-2 lg:gap-4",
            ),
            class_name="mx-auto grid w-full max-w-[1440px] grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-x-2 gap-y-2 px-4 py-2 sm:px-6 md:grid-cols-[minmax(0,1fr)_minmax(0,1.5fr)_minmax(0,1fr)] md:gap-x-5 md:gap-y-0 md:px-6 md:py-2 lg:px-12",
        ),
        rx.el.nav(
            stores_menu(),
            rx.el.details(
                rx.el.summary(
                    "Categorias",
                    rx.icon("chevron-down", class_name="h-3.5 w-3.5"),
                    class_name="flex cursor-pointer list-none items-center gap-2 px-4 py-2 text-sm text-[#f5f1e8] hover:text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37] [&::-webkit-details-marker]:hidden",
                ),
                rx.el.div(
                    rx.foreach(
                        StorefrontState.categories,
                        category_link,
                    ),
                    class_name="absolute left-0 top-full z-30 w-52 border border-[#d4af37]/25 bg-[var(--brand-petroleum)] p-2",
                ),
                class_name="relative",
            ),
            rx.foreach(
                StorefrontState.categories,
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
                    StorefrontState.categories,
                    category_link,
                ),
                class_name="flex flex-col border-t border-white/10 bg-[var(--brand-petroleum)] px-3 pb-3 md:hidden",
                id="mobile-navigation",
                aria_label="Menu móvel",
            ),
        ),
        on_mount=[
            AdminState.load_role,
            FavoriteState.sync_auth,
            StorefrontState.load_catalog,
        ],
        class_name="relative z-20 w-full bg-[var(--brand-petroleum)] text-[#f5f1e8]",
    )
