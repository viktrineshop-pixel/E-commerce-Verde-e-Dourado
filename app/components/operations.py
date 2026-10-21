import reflex as rx

from app.states.import_state import ImportState
from app.states.operations_state import OperationsState
from app.catalog_import import KINDS
from app.discovery import LABELS

BUTTON = "flex min-h-11 w-fit items-center justify-center gap-2 rounded-sm border border-[#deded3] bg-[#073238] px-4 py-2 text-xs text-[#faf9f4] hover:bg-[#0B4146] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#d4af37] disabled:opacity-50"
INPUT = "min-h-11 w-full rounded-sm border border-[#deded3] bg-[#faf9f4] px-3 text-sm text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37]"
SECTION = (
    "mb-7 w-full min-w-0 rounded-sm border border-[#deded3] bg-white p-5 md:p-7"
)


def import_kind(kind: str) -> rx.Component:
    return rx.el.button(
        rx.Var.create(LABELS).get(kind, kind),
        type="button",
        on_click=ImportState.choose(kind),
        disabled=ImportState.busy,
        aria_pressed=ImportState.kind == kind,
        class_name=rx.cond(
            ImportState.kind == kind,
            BUTTON,
            "min-h-11 rounded-sm border border-[#deded3] bg-[#faf9f4] px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
        ),
    )


