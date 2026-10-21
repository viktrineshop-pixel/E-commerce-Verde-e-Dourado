import reflex as rx

from app.states.discovery_state import DiscoveryState
from app.discovery import LABELS, STATUS_NAMES
from app.components.discovery_audit import discovery_audit


PANELS = [
    {"key": key, "label": label}
    for key, label in LABELS.items()
    if key != "audit"
]


def panel_button(panel: dict[str, str]) -> rx.Component:
    return rx.el.button(
        panel["label"],
        type="button",
        on_click=DiscoveryState.choose_panel(panel["key"]),
        disabled=DiscoveryState.loading | DiscoveryState.saving,
        aria_pressed=DiscoveryState.kind == panel["key"],
        class_name=rx.cond(
            DiscoveryState.kind == panel["key"],
            "min-h-11 rounded-sm border border-[#073238] bg-[#073238] px-4 text-xs font-medium text-[#faf9f4] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            "min-h-11 rounded-sm border border-[#deded3] bg-white px-4 text-xs font-medium text-[#073238] hover:border-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
        ),
        key=panel["key"],
    )


def editor_control(field: dict[str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            field["label"],
            html_for=f"discovery-{field['name']}",
            class_name="mb-2 block text-xs font-medium text-[#073238]",
        ),
        rx.match(
            field["control"],
            (
                "textarea",
                rx.el.textarea(
                    id=f"discovery-{field['name']}",
                    name=field["name"],
                    default_value=DiscoveryState.draft.get(field["name"], ""),
                    rows=4,
                    disabled=DiscoveryState.saving,
                    class_name="w-full rounded-sm border border-[#deded3] bg-[#faf9f4] p-3 text-sm text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
            ),
            (
                "select",
                rx.el.div(
                    rx.el.select(
                        rx.foreach(
                            field["choices"].split("|"),
                            lambda choice: rx.el.option(
                                rx.Var.create(STATUS_NAMES).get(choice, choice),
                                value=choice,
                            ),
                        ),
                        id=f"discovery-{field['name']}",
                        name=field["name"],
                        default_value=DiscoveryState.draft.get(
                            field["name"], ""
                        ),
                        disabled=DiscoveryState.saving,
                        class_name="min-h-11 w-full appearance-none rounded-sm border border-[#deded3] bg-[#faf9f4] p-3 pr-10 text-sm text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                    ),
                    rx.icon(
                        "chevron-down",
                        aria_hidden=True,
                        class_name="pointer-events-none absolute right-3 top-3.5 h-4 w-4 text-[#073238]",
                    ),
                    class_name="relative w-full",
                ),
            ),
            rx.el.input(
                id=f"discovery-{field['name']}",
                name=field["name"],
                type=field["control"],
                default_value=DiscoveryState.draft.get(field["name"], ""),
                key=DiscoveryState.draft.get(field["name"], ""),
                disabled=DiscoveryState.saving,
                class_name="min-h-11 w-full rounded-sm border border-[#deded3] bg-[#faf9f4] p-3 text-sm text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
            ),
        ),
        key=field["name"],
        class_name="min-w-0 w-full",
    )


def editor() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.h3(
                rx.cond(
                    DiscoveryState.record_id > 0,
                    f"Editar registro #{DiscoveryState.record_id}",
                    "Novo registro",
                ),
                class_name="font-['Cormorant_Garamond'] text-3xl text-[#073238]",
            ),
            rx.cond(
                DiscoveryState.kind != "duplicate",
                rx.el.button(
                    rx.icon("plus", class_name="h-4 w-4"),
                    "Novo",
                    on_click=DiscoveryState.new_record,
                    type="button",
                    disabled=DiscoveryState.saving | DiscoveryState.loading,
                    class_name="flex min-h-11 items-center gap-2 rounded-sm border border-[#deded3] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
                ),
            ),
            class_name="flex flex-wrap items-center justify-between gap-3",
        ),
        rx.cond(
            (DiscoveryState.kind == "duplicate")
            & (DiscoveryState.record_id == 0),
            rx.el.p(
                "Selecione um candidato na lista para registrar sua decisão. Candidatos são detectados por GTIN de produtos/variantes ou marca e modelo; nenhum registro é mesclado automaticamente.",
                class_name="mt-5 text-sm leading-6 text-[#596c69]",
            ),
            rx.el.form(
                rx.foreach(DiscoveryState.definitions, editor_control),
                rx.el.div(
                    rx.el.input(
                        id="discovery-reviewed",
                        name="reviewed",
                        type="checkbox",
                        disabled=DiscoveryState.saving,
                        class_name="h-4 w-4 accent-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                    ),
                    rx.el.label(
                        rx.match(
                            DiscoveryState.kind,
                            (
                                "link",
                                "Revisei manualmente os dois URLs, a loja/programa e a validade. Confirmo que correspondem ao MESMO item desta oferta. Não realizei teste automático de redirecionamento.",
                            ),
                            (
                                "observation",
                                "Observei efetivamente este preço na fonte/evidência e horário informados. Não estou usando um preço demonstrativo.",
                            ),
                            (
                                "duplicate",
                                "Revisei as evidências e confirmo a decisão indicada, sem mesclar ou excluir produtos.",
                            ),
                            "Revisei manualmente os campos e evidências deste registro. Publicar não significa verificação automática por marketplace.",
                        ),
                        html_for="discovery-reviewed",
                        class_name="text-xs leading-6 text-[#073238]",
                    ),
                    class_name="flex items-start gap-3 rounded-sm border border-[#deded3] bg-[#faf9f4] p-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Motivo / contexto / evidência da alteração *",
                        html_for="discovery-reason",
                        class_name="mb-2 block text-xs font-medium text-[#073238]",
                    ),
                    rx.el.textarea(
                        id="discovery-reason",
                        name="reason",
                        required=True,
                        max_length=2000,
                        rows=3,
                        disabled=DiscoveryState.saving,
                        class_name="w-full rounded-sm border border-[#deded3] bg-[#faf9f4] p-3 text-sm text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                    ),
                ),
                rx.el.button(
                    rx.icon("save", class_name="h-4 w-4"),
                    rx.cond(
                        DiscoveryState.saving,
                        "Salvando com auditoria…",
                        "Salvar e validar",
                    ),
                    type="submit",
                    disabled=DiscoveryState.saving | DiscoveryState.loading,
                    class_name="flex min-h-12 w-full items-center justify-center gap-2 rounded-sm bg-[#073238] px-5 text-sm font-medium text-[#faf9f4] hover:bg-[#0B4146] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
                ),
                on_submit=DiscoveryState.save,
                key=DiscoveryState.version,
                class_name="mt-6 flex w-full flex-col gap-5",
            ),
        ),
        id="discovery-editor",
        class_name="min-w-0 w-full scroll-mt-6 rounded-sm border border-[#deded3] bg-white p-5 md:p-7",
    )


def record_card(row: dict[str, str]) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.h3(
                f"#{row['id']} · {row['title']}",
                class_name="break-words text-sm font-medium text-[#073238]",
            ),
            rx.el.span(
                row["status"],
                class_name="w-fit shrink-0 rounded-sm border border-[#deded3] bg-[#faf9f4] px-2 py-1 text-xs text-[#073238]",
            ),
            class_name="flex flex-wrap items-start justify-between gap-3",
        ),
        rx.el.p(
            row["details"],
            class_name="mt-3 break-words text-xs leading-6 text-[#596c69]",
        ),
        rx.cond(
            row["demo"] == "true",
            rx.el.p(
                "Demonstração · somente rascunho · preço legado não é evidência.",
                class_name="mt-2 text-xs leading-5 text-[#8b7846]",
            ),
        ),
        rx.cond(
            DiscoveryState.kind == "duplicate",
            rx.el.pre(
                row["extra"],
                class_name="mt-3 max-h-48 overflow-auto whitespace-pre-wrap break-words rounded-sm bg-[#faf9f4] p-3 text-xs text-[#073238]",
            ),
        ),
        rx.cond(
            DiscoveryState.kind != "observation",
            rx.el.button(
                rx.icon("pencil", class_name="h-4 w-4"),
                "Abrir / revisar",
                type="button",
                on_click=DiscoveryState.edit(row["id"]),
                disabled=DiscoveryState.saving | DiscoveryState.loading,
                aria_label=f"Editar registro {row['id']}",
                class_name="mt-4 flex min-h-10 items-center gap-2 rounded-sm border border-[#deded3] bg-white px-3 text-xs text-[#073238] hover:bg-[#faf9f4] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
        ),
        key=row["id"],
        class_name="w-full border-b border-[#deded3] py-5 last:border-b-0",
    )


def record_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.h3(
                "Registros & revisão",
                class_name="font-['Cormorant_Garamond'] text-3xl text-[#073238]",
            ),
            rx.el.button(
                rx.icon("refresh-cw", class_name="h-4 w-4"),
                "Atualizar",
                on_click=DiscoveryState.load,
                disabled=DiscoveryState.loading | DiscoveryState.saving,
                type="button",
                class_name="flex min-h-11 items-center gap-2 rounded-sm border border-[#deded3] bg-white px-3 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            class_name="flex flex-wrap items-center justify-between gap-3",
        ),
        rx.el.form(
            rx.el.div(
                rx.el.label(
                    "Buscar por título/nome ou ID",
                    html_for="discovery-query",
                    class_name="mb-2 block text-xs text-[#073238]",
                ),
                rx.el.input(
                    id="discovery-query",
                    name="query",
                    default_value=DiscoveryState.query,
                    key=DiscoveryState.query,
                    class_name="min-h-11 w-full rounded-sm border border-[#deded3] bg-[#faf9f4] p-3 text-sm text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
            ),
            rx.el.div(
                rx.el.label(
                    "Contexto: ID do produto (opcional)",
                    html_for="discovery-product-filter",
                    class_name="mb-2 block text-xs text-[#073238]",
                ),
                rx.el.input(
                    id="discovery-product-filter",
                    name="product_filter",
                    type="number",
                    default_value=rx.cond(
                        DiscoveryState.product_filter > 0,
                        DiscoveryState.product_filter.to_string(),
                        "",
                    ),
                    key=DiscoveryState.product_filter,
                    class_name="min-h-11 w-full rounded-sm border border-[#deded3] bg-[#faf9f4] p-3 text-sm text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
            ),
            rx.el.div(
                rx.el.label(
                    "Estado (vazio = todos)",
                    html_for="discovery-status-filter",
                    class_name="mb-2 block text-xs text-[#073238]",
                ),
                rx.el.div(
                    rx.el.select(
                        rx.el.option("Todos", value=""),
                        rx.foreach(
                            [
                                "draft",
                                "in_review",
                                "published",
                                "archived",
                                "active",
                                "inactive",
                                "unavailable",
                                "invalid",
                                "pending",
                                "valid",
                                "expired",
                                "duplicate",
                                "distinct",
                                "dismissed",
                            ],
                            lambda status: rx.el.option(
                                rx.Var.create(STATUS_NAMES).get(status, status),
                                value=status,
                            ),
                        ),
                        id="discovery-status-filter",
                        name="status",
                        default_value=DiscoveryState.status_filter,
                        class_name="min-h-11 w-full appearance-none rounded-sm border border-[#deded3] bg-[#faf9f4] p-3 pr-10 text-sm text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                    ),
                    rx.icon(
                        "chevron-down",
                        aria_hidden=True,
                        class_name="pointer-events-none absolute right-3 top-3.5 h-4 w-4 text-[#073238]",
                    ),
                    class_name="relative",
                ),
            ),
            rx.el.button(
                "Filtrar / limpar com campos vazios",
                type="submit",
                disabled=DiscoveryState.loading | DiscoveryState.saving,
                class_name="min-h-11 rounded-sm border border-[#deded3] bg-white px-3 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            on_submit=DiscoveryState.filter_records,
            class_name="mt-6 flex flex-col gap-4",
        ),
        rx.el.p(
            f"{DiscoveryState.total} registros · página {DiscoveryState.page}",
            class_name="mt-6 text-xs text-[#596c69]",
        ),
        rx.cond(
            DiscoveryState.loading,
            rx.el.div(
                "Carregando registros…",
                role="status",
                class_name="mt-5 animate-pulse rounded-sm bg-[#faf9f4] p-8 text-sm text-[#596c69]",
            ),
            rx.cond(
                DiscoveryState.rows.length() == 0,
                rx.el.div(
                    rx.icon(
                        "folder-open",
                        class_name="mx-auto h-7 w-7 text-[#8b7846]",
                    ),
                    rx.el.p(
                        "Nenhum registro neste contexto. Crie um registro, limpe os filtros ou atualize. Ofertas e observações não são geradas a partir do catálogo demonstrativo.",
                        class_name="mt-4 text-sm leading-6 text-[#596c69]",
                    ),
                    class_name="mt-5 border border-dashed border-[#deded3] bg-[#faf9f4] p-6 text-center",
                ),
                rx.el.div(
                    rx.foreach(DiscoveryState.rows, record_card),
                    class_name="mt-3 w-full",
                ),
            ),
        ),
        rx.el.div(
            rx.el.button(
                "Anterior",
                on_click=DiscoveryState.change_page(-1),
                disabled=(DiscoveryState.page <= 1)
                | DiscoveryState.loading
                | DiscoveryState.saving,
                class_name="min-h-11 rounded-sm border border-[#deded3] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-40",
            ),
            rx.el.button(
                "Próxima",
                on_click=DiscoveryState.change_page(1),
                disabled=(DiscoveryState.page * 15 >= DiscoveryState.total)
                | DiscoveryState.loading
                | DiscoveryState.saving,
                class_name="min-h-11 rounded-sm border border-[#deded3] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-40",
            ),
            class_name="mt-6 flex justify-between gap-3",
        ),
        class_name="min-w-0 w-full rounded-sm border border-[#deded3] bg-white p-5 md:p-7",
    )


def discovery_workspace() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.icon("notebook-pen", class_name="h-5 w-5 text-[#d4af37]"),
                rx.el.p(
                    "Viktrine · CURADORIA EDITORIAL",
                    class_name="text-[10px] tracking-[0.18em] text-[#d4af37]",
                ),
                class_name="flex items-center gap-3",
            ),
            rx.el.h2(
                "Do produto à oferta, com evidência.",
                class_name="mt-4 font-['Cormorant_Garamond'] text-4xl text-[#faf9f4]",
            ),
            rx.el.p(
                "1. Cadastre categorias, lojas e programas. 2. Crie o produto e suas variantes. 3. Cadastre ofertas independentes e seus links. 4. Registre preço real, revise o link e publique a oferta. 5. Revise duplicados e publique o editorial.",
                class_name="mt-4 max-w-4xl text-sm leading-7 text-[#faf9f4]",
            ),
            rx.el.p(
                "Observação manual registra apenas o que o administrador viu na fonte e horário informados. Não há conexão automática com marketplaces, comprovação de venda ou comissão. Checagem HTTP sob demanda está disponível em Operações, sem seguir redirecionamentos nem substituir a revisão manual. Alterações que invalidam evidências retiram a publicação dependente, com auditoria. Não há exclusão física de registros editoriais.",
                class_name="mt-4 max-w-4xl text-xs leading-6 text-[#faf9f4]",
            ),
            class_name="mb-7 rounded-sm bg-[#073238] p-6 md:p-9",
        ),
        rx.el.nav(
            rx.foreach(PANELS, panel_button),
            aria_label="Painéis de curadoria",
            class_name="mb-7 flex flex-wrap gap-2",
        ),
        rx.el.h2(
            DiscoveryState.heading,
            class_name="mb-3 font-['Cormorant_Garamond'] text-4xl text-[#073238]",
        ),
        rx.el.p(
            DiscoveryState.context, class_name="mb-5 text-xs text-[#596c69]"
        ),
        rx.el.p(
            "Os IDs exibidos na lista vinculam registros. Use o filtro de produto para trabalhar suas variantes, ofertas, links, evidências e duplicados. Salve o rascunho antes de cadastrar seus vínculos. Revisões precisam ser reconfirmadas ao editar; novas observações preservam o histórico e exigem nova revisão da oferta.",
            class_name="mb-6 text-xs leading-6 text-[#596c69]",
        ),
        rx.cond(
            DiscoveryState.error != "",
            rx.el.p(
                DiscoveryState.error,
                role="alert",
                class_name="mb-5 rounded-sm border border-red-200 bg-red-50 p-4 text-sm text-red-700",
            ),
        ),
        rx.cond(
            DiscoveryState.notice != "",
            rx.el.p(
                DiscoveryState.notice,
                role="status",
                class_name="mb-5 rounded-sm border border-green-200 bg-green-50 p-4 text-sm text-green-700",
            ),
        ),
        rx.el.div(
            editor(),
            record_list(),
            class_name="grid w-full grid-cols-1 items-start gap-6 xl:grid-cols-2",
        ),
        discovery_audit(),
        class_name="mb-10 w-full",
    )
