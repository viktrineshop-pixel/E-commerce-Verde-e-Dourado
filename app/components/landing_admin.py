import reflex as rx
from app.landing_products import LandingView, LandingMedia
from app.states.landing_admin_state import LandingAdminState
from app.states.admin_state import AdminState


def landing_field(
    name: str, label: str, limit: int, placeholder: str = ""
) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            html_for=f"landing-{name}",
            class_name="mb-2 block text-xs font-medium text-[#073238]",
        ),
        rx.el.input(
            name=name,
            id=f"landing-{name}",
            default_value=LandingAdminState.draft[name],
            key=LandingAdminState.draft[name],
            required=name != "slug",
            max_length=limit,
            placeholder=placeholder,
            disabled=LandingAdminState.busy,
            class_name="min-h-11 w-full rounded-sm border border-[#d8d7cc] bg-[#faf9f4] px-3 py-2 text-sm text-[#073238] placeholder:text-gray-500 focus:outline-2 focus:outline-[#d4af37] disabled:opacity-50",
        ),
        class_name="w-full",
    )


def landing_editor() -> rx.Component:
    return rx.el.section(
        rx.el.h2(
            rx.cond(
                LandingAdminState.editing_id > 0,
                "Editar página de produto",
                "Novo produto de afiliado",
            ),
            class_name="font-['Cormorant_Garamond'] text-3xl text-[#073238]",
        ),
        rx.el.p(
            "Salvar cria um rascunho ou despublica alterações. A publicação exige sua confirmação de revisão na lista abaixo.",
            class_name="mt-3 text-sm leading-6 text-gray-600",
        ),
        rx.el.form(
            landing_field("nome", "Nome do produto *", 250),
            rx.el.div(
                rx.el.label(
                    "Descrição *",
                    html_for="landing-descricao",
                    class_name="mb-2 block text-xs font-medium text-[#073238]",
                ),
                rx.el.textarea(
                    name="descricao",
                    id="landing-descricao",
                    default_value=LandingAdminState.draft["descricao"],
                    key=LandingAdminState.draft["descricao"],
                    required=True,
                    max_length=10000,
                    rows=5,
                    disabled=LandingAdminState.busy,
                    class_name="w-full rounded-sm border border-[#d8d7cc] bg-[#faf9f4] px-3 py-2 text-sm text-[#073238] focus:outline-2 focus:outline-[#d4af37] disabled:opacity-50",
                ),
            ),
            landing_field(
                "url", "URL original HTTPS de afiliado *", 2048, "https://…"
            ),
            landing_field(
                "slug",
                "Slug da página (editável)",
                250,
                "Gerado pelo nome se você deixar em branco",
            ),
            rx.el.button(
                "Gerar slug único pelo nome",
                type="button",
                disabled=LandingAdminState.busy,
                on_click=rx.call_script(
                    "document.getElementById('landing-nome').value",
                    callback=LandingAdminState.generate_slug,
                ),
                class_name="w-fit min-h-11 border border-[#d8d7cc] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            rx.el.p(
                "Endereço: /produto/seu-slug · Letras, números e hífens; acentos são normalizados. Slugs numéricos recebem o prefixo produto- para preservar o catálogo editorial.",
                class_name="text-xs leading-6 text-gray-600",
            ),
            rx.el.div(
                rx.el.button(
                    rx.cond(
                        LandingAdminState.busy, "Salvando…", "Salvar rascunho"
                    ),
                    type="submit",
                    disabled=LandingAdminState.busy,
                    class_name="min-h-12 rounded-sm bg-[#073238] px-5 py-3 text-sm font-medium text-[#faf9f4] hover:bg-[#0B4146] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
                ),
                rx.el.button(
                    "Novo cadastro",
                    type="button",
                    on_click=LandingAdminState.new_draft,
                    disabled=LandingAdminState.busy,
                    class_name="min-h-12 border border-[#d8d7cc] bg-white px-5 text-sm text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
                ),
                class_name="flex flex-wrap gap-3",
            ),
            on_submit=LandingAdminState.save_form,
            key=LandingAdminState.revision,
            class_name="mt-6 flex flex-col gap-5",
        ),
        rx.cond(
            LandingAdminState.editing_id > 0,
            rx.el.div(
                rx.el.h3(
                    "Imagens e vídeos deste produto",
                    class_name="font-['Cormorant_Garamond'] text-2xl text-[#073238]",
                ),
                rx.el.p(
                    f"Produto selecionado: {LandingAdminState.draft['nome']} · ID {LandingAdminState.editing_id}",
                    class_name="mt-2 text-sm text-gray-600",
                ),
                rx.el.p(
                    "JPEG, PNG, WebP, MP4 ou WebM. Até 6 arquivos por envio, 15 MiB por arquivo e 40 MiB por lote. Conteúdo conferido no servidor; o lote é salvo integralmente ou cancelado.",
                    class_name="mt-3 text-xs leading-6 text-gray-600",
                ),
                rx.upload.root(
                    rx.icon(
                        "upload",
                        class_name="mx-auto mb-3 h-6 w-6 text-[#8b7846]",
                    ),
                    rx.el.p(
                        "Selecionar imagens e vídeos ou arrastar arquivos aqui",
                        class_name="text-sm text-[#073238]",
                    ),
                    id="landing-media",
                    multiple=True,
                    max_files=6,
                    max_size=15728640,
                    accept={
                        "image/jpeg": [".jpg", ".jpeg"],
                        "image/png": [".png"],
                        "image/webp": [".webp"],
                        "video/mp4": [".mp4"],
                        "video/webm": [".webm"],
                    },
                    disabled=LandingAdminState.busy,
                    class_name="mt-4 cursor-pointer rounded-sm border border-dashed border-[#d8d7cc] bg-[#faf9f4] p-6 text-center text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
                rx.el.ul(
                    rx.foreach(
                        rx.selected_files("landing-media"),
                        lambda filename: rx.el.li(
                            filename,
                            class_name="break-all text-xs text-gray-600",
                        ),
                    ),
                    class_name="mt-3 space-y-2",
                ),
                rx.el.div(
                    rx.el.button(
                        rx.cond(
                            LandingAdminState.busy,
                            "Processando…",
                            "Enviar mídias para este produto",
                        ),
                        type="button",
                        disabled=LandingAdminState.busy,
                        on_click=LandingAdminState.upload_media(
                            rx.upload_files(upload_id="landing-media")
                        ),
                        class_name="min-h-11 bg-[#073238] px-4 py-3 text-xs text-[#faf9f4] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
                    ),
                    rx.el.button(
                        "Limpar seleção",
                        type="button",
                        on_click=rx.clear_selected_files("landing-media"),
                        disabled=LandingAdminState.busy,
                        class_name="min-h-11 border border-[#d8d7cc] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
                    ),
                    class_name="mt-4 flex flex-wrap gap-3",
                ),
                rx.el.p(
                    "Novas mídias despublicam o produto até a próxima revisão. Não apresente estes materiais como depoimentos de compradores verificados.",
                    class_name="mt-3 text-xs leading-6 text-gray-600",
                ),
                class_name="mt-8 border-t border-[#deded3] pt-6",
            ),
        ),
        class_name="rounded-sm border border-[#deded3] bg-white p-5 md:p-7",
    )


def admin_media_item(media: LandingMedia, product: LandingView) -> rx.Component:
    return rx.el.li(
        rx.el.span(
            f"{media['filename']} · {media['content_type']}",
            class_name="min-w-0 break-all text-xs text-gray-600",
        ),
        rx.el.button(
            "Remover mídia",
            on_click=LandingAdminState.remove_media(product["id"], media["id"]),
            disabled=LandingAdminState.busy,
            aria_label=f"Remover {media['filename']} de {product['nome']}",
            class_name="min-h-10 shrink-0 px-3 text-xs text-red-700 underline focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
        ),
        key=media["id"],
        class_name="flex flex-wrap items-center justify-between gap-3",
    )


def landing_admin_row(product: LandingView) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.h3(
                product["nome"],
                class_name="font-['Cormorant_Garamond'] text-2xl text-[#073238]",
            ),
            rx.el.span(
                rx.cond(product["published"], "Publicado", "Rascunho"),
                class_name=rx.cond(
                    product["published"],
                    "w-fit rounded-full bg-green-100 px-3 py-1 text-xs text-green-800",
                    "w-fit rounded-full bg-[#efede4] px-3 py-1 text-xs text-[#073238]",
                ),
            ),
            class_name="flex flex-wrap items-center justify-between gap-3",
        ),
        rx.el.p(
            product["descricao"],
            class_name="mt-3 whitespace-pre-wrap text-sm leading-6 text-gray-600",
        ),
        rx.el.p(
            f"/produto/{product['slug']}",
            class_name="mt-3 break-all text-xs text-[#073238]",
        ),
        rx.el.p(
            f"Destino original: {product['url']}",
            class_name="mt-2 break-all text-xs text-gray-600",
        ),
        rx.el.div(
            rx.el.button(
                "Editar / adicionar mídias",
                on_click=[
                    LandingAdminState.edit_product(product["id"]),
                    rx.clear_selected_files("landing-media"),
                ],
                disabled=LandingAdminState.busy,
                class_name="min-h-11 border border-[#d8d7cc] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
            ),
            rx.cond(
                product["published"],
                rx.el.button(
                    "Despublicar",
                    on_click=LandingAdminState.set_publication(
                        product["id"], False
                    ),
                    disabled=LandingAdminState.busy,
                    class_name="min-h-11 border border-[#073238] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
                ),
                rx.el.details(
                    rx.el.summary(
                        "Revisar para publicar",
                        class_name="cursor-pointer bg-[#073238] px-4 py-3 text-xs text-[#faf9f4] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                    ),
                    rx.el.p(
                        "Confirme que revisou o nome, a descrição, o destino original e todas as mídias listadas. Verifique direitos de uso e evite alegações não comprovadas. A página ficará pública ao confirmar.",
                        class_name="mt-3 max-w-xl text-xs leading-6 text-gray-600",
                    ),
                    rx.el.button(
                        "Revisei o conteúdo e as mídias — publicar",
                        on_click=LandingAdminState.set_publication(
                            product["id"], True
                        ),
                        disabled=LandingAdminState.busy,
                        class_name="mt-3 min-h-11 bg-[#073238] px-4 text-xs text-[#faf9f4] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
                    ),
                ),
            ),
            rx.cond(
                product["published"],
                rx.el.a(
                    "Abrir página pública",
                    href=f"/produto/{product['slug']}",
                    target="_blank",
                    rel="noopener noreferrer",
                    class_name="inline-flex min-h-11 items-center px-3 text-xs text-[#073238] underline focus-visible:outline-2 focus-visible:outline-[#d4af37]",
                ),
                rx.el.p(
                    "Prévia pública indisponível para rascunhos.",
                    class_name="self-center text-xs text-gray-600",
                ),
            ),
            class_name="mt-4 flex flex-wrap gap-3",
        ),
        rx.el.p(
            f"{product['media'].length()} mídias fornecidas pela administração",
            class_name="mt-4 text-xs text-gray-600",
        ),
        rx.el.ul(
            rx.foreach(
                product["media"], lambda media: admin_media_item(media, product)
            ),
            class_name="mt-2 space-y-2",
        ),
        key=product["id"],
        class_name="border-b border-[#deded3] py-6 last:border-b-0",
    )


