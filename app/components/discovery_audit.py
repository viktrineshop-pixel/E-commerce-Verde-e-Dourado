import reflex as rx
from app.states.discovery_audit_state import DiscoveryAuditState


def audit_entry(row: dict[str, str]) -> rx.Component:
    return rx.el.details(
        rx.el.summary(
            rx.el.span(
                row["title"], class_name="text-sm font-medium text-[#073238]"
            ),
            rx.el.p(
                row["details"],
                class_name="mt-2 break-words text-xs leading-6 text-[#596c69]",
            ),
            class_name="cursor-pointer p-4 focus-visible:outline-2 focus-visible:outline-[#d4af37]",
        ),
        rx.el.pre(
            row["extra"],
            class_name="max-h-96 overflow-auto whitespace-pre-wrap break-words border-t border-[#deded3] bg-[#faf9f4] p-4 text-xs text-[#073238]",
        ),
        key=row["id"],
        class_name="rounded-sm border border-[#deded3] bg-white",
    )


def discovery_audit() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.h2(
                "Rastro de curadoria",
                class_name="font-['Cormorant_Garamond'] text-3xl text-[#073238]",
            ),
            rx.el.button(
                "Atualizar histórico",
                on_click=DiscoveryAuditState.load,
                disabled=DiscoveryAuditState.loading,
                class_name="min-h-11 rounded-sm border border-[#deded3] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            class_name="flex flex-wrap items-center justify-between gap-3",
        ),
        rx.el.p(
            "Histórico somente leitura: identidade responsável, motivo e campos alterados antes/depois. Observações de preço são imutáveis; correções são novas observações.",
            class_name="mt-3 text-xs leading-6 text-[#596c69]",
        ),
        rx.el.form(
            rx.el.div(
                rx.el.label(
                    "ID do produto (vazio = todo o histórico)",
                    html_for="audit-product",
                    class_name="mb-2 block text-xs text-[#073238]",
                ),
                rx.el.input(
                    id="audit-product",
                    name="product_id",
                    type="number",
                    default_value=rx.cond(
                        DiscoveryAuditState.audit_product_id > 0,
                        DiscoveryAuditState.audit_product_id.to_string(),
                        "",
                    ),
                    key=DiscoveryAuditState.audit_product_id,
                    class_name="min-h-11 w-full rounded-sm border border-[#deded3] bg-[#faf9f4] p-3 text-sm text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
            ),
            rx.el.button(
                "Filtrar histórico",
                type="submit",
                disabled=DiscoveryAuditState.loading,
                class_name="min-h-11 rounded-sm bg-[#073238] px-4 text-xs text-[#faf9f4] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            on_submit=DiscoveryAuditState.filter_history,
            class_name="mt-5 flex flex-wrap items-end gap-3",
        ),
        rx.cond(
            DiscoveryAuditState.error != "",
            rx.el.p(
                DiscoveryAuditState.error,
                role="alert",
                class_name="mt-4 rounded-sm bg-red-50 p-4 text-sm text-red-700",
            ),
        ),
        rx.cond(
            DiscoveryAuditState.loading,
            rx.el.div(
                "Carregando auditoria…",
                role="status",
                class_name="mt-5 animate-pulse bg-[#faf9f4] p-6 text-sm text-[#596c69]",
            ),
            rx.cond(
                DiscoveryAuditState.rows.length() == 0,
                rx.el.p(
                    "Nenhuma alteração editorial registrada neste contexto.",
                    class_name="mt-5 border border-dashed border-[#deded3] bg-[#faf9f4] p-6 text-sm text-[#596c69]",
                ),
                rx.el.div(
                    rx.foreach(DiscoveryAuditState.rows, audit_entry),
                    class_name="mt-5 flex flex-col gap-3",
                ),
            ),
        ),
        rx.el.div(
            rx.el.button(
                "Anterior",
                on_click=DiscoveryAuditState.change_page(-1),
                disabled=(DiscoveryAuditState.page <= 1)
                | DiscoveryAuditState.loading,
                class_name="min-h-11 rounded-sm border border-[#deded3] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-40",
            ),
            rx.el.p(
                f"{DiscoveryAuditState.total} alterações · página {DiscoveryAuditState.page}",
                class_name="text-xs text-[#596c69]",
            ),
            rx.el.button(
                "Próxima",
                on_click=DiscoveryAuditState.change_page(1),
                disabled=(
                    DiscoveryAuditState.page * 15 >= DiscoveryAuditState.total
                )
                | DiscoveryAuditState.loading,
                class_name="min-h-11 rounded-sm border border-[#deded3] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-40",
            ),
            class_name="mt-6 flex flex-wrap items-center justify-between gap-3",
        ),
        class_name="mt-8 w-full rounded-sm border border-[#deded3] bg-white p-5 md:p-7",
    )
