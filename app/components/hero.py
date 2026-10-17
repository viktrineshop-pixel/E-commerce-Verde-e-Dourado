import reflex as rx
from app.states.storefront_state import StorefrontState
from app.states.hero_state import HeroState


def hero_cta(label: str = "Explorar a coleção") -> rx.Component:
    return rx.el.a(
        label,
        rx.icon("arrow-up-right", class_name="h-4 w-4"),
        href="/#catalogo",
        on_click=StorefrontState.clear_filters,
        class_name="mt-4 flex min-h-10 w-fit items-center gap-3 border border-[#d4af37] bg-[#d4af37] px-4 py-2 text-[11px] font-semibold text-[#073238] transition-colors hover:bg-[#e1c25c] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#d4af37]",
    )


def brand_slide() -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.p(
                "SEU PRÓXIMO ACHADINHO ESTÁ AQUI",
                class_name="mb-2 font-['Inter'] text-[9px] font-semibold tracking-[0.08em] text-[#073238] sm:text-xs sm:tracking-[0.2em]",
            ),
            rx.el.h1(
                "Descubra o que combina com você.",
                class_name="max-w-[760px] font-['Cormorant_Garamond'] text-[30px] font-medium leading-[1.02] text-[#073238] sm:text-4xl lg:text-5xl",
            ),
            rx.el.p(
                "Produtos, novidades e oportunidades para encontrar o que você procura.",
                class_name="mt-2 max-w-[680px] font-['Cormorant_Garamond'] text-xl italic leading-tight text-[#0B4146] sm:text-3xl",
            ),
            rx.el.div(
                rx.el.a(
                    "↓ Explorar achadinhos ↓",
                    href="/#catalogo",
                    on_click=StorefrontState.clear_filters,
                    class_name="mt-4 flex min-h-10 w-fit items-center border border-[#d4af37] bg-[#d4af37] px-4 py-2 font-['Inter'] text-[11px] font-semibold text-[#073238] transition-colors hover:bg-[#e1c25c] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#d4af37]",
                ),
                class_name="flex w-full justify-center",
            ),
            class_name="mx-auto flex h-[283.5px] max-h-[283.5px] w-full max-w-[1440px] flex-col justify-start overflow-y-auto px-5 pt-5 pb-3 sm:h-[315px] sm:max-h-[315px] sm:justify-center sm:px-8 sm:py-4 lg:px-12",
        ),
        id="vk-slide-0",
        role="group",
        aria_roledescription="slide",
        aria_label="1 de 3: VIKTRINE SHOP",
        aria_hidden=HeroState.active_slide != 0,
        inert=HeroState.active_slide != 0,
        class_name=rx.cond(
            HeroState.active_slide == 0,
            "vk-champagne-banner col-start-1 row-start-1 h-[315px] max-h-[315px] w-full opacity-100 transition-opacity duration-300 motion-reduce:transition-none",
            "vk-champagne-banner invisible col-start-1 row-start-1 h-[315px] max-h-[315px] w-full opacity-0 transition-opacity duration-300 motion-reduce:transition-none",
        ),
    )


def whatsapp_slide() -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                rx.icon("messages-square", class_name="h-5 w-5 text-[#d4af37]"),
                rx.el.span(
                    "NOVIDADES EM PRIMEIRA MÃO",
                    class_name="text-[9px] tracking-[0.14em] text-[#e7d49a] sm:text-[10px]",
                ),
                class_name="mb-2 flex items-center gap-2",
            ),
            rx.el.h2(
                "Acessar o grupo WhatsApp para inscritos",
                class_name="w-full max-w-full font-['Cormorant_Garamond'] text-[28px] font-medium leading-[1.02] text-[#f5e9c9] sm:max-w-[720px] sm:text-4xl lg:text-5xl",
            ),
            rx.el.p(
                "Um espaço para receber novidades, oportunidades e comunicados especiais da VIKTRINE SHOP.",
                class_name="mt-3 w-full max-w-full text-xs leading-5 text-[#faf9f4] sm:max-w-[620px] sm:text-sm",
            ),
            rx.el.div(
                rx.icon("clock-3", class_name="h-4 w-4"),
                rx.el.span(
                    "Link oficial pendente — em breve",
                    class_name="text-xs font-semibold sm:text-sm",
                ),
                class_name="mt-4 flex w-fit max-w-full items-center gap-2 border border-[#d4af37]/70 bg-[#073238]/80 px-3 py-2 text-[#f5e9c9]",
            ),
            class_name="mx-auto flex h-[315px] max-h-[315px] w-full min-w-0 max-w-full flex-col justify-center overflow-y-auto px-5 py-4 sm:px-8 sm:py-4 lg:px-12",
        ),
        id="vk-slide-1",
        role="group",
        aria_roledescription="slide",
        aria_label="2 de 3: Grupo WhatsApp para inscritos, link oficial em breve",
        aria_hidden=HeroState.active_slide != 1,
        inert=HeroState.active_slide != 1,
        class_name=rx.cond(
            HeroState.active_slide == 1,
            "vk-whatsapp-banner col-start-1 row-start-1 h-[315px] max-h-[315px] w-full opacity-100 transition-opacity duration-300 motion-reduce:transition-none",
            "vk-whatsapp-banner invisible col-start-1 row-start-1 h-[315px] max-h-[315px] w-full opacity-0 transition-opacity duration-300 motion-reduce:transition-none",
        ),
    )


