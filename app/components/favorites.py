import reflex as rx
from app.states.favorite_state import FavoriteState, FavoriteProduct
from app.click_tracking import tracking_url


def favorite_control(
    product_id: rx.Var[int], title: rx.Var[str]
) -> rx.Component:
    return rx.cond(
        FavoriteState.signed_in,
        rx.el.button(
            rx.cond(
                FavoriteState.loading
                | (FavoriteState.pending_id == product_id),
                rx.icon(
                    "loader-circle",
                    aria_hidden=True,
                    class_name="h-4 w-4 animate-spin",
                ),
                rx.icon(
                    "heart",
                    aria_hidden=True,
                    class_name=rx.cond(
                        FavoriteState.ready
                        & FavoriteState.saved_ids.contains(product_id),
                        "h-4 w-4 fill-[#d4af37] stroke-[#073238]",
                        "h-4 w-4 stroke-[#073238]",
                    ),
                ),
            ),
            aria_label=rx.cond(
                FavoriteState.ready
                & FavoriteState.saved_ids.contains(product_id),
                f"Remover dos favoritos: {title}",
                f"Salvar nos favoritos: {title}",
            ),
            aria_pressed=FavoriteState.ready
            & FavoriteState.saved_ids.contains(product_id),
            aria_busy=FavoriteState.loading
            | (FavoriteState.pending_id == product_id),
            disabled=FavoriteState.loading
            | (FavoriteState.pending_id != 0)
            | ~FavoriteState.ready,
            on_click=FavoriteState.set_saved(
                product_id, ~FavoriteState.saved_ids.contains(product_id)
            ),
            type="button",
            title="Salvar ou remover dos favoritos",
            class_name="flex h-11 w-11 items-center justify-center rounded-full border border-[#d4af37]/50 bg-[#faf9f4]/95 text-[#073238] hover:bg-[#f0e8ce] disabled:cursor-wait disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#073238]",
        ),
        rx.el.a(
            rx.icon("heart", aria_hidden=True, class_name="h-4 w-4"),
            "Entrar para salvar",
            href="/login?redirect_to=/",
            aria_label=f"Entrar para salvar nos favoritos: {title}",
            class_name="flex min-h-11 items-center justify-center gap-1.5 rounded-full border border-[#d4af37]/50 bg-[#faf9f4]/95 px-2.5 text-[10px] font-medium text-[#073238] hover:bg-[#f0e8ce] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#073238]",
        ),
    )


def favorite_feedback() -> rx.Component:
    return rx.cond(
        FavoriteState.signed_in,
        rx.el.div(
            rx.cond(
                FavoriteState.error != "",
                rx.el.div(
                    rx.icon(
                        "circle-alert",
                        aria_hidden=True,
                        class_name="h-4 w-4 shrink-0",
                    ),
                    rx.el.p(FavoriteState.error),
                    rx.el.button(
                        "Tentar novamente",
                        type="button",
                        on_click=FavoriteState.load_favorites,
                        disabled=FavoriteState.loading
                        | (FavoriteState.pending_id != 0),
                        class_name="shrink-0 underline underline-offset-4 disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-[#073238]",
                    ),
                    role="alert",
                    class_name="flex flex-wrap items-center gap-3 border border-red-200 bg-red-50 p-4 text-xs text-red-700",
                ),
            ),
            rx.el.p(
                rx.cond(
                    FavoriteState.pending_id != 0,
                    "Atualizando favoritos…",
                    FavoriteState.notice,
                ),
                role="status",
                aria_live="polite",
                aria_atomic=True,
                class_name="text-xs text-[#073238] empty:hidden",
            ),
            class_name="flex flex-col gap-3",
        ),
    )