def landing_admin_workspace() -> rx.Component:
    return rx.el.div(
        rx.cond(
            LandingAdminState.error != "",
            rx.el.p(
                LandingAdminState.error,
                role="alert",
                class_name="mb-5 border border-red-200 bg-red-50 p-4 text-sm text-red-700",
            ),
        ),
        rx.cond(
            LandingAdminState.notice != "",
            rx.el.p(
                LandingAdminState.notice,
                role="status",
                class_name="mb-5 border border-green-200 bg-green-50 p-4 text-sm text-green-800",
            ),
        ),
        landing_editor(),
        rx.el.section(
            rx.el.div(
                rx.el.h2(
                    "Páginas de produtos de afiliados",
                    class_name="font-['Cormorant_Garamond'] text-3xl text-[#073238]",
                ),
                rx.el.button(
                    "Atualizar lista",
                    on_click=LandingAdminState.load_products,
                    disabled=LandingAdminState.busy,
                    class_name="min-h-11 border border-[#d8d7cc] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
                ),
                class_name="flex flex-wrap items-center justify-between gap-3",
            ),
            rx.el.p(
                f"{LandingAdminState.total} produtos · página {LandingAdminState.page}",
                class_name="mt-3 text-xs text-gray-600",
            ),
            rx.cond(
                LandingAdminState.products.length() == 0,
                rx.el.p(
                    "Nenhum produto nesta página. Crie um rascunho acima ou atualize a lista.",
                    class_name="py-8 text-sm text-gray-600",
                ),
                rx.foreach(LandingAdminState.products, landing_admin_row),
            ),
            rx.el.div(
                rx.el.button(
                    "Anterior",
                    on_click=LandingAdminState.change_page(-1),
                    disabled=(LandingAdminState.page <= 1)
                    | LandingAdminState.busy,
                    class_name="min-h-11 border border-[#d8d7cc] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
                ),
                rx.el.button(
                    "Próxima",
                    on_click=LandingAdminState.change_page(1),
                    disabled=(
                        LandingAdminState.page * 20 >= LandingAdminState.total
                    )
                    | LandingAdminState.busy,
                    class_name="min-h-11 border border-[#d8d7cc] bg-white px-4 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#d4af37] disabled:opacity-50",
                ),
                class_name="mt-5 flex justify-between gap-3",
            ),
            class_name="mt-8 rounded-sm border border-[#deded3] bg-white p-5 md:p-7",
        ),
        class_name="w-full",
    )