def promotion_slide() -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                rx.icon("gift", class_name="h-5 w-5 text-[#d4af37]"),
                rx.el.span(
                    "UM CARINHO A MAIS PARA VOCÊ",
                    class_name="text-[9px] tracking-[0.14em] text-[#e7d49a] sm:text-[10px]",
                ),
                class_name="mb-2 flex items-center gap-2",
            ),
            rx.el.h2(
                "SORTEIO MENSAL NO PIX!",
                class_name="max-w-[800px] font-['Cormorant_Garamond'] text-[28px] font-medium leading-[1.02] text-[#f5e9c9] sm:text-4xl lg:text-5xl",
            ),
            rx.el.p(
                "Mensalmente ocorre um sorteio onde é escolhida a compra de uma pessoa que terá 20% do valor da compra devolvido no PIX!",
                class_name="mt-2 max-w-[650px] text-xs leading-[1.15rem] text-[#faf9f4] sm:text-sm sm:leading-5",
            ),
            rx.el.p(
                "Regra essencial: O cliente precisa seguir a VIKTRINE em todas as redes sociais há mais de um mês para validar o prêmio.",
                class_name="mt-2 max-w-[650px] border-l-2 border-[#d4af37] bg-[#073238]/85 py-2 pl-3 pr-3 text-[10px] leading-[1.05rem] text-[#f5e9c9] sm:text-xs sm:leading-5",
            ),
            rx.el.p(
                "A lista mensal será publicada aqui quando estiver disponível. Aguardem a divulgação oficial.",
                class_name="mt-2 w-fit border border-[#d4af37]/70 bg-[#073238]/85 px-3 py-2 text-[10px] font-semibold leading-4 text-[#f5e9c9] sm:text-xs",
            ),
            hero_cta(),
            class_name="mx-auto flex h-[315px] max-h-[315px] w-full max-w-[1440px] flex-col justify-start overflow-y-auto px-5 pt-3 pb-5 sm:px-8 sm:pt-3 sm:pb-5 lg:px-12",
        ),
        id="vk-slide-2",
        role="group",
        aria_roledescription="slide",
        aria_label="3 de 3: Sorteio mensal no PIX; lista pendente de publicação",
        aria_hidden=HeroState.active_slide != 2,
        inert=HeroState.active_slide != 2,
        class_name=rx.cond(
            HeroState.active_slide == 2,
            "vk-promotion-banner col-start-1 row-start-1 h-[315px] max-h-[315px] w-full opacity-100 transition-opacity duration-300 motion-reduce:transition-none",
            "vk-promotion-banner invisible col-start-1 row-start-1 h-[315px] max-h-[315px] w-full opacity-0 transition-opacity duration-300 motion-reduce:transition-none",
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
        aria_label=f"Mostrar banner {index + 1} de 3",
        aria_controls=f"vk-slide-{index}",
        aria_pressed=HeroState.active_slide == index,
        on_click=[
            rx.call_script(
                "window.__vkScheduleCarousel && window.__vkScheduleCarousel(15000);"
            ),
            HeroState.select_slide(index),
        ],
        class_name="flex h-11 min-w-11 items-center justify-center bg-transparent text-[#faf9f4] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
    )