def csv_import() -> rx.Component:
    return rx.el.section(
        rx.el.h2(
            "Importação responsável",
            class_name="font-['Cormorant_Garamond'] text-3xl text-[#073238]",
        ),
        rx.el.p(
            "Um tipo por arquivo · UTF-8 com ou sem BOM · vírgulas · até 512 KiB e 100 registros. Apenas inserções; nunca sobrescreve pedidos, demonstrações ou evidências. IDs dependentes devem existir antes do envio.",
            class_name="mt-3 text-xs leading-6 text-[#596c69]",
        ),
        rx.el.nav(
            rx.foreach(list(KINDS), import_kind),
            aria_label="Tipo de importação",
            class_name="mt-5 flex flex-wrap gap-2",
        ),
        rx.el.details(
            rx.el.summary(
                "Colunas, tipos e regras do modelo",
                class_name="cursor-pointer py-4 text-sm font-medium text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
            ),
            rx.el.pre(
                ImportState.header_template,
                class_name="overflow-x-auto whitespace-pre-wrap break-all bg-[#faf9f4] p-4 text-xs text-[#073238]",
            ),
            rx.el.p(
                "Campos de texto: texto simples, sem HTML (limites do editor). *_id: inteiro positivo existente; opcionais podem ficar vazios. position: inteiro ≥ 0. active: true/false. status: somente draft. validation_status: somente pending. attributes: objeto JSON. gtin: 8/12/13/14 dígitos com verificador. URLs: HTTPS seguro; imagens também aceitam caminhos permanentes locais. expires_at: ISO 8601 com fuso. Domínios: separados por espaço ou quebra de linha, sem protocolo/porta/curinga. Células com vírgula, quebra de linha ou aspas precisam de aspas CSV; duplique aspas internas. Colunas opcionais podem ser omitidas. Proveniência/evidências, preços, estoque, horários de observação e revisão não são importáveis. Loja/programa importados ficam rascunhos; ative manualmente antes de importar ofertas dependentes.",
                class_name="mt-3 text-xs leading-6 text-[#596c69]",
            ),
            rx.el.p(
                "Obrigatórios: categoria name; loja name; programa merchant_id e code; produto title; variante product_id e variant_key; oferta product_id e merchant_id; link offer_id, destination_url e affiliate_url. Colunas adicionais ou repetidas são recusadas. Não inclua credenciais nem dados pessoais.",
                class_name="mt-3 text-xs leading-6 text-[#596c69]",
            ),
        ),
        rx.el.button(
            rx.icon("download", class_name="h-4 w-4"),
            "Baixar cabeçalho CSV",
            type="button",
            on_click=ImportState.download_template,
            disabled=ImportState.busy,
            class_name=BUTTON,
        ),
        rx.upload.root(
            rx.icon("file-up", class_name="mx-auto h-7 w-7 text-[#8b7846]"),
            rx.el.p(
                "Selecionar CSV ou arrastar arquivo",
                class_name="mt-3 text-sm text-[#073238]",
            ),
            id="operational_csv",
            multiple=False,
            max_files=1,
            max_size=524288,
            accept={"text/csv": [".csv"]},
            disabled=ImportState.busy,
            class_name="mt-5 w-full cursor-pointer rounded-sm border border-dashed border-[#d4af37] bg-[#faf9f4] p-7 text-center focus-visible:outline-2 focus-visible:outline-[#d4af37]",
        ),
        rx.el.div(
            rx.foreach(
                rx.selected_files("operational_csv"),
                lambda name: rx.el.p(
                    name, class_name="break-all text-xs text-[#073238]"
                ),
            ),
            class_name="my-3",
        ),
        rx.el.button(
            rx.icon("scan-text", class_name="h-4 w-4"),
            rx.cond(
                ImportState.busy,
                "Processando…",
                "Enviar e validar sem escrever",
            ),
            on_click=ImportState.upload(
                rx.upload_files(upload_id="operational_csv")
            ),
            disabled=ImportState.busy,
            type="button",
            class_name=BUTTON,
        ),
        rx.cond(
            ImportState.busy,
            rx.el.p(
                "Validando ou confirmando lote…",
                role="status",
                class_name="mt-4 animate-pulse bg-[#faf9f4] p-4 text-xs text-[#073238]",
            ),
        ),
        rx.el.div(
            rx.foreach(
                ImportState.errors,
                lambda error: rx.el.p(
                    error,
                    role="alert",
                    class_name="mt-3 rounded-sm bg-red-50 p-3 text-xs text-red-700",
                ),
            )
        ),
        rx.cond(
            ImportState.notice != "",
            rx.el.p(
                ImportState.notice,
                role="status",
                class_name="mt-4 text-sm leading-6 text-[#073238]",
            ),
        ),
        rx.cond(
            ImportState.preview.length() > 0,
            rx.el.details(
                rx.el.summary(
                    f"Prévia · {ImportState.count} registros (até 20 exibidos)",
                    class_name="cursor-pointer py-4 text-sm text-[#073238]",
                ),
                rx.el.div(
                    rx.foreach(
                        ImportState.preview,
                        lambda row: rx.el.p(
                            row,
                            class_name="border-b border-[#deded3] py-3 text-xs text-[#073238]",
                        ),
                    ),
                    class_name="max-h-80 overflow-auto break-all",
                ),
                open=True,
            ),
        ),
        rx.cond(
            ImportState.ready,
            rx.el.form(
                rx.el.label(
                    "Motivo da importação *",
                    html_for="import-reason",
                    class_name="block text-xs font-medium text-[#073238]",
                ),
                rx.el.textarea(
                    id="import-reason",
                    name="reason",
                    required=True,
                    max_length=2000,
                    class_name=INPUT,
                ),
                rx.el.div(
                    rx.el.input(
                        id="import-confirm",
                        name="confirm",
                        type="checkbox",
                        required=True,
                        class_name="h-4 w-4 accent-[#073238]",
                    ),
                    rx.el.label(
                        "Conferi o lote. Confirmo inserir TODOS os registros como rascunho/pendente, sem evidência ou verificação. A transação será revalidada e revertida inteira se falhar.",
                        html_for="import-confirm",
                        class_name="text-xs leading-6 text-[#073238]",
                    ),
                    class_name="flex items-start gap-3",
                ),
                rx.el.button(
                    "Confirmar importação atômica",
                    type="submit",
                    disabled=ImportState.busy,
                    class_name=BUTTON,
                ),
                on_submit=ImportState.confirm,
                class_name="mt-6 flex flex-col gap-4 border-t border-[#deded3] pt-5",
            ),
        ),
        class_name=SECTION,
    )


def report_field(name: str, label: str, kind: str) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            html_for=f"op-{name}",
            class_name="mb-2 block text-xs text-[#073238]",
        ),
        rx.el.input(id=f"op-{name}", name=name, type=kind, class_name=INPUT),
        class_name="min-w-0 flex-1",
    )


def report_row(row: dict[str, str]) -> rx.Component:
    return rx.el.article(
        rx.el.h3(
            f"Oferta #{row['offer_id']} · {row['title']}",
            class_name="text-sm font-medium text-[#073238]",
        ),
        rx.el.p(
            f"{row['merchant']} · loja #{row['merchant_id']} · {row['clicks']} cliques · último: {row['latest']}",
            class_name="mt-2 text-xs leading-6 text-[#596c69]",
        ),
        key=row["offer_id"],
        class_name="border-b border-[#deded3] py-4",
    )


