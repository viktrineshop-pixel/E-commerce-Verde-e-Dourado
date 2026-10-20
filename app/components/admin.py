import reflex as rx
import json
from app.states.admin_state import AdminState, AdminProduct
from app.components.admin_orders import admin_orders
from app.components.admin_clicks import admin_clicks
from app.components.admin_coupons import admin_coupons
from app.components.discovery import discovery_workspace


_CATEGORY_SUGGESTIONS = [
    rx.el.button(
        label,
        type="button",
        on_click=[
            AdminState.set_field("category", label),
            rx.call_script(
                f"(() => {{ const input = document.getElementById('admin-category'); if (input) {{ input.value = {json.dumps(label)}; }} }})()"
            ),
        ],
        disabled=AdminState.busy,
        key=label,
        class_name="min-h-9 w-fit rounded-full border border-[#d8d7cc] bg-[#faf9f4] px-3 py-1 text-[11px] text-[#073238] hover:border-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
    )
    for label in (
        "Feminino",
        "Masculino",
        "Acessórios",
        "Casa",
        "Veículos",
        "Jardinagem",
        "Eletrodomésticos",
        "Notebooks",
    )
]


def admin_field(field: str, label: str, placeholder: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            html_for=f"admin-{field}",
            class_name="mb-2 block text-xs font-medium text-[#0d231d]",
        ),
        rx.el.input(
            id=f"admin-{field}",
            on_change=lambda value: AdminState.set_field(field, value),
            placeholder=placeholder,
            disabled=AdminState.busy,
            aria_invalid=AdminState.errors.get(field, "") != "",
            aria_describedby=f"error-{field}",
            class_name="min-h-11 w-full rounded-sm border border-[#d8d7cc] bg-[#faf9f4] px-3 py-2 text-sm text-[#0d231d] placeholder:text-[#7b827a] focus:border-[#073238] focus:outline-2 focus:outline-[#d4af37] disabled:opacity-50",
            default_value=AdminState.draft[field],
        ),
        rx.el.p(
            AdminState.errors.get(field, ""),
            id=f"error-{field}",
            class_name="mt-1 text-xs text-red-600",
        ),
        class_name="min-w-0 w-full",
    )


