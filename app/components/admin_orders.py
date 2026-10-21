import reflex as rx
from app.states.admin_order_state import (
    AdminOrderState,
    AdminOrder,
    AdminOrderItem,
)


def order_item(item: AdminOrderItem) -> rx.Component:
    return rx.el.li(
        rx.el.span(
            item["title"],
            class_name="min-w-0 flex-1 break-words text-[#0d231d]",
        ),
        rx.el.span(
            f"× {item['quantity']}",
            class_name="shrink-0 font-medium text-[#073238]",
        ),
        key=item["id"],
        class_name="flex justify-between gap-4 py-1 text-xs leading-5",
    )


def order_status_form(order: AdminOrder) -> rx.Component:
    return rx.el.form(
        rx.el.input(type="hidden", name="order_id", value=str(order["id"])),
        rx.el.input(type="hidden", name="expected", value=order["status"]),
        rx.el.label(
            "Registrar status",
            html_for=f"order-status-{order['id']}",
            class_name="mb-2 block text-xs font-medium text-[#073238]",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.select(
                    rx.el.option("Escolha um status…", value="", disabled=True),
                    rx.el.option("Recebido", value="pending"),
                    rx.el.option("Em preparação", value="processing"),
                    rx.el.option("Enviado", value="shipped"),
                    rx.el.option("Cancelado", value="cancelled"),
                    name="status",
                    id=f"order-status-{order['id']}",
                    default_value=rx.cond(
                        (order["status"] == "paid")
                        | (order["status"] == "delivered")
                        | (order["status"] == "refunded"),
                        "",
                        order["status"],
                    ),
                    required=True,
                    disabled=AdminOrderState.loading | AdminOrderState.saving,
                    class_name="min-h-11 w-full appearance-none rounded-sm border border-[#d8d7cc] bg-[#faf9f4] px-3 py-2 pr-10 text-xs text-[#0d231d] focus:outline-2 focus:outline-[#d4af37] disabled:opacity-50",
                ),
                rx.icon(
                    "chevron-down",
                    aria_hidden=True,
                    class_name="pointer-events-none absolute right-3 top-3.5 h-4 w-4 text-[#073238]",
                ),
                class_name="relative min-w-0 flex-1",
            ),
            rx.el.button(
                rx.icon("save", class_name="h-4 w-4"),
                rx.cond(
                    AdminOrderState.saving_id == order["id"],
                    "Salvando…",
                    "Salvar status",
                ),
                type="submit",
                disabled=AdminOrderState.loading | AdminOrderState.saving,
                class_name="flex min-h-11 items-center justify-center gap-2 rounded-sm bg-[#073238] px-4 py-2 text-xs font-medium text-[#faf9f4] hover:bg-[#0d231d] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#d4af37] disabled:cursor-wait disabled:opacity-50",
            ),
            class_name="flex flex-col gap-3 sm:flex-row",
        ),
        on_submit=AdminOrderState.save_status,
        key=f"{order['id']}-{order['status']}",
        class_name="mt-5 border-t border-[#deded3] pt-4",
    )


def admin_order_card(order: AdminOrder) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    order["number"],
                    class_name="text-sm font-semibold tracking-wide text-[#073238]",
                ),
                rx.el.p(
                    f"{order['date']} · São Paulo",
                    class_name="mt-1 text-xs text-[#596559]",
                ),
            ),
            rx.el.span(
                order["status_label"],
                class_name="w-fit rounded-full border border-[#d4af37]/50 bg-[#faf9f4] px-3 py-1.5 text-xs font-medium text-[#073238]",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.icon(
                "user-round",
                aria_hidden=True,
                class_name="mt-0.5 h-4 w-4 shrink-0 text-[#073238]",
            ),
            rx.el.div(
                rx.el.p(
                    rx.cond(
                        order["contact_name"] != "",
                        order["contact_name"],
                        "Nome não informado",
                    ),
                    class_name="break-words text-sm font-medium text-[#0d231d]",
                ),
                rx.el.p(
                    rx.cond(
                        order["contact_email"] != "",
                        order["contact_email"],
                        "E-mail não informado",
                    ),
                    class_name="mt-1 break-all text-xs text-[#596559]",
                ),
                class_name="min-w-0",
            ),
            class_name="mt-5 flex items-start gap-2",
        ),
        rx.el.h4(
            "Itens registrados no pedido",
            class_name="mt-5 text-xs font-medium text-[#073238]",
        ),
        rx.cond(
            order["items"].length() > 0,
            rx.el.ul(
                rx.foreach(order["items"], order_item),
                class_name="mt-2 text-[#0d231d]",
            ),
            rx.el.p(
                "Nenhum item registrado neste pedido.",
                class_name="mt-2 text-xs text-[#596559]",
            ),
        ),
        rx.el.div(
            rx.el.span("Total registrado", class_name="text-xs text-[#596559]"),
            rx.el.span(
                order["total"],
                class_name="text-base font-semibold text-[#073238]",
            ),
            class_name="mt-4 flex flex-wrap justify-between gap-3",
        ),
        rx.el.p(
            "Arquivo demonstrativo · somente leitura; status histórico não confirma pagamento ou envio.",
            class_name="mt-5 border-t border-[#deded3] pt-4 text-xs leading-6 text-[#596559]",
        ),
        key=order["id"],
        class_name="min-w-0 rounded-sm border border-[#deded3] bg-white p-5 text-[#0d231d]",
    )