def pages(links: bool) -> rx.Component:
    return rx.el.div(
        rx.el.button(
            "Anterior",
            on_click=OperationsState.paginate(-1, links),
            disabled=OperationsState.loading
            | rx.cond(
                links, OperationsState.link_page <= 1, OperationsState.page <= 1
            ),
            class_name=BUTTON,
        ),
        rx.el.p(
            rx.cond(
                links,
                f"{OperationsState.link_total} links · página {OperationsState.link_page}",
                f"{OperationsState.total} ofertas com cliques · página {OperationsState.page}",
            ),
            class_name="text-xs text-[#596c69]",
        ),
        rx.el.button(
            "Próxima",
            on_click=OperationsState.paginate(1, links),
            disabled=OperationsState.loading
            | rx.cond(
                links,
                OperationsState.link_page * 15 >= OperationsState.link_total,
                OperationsState.page * 15 >= OperationsState.total,
            ),
            class_name=BUTTON,
        ),
        class_name="mt-5 flex flex-wrap items-center justify-between gap-3",
    )


def health_row(row: dict[str, str]) -> rx.Component:
    return rx.el.article(
        rx.el.h3(
            f"Oferta #{row['offer_id']} · {row['title']} · {row['merchant']}",
            class_name="text-sm font-medium text-[#073238]",
        ),
        rx.el.p(
            f"Revisão do link: {row['validation_status']} · saúde HTTP: {row['network_health']} · HTTP: {row['http_status']} · checado em: {row['last_checked_at']}",
            class_name="mt-2 text-xs leading-6 text-[#596c69]",
        ),
        rx.cond(
            row["last_checked_at"] == "",
            rx.el.p(
                "Ainda não checado por HTTP.",
                class_name="mt-2 text-xs text-[#596c69]",
            ),
        ),
        rx.cond(
            row["validation_error"] != "",
            rx.el.p(
                row["validation_error"], class_name="mt-2 text-xs text-red-700"
            ),
        ),
        rx.cond(
            row["resolved_url"] != "",
            rx.el.p(
                f"URL acessada sem seguir redirects: {row['resolved_url']}",
                class_name="mt-2 break-all text-xs text-[#596c69]",
            ),
        ),
        rx.el.button(
            rx.icon("shield-check", class_name="h-4 w-4"),
            rx.cond(
                OperationsState.checking
                & (OperationsState.checking_id.to_string() == row["offer_id"]),
                "Checando…",
                "Checar HTTP desta oferta",
            ),
            on_click=OperationsState.check(row["offer_id"]),
            disabled=OperationsState.checking | OperationsState.loading,
            class_name=BUTTON,
        ),
        key=row["offer_id"],
        class_name="flex flex-col gap-3 border-b border-[#deded3] py-5",
    )