def product_editor() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.h2(
                rx.cond(AdminState.editing, "Editar produto", "Criar produto"),
                class_name="font-['Cormorant_Garamond'] text-3xl text-[#073238]",
            ),
            rx.el.button(
                rx.icon("plus", class_name="h-4 w-4"),
                "Novo cadastro",
                type="button",
                on_click=AdminState.new_product,
                disabled=AdminState.busy,
                class_name="flex min-h-11 items-center gap-2 rounded-sm border border-[#d8d7cc] bg-white px-3 text-xs text-[#073238] hover:bg-[#faf9f4] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            class_name="flex flex-wrap items-center justify-between gap-3",
        ),
        rx.el.p(
            "SKU · Identificador permanente",
            class_name="mt-5 text-xs font-medium text-[#687268]",
        ),
        rx.el.p(
            AdminState.sku, class_name="mt-1 break-all text-xs text-[#0d231d]"
        ),
        rx.el.div(
            admin_field("title", "Título *", "Nome do produto"),
            admin_field(
                "description",
                "Descrição *",
                "Detalhes, materiais, medidas e características",
            ),
            admin_field(
                "category",
                "Categoria *",
                "Escolha uma sugestão abaixo ou digite uma categoria",
            ),
            rx.el.div(
                *_CATEGORY_SUGGESTIONS,
                class_name="flex flex-wrap gap-2",
            ),
            rx.el.div(
                rx.el.label(
                    "Loja parceira *",
                    html_for="admin-partner_name",
                    class_name="mb-2 block text-xs font-medium text-[#0d231d]",
                ),
                rx.el.div(
                    rx.el.select(
                        rx.foreach(
                            ["Amazon", "Mercado Livre", "Shopee"],
                            lambda partner: rx.el.option(
                                partner, value=partner
                            ),
                        ),
                        id="admin-partner_name",
                        value=AdminState.draft["partner_name"],
                        on_change=lambda value: AdminState.set_field(
                            "partner_name", value
                        ),
                        disabled=AdminState.busy,
                        aria_invalid=AdminState.errors.get("partner_name", "")
                        != "",
                        aria_describedby="error-partner_name",
                        class_name="min-h-11 w-full appearance-none rounded-sm border border-[#d8d7cc] bg-[#faf9f4] px-3 py-2 pr-10 text-sm text-[#0d231d] focus:outline-2 focus:outline-[#d4af37] disabled:opacity-50",
                    ),
                    rx.icon(
                        "chevron-down",
                        aria_hidden=True,
                        class_name="pointer-events-none absolute right-3 top-3.5 h-4 w-4 text-[#073238]",
                    ),
                    class_name="relative w-full",
                ),
                rx.el.p(
                    AdminState.errors.get("partner_name", ""),
                    id="error-partner_name",
                    class_name="mt-1 text-xs text-red-600",
                ),
                class_name="w-full",
            ),
            admin_field(
                "affiliate_url", "URL de afiliado HTTPS (opcional)", "https://…"
            ),
            rx.el.p(
                "Deixe em branco para abrir a página interna da loja selecionada. Nenhum link externo é criado automaticamente.",
                class_name="text-xs leading-5 text-[#687268]",
            ),
            admin_field(
                "image_url",
                "URL de imagem permanente *",
                "https://… ou /imagem.png",
            ),
            rx.el.div(
                rx.el.img(
                    src=AdminState.preview_url,
                    alt="Prévia da imagem do produto",
                    class_name="h-40 w-32 shrink-0 rounded-sm bg-[#faf9f4] object-contain",
                ),
                rx.el.p(
                    "Prévia ao digitar. Use uma imagem acessível e permanente. Imagens externas são carregadas diretamente da URL; uploads temporários não são aceitos.",
                    class_name="text-xs leading-5 text-[#687268]",
                ),
                class_name="flex items-center gap-4 rounded-sm border border-[#deded3] p-3",
            ),
            rx.el.div(
                admin_field("price", "Preço em BRL *", "129,90"),
                admin_field(
                    "compare_price",
                    "Preço anterior em BRL (opcional)",
                    "159,90",
                ),
                class_name="grid grid-cols-1 gap-4 sm:grid-cols-2",
            ),
            rx.el.div(
                admin_field("stock", "Estoque *", "0"),
                admin_field("badge", "Selo (opcional)", "Novidade"),
                class_name="grid grid-cols-1 gap-4 sm:grid-cols-2",
            ),
            rx.el.button(
                rx.cond(
                    AdminState.featured,
                    rx.icon(
                        "square-check", class_name="h-5 w-5 text-[#073238]"
                    ),
                    rx.icon("square", class_name="h-5 w-5 text-[#073238]"),
                ),
                "Destaque / achados",
                type="button",
                role="switch",
                aria_checked=AdminState.featured,
                on_click=AdminState.toggle_featured,
                disabled=AdminState.busy,
                class_name="flex min-h-11 w-fit items-center gap-3 rounded-sm bg-[#faf9f4] px-3 text-sm text-[#0d231d] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            rx.el.button(
                rx.icon("save", class_name="h-4 w-4"),
                rx.cond(AdminState.busy, "Processando…", "Salvar produto"),
                type="button",
                on_click=rx.call_script(
                    "Object.fromEntries(Array.from(document.querySelectorAll('#product-editor input, #product-editor select')).map(el => [el.id.replace('admin-', ''), el.value]))",
                    callback=AdminState.save_product,
                ),
                disabled=AdminState.busy,
                class_name="flex min-h-12 w-full items-center justify-center gap-2 rounded-sm bg-[#073238] px-5 py-3 text-sm font-medium text-[#faf9f4] hover:bg-[#0d231d] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            rx.el.p(
                "* Campos obrigatórios. Valores com até duas casas decimais; estoque inteiro. Salvar mantém o formulário para ajustes adicionais.",
                class_name="text-xs leading-5 text-[#687268]",
            ),
            class_name="mt-6 flex flex-col gap-5",
        ),
        id="product-editor",
        key=AdminState.sku,
        class_name="min-w-0 scroll-mt-6 rounded-sm border border-[#deded3] bg-white p-5 md:p-7",
    )


