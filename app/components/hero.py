import reflex as rx
from app.states.storefront_state import StorefrontState
from app.states.hero_state import HeroState


def hero_cta() -> rx.Component:
    return rx.el.a(
        "Explorar a coleção",
        rx.icon("arrow-up-right", class_name="h-4 w-4"),
        href="/#catalogo",
        on_click=StorefrontState.clear_filters,
        class_name="mt-7 flex min-h-11 w-fit items-center gap-7 border border-[#d4af37] bg-[#d4af37] px-6 py-3.5 text-xs font-semibold text-[#073238] transition-colors hover:bg-[#e1c25c] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#d4af37]",
    )


def brand_slide() -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.p(
                "VK VIKTRINE SHOP -",
                class_name="mb-6 text-xs font-semibold tracking-[0.2em] text-[#073238] sm:text-sm",
            ),
            rx.el.h1(
                "MAIS QUE PRODUTOS,",
                rx.el.br(),
                "É A SUA VITRENE.",
                class_name="max-w-[760px] font-['Cormorant_Garamond'] text-[42px] font-medium leading-[1.02] text-[#073238] sm:text-6xl lg:text-[76px] xl:text-[88px]",
            ),
            rx.el.p(
                "Tudo em um.",
                class_name="mt-5 font-['Cormorant_Garamond'] text-4xl italic text-[#0B4146] sm:text-5xl",
            ),
            hero_cta(),
            class_name="mx-auto flex min-h-[530px] w-full max-w-[1440px] flex-col justify-center px-6 py-12 sm:min-h-[570px] sm:px-12 lg:min-h-[610px] lg:px-20",
        ),
        id="vk-slide-0",
        role="group",
        aria_roledescription="slide",
        aria_label="1 de 2: VIKTRINE SHOP",
        aria_hidden=HeroState.active_slide != 0,
        inert=HeroState.active_slide != 0,
        class_name=rx.cond(
            HeroState.active_slide == 0,
            "vk-champagne-banner col-start-1 row-start-1 w-full opacity-100 transition-opacity duration-300 motion-reduce:transition-none",
            "vk-champagne-banner invisible col-start-1 row-start-1 w-full opacity-0 transition-opacity duration-300 motion-reduce:transition-none",
        ),
    )


def promotion_slide() -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                rx.icon("gift", class_name="h-5 w-5 text-[#d4af37]"),
                rx.el.span(
                    "UM CARINHO A MAIS PARA VOCÊ",
                    class_name="text-[10px] tracking-[0.18em] text-[#e7d49a]",
                ),
                class_name="mb-6 flex items-center gap-3",
            ),
            rx.el.h2(
                "SORTEIO MENSAL NO PIX!",
                class_name="max-w-[800px] font-['Cormorant_Garamond'] text-[44px] font-medium leading-[1.02] text-[#f5e9c9] sm:text-6xl lg:text-[76px]",
            ),
            rx.el.p(
                "Mensalmente ocorre um sorteio onde é escolhida a compra de uma pessoa que terá 20% do valor da compra devolvido no PIX!",
                class_name="mt-6 max-w-[650px] text-sm leading-7 text-[#faf9f4] sm:text-base",
            ),
            rx.el.p(
                "Regra essencial: O cliente precisa seguir a VIKTRINE em todas as redes sociais há mais de um mês para validar o prêmio.",
                class_name="mt-5 max-w-[650px] border-l-2 border-[#d4af37] bg-[#073238]/85 py-3 pl-4 pr-4 text-xs leading-6 text-[#f5e9c9] sm:text-sm",
            ),
            hero_cta(),
            class_name="mx-auto flex min-h-[530px] w-full max-w-[1440px] flex-col justify-center px-6 py-12 sm:min-h-[570px] sm:px-12 lg:min-h-[610px] lg:px-20",
        ),
        id="vk-slide-1",
        role="group",
        aria_roledescription="slide",
        aria_label="2 de 2: Sorteio mensal no PIX",
        aria_hidden=HeroState.active_slide != 1,
        inert=HeroState.active_slide != 1,
        class_name=rx.cond(
            HeroState.active_slide == 1,
            "vk-promotion-banner col-start-1 row-start-1 w-full opacity-100 transition-opacity duration-300 motion-reduce:transition-none",
            "vk-promotion-banner invisible col-start-1 row-start-1 w-full opacity-0 transition-opacity duration-300 motion-reduce:transition-none",
        ),
    )