def order_search_form() -> rx.Component:
    return rx.el.form(
        rx.el.label(
            "Buscar pedidos",
            html_for="admin-order-search",
            class_name="font-['Cormorant_Garamond'] text-xl text-[#073238]",
        ),
        rx.el.p(
            "Número exato (ML-000123 ou 123) ou parte do e-mail do cliente, sem diferenciar maiúsculas.",
            id="admin-order-search-help",
            class_name="mt-1 text-xs text-[#596559]",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "search",
                    aria_hidden=True,
                    class_name="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-[#073238]",
                ),
                rx.el.input(
                    id="admin-order-search",
                    name="query",
                    type="search",
                    placeholder="ML-000123 ou cliente@email.com",
                    default_value=AdminOrderState.query_text,
                    max_length=320,
                    auto_complete="off",
                    aria_describedby=rx.cond(
                        AdminOrderState.search_error != "",
                        "admin-order-search-help admin-order-search-error",
                        "admin-order-search-help",
                    ),
                    aria_invalid=rx.cond(
                        AdminOrderState.search_error != "", "true", "false"
                    ),
                    class_name="min-h-11 w-full rounded-sm border border-[#d8d7cc] bg-white py-2 pl-10 pr-3 text-sm text-[#0d231d] placeholder:text-[#7a857c] focus:outline-2 focus:outline-[#d4af37]",
                ),
                class_name="relative min-w-0 flex-1",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("search", class_name="h-4 w-4"),
                    "Buscar",
                    type="submit",
                    disabled=AdminOrderState.loading | AdminOrderState.saving,
                    class_name="flex min-h-11 flex-1 items-center justify-center gap-2 rounded-sm bg-[#073238] px-5 text-xs font-medium text-[#faf9f4] hover:bg-[#0d231d] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#d4af37] disabled:cursor-wait disabled:opacity-50 sm:flex-none",
                ),
                rx.el.button(
                    rx.icon("x", class_name="h-4 w-4"),
                    "Limpar",
                    type="button",
                    on_click=AdminOrderState.clear_search,
                    disabled=AdminOrderState.loading | AdminOrderState.saving,
                    class_name="flex min-h-11 flex-1 items-center justify-center gap-2 rounded-sm border border-[#d8d7cc] bg-white px-5 text-xs text-[#073238] hover:bg-[#faf9f4] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50 sm:flex-none",
                ),
                class_name="flex gap-3",
            ),
            class_name="mt-3 flex flex-col gap-3 sm:flex-row",
        ),
        rx.cond(
            AdminOrderState.search_error != "",
            rx.el.p(
                rx.icon(
                    "circle-alert",
                    aria_hidden=True,
                    class_name="h-4 w-4 shrink-0",
                ),
                AdminOrderState.search_error,
                id="admin-order-search-error",
                role="alert",
                class_name="mt-3 flex items-start gap-2 text-xs text-red-700",
            ),
        ),
        rx.cond(
            AdminOrderState.search_kind != "",
            rx.el.p(
                rx.icon(
                    "filter",
                    aria_hidden=True,
                    class_name="h-4 w-4 shrink-0 text-[#d4af37]",
                ),
                f"Filtro aplicado: {AdminOrderState.search_label} · Página {AdminOrderState.page}",
                role="status",
                class_name="mt-3 flex items-center gap-2 break-all text-xs font-medium text-[#073238]",
            ),
        ),
        on_submit=AdminOrderState.search_orders,
        key=AdminOrderState.form_version.to_string(),
        role="search",
        aria_label="Buscar pedidos por número ou e-mail",
        class_name="mt-5 rounded-sm border border-[#deded3] bg-[#faf9f4] p-4",
    )