def admin_product_row(product: AdminProduct) -> rx.Component:
    return rx.el.article(
        rx.el.img(
            src=product["image_url"],
            alt=product["title"],
            loading="lazy",
            class_name="h-20 w-16 shrink-0 rounded-sm bg-[#faf9f4] object-cover",
        ),
        rx.el.div(
            rx.el.h3(
                product["title"],
                class_name="break-words text-sm font-medium text-[#0d231d]",
            ),
            rx.el.p(
                f"{product['category']} · {product['partner_name']}",
                class_name="mt-1 text-xs text-[#687268]",
            ),
            rx.el.p(
                product["sku"],
                class_name="mt-1 break-all text-[10px] text-[#7b827a]",
            ),
            rx.el.div(
                rx.el.span(
                    product["price"],
                    class_name="text-sm font-semibold text-[#073238]",
                ),
                rx.el.span(
                    f"{product['stock']} em estoque",
                    class_name="text-xs text-[#687268]",
                ),
                class_name="mt-3 flex flex-wrap items-center gap-4",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("pencil", class_name="h-3.5 w-3.5"),
                    "Editar",
                    type="button",
                    on_click=AdminState.edit_product(product["id"]),
                    disabled=AdminState.busy,
                    aria_label=f"Editar {product['title']}",
                    class_name="flex min-h-10 items-center gap-2 rounded-sm border border-[#d8d7cc] bg-white px-3 text-xs text-[#073238] hover:bg-[#faf9f4] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
                ),
                rx.el.button(
                    rx.icon("trash-2", class_name="h-3.5 w-3.5"),
                    "Excluir",
                    type="button",
                    on_click=AdminState.request_delete(product["id"]),
                    disabled=AdminState.busy,
                    aria_label=f"Excluir {product['title']}",
                    class_name="flex min-h-10 items-center gap-2 rounded-sm border border-red-200 bg-white px-3 text-xs text-red-600 hover:bg-red-50 focus-visible:outline-2 focus-visible:outline-red-500 disabled:opacity-50",
                ),
                class_name="mt-3 flex flex-wrap gap-2",
            ),
            class_name="min-w-0 flex-1",
        ),
        key=product["id"],
        class_name="flex min-w-0 gap-4 border-b border-[#deded3] py-5 last:border-b-0",
    )


def product_list() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.h2(
                "Seu catálogo",
                class_name="font-['Cormorant_Garamond'] text-3xl text-[#073238]",
            ),
            rx.el.button(
                rx.icon("refresh-cw", class_name="h-4 w-4"),
                "Atualizar",
                type="button",
                on_click=AdminState.load_products,
                disabled=AdminState.loading | AdminState.busy,
                class_name="flex min-h-11 items-center gap-2 rounded-sm border border-[#d8d7cc] bg-white px-3 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            class_name="flex flex-wrap items-center justify-between gap-3",
        ),
        rx.el.p(
            f"{AdminState.total} produtos · página {AdminState.page}",
            class_name="mt-3 text-xs text-[#687268]",
        ),
        rx.cond(
            AdminState.loading,
            rx.el.div(
                "Carregando catálogo…",
                role="status",
                class_name="mt-6 animate-pulse rounded-sm bg-[#faf9f4] p-8 text-sm text-[#687268]",
            ),
            rx.cond(
                AdminState.products.length() == 0,
                rx.el.div(
                    rx.icon(
                        "package-open",
                        class_name="mx-auto h-8 w-8 text-[#8b7846]",
                    ),
                    rx.el.p(
                        "Nenhum produto nesta lista. Crie seu primeiro cadastro ou atualize para tentar novamente.",
                        class_name="mt-4 text-sm text-[#687268]",
                    ),
                    class_name="mt-6 border border-dashed border-[#d8d7cc] p-8 text-center",
                ),
                rx.el.div(
                    rx.foreach(AdminState.products, admin_product_row),
                    class_name="mt-2 w-full",
                ),
            ),
        ),
        rx.el.div(
            rx.el.button(
                "Anterior",
                type="button",
                on_click=AdminState.change_page(-1),
                disabled=(AdminState.page <= 1)
                | AdminState.loading
                | AdminState.busy,
                class_name="min-h-11 rounded-sm border border-[#d8d7cc] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-40",
            ),
            rx.el.button(
                "Próxima",
                type="button",
                on_click=AdminState.change_page(1),
                disabled=(AdminState.page * 20 >= AdminState.total)
                | AdminState.loading
                | AdminState.busy,
                class_name="min-h-11 rounded-sm border border-[#d8d7cc] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-40",
            ),
            class_name="mt-5 flex justify-between gap-3",
        ),
        class_name="min-w-0 rounded-sm border border-[#deded3] bg-white p-5 md:p-7",
    )