def slide_dot(index: int) -> rx.Component:
    return rx.el.button(
        rx.el.span(
            class_name=rx.cond(
                HeroState.active_slide == index,
                "h-2 w-7 rounded-full bg-[#d4af37] transition-all motion-reduce:transition-none",
                "h-2 w-2 rounded-full bg-[#faf9f4]/50 transition-all motion-reduce:transition-none",
            )
        ),
        id=f"vk-slide-dot-{index}",
        type="button",
        aria_label=f"Mostrar banner {index + 1} de 2",
        aria_controls=f"vk-slide-{index}",
        aria_pressed=HeroState.active_slide == index,
        on_click=HeroState.select_slide(index),
        class_name="flex h-11 min-w-11 items-center justify-center bg-transparent text-[#faf9f4] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
    )


def category_tile(tile: dict[str, str]) -> rx.Component:
    return rx.el.a(
        rx.el.img(
            src=tile["photo"],
            alt=tile["alt"],
            loading="lazy",
            draggable=False,
            class_name="h-20 w-20 rounded-full bg-[#ece5d5] object-cover transition-transform group-hover:scale-105 motion-reduce:transition-none sm:h-24 sm:w-24 lg:h-28 lg:w-28",
        ),
        rx.el.span(
            tile["label"],
            class_name="mt-3 text-xs font-medium text-[#073238] sm:text-sm",
        ),
        href="/#catalogo",
        on_click=StorefrontState.choose_home_category(tile["label"]),
        class_name="group flex shrink-0 snap-start flex-col items-center px-2 py-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#8b7846]",
    )


def category_strip() -> rx.Component:
    return rx.el.nav(
        rx.el.div(
            rx.foreach(
                [
                    {
                        "label": "Camining",
                        "photo": "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=240&q=80",
                        "alt": "Moda e compras: inspiração para Camining",
                    },
                    {
                        "label": "Destaques",
                        "photo": "https://images.unsplash.com/photo-1445205170230-053b83016050?auto=format&fit=crop&w=240&q=80",
                        "alt": "Seleção de roupas em destaque",
                    },
                    {
                        "label": "Infantil",
                        "photo": "https://images.unsplash.com/photo-1519689680058-324335c77eba?auto=format&fit=crop&w=240&q=80",
                        "alt": "Bebê: inspiração para moda infantil",
                    },
                    {
                        "label": "Masculino",
                        "photo": "https://images.unsplash.com/photo-1617137968427-85924c800a22?auto=format&fit=crop&w=240&q=80",
                        "alt": "Look de moda masculina",
                    },
                    {
                        "label": "Vestidos",
                        "photo": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=240&q=80",
                        "alt": "Vestido em fotografia editorial",
                    },
                    {
                        "label": "Papaya",
                        "photo": "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=240&q=80&crop=faces",
                        "alt": "Inspiração de moda para Papaya, fotografia ilustrativa",
                    },
                    {
                        "label": "Makeup",
                        "photo": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=240&q=80",
                        "alt": "Produtos e acessórios de maquiagem",
                    },
                ],
                category_tile,
            ),
            class_name="mx-auto flex w-full max-w-[1100px] snap-x snap-proximity items-start justify-between gap-4 overflow-x-auto overscroll-x-contain px-6 py-6 sm:gap-6 sm:px-10 lg:py-8",
        ),
        aria_label="Explorar categorias no catálogo demonstrativo",
        class_name="w-full border-b border-[#d8d7cc] bg-[#faf9f4] text-[#073238]",
    )


