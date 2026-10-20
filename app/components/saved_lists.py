import reflex as rx
from app.states.saved_list_state import (
    SavedListState,
    SavedListView,
    SavedItemView,
)
from app.states.favorite_state import FavoriteState


def list_add_control(product_id: rx.Var[int]) -> rx.Component:
    return rx.cond(
        FavoriteState.signed_in,
        rx.el.details(
            rx.el.summary(
                "Adicionar a uma lista",
                class_name="cursor-pointer py-3 text-xs text-[#073238] underline focus-visible:outline-2 focus-visible:outline-[#d4af37]",
            ),
            rx.el.form(
                rx.el.input(type="hidden", name="product_id", value=product_id),
                rx.el.label(
                    "Lista privada",
                    html_for=f"list-{product_id}",
                    class_name="block text-xs text-[#073238]",
                ),
                rx.el.div(
                    rx.el.select(
                        rx.el.option("Selecione sua lista", value="0"),
                        rx.foreach(
                            SavedListState.lists,
                            lambda l: rx.el.option(l["title"], value=l["id"]),
                        ),
                        name="list_id",
                        id=f"list-{product_id}",
                        class_name="mt-2 min-h-11 w-full appearance-none border border-gray-200 bg-white px-3 pr-8 text-xs text-[#073238] focus-visible:outline-2 focus-visible:outline-[#073238]",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="pointer-events-none absolute right-3 top-6 h-3 w-3 text-[#073238]",
                    ),
                    class_name="relative",
                ),
                rx.el.label(
                    "Nota (opcional)",
                    html_for=f"note-{product_id}",
                    class_name="mt-3 block text-xs text-[#073238]",
                ),
                rx.el.input(
                    name="note",
                    id=f"note-{product_id}",
                    class_name="mt-2 min-h-11 w-full border border-gray-200 bg-white px-3 text-xs text-[#073238]",
                ),
                rx.el.button(
                    "Salvar na lista",
                    type="submit",
                    disabled=SavedListState.loading,
                    class_name="mt-3 min-h-11 border border-[#d4af37] bg-[#073238] px-4 text-xs text-white disabled:opacity-50",
                ),
                rx.el.a(
                    "Criar ou gerenciar listas",
                    href="/minha-conta#listas",
                    class_name="mt-3 block text-xs text-[#073238] underline",
                ),
                on_submit=SavedListState.add_from_form,
                class_name="border border-gray-200 bg-[#faf9f4] p-4",
            ),
            class_name="w-full",
        ),
    )


def list_button(item: SavedListView) -> rx.Component:
    return rx.el.button(
        f"{item['title']} ({item['count']})",
        on_click=SavedListState.select_list(item["id"]),
        key=item["id"],
        class_name=rx.cond(
            SavedListState.selected == item["id"],
            "border border-[#d4af37] bg-[#073238] px-4 py-3 text-left text-xs text-white focus-visible:outline-2 focus-visible:outline-[#d4af37]",
            "border border-gray-200 bg-white px-4 py-3 text-left text-xs text-[#073238] hover:border-[#d4af37] focus-visible:outline-2 focus-visible:outline-[#d4af37]",
        ),
    )


def list_item(item: SavedItemView) -> rx.Component:
    return rx.el.div(
        rx.cond(
            item["published"],
            rx.el.a(
                item["title"],
                href=f"/produto/{item['id']}",
                class_name="text-sm text-[#073238] underline",
            ),
            rx.el.p(
                f"{item['title']} · Fora da descoberta pública",
                class_name="text-sm text-gray-600",
            ),
        ),
        rx.el.p(
            item["note"],
            class_name="mt-2 whitespace-pre-wrap text-xs text-gray-600",
        ),
        rx.el.button(
            "Remover",
            on_click=SavedListState.mutate(
                "remove", SavedListState.selected, item["id"], "", ""
            ),
            disabled=SavedListState.loading,
            class_name="mt-3 py-2 text-xs text-[#073238] underline",
        ),
        key=item["id"],
        class_name="border-b border-gray-200 py-4",
    )