def orders_empty_state() -> rx.Component:
    return rx.el.div(
        rx.cond(
            AdminOrderState.search_kind != "",
            rx.icon(
                "search-x",
                aria_hidden=True,
                class_name="mx-auto h-8 w-8 text-[#073238]",
            ),
            rx.icon(
                "package-open",
                aria_hidden=True,
                class_name="mx-auto h-8 w-8 text-[#073238]",
            ),
        ),
        rx.el.p(
            rx.cond(
                AdminOrderState.search_kind != "",
                f"Nenhum pedido corresponde a: {AdminOrderState.search_label}.",
                rx.cond(
                    AdminOrderState.page <= 1,
                    "Nenhum pedido anterior neste arquivo.",
                    "Nenhum pedido registrado nesta página.",
                ),
            ),
            class_name="mt-3 break-all text-sm text-[#596559]",
        ),
        rx.cond(
            AdminOrderState.search_kind != "",
            rx.el.button(
                rx.icon("x", class_name="h-4 w-4"),
                "Limpar busca e ver todos",
                type="button",
                on_click=AdminOrderState.clear_search,
                disabled=AdminOrderState.loading | AdminOrderState.saving,
                class_name="mx-auto mt-4 flex min-h-11 items-center gap-2 rounded-sm border border-[#d8d7cc] bg-white px-4 text-xs text-[#073238] hover:bg-[#faf9f4] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
        ),
        role="status",
        class_name="mt-5 rounded-sm border border-dashed border-[#d8d7cc] bg-[#faf9f4] p-8 text-center",
    )


def admin_orders() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Arquivo demonstrativo de pedidos anteriores",
                    class_name="font-['Cormorant_Garamond'] text-3xl text-[#073238]",
                ),
                rx.el.p(
                    "Pedidos mais recentes primeiro · 10 por página",
                    class_name="mt-2 text-xs text-[#596559]",
                ),
            ),
            rx.el.button(
                rx.icon("refresh-cw", class_name="h-4 w-4"),
                "Atualizar arquivo",
                type="button",
                on_click=AdminOrderState.load_orders(0),
                disabled=AdminOrderState.loading | AdminOrderState.saving,
                class_name="flex min-h-11 items-center gap-2 rounded-sm border border-[#d8d7cc] bg-white px-3 text-xs text-[#073238] hover:bg-[#faf9f4] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            class_name="flex flex-wrap items-center justify-between gap-4",
        ),
        rx.el.p(
            "Arquivo somente leitura. Busca e paginação consultam registros anteriores preservados. Não é possível criar pedidos ou alterar status, pagamentos e envios.",
            class_name="mt-4 rounded-sm border border-[#d4af37]/40 bg-[#faf9f4] p-3 text-xs leading-6 text-[#596559]",
        ),
        order_search_form(),
        rx.cond(
            AdminOrderState.error != "",
            rx.el.p(
                AdminOrderState.error,
                role="alert",
                class_name="mt-4 rounded-sm border border-red-200 bg-red-50 p-4 text-sm text-red-700",
            ),
        ),
        rx.cond(
            AdminOrderState.notice != "",
            rx.el.p(
                AdminOrderState.notice,
                role="status",
                class_name="mt-4 rounded-sm border border-green-200 bg-green-50 p-4 text-sm text-green-700",
            ),
        ),
        rx.cond(
            AdminOrderState.loading,
            rx.el.div(
                "Carregando pedidos…",
                role="status",
                class_name="mt-5 animate-pulse rounded-sm bg-[#faf9f4] p-8 text-sm text-[#596559]",
            ),
            rx.cond(
                AdminOrderState.orders.length() > 0,
                rx.el.div(
                    rx.foreach(AdminOrderState.orders, admin_order_card),
                    class_name="mt-5 grid w-full grid-cols-1 items-start gap-4 lg:grid-cols-2",
                ),
                rx.cond(
                    AdminOrderState.error == "",
                    orders_empty_state(),
                ),
            ),
        ),
        rx.el.nav(
            rx.el.button(
                rx.icon("chevron-left", class_name="h-4 w-4"),
                "Anterior",
                type="button",
                on_click=AdminOrderState.load_orders(-1),
                disabled=(AdminOrderState.page <= 1)
                | AdminOrderState.loading
                | AdminOrderState.saving,
                class_name="flex min-h-11 items-center gap-2 rounded-sm border border-[#d8d7cc] bg-white px-3 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-40",
            ),
            rx.el.span(
                f"Página {AdminOrderState.page}",
                class_name="text-xs text-[#596559]",
            ),
            rx.el.button(
                "Próxima",
                rx.icon("chevron-right", class_name="h-4 w-4"),
                type="button",
                on_click=AdminOrderState.load_orders(1),
                disabled=(~AdminOrderState.has_next)
                | AdminOrderState.loading
                | AdminOrderState.saving,
                class_name="flex min-h-11 items-center gap-2 rounded-sm border border-[#d8d7cc] bg-white px-3 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-40",
            ),
            aria_label="Paginação dos pedidos administrativos",
            class_name="mt-5 flex flex-wrap items-center justify-between gap-3",
        ),
        aria_busy=AdminOrderState.loading | AdminOrderState.saving,
        class_name="mb-6 w-full min-w-0 rounded-sm border border-[#deded3] bg-white p-5 md:p-7",
    )