def favorite_card(product: FavoriteProduct) -> rx.Component:
    return rx.el.article(
        rx.el.img(
            src=product["image_url"],
            alt=product["title"],
            loading="lazy",
            class_name="h-40 w-28 shrink-0 bg-[#efede4] object-cover sm:h-44 sm:w-32",
        ),
        rx.el.div(
            rx.el.p(
                product["partner_name"],
                class_name="text-[10px] uppercase tracking-[0.15em] text-[#71602f]",
            ),
            rx.el.h3(
                product["title"],
                class_name="mt-2 font-['Cormorant_Garamond'] text-2xl font-medium leading-tight text-[#073238]",
            ),
            rx.el.p(
                product["price"],
                class_name="mt-3 text-sm font-semibold text-[#073238]",
            ),
            rx.el.div(
                rx.el.a(
                    "Ir para a loja",
                    rx.icon(
                        "arrow-up-right", aria_hidden=True, class_name="h-4 w-4"
                    ),
                    href=tracking_url(product["id"]),
                    aria_label=f"Ir para a loja {product['partner_name']}: {product['title']}",
                    class_name="inline-flex min-h-11 items-center gap-2 border border-[#d4af37] bg-[#d4af37] px-3 py-2 text-xs font-medium text-[#073238] hover:bg-[#e1c25c] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#073238]",
                ),
                rx.el.button(
                    rx.cond(
                        FavoriteState.pending_id == product["id"],
                        rx.icon(
                            "loader-circle",
                            aria_hidden=True,
                            class_name="h-4 w-4 animate-spin",
                        ),
                        rx.icon(
                            "heart",
                            aria_hidden=True,
                            class_name="h-4 w-4 fill-[#d4af37]",
                        ),
                    ),
                    "Remover",
                    aria_label=f"Remover dos favoritos: {product['title']}",
                    aria_pressed=True,
                    aria_busy=FavoriteState.pending_id == product["id"],
                    on_click=FavoriteState.set_saved(product["id"], False),
                    disabled=FavoriteState.loading
                    | (FavoriteState.pending_id != 0),
                    type="button",
                    class_name="inline-flex min-h-11 items-center gap-2 px-2 py-2 text-xs text-[#073238] hover:underline disabled:cursor-wait disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
                class_name="mt-4 flex flex-wrap items-center gap-2",
            ),
            class_name="min-w-0 flex-1",
        ),
        key=product["id"],
        class_name="flex min-w-0 gap-4 border border-[#dedfd5] bg-white p-5 text-[#073238] sm:gap-5 sm:p-6",
    )


def favorites_section() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "SUAS ESCOLHAS",
                    class_name="text-[10px] tracking-[0.2em] text-[#71602f]",
                ),
                rx.el.h2(
                    "Meus favoritos",
                    class_name="mt-2 font-['Cormorant_Garamond'] text-4xl text-[#073238] sm:text-5xl",
                ),
                rx.el.p(
                    "Guarde os seus achados para voltar a eles quando quiser.",
                    class_name="mt-3 text-sm text-[#687268]",
                ),
            ),
            rx.el.button(
                rx.icon("refresh-cw", aria_hidden=True, class_name="h-4 w-4"),
                "Atualizar favoritos",
                on_click=FavoriteState.load_favorites,
                disabled=FavoriteState.loading
                | (FavoriteState.pending_id != 0),
                type="button",
                class_name="flex w-fit items-center gap-2 border border-[#dedfd5] bg-white px-4 py-3 text-xs text-[#073238] hover:border-[#d4af37] disabled:cursor-wait disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-[#d4af37]",
            ),
            class_name="mb-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-end",
        ),
        rx.cond(
            FavoriteState.signed_in,
            rx.el.div(
                favorite_feedback(),
                rx.cond(
                    FavoriteState.loading,
                    rx.el.div(
                        rx.el.p(
                            "Carregando seus favoritos…",
                            class_name="text-sm text-[#687268]",
                        ),
                        rx.el.div(
                            class_name="mt-4 h-48 animate-pulse border border-[#dedfd5] bg-[#efede4]"
                        ),
                        role="status",
                        aria_busy=True,
                        aria_live="polite",
                    ),
                    rx.cond(
                        FavoriteState.error == "",
                        rx.cond(
                            FavoriteState.favorites.length() == 0,
                            rx.el.div(
                                rx.icon(
                                    "heart",
                                    aria_hidden=True,
                                    class_name="mx-auto h-8 w-8 text-[#71602f]",
                                ),
                                rx.el.h3(
                                    "Seus próximos achados esperam por você.",
                                    class_name="mt-5 font-['Cormorant_Garamond'] text-3xl text-[#073238]",
                                ),
                                rx.el.p(
                                    "Você ainda não salvou produtos. Toque no coração de uma peça no catálogo para começar.",
                                    class_name="mx-auto mt-3 max-w-lg text-sm leading-7 text-[#687268]",
                                ),
                                class_name="border border-[#dedfd5] bg-white px-6 py-12 text-center",
                            ),
                            rx.el.div(
                                rx.foreach(
                                    FavoriteState.favorites, favorite_card
                                ),
                                class_name="grid w-full grid-cols-1 gap-5 lg:grid-cols-2",
                            ),
                        ),
                    ),
                ),
                rx.cond(
                    (FavoriteState.page_number > 1) | FavoriteState.has_next,
                    rx.el.nav(
                        rx.el.button(
                            "Anteriores",
                            on_click=FavoriteState.change_page(-1),
                            disabled=(FavoriteState.page_number == 1)
                            | FavoriteState.loading
                            | (FavoriteState.pending_id != 0),
                            class_name="min-h-11 border border-[#dedfd5] bg-white px-4 text-xs text-[#073238] disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                        ),
                        rx.el.span(
                            f"Página {FavoriteState.page_number}",
                            class_name="text-xs text-[#687268]",
                        ),
                        rx.el.button(
                            "Próximos",
                            on_click=FavoriteState.change_page(1),
                            disabled=~FavoriteState.has_next
                            | FavoriteState.loading
                            | (FavoriteState.pending_id != 0),
                            class_name="min-h-11 border border-[#dedfd5] bg-white px-4 text-xs text-[#073238] disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                        ),
                        aria_label="Paginação dos favoritos",
                        class_name="flex flex-wrap items-center justify-between gap-4",
                    ),
                ),
                class_name="flex flex-col gap-5",
            ),
            rx.el.p(
                "Entre na sua conta para consultar seus favoritos.",
                class_name="text-sm text-[#687268]",
            ),
        ),
        rx.el.a(
            "Voltar ao catálogo",
            rx.icon("arrow-up-right", aria_hidden=True, class_name="h-4 w-4"),
            href="/#catalogo",
            class_name="mt-6 inline-flex min-h-11 items-center gap-2 text-xs text-[#073238] underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-[#d4af37]",
        ),
        aria_label="Meus favoritos",
        class_name="mx-auto w-full max-w-[1440px] border-t border-[#dedfd5] px-6 py-10 text-[#073238] lg:px-12 lg:py-14",
    )
