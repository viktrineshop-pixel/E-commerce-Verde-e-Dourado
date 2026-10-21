import reflex as rx
from app.states.admin_click_state import (
    AdminClickState,
    MarketplaceClicks,
    ProductClicks,
)


def marketplace_clicks(row: MarketplaceClicks) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            row["marketplace"], class_name="text-xs font-medium text-[#596559]"
        ),
        rx.el.p(
            f"{row['clicks']:,} cliques",
            class_name="mt-2 text-lg font-semibold text-[#073238]",
        ),
        key=row["marketplace"],
        class_name="w-full rounded-sm border border-[#deded3] bg-[#faf9f4] p-4",
    )


def product_clicks(row: ProductClicks) -> rx.Component:
    return rx.el.li(
        rx.el.span(
            f"{row['rank']}.",
            class_name="w-7 shrink-0 text-sm font-semibold text-[#073238]",
        ),
        rx.el.div(
            rx.el.h4(
                row["title"],
                class_name="break-words text-sm font-medium text-[#073238]",
            ),
            rx.el.p(
                f"{row['sku']} · {row['marketplace']}",
                class_name="mt-1 break-all text-xs text-[#596559]",
            ),
            class_name="min-w-0 flex-1",
        ),
        rx.el.span(
            f"{row['clicks']:,} cliques",
            class_name="shrink-0 text-xs font-semibold text-[#073238]",
        ),
        key=f"{row['sku']}-{row['title']}-{row['marketplace']}",
        class_name="flex items-start gap-3 border-b border-[#deded3] py-4 last:border-b-0",
    )


def click_report_results() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "Total registrado",
                    class_name="text-xs font-medium text-[#596559]",
                ),
                rx.el.p(
                    f"{AdminClickState.total:,} cliques",
                    class_name="mt-2 text-lg font-semibold text-[#073238]",
                ),
                class_name="w-full rounded-sm border border-[#d4af37]/50 bg-[#faf9f4] p-4",
            ),
            rx.foreach(AdminClickState.marketplaces, marketplace_clicks),
            class_name="mt-5 grid w-full grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4",
        ),
        rx.el.h3(
            "Produtos mais acessados",
            class_name="mt-6 font-['Cormorant_Garamond'] text-2xl text-[#073238]",
        ),
        rx.el.p(
            "Até 20 posições · agrupadas por SKU, título e loja no momento do clique. Alterações de título ou loja aparecem em grupos separados; produtos excluídos mantêm seu histórico.",
            class_name="mt-2 text-xs leading-5 text-[#596559]",
        ),
        rx.el.ol(
            rx.foreach(AdminClickState.products, product_clicks),
            class_name="mt-2 w-full text-[#073238]",
        ),
    )


def admin_clicks() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Arquivo de cliques legados",
                    id="click-report-title",
                    class_name="font-['Cormorant_Garamond'] text-3xl text-[#073238]",
                ),
                rx.el.p(
                    "Somente cliques históricos sem offer_id, separados das ofertas atuais. Cliques não representam compras nem visitantes únicos.",
                    class_name="mt-2 text-xs leading-5 text-[#596559]",
                ),
            ),
            rx.el.button(
                rx.icon("refresh-cw", aria_hidden=True, class_name="h-4 w-4"),
                "Atualizar relatório",
                type="button",
                on_click=AdminClickState.load_report,
                disabled=AdminClickState.loading,
                class_name="flex min-h-11 items-center gap-2 rounded-sm border border-[#d8d7cc] bg-white px-3 text-xs text-[#073238] hover:bg-[#faf9f4] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            class_name="flex flex-wrap items-center justify-between gap-4",
        ),
        rx.cond(
            AdminClickState.loading,
            rx.el.div(
                "Carregando cliques…",
                role="status",
                class_name="mt-5 animate-pulse rounded-sm bg-[#faf9f4] p-8 text-sm text-[#596559]",
            ),
            rx.cond(
                AdminClickState.error != "",
                rx.el.p(
                    AdminClickState.error,
                    role="alert",
                    class_name="mt-5 rounded-sm border border-red-200 bg-red-50 p-4 text-sm text-red-700",
                ),
                rx.cond(
                    AdminClickState.total == 0,
                    rx.el.div(
                        rx.icon(
                            "mouse-pointer-click",
                            aria_hidden=True,
                            class_name="mx-auto h-8 w-8 text-[#073238]",
                        ),
                        rx.el.p(
                            "Nenhum clique registrado ainda.",
                            class_name="mt-3 text-sm text-[#073238]",
                        ),
                        rx.el.p(
                            "Cliques das ofertas atuais aparecem no painel Operações, não neste arquivo legado.",
                            class_name="mt-2 text-xs text-[#596559]",
                        ),
                        class_name="mt-5 rounded-sm border border-dashed border-[#d8d7cc] bg-[#faf9f4] p-8 text-center",
                    ),
                    click_report_results(),
                ),
            ),
        ),
        aria_labelledby="click-report-title",
        aria_busy=AdminClickState.loading,
        class_name="mb-6 w-full min-w-0 rounded-sm border border-[#deded3] bg-white p-5 md:p-7",
    )