def admin_workspace() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.cond(
                AdminState.error != "",
                rx.el.p(
                    AdminState.error,
                    role="alert",
                    class_name="mb-4 rounded-sm border border-red-200 bg-red-50 p-4 text-sm text-red-700",
                ),
            ),
            rx.cond(
                AdminState.notice != "",
                rx.el.p(
                    AdminState.notice,
                    role="status",
                    class_name="mb-4 rounded-sm border border-green-200 bg-green-50 p-4 text-sm text-green-700",
                ),
            ),
            aria_live="polite",
        ),
        rx.cond(
            AdminState.delete_title != "",
            rx.el.div(
                rx.el.h2(
                    "Confirmar exclusão",
                    class_name="text-base font-semibold text-red-700",
                ),
                rx.el.p(
                    f"Excluir definitivamente “{AdminState.delete_title}”? Esta ação não pode ser desfeita.",
                    class_name="mt-2 break-words text-sm text-[#0d231d]",
                ),
                rx.el.p(
                    "O produto será retirado das sacolas. Os dados históricos dos pedidos serão preservados.",
                    class_name="mt-2 text-xs text-[#687268]",
                ),
                rx.el.div(
                    rx.el.button(
                        "Cancelar",
                        type="button",
                        on_click=AdminState.cancel_delete,
                        disabled=AdminState.busy,
                        class_name="min-h-11 rounded-sm border border-[#d8d7cc] bg-white px-4 text-sm text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
                    ),
                    rx.el.button(
                        "Sim, excluir definitivamente",
                        type="button",
                        on_click=AdminState.confirm_delete,
                        disabled=AdminState.busy,
                        class_name="min-h-11 rounded-sm bg-red-700 px-4 text-sm text-white hover:bg-red-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-500 disabled:opacity-50",
                    ),
                    class_name="mt-4 flex flex-wrap gap-3",
                ),
                role="alert",
                class_name="mb-6 rounded-sm border border-red-200 bg-red-50 p-5",
            ),
        ),
        discovery_workspace(),
        admin_orders(),
        admin_clicks(),
        admin_coupons(),
        class_name="w-full",
    )


def admin_content() -> rx.Component:
    return rx.el.div(
        rx.el.p(
            "Viktrine · ADMINISTRAÇÃO",
            class_name="text-[10px] font-medium tracking-[0.2em] text-[#8b7846]",
        ),
        rx.el.h1(
            "A curadoria está em suas mãos.",
            class_name="mt-3 font-['Cormorant_Garamond'] text-4xl leading-tight text-[#073238] sm:text-5xl",
        ),
        rx.el.p(
            "Organize produtos editoriais e ofertas de lojas externas, com revisão, evidências e auditoria. Os pedidos históricos, relatórios e cupons existentes são preservados nesta etapa.",
            class_name="mt-4 max-w-3xl text-sm leading-6 text-[#687268]",
        ),
        rx.el.div(
            rx.cond(
                AdminState.role_loading,
                rx.el.div(
                    "Verificando seu acesso…",
                    role="status",
                    class_name="animate-pulse rounded-sm border border-[#deded3] bg-white p-8 text-sm text-[#687268]",
                ),
                rx.cond(
                    AdminState.can_manage,
                    admin_workspace(),
                    rx.el.section(
                        rx.icon(
                            "shield-alert", class_name="h-8 w-8 text-[#8b7846]"
                        ),
                        rx.el.h2(
                            "Área exclusiva da administração",
                            class_name="mt-4 font-['Cormorant_Garamond'] text-3xl text-[#073238]",
                        ),
                        rx.el.p(
                            rx.cond(
                                AdminState.role_error != "",
                                AdminState.role_error,
                                "Sua conta não possui permissão para gerenciar produtos. Você pode continuar explorando a vitrine e consultando seus pedidos.",
                            ),
                            class_name="mt-3 text-sm leading-6 text-[#687268]",
                        ),
                        rx.el.div(
                            rx.el.a(
                                "Voltar à vitrine",
                                href="/",
                                class_name="flex min-h-11 items-center rounded-sm bg-[#073238] px-4 text-xs text-[#faf9f4] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                            ),
                            rx.el.button(
                                "Verificar acesso novamente",
                                type="button",
                                on_click=AdminState.load_dashboard,
                                class_name="min-h-11 rounded-sm border border-[#d8d7cc] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                            ),
                            class_name="mt-5 flex flex-wrap gap-3",
                        ),
                        class_name="rounded-sm border border-[#deded3] bg-white p-6 sm:p-10",
                    ),
                ),
            ),
            class_name="mt-8 w-full",
        ),
        class_name="mx-auto w-full max-w-[1440px] px-4 py-10 sm:px-6 lg:px-12 lg:py-14",
    )