def hero() -> rx.Component:
    return rx.fragment(
        rx.el.section(
            rx.el.div(
                brand_slide(),
                promotion_slide(),
                custom_attrs={"data-carousel-surface": "true"},
                class_name="grid w-full touch-pan-y select-none cursor-grab active:cursor-grabbing",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("chevron-left", class_name="h-5 w-5"),
                    id="vk-slide-previous",
                    type="button",
                    aria_label="Banner anterior",
                    aria_controls="vk-slide-0 vk-slide-1",
                    on_click=HeroState.previous_slide,
                    class_name="flex h-11 w-11 items-center justify-center rounded-full border border-[#d4af37]/50 bg-transparent text-[#faf9f4] hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
                rx.el.div(
                    rx.foreach([0, 1], slide_dot),
                    class_name="flex items-center gap-1",
                ),
                rx.el.button(
                    rx.icon("chevron-right", class_name="h-5 w-5"),
                    id="vk-slide-next",
                    type="button",
                    aria_label="Próximo banner",
                    aria_controls="vk-slide-0 vk-slide-1",
                    on_click=HeroState.next_slide,
                    class_name="flex h-11 w-11 items-center justify-center rounded-full border border-[#d4af37]/50 bg-transparent text-[#faf9f4] hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
                rx.el.span(
                    "Arraste ou use as setas",
                    class_name="ml-4 hidden text-[10px] tracking-wide text-[#faf9f4]/70 sm:inline",
                ),
                class_name="flex items-center justify-center gap-5 border-t border-[#d4af37]/20 bg-[#073238] px-6 py-3 text-[#faf9f4]",
            ),
            rx.el.p(
                rx.cond(
                    HeroState.active_slide == 0,
                    "Banner 1 de 2: VIKTRINE SHOP",
                    "Banner 2 de 2: Sorteio mensal no PIX",
                ),
                aria_live="polite",
                aria_atomic=True,
                class_name="sr-only",
            ),
            id="vk-home-carousel",
            role="region",
            aria_roledescription="carrossel",
            aria_label="Novidades VIKTRINE SHOP. Use as setas esquerda e direita, Home ou End para navegar.",
            tab_index=0,
            on_mount=HeroState.initialize_carousel,
            class_name="w-full bg-[#073238] text-[#faf9f4] focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[#d4af37]",
        ),
        category_strip(),
    )


def footer() -> rx.Component:
    return rx.el.footer(
        rx.el.div(
            rx.el.div(
                rx.el.a(
                    "VIKTRINE SHOP",
                    href="/",
                    class_name="font-['Cormorant_Garamond'] text-3xl font-semibold tracking-[0.12em] text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
                rx.el.p(
                    "Seu estilo começa nos detalhes.",
                    class_name="mt-3 text-xs text-[#b2bdaf]",
                ),
            ),
            rx.el.nav(
                rx.el.a(
                    "Explorar a coleção",
                    href="/#catalogo",
                    class_name="text-xs text-[#f5f1e8] hover:text-[#d4af37]",
                ),
                rx.el.a(
                    "Minha conta",
                    href="/minha-conta",
                    class_name="text-xs text-[#f5f1e8] hover:text-[#d4af37]",
                ),
                rx.el.a(
                    "Sacola",
                    href="/carrinho",
                    class_name="text-xs text-[#f5f1e8] hover:text-[#d4af37]",
                ),
                class_name="flex flex-wrap gap-6",
            ),
            class_name="flex flex-col justify-between gap-8 md:flex-row md:items-center",
        ),
        rx.el.p(
            "VIKTRINE SHOP · Vitrine demonstrativa de moda e acessórios. Fotos ilustrativas de Unsplash.",
            class_name="mt-9 border-t border-white/10 pt-5 text-[10px] leading-relaxed text-[#b2bdaf]",
        ),
        class_name="w-full bg-[var(--brand-petroleum-deep)] px-6 py-12 text-[#f5f1e8] lg:px-12",
    )