def landing_admin_content() -> rx.Component:
    return rx.el.div(
        rx.el.a(
            "Voltar à administração",
            href="/admin",
            class_name="text-sm text-[#073238] underline focus-visible:outline-2 focus-visible:outline-[#d4af37]",
        ),
        rx.el.h1(
            "Produtos e materiais de divulgação",
            class_name="mt-5 font-['Cormorant_Garamond'] text-4xl text-[#073238] sm:text-5xl",
        ),
        rx.el.p(
            "Páginas independentes do catálogo editorial, sem preços inventados, checkout ou depoimentos verificados. Publicação manual após revisão.",
            class_name="mt-4 text-sm leading-6 text-gray-600",
        ),
        rx.cond(
            AdminState.role_loading,
            rx.el.p(
                "Verificando seu acesso…",
                role="status",
                class_name="mt-8 animate-pulse bg-white p-8 text-sm text-gray-600",
            ),
            rx.cond(
                AdminState.can_manage,
                landing_admin_workspace(),
                rx.el.p(
                    "Área exclusiva da administração. Sua conta não possui permissão para gerenciar estas páginas.",
                    role="alert",
                    class_name="mt-8 border border-[#deded3] bg-white p-8 text-sm text-[#073238]",
                ),
            ),
        ),
        class_name="mx-auto w-full max-w-[1440px] px-6 py-12 lg:px-12",
    )