def operations() -> rx.Component:
    return rx.el.div(
        csv_import(),
        rx.el.section(
            rx.el.div(
                rx.el.h2(
                    "Operações & cliques reais",
                    class_name="font-['Cormorant_Garamond'] text-3xl text-[#073238]",
                ),
                rx.el.button(
                    rx.icon("refresh-cw", class_name="h-4 w-4"),
                    "Atualizar operações e links",
                    on_click=OperationsState.load,
                    disabled=OperationsState.loading,
                    class_name=BUTTON,
                ),
                class_name="flex flex-wrap items-center justify-between gap-3",
            ),
            rx.el.p(
                "Cliques registrados por offer_id, vinculados à oferta e loja atuais. Não são vendas, comissões, conversões ou visitantes únicos. Datas inclusivas em UTC. O resumo de lojas mostra até 15 lojas com mais cliques; a lista de ofertas é paginada.",
                class_name="mt-3 text-xs leading-6 text-[#596c69]",
            ),
            rx.el.form(
                report_field("start", "De (UTC)", "date"),
                report_field("end", "Até (UTC)", "date"),
                report_field(
                    "merchant", "ID da loja (vazio = todas)", "number"
                ),
                rx.el.button(
                    "Aplicar filtros",
                    type="submit",
                    disabled=OperationsState.loading,
                    class_name=BUTTON,
                ),
                on_submit=OperationsState.filter_report,
                class_name="mt-5 flex flex-col items-stretch gap-4 sm:flex-row sm:items-end",
            ),
            rx.cond(
                OperationsState.error != "",
                rx.el.p(
                    OperationsState.error,
                    role="alert",
                    class_name="mt-4 bg-red-50 p-4 text-sm text-red-700",
                ),
            ),
            rx.cond(
                OperationsState.notice != "",
                rx.el.p(
                    OperationsState.notice,
                    role="status",
                    class_name="mt-4 bg-[#faf9f4] p-4 text-sm leading-6 text-[#073238]",
                ),
            ),
            rx.cond(
                OperationsState.loading,
                rx.el.p(
                    "Carregando dados persistidos…",
                    role="status",
                    class_name="mt-5 animate-pulse bg-[#faf9f4] p-6 text-sm text-[#073238]",
                ),
            ),
            rx.el.div(
                rx.foreach(
                    OperationsState.stores,
                    lambda row: rx.el.p(
                        f"{row['merchant']} · loja #{row['merchant_id']} · {row['clicks']} cliques",
                        class_name="rounded-sm border border-[#deded3] bg-[#faf9f4] p-4 text-xs text-[#073238]",
                    ),
                ),
                class_name="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3",
            ),
            rx.cond(
                OperationsState.reports.length() == 0,
                rx.el.p(
                    "Nenhum clique por oferta neste período/filtro.",
                    class_name="mt-5 border border-dashed border-[#deded3] p-5 text-sm text-[#596c69]",
                ),
                rx.el.div(rx.foreach(OperationsState.reports, report_row)),
            ),
            pages(False),
            rx.el.p(
                f"Arquivo legado separado: {OperationsState.legacy} cliques sem offer_id no período. Não são atribuídos a ofertas; o filtro de loja não se aplica a esses registros históricos.",
                class_name="mt-5 border-t border-[#deded3] pt-4 text-xs leading-6 text-[#596c69]",
            ),
            class_name=SECTION,
        ),
        rx.el.section(
            rx.el.h2(
                "Saúde HTTP dos links",
                class_name="font-['Cormorant_Garamond'] text-3xl text-[#073238]",
            ),
            rx.el.p(
                "Checagem sob demanda dos dois URLs persistidos da oferta. HTTPS, domínios autorizados e DNS com todos os IPs públicos; conexão fixada ao IP validado com TLS para o domínio. Redirects desligados, HEAD e GET limitado somente se HEAD não for suportado. Falhas invalidam o link e reavaliam publicações. HTTP 200 não comprova produto, preço, compra ou comissão. Uma checagem saudável nunca publica nem substitui a revisão manual. Cada resultado confirmado é auditado.",
                class_name="mt-3 text-xs leading-6 text-[#596c69]",
            ),
            rx.cond(
                OperationsState.links.length() == 0,
                rx.el.p(
                    "Nenhum link cadastrado para checar. Cadastre uma oferta e seu link pendente na curadoria.",
                    class_name="mt-5 border border-dashed border-[#deded3] p-5 text-sm text-[#596c69]",
                ),
                rx.el.div(rx.foreach(OperationsState.links, health_row)),
            ),
            pages(True),
            class_name=SECTION,
        ),
        rx.el.section(
            rx.el.h2(
                "Dependências externas · não conectadas",
                class_name="font-['Cormorant_Garamond'] text-3xl text-[#d4af37]",
            ),
            rx.el.p(
                "Conversões, vendas e comissões dependem das APIs/relatórios oficiais dos marketplaces ou redes de afiliados e atribuição comprovada. Cadastrar programa, importar CSV ou registrar clique não conecta essas fontes.",
                class_name="mt-4 text-sm leading-7 text-[#faf9f4]",
            ),
            rx.el.p(
                "Notificações dependem de um provedor autorizado e consentimento. Verificações recorrentes e automações dependem de agendamento e processamento de tarefas; atualmente a checagem é somente sob demanda. Operação contínua depende de serviços externos apropriados. Nada disso foi inicializado ou simulado. Não informe credenciais em formulários ou arquivos CSV. A checagem HTTP geral não precisa de chave de marketplace.",
                class_name="mt-3 text-sm leading-7 text-[#faf9f4]",
            ),
            class_name="mb-7 rounded-sm bg-[#073238] p-6 md:p-8",
        ),
        class_name="w-full min-w-0",
    )