def category_tile(tile: dict[str, str]) -> rx.Component:
    return rx.el.a(
        rx.el.span(
            tile["monogram"],
            aria_hidden=True,
            class_name="flex h-[72px] w-[72px] shrink-0 items-center justify-center rounded-full border border-[#d4af37] bg-[#0B4146] font-['Cormorant_Garamond'] text-2xl font-semibold text-[#d4af37] transition-colors group-hover:bg-[#12545a] motion-reduce:transition-none sm:h-24 sm:w-24 sm:text-3xl lg:h-28 lg:w-28",
        ),
        rx.el.span(
            tile["label"],
            class_name="mt-2 min-h-8 w-full text-center font-['Inter'] text-[10px] font-medium leading-4 text-[#faf9f4] sm:text-xs",
        ),
        href=tile["href"],
        aria_label=f"Acessar página editorial de {tile['label']}",
        class_name=rx.cond(
            tile["label"] == "Shopee",
            "group mr-2 flex w-[72px] shrink-0 flex-col items-center rounded-sm py-1 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#d4af37] sm:mr-4 sm:w-24 lg:w-28",
            "group flex w-[72px] shrink-0 flex-col items-center rounded-sm py-1 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#d4af37] sm:w-24 lg:w-28",
        ),
    )


def recommendation_social(label: str, kind: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                rx.match(
                    kind,
                    (
                        "youtube",
                        rx.icon(
                            "play",
                            class_name="h-7 w-7 fill-[#d4af37] text-[#d4af37] sm:h-9 sm:w-9",
                        ),
                    ),
                    (
                        "whatsapp",
                        rx.el.span(
                            rx.icon(
                                "message-circle",
                                class_name="h-9 w-9 text-[#d4af37] sm:h-12 sm:w-12",
                            ),
                            rx.icon(
                                "phone",
                                class_name="absolute left-1/2 top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 text-[#d4af37] sm:h-5 sm:w-5",
                            ),
                            class_name="relative inline-flex items-center justify-center",
                        ),
                    ),
                    (
                        "instagram",
                        rx.icon(
                            "camera",
                            class_name="h-8 w-8 text-[#d4af37] sm:h-11 sm:w-11",
                        ),
                    ),
                    (
                        "facebook",
                        rx.el.span(
                            "f",
                            class_name="font-['Inter'] text-4xl font-bold leading-none text-[#d4af37] sm:text-5xl",
                        ),
                    ),
                    rx.icon(
                        "mail",
                        class_name="h-8 w-8 text-[#d4af37] sm:h-11 sm:w-11",
                    ),
                ),
                aria_hidden=True,
                class_name=rx.match(
                    kind,
                    (
                        "youtube",
                        "flex h-[43.2px] w-[64.8px] shrink-0 items-center justify-center rounded-xl border border-[#d4af37]/70 bg-[#0B4146]/50 sm:h-[57.6px] sm:w-[86.4px] lg:h-[67.2px] lg:w-[100.8px]",
                    ),
                    (
                        "whatsapp",
                        "flex h-[64.8px] w-[64.8px] shrink-0 items-center justify-center rounded-full border border-[#d4af37]/70 bg-[#0B4146]/50 sm:h-[86.4px] sm:w-[86.4px] lg:h-[100.8px] lg:w-[100.8px]",
                    ),
                    "flex h-[64.8px] w-[64.8px] shrink-0 items-center justify-center rounded-2xl border border-[#d4af37]/70 bg-[#0B4146]/50 sm:h-[86.4px] sm:w-[86.4px] lg:h-[100.8px] lg:w-[100.8px]",
                ),
            ),
            class_name="flex h-[72px] w-full items-center justify-center sm:h-24 lg:h-28",
        ),
        rx.el.span(
            label,
            class_name="mt-2 min-h-8 w-full text-center font-['Inter'] text-[10px] font-medium leading-4 text-[#faf9f4] sm:text-xs",
        ),
        rx.el.span(
            "Link pendente",
            class_name="text-center font-['Inter'] text-[9px] leading-4 text-[#e7d49a]",
        ),
        role="group",
        aria_disabled=True,
        aria_label=f"{label}: aguardando link oficial",
        title=f"{label}: aguardando link oficial",
        class_name="flex w-[72px] shrink-0 cursor-not-allowed flex-col items-center py-1 sm:w-24 lg:w-28",
    )


