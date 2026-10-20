import reflex as rx
import reflex_enterprise as rxe
import logging
from typing import Any, TypedDict
from uuid import uuid4
from sqlalchemy import text
from reflex_enterprise.auth import User
from app.public_catalog import PUBLIC_CTE, eligible_product


class SavedListView(TypedDict):
    id: int
    title: str
    description: str
    count: int


class SavedItemView(TypedDict):
    id: int
    title: str
    note: str
    published: bool


class SavedListState(rx.State):
    lists: list[SavedListView] = rxe.field([], auth=True)
    items: list[SavedItemView] = rxe.field([], auth=True)
    selected: int = rxe.field(0, auth=True)
    title: str = rxe.field("", auth=True)
    description: str = rxe.field("", auth=True)
    loading: bool = rxe.field(False, auth=True)
    error: str = rxe.field("", auth=True)
    notice: str = rxe.field("", auth=True)
    page: int = rxe.field(1, auth=True)
    has_next: bool = rxe.field(False, auth=True)
    list_page: int = rxe.field(1, auth=True)
    more_lists: bool = rxe.field(False, auth=True)
    _generation: int = 0

    @rxe.event(auth=False)
    def clear_presentation(self):
        self._generation += 1
        self.lists = []
        self.items = []
        self.selected = 0
        self.title = ""
        self.description = ""
        self.error = ""
        self.notice = ""
        self.loading = False
        self.page = 1
        self.list_page = 1
        self.more_lists = False
        self.has_next = False

    async def _subject(self) -> str:
        subject = (await User.current() or {}).get("sub", "")
        if (
            not isinstance(subject, str)
            or not subject.strip()
            or len(subject) > 255
        ):
            raise ValueError("Entre na conta para gerenciar suas listas.")
        return subject

    @rxe.event(auth=True)
    def select_list(self, list_id: int):
        self.selected = list_id
        self.page = 1
        return SavedListState.load_lists

    @rxe.event(auth=True)
    def change_page(self, direction: int):
        if direction == 1 and not self.has_next:
            return
        self.page = max(1, self.page + direction)
        return SavedListState.load_lists

    @rxe.event(auth=True)
    def change_list_page(self, direction: int):
        if direction == 1 and not self.more_lists:
            return
        self.list_page = max(1, self.list_page + direction)
        return SavedListState.load_lists

    @rxe.event(auth=True, background=True)
    async def load_lists(self):
        async with self:
            self._generation += 1
            generation = self._generation
            selected, page, list_page = self.selected, self.page, self.list_page
            self.loading = True
            self.error = ""
        try:
            subject = await self._subject()
            async with rx.asession() as session:
                lists = (
                    (
                        await session.execute(
                            text("""
                    SELECT l.id, l.title, l.description, count(i.id) AS count
                    FROM saved_lists l LEFT JOIN saved_list_items i ON i.list_id = l.id AND i.owner_sub = l.owner_sub
                    WHERE l.owner_sub = :sub AND l.slug <> 'favorites'
                    GROUP BY l.id ORDER BY l.updated_at DESC, l.id DESC LIMIT 21 OFFSET :offset
                """),
                            {"sub": subject, "offset": (list_page - 1) * 20},
                        )
                    )
                    .mappings()
                    .all()
                )
                current = (
                    (
                        await session.execute(
                            text(
                                "SELECT id, title, description FROM saved_lists WHERE id = :id AND owner_sub = :sub AND slug <> 'favorites'"
                            ),
                            {"id": selected, "sub": subject},
                        )
                    )
                    .mappings()
                    .first()
                )
                items = (
                    (
                        await session.execute(
                            text(f"""{PUBLIC_CTE}
                    SELECT p.id, p.title, i.note, EXISTS(SELECT 1 FROM eligible e WHERE e.product_id = p.id) AS published
                    FROM saved_list_items i JOIN saved_lists l ON l.id = i.list_id AND l.owner_sub = i.owner_sub
                    JOIN products p ON p.id = i.product_id
                    WHERE l.id = :id AND l.owner_sub = :sub AND l.slug <> 'favorites'
                    ORDER BY i.position, i.id LIMIT 21 OFFSET :offset
                """),
                            {
                                "id": selected,
                                "sub": subject,
                                "offset": (page - 1) * 20,
                            },
                        )
                    )
                    .mappings()
                    .all()
                )
            if await self._subject() != subject:
                return
            async with self:
                if generation != self._generation:
                    return
                self.lists = [
                    SavedListView(
                        id=r["id"],
                        title=r["title"],
                        description=r["description"] or "",
                        count=r["count"],
                    )
                    for r in lists[:20]
                ]
                self.more_lists = len(lists) > 20
                self.items = [
                    SavedItemView(
                        id=r["id"],
                        title=r["title"],
                        note=r["note"] or "",
                        published=r["published"],
                    )
                    for r in items[:20]
                ]
                self.has_next = len(items) > 20
                self.title = current["title"] if current else ""
                self.description = (
                    (current["description"] or "") if current else ""
                )
                if not current:
                    self.selected = 0
                self.loading = False
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                if generation == self._generation:
                    self.items = []
                    self.lists = []
                    self.loading = False
                    self.error = (
                        str(e)
                        if isinstance(e, ValueError)
                        else "Não foi possível carregar as listas."
                    )

    @rxe.event(auth=True)
    def save_list(self, form_data: dict[str, Any]):
        try:
            list_id = int(form_data.get("list_id", 0))
        except (ValueError, TypeError) as e:
            logging.exception(f"Error: {e}")
            return rx.toast("Lista inválida. Seu formulário foi mantido.")
        return SavedListState.mutate(
            "save",
            list_id,
            0,
            str(form_data.get("title", "")),
            str(form_data.get("description", "")),
        )

    @rxe.event(auth=True)
    def add_from_form(self, form_data: dict[str, Any]):
        try:
            list_id, product_id = (
                int(form_data.get("list_id", 0)),
                int(form_data.get("product_id", 0)),
            )
        except (ValueError, TypeError) as e:
            logging.exception(f"Error: {e}")
            return rx.toast("Selecione uma lista válida.")
        return SavedListState.mutate(
            "add", list_id, product_id, str(form_data.get("note", "")), ""
        )

    @rxe.event(auth=True, background=True)
    async def mutate(
        self,
        action: str,
        list_id: int,
        product_id: int,
        title: str,
        description: str,
    ):
        async with self:
            if self.loading:
                return
            self.loading = True
            self.error = ""
            generation = self._generation
        try:
            subject = await self._subject()
            if (
                action not in ("save", "delete", "add", "remove")
                or list_id < 0
                or list_id > 2147483647
            ):
                raise ValueError("Operação inválida.")
            async with rx.asession() as session:
                async with session.begin():
                    await session.execute(
                        text(
                            "SELECT pg_advisory_xact_lock(hashtextextended(:sub, 0))"
                        ),
                        {"sub": subject},
                    )
                    await session.execute(
                        text("SELECT pg_advisory_xact_lock(71420932)")
                    )
                    if list_id:
                        owned = await session.scalar(
                            text(
                                "SELECT id FROM saved_lists WHERE id = :id AND owner_sub = :sub AND slug <> 'favorites' FOR UPDATE"
                            ),
                            {"id": list_id, "sub": subject},
                        )
                        if not owned:
                            raise ValueError(
                                "Lista não encontrada nesta conta."
                            )
                    elif action != "save":
                        raise ValueError("Selecione uma lista.")
                    params = {
                        "id": list_id,
                        "sub": subject,
                        "title": title,
                        "description": description,
                        "product": product_id,
                    }
                    if action == "save":
                        if (
                            not title.strip()
                            or len(title) > 250
                            or len(description) > 10000
                        ):
                            raise ValueError(
                                "Informe um nome de até 250 caracteres e descrição de até 10.000. Seu texto não será normalizado."
                            )
                        if list_id:
                            await session.execute(
                                text(
                                    "UPDATE saved_lists SET title = :title, description = :description, updated_at = CURRENT_TIMESTAMP WHERE id = :id AND owner_sub = :sub"
                                ),
                                params,
                            )
                        else:
                            list_id = await session.scalar(
                                text(
                                    "INSERT INTO saved_lists (owner_sub, slug, title, description, visibility) VALUES (:sub, :slug, :title, :description, 'private') RETURNING id"
                                ),
                                {**params, "slug": uuid4().hex},
                            )
                    elif action == "delete":
                        await session.execute(
                            text(
                                "DELETE FROM saved_lists WHERE id = :id AND owner_sub = :sub"
                            ),
                            params,
                        )
                    elif action == "add":
                        if (
                            not 0 < product_id <= 2147483647
                            or not await eligible_product(session, product_id)
                        ):
                            raise ValueError(
                                "O produto não possui oferta pública elegível e não pode ser adicionado."
                            )
                        if len(title) > 10000:
                            raise ValueError(
                                "Nota: limite de 10.000 caracteres."
                            )
                        await session.execute(
                            text(
                                "INSERT INTO saved_list_items (list_id, owner_sub, product_id, note, position) VALUES (:id, :sub, :product, :title, 0) ON CONFLICT (list_id, product_id) DO UPDATE SET note = EXCLUDED.note"
                            ),
                            params,
                        )
                    else:
                        await session.execute(
                            text(
                                "DELETE FROM saved_list_items WHERE list_id = :id AND owner_sub = :sub AND product_id = :product"
                            ),
                            params,
                        )
            if await self._subject() != subject:
                return
            async with self:
                if generation != self._generation:
                    return
                self.selected = 0 if action == "delete" else list_id
                self.notice = "Alteração salva na sua lista privada."
                self.loading = False
            yield SavedListState.load_lists
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                if generation == self._generation:
                    self.loading = False
                    self.error = (
                        str(e)
                        if isinstance(e, ValueError)
                        else "Não foi possível salvar. Seu formulário foi mantido."
                    )