def list_editor(editing: bool) -> rx.Component:
    return rx.el.form(
        rx.el.input(
            type="hidden",
            name="list_id",
            value=rx.cond(editing, SavedListState.selected, 0),
        ),
        rx.el.label(
            rx.cond(editing, "Nome da lista selecionada", "Nome da nova lista"),
            html_for=rx.cond(editing, "edit-list-title", "new-list-title"),
            class_name="block text-xs text-[#073238]",
        ),
        rx.el.input(
            name="title",
            id=rx.cond(editing, "edit-list-title", "new-list-title"),
            default_value=rx.cond(editing, SavedListState.title, ""),
            key=rx.cond(editing, SavedListState.title, "new-title"),
            required=True,
            max_length=250,
            class_name="mt-2 min-h-11 w-full border border-gray-200 bg-white px-3 text-sm text-[#073238]",
        ),
        rx.el.label(
            "Descrição (opcional)",
            html_for=rx.cond(
                editing, "edit-list-description", "new-list-description"
            ),
            class_name="mt-3 block text-xs text-[#073238]",
        ),
        rx.el.input(
            name="description",
            id=rx.cond(
                editing, "edit-list-description", "new-list-description"
            ),
            default_value=rx.cond(editing, SavedListState.description, ""),
            key=rx.cond(editing, SavedListState.description, "new-description"),
            class_name="mt-2 min-h-11 w-full border border-gray-200 bg-white px-3 text-sm text-[#073238]",
        ),
        rx.el.button(
            rx.cond(editing, "Salvar alterações", "Criar lista privada"),
            type="submit",
            disabled=SavedListState.loading,
            class_name="mt-4 min-h-11 border border-[#d4af37] bg-[#073238] px-4 text-xs text-white disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-[#d4af37]",
        ),
        on_submit=SavedListState.save_list,
        class_name="border border-gray-200 bg-white p-5",
    )


def lists_section() -> rx.Component:
    return rx.cond(
        FavoriteState.signed_in,
        rx.el.section(
            rx.el.h2(
                "Minhas listas privadas",
                class_name="font-['Cormorant_Garamond'] text-4xl text-[#073238]",
            ),
            rx.el.p(
                "Organize produtos sem reservar estoque nem comprar na Viktrine. Listas são exclusivas desta conta.",
                class_name="mt-3 text-sm text-gray-600",
            ),
            rx.el.p(
                SavedListState.error,
                role="alert",
                class_name="mt-4 text-sm text-red-700 empty:hidden",
            ),
            rx.el.p(
                SavedListState.notice,
                role="status",
                class_name="mt-3 text-sm text-[#073238] empty:hidden",
            ),
            rx.el.button(
                "Atualizar listas",
                on_click=SavedListState.load_lists,
                class_name="my-4 py-2 text-xs text-[#073238] underline",
            ),
            rx.cond(
                SavedListState.loading,
                rx.el.p(
                    "Atualizando listas…",
                    role="status",
                    class_name="animate-pulse text-sm text-gray-600",
                ),
            ),
            rx.el.div(
                list_editor(False),
                rx.el.div(
                    rx.foreach(SavedListState.lists, list_button),
                    class_name="flex flex-col gap-3",
                ),
                class_name="mt-5 grid gap-5 md:grid-cols-2",
            ),
            rx.el.div(
                rx.el.button(
                    "Listas anteriores",
                    on_click=SavedListState.change_list_page(-1),
                    disabled=SavedListState.list_page == 1,
                    class_name="py-3 text-xs text-[#073238] disabled:opacity-40",
                ),
                rx.el.button(
                    "Próximas listas",
                    on_click=SavedListState.change_list_page(1),
                    disabled=~SavedListState.more_lists,
                    class_name="py-3 text-xs text-[#073238] disabled:opacity-40",
                ),
                class_name="flex gap-6",
            ),
            rx.cond(
                SavedListState.selected > 0,
                rx.el.div(
                    list_editor(True),
                    rx.el.details(
                        rx.el.summary(
                            "Excluir esta lista",
                            class_name="cursor-pointer py-3 text-xs text-red-700",
                        ),
                        rx.el.button(
                            "Confirmar exclusão da lista e seus itens",
                            on_click=SavedListState.mutate(
                                "delete", SavedListState.selected, 0, "", ""
                            ),
                            class_name="border border-red-200 bg-red-50 p-3 text-xs text-red-700",
                        ),
                    ),
                    rx.cond(
                        SavedListState.items.length() == 0,
                        rx.el.p(
                            "Esta lista ainda não tem itens.",
                            class_name="py-5 text-sm text-gray-600",
                        ),
                        rx.foreach(SavedListState.items, list_item),
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Itens anteriores",
                            on_click=SavedListState.change_page(-1),
                            disabled=SavedListState.page == 1,
                            class_name="py-3 text-xs text-[#073238] disabled:opacity-40",
                        ),
                        rx.el.button(
                            "Próximos itens",
                            on_click=SavedListState.change_page(1),
                            disabled=~SavedListState.has_next,
                            class_name="py-3 text-xs text-[#073238] disabled:opacity-40",
                        ),
                        class_name="flex gap-6",
                    ),
                    class_name="mt-6",
                ),
            ),
            id="listas",
            class_name="mx-auto w-full max-w-[1440px] border-t border-gray-200 px-6 py-12 text-[#073238] lg:px-12",
        ),
    )