def category_strip() -> rx.Component:
    return rx.el.nav(
        rx.el.h2(
            "Nossas Recomendações",
            class_name="text-center font-['Cormorant_Garamond'] text-xl font-medium text-[#d4af37] sm:text-2xl",
        ),
        rx.el.div(
            rx.foreach(
                [
                    {
                        "label": "Amazon",
                        "monogram": "A",
                        "href": "/lojas/amazon",
                    },
                    {
                        "label": "Mercado Livre",
                        "monogram": "ML",
                        "href": "/lojas/mercado-livre",
                    },
                    {
                        "label": "Shopee",
                        "monogram": "S",
                        "href": "/lojas/shopee",
                    },
                ],
                category_tile,
            ),
            recommendation_social("YouTube vitrine", "youtube"),
            recommendation_social("WhatsApp Viktrine", "whatsapp"),
            recommendation_social("Instagram vitrine", "instagram"),
            recommendation_social("Facebook", "facebook"),
            recommendation_social("E-mail vitrine", "email"),
            id="vk-recommendations-scroll",
            role="region",
            aria_label="Lojas parceiras e redes sociais. Role para a direita para ver as redes sociais.",
            aria_describedby="vk-recommendations-hint",
            tab_index=0,
            overflow_x="scroll",
            class_name="mx-auto mt-2 flex w-[240px] max-w-full flex-nowrap items-start gap-2 overflow-x-scroll overscroll-x-contain touch-pan-x px-1 py-2 [scrollbar-color:#d4af37_#073238] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#d4af37] sm:w-[328px] sm:gap-4 lg:w-[376px]",
        ),
        rx.el.p(
            rx.icon(
                "move-horizontal",
                aria_hidden=True,
                class_name="h-4 w-4 shrink-0 text-[#d4af37]",
            ),
            "Deslize para ver as redes sociais →",
            id="vk-recommendations-hint",
            class_name="mt-2 flex items-center justify-center gap-2 font-['Inter'] text-[10px] text-[#faf9f4] sm:text-xs",
        ),
        rx.el.p(
            "Com a faixa em foco, use as setas do teclado. Redes sociais aguardando link oficial.",
            class_name="mt-1 text-center font-['Inter'] text-[9px] leading-4 text-[#e7d49a] sm:text-[10px]",
        ),
        id="lojas-parceiras",
        aria_label="Nossas recomendações de lojas e redes sociais",
        class_name="w-full bg-[#073238] px-3 py-5 text-[#faf9f4] sm:px-6 sm:py-6",
    )


def hero() -> rx.Component:
    return rx.fragment(
        rx.el.section(
            rx.el.div(
                brand_slide(),
                whatsapp_slide(),
                promotion_slide(),
                custom_attrs={"data-carousel-surface": "true"},
                class_name="grid h-[315px] max-h-[315px] w-full touch-pan-y select-none cursor-grab active:cursor-grabbing",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("chevron-left", class_name="h-5 w-5"),
                    id="vk-slide-previous",
                    type="button",
                    aria_label="Banner anterior",
                    aria_controls="vk-slide-0 vk-slide-1 vk-slide-2",
                    on_click=[
                        rx.call_script(
                            "window.__vkScheduleCarousel && window.__vkScheduleCarousel(15000);"
                        ),
                        HeroState.previous_slide,
                    ],
                    class_name="flex h-11 w-11 items-center justify-center rounded-full border border-[#d4af37]/50 bg-transparent text-[#faf9f4] hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
                rx.el.div(
                    rx.foreach([0, 1, 2], slide_dot),
                    class_name="flex items-center gap-1",
                ),
                rx.el.button(
                    rx.icon("chevron-right", class_name="h-5 w-5"),
                    id="vk-slide-next",
                    type="button",
                    aria_label="Próximo banner",
                    aria_controls="vk-slide-0 vk-slide-1 vk-slide-2",
                    on_click=[
                        rx.call_script(
                            "window.__vkScheduleCarousel && window.__vkScheduleCarousel(15000);"
                        ),
                        HeroState.next_slide,
                    ],
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
                    "Banner 1 de 3: VIKTRINE SHOP",
                    rx.cond(
                        HeroState.active_slide == 1,
                        "Banner 2 de 3: Grupo WhatsApp para inscritos, link em breve",
                        "Banner 3 de 3: Sorteio mensal no PIX, lista pendente de publicação",
                    ),
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
            on_unmount=HeroState.stop_carousel,
            class_name="w-full bg-[#073238] text-[#faf9f4] focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[#d4af37]",
        ),
        category_strip(),
    )


def history_chapter(title: str, paragraphs: list[str]) -> rx.Component:
    return rx.el.section(
        rx.el.h2(
            title,
            class_name="font-['Cormorant_Garamond'] text-3xl font-semibold text-[#000000] sm:text-4xl",
        ),
        rx.foreach(
            paragraphs,
            lambda paragraph: rx.el.p(
                paragraph,
                class_name="mt-4 font-['Inter'] text-sm leading-7 text-[#000000] sm:text-base sm:leading-8",
            ),
        ),
        class_name="min-w-0 border-t border-[#d4af37]/40 pt-5",
    )


def history_section() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                history_chapter(
                    "Origem",
                    [
                        "A VIKTRINE SHOP nasceu da união de pessoas de origem humilde que, mesmo diante das dificuldades, encontraram na educação uma oportunidade para construir um futuro melhor."
                    ],
                ),
                history_chapter(
                    "Nossa História",
                    [
                        "Ao longo dessa trajetória, conseguimos chegar à faculdade e transformar tudo o que aprendemos em conhecimento, experiência e vontade de criar algo que pudesse fazer a diferença na vida das pessoas.",
                        "Foi assim que surgiu a VIKTRINE SHOP: como um projeto criado para facilitar a vida, encontrar boas oportunidades e compartilhar achadinhos que realmente valem a pena.",
                    ],
                ),
                history_chapter(
                    "Nosso Propósito",
                    [
                        "Mais do que uma loja, somos uma vitrine de descobertas. Buscamos produtos, oportunidades e novidades para ajudar você a encontrar aquilo que procura e economizar no caminho."
                    ],
                ),
                history_chapter(
                    "A Alma do Negócio",
                    [
                        "Nosso atendimento e nossa alegria são a alma da VIKTRINE SHOP. Queremos que cada pessoa se sinta bem aqui, descubra algo interessante e possa compartilhar esses achadinhos com sua família e com quem ama."
                    ],
                ),
                history_chapter(
                    "O Futuro",
                    [
                        "Temos planos de fazer esse projeto crescer e, no futuro, transformar essa conquista em novas oportunidades para outras pessoas, incluindo ações com instituições de caridade e iniciativas voltadas à educação."
                    ],
                ),
                class_name="grid w-full grid-cols-1 items-start gap-x-10 gap-y-9 md:grid-cols-2 lg:grid-cols-3",
            ),
            rx.el.p(
                "A VIKTRINE SHOP nasceu de uma origem simples, cresceu através da educação e continua avançando com um propósito: facilitar a vida das pessoas, compartilhar oportunidades e construir algo que possa fazer o bem. Cada clique seu aqui apoia esse sonho a continuar de pé. Obrigado por fazer parte da nossa história!",
                class_name="mt-10 border-t border-[#d4af37]/40 pt-8 font-['Cormorant_Garamond'] text-2xl leading-relaxed text-[#000000] md:text-3xl",
            ),
            class_name="mx-auto w-full max-w-[1440px] px-6 py-16 lg:px-12 lg:py-20",
        ),
        id="nossa-historia",
        background_color="#FFFFFF",
        color="#000000",
        class_name="w-full bg-[#FFFFFF] text-[#000000]",
    )


def footer() -> rx.Component:
    return rx.el.footer(
        rx.el.div(
            rx.el.div(
                rx.el.a(
                    rx.el.span("VIKTRINE", class_name="block"),
                    rx.el.span("SHOP", class_name="block"),
                    href="/",
                    aria_label="VIKTRINE SHOP · Início",
                    class_name="inline-block font-['Cormorant_Garamond'] text-5xl font-bold leading-[0.95] tracking-[0.12em] text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37] sm:text-6xl",
                ),
            ),
            rx.el.nav(
                rx.el.a(
                    "Ver Achadinhos",
                    href="/#catalogo",
                    class_name="text-xs text-[#f5f1e8] hover:text-[#d4af37]",
                ),
                rx.el.a(
                    "Lojas Parceiras",
                    href="/#lojas-parceiras",
                    class_name="text-xs text-[#f5f1e8] hover:text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
                rx.el.a(
                    "Minha conta",
                    href="/minha-conta",
                    class_name="text-xs text-[#f5f1e8] hover:text-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
                class_name="flex flex-wrap gap-6",
            ),
            class_name="flex flex-col justify-between gap-8 md:flex-row md:items-center",
        ),
        class_name="w-full bg-[var(--brand-petroleum-deep)] px-6 py-12 text-[#f5f1e8] lg:px-12",
    )
