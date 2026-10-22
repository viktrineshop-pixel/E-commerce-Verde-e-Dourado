import reflex as rx
import reflex_enterprise as rxe
import logging
from typing import TypedDict
from sqlalchemy import bindparam, text
from app.public_catalog import PUBLIC_CTE, eligible_product


class FavoriteProduct(TypedDict):
    id: int
    title: str
    image_url: str
    price: str
    partner_name: str


class FavoriteState(rx.State):
    signed_in: bool = False
    ready: bool = False
    saved_ids: list[int] = []
    favorites: list[FavoriteProduct] = []
    loading: bool = True
    pending_id: int = 0
    error: str = ""
    notice: str = ""
    page_number: int = 1
    has_next: bool = False
    _subject: str = ""
    _generation: int = 0

    async def _current_subject(self) -> str:
        subject = ""
        if (
            not isinstance(subject, str)
            or not subject.strip()
            or len(subject) > 255
        ):
            return ""
        return subject

    def _clear(self):
        self._generation += 1
        self._subject = ""
        self.signed_in = False
        self.ready = False
        self.saved_ids = []
        self.favorites = []
        self.loading = False
        self.pending_id = 0
        self.error = ""
        self.notice = ""
        self.page_number = 1
        self.has_next = False

    @rx.event
    def clear_presentation(self):
        self._clear()
        from app.states.saved_list_state import SavedListState

        return SavedListState.clear_presentation

    @rxe.event(auth=False)
    async def sync_auth(self):
        self.ready = False
        try:
            subject = await self._current_subject()
            if not subject:
                self._clear()
                from app.states.saved_list_state import SavedListState

                yield SavedListState.clear_presentation
                return
            if subject != self._subject:
                self._clear()
                from app.states.saved_list_state import SavedListState

                lists = await self.get_state(SavedListState)
                lists.clear_presentation()
            self._subject = subject
            self.signed_in = True
            yield FavoriteState.load_favorites
            from app.states.saved_list_state import SavedListState

            yield SavedListState.load_lists
        except Exception as e:
            logging.exception(f"Error: {e}")
            self._clear()
            yield rx.toast(
                "Não foi possível verificar sua conta. Tente atualizar a página."
            )

    @rx.event(background=True)
    async def load_favorites(self):
        from app.states.storefront_state import StorefrontState

        try:
            subject = await self._current_subject()
            async with self:
                if not subject:
                    self._clear()
                    return
                if subject != self._subject:
                    self._clear()
                if self.pending_id:
                    return
                self._subject = subject
                self.signed_in = True
                self._generation += 1
                generation = self._generation
                self.loading = True
                self.ready = False
                self.error = ""
                storefront = await self.get_state(StorefrontState)
                from app.states.product_detail_state import ProductDetailState

                detail = await self.get_state(ProductDetailState)
                catalog_ids = list(
                    set(
                        [product["id"] for product in storefront.products]
                        + [product["id"] for product in detail.groups]
                    )
                )
                page = self.page_number
            async with rx.asession() as session:
                await session.execute(
                    text(
                        "SELECT pg_advisory_xact_lock(hashtextextended(:subject, 0))"
                    ),
                    {"subject": subject},
                )
                await session.execute(
                    text("""
                    INSERT INTO saved_lists (owner_sub, slug, title, visibility)
                    SELECT :subject, 'favorites', 'Favoritos', 'private'
                    WHERE EXISTS (SELECT 1 FROM customer_favorites WHERE subject = :subject)
                    ON CONFLICT (owner_sub, slug) DO NOTHING
                """),
                    {"subject": subject},
                )
                await session.execute(
                    text("""
                    INSERT INTO saved_list_items (list_id, owner_sub, product_id, position, created_at)
                    SELECT l.id, l.owner_sub, f.product_id, 0, f.created_at
                    FROM customer_favorites f JOIN saved_lists l ON l.owner_sub = f.subject AND l.slug = 'favorites'
                    WHERE f.subject = :subject
                    ON CONFLICT (list_id, product_id) DO NOTHING
                """),
                    {"subject": subject},
                )
                await session.execute(
                    text(
                        "DELETE FROM customer_favorites WHERE subject = :subject"
                    ),
                    {"subject": subject},
                )
                await session.commit()
                saved_ids = []
                if catalog_ids:
                    saved_ids = list(
                        (
                            await session.scalars(
                                text(f"""{PUBLIC_CTE}
                            SELECT i.product_id FROM saved_list_items i
                            JOIN saved_lists l ON l.id = i.list_id AND l.owner_sub = i.owner_sub
                            WHERE l.owner_sub = :subject AND l.slug = 'favorites' AND i.product_id IN :ids
                              AND EXISTS (SELECT 1 FROM eligible e WHERE e.product_id = i.product_id)
                        """).bindparams(bindparam("ids", expanding=True)),
                                {"subject": subject, "ids": catalog_ids},
                            )
                        ).all()
                    )
                rows = (
                    (
                        await session.execute(
                            text(f"""{PUBLIC_CTE}
                        SELECT p.id, p.title, p.image_url
                        FROM saved_list_items i JOIN saved_lists l ON l.id = i.list_id AND l.owner_sub = i.owner_sub
                        JOIN products p ON p.id = i.product_id
                        WHERE l.owner_sub = :subject AND l.slug = 'favorites'
                          AND EXISTS (SELECT 1 FROM eligible e WHERE e.product_id = p.id)
                        ORDER BY i.created_at DESC, i.id DESC LIMIT 13 OFFSET :offset
                    """),
                            {"subject": subject, "offset": (page - 1) * 12},
                        )
                    )
                    .mappings()
                    .all()
                )
            favorites = [
                FavoriteProduct(
                    id=row["id"],
                    title=row["title"],
                    image_url=row["image_url"] or "/placeholder.svg",
                    price="Compare os preços observados no detalhe",
                    partner_name="Produto editorial",
                )
                for row in rows[:12]
            ]
            current = await self._current_subject()
            async with self:
                if generation != self._generation:
                    return
                if current != subject:
                    self._clear()
                    return
                self.saved_ids = saved_ids
                self.favorites = favorites
                self.has_next = len(rows) > 12
                self.loading = False
                self.ready = True
                retry_previous = not rows and page > 1
                if retry_previous:
                    self.page_number -= 1
            if retry_previous:
                yield FavoriteState.load_favorites
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                if (
                    "generation" not in locals()
                    or generation == self._generation
                ):
                    self.saved_ids = []
                    self.favorites = []
                    self.has_next = False
                    self.loading = False
                    self.ready = False
                    self.error = "Não foi possível carregar seus favoritos. Tente novamente."

    @rx.event
    def change_page(self, direction: int):
        if self.loading or self.pending_id or direction not in (-1, 1):
            return
        if direction == 1 and not self.has_next:
            return
        self.page_number = max(1, self.page_number + direction)
        return FavoriteState.load_favorites

    @rxe.event(auth=True, background=True)
    async def set_saved(self, product_id: int, saved: bool):
        generation = -1
        committed = False
        try:
            subject = await self._current_subject()
            async with self:
                if not subject:
                    self._clear()
                    return
                if self.pending_id:
                    return
                if subject != self._subject:
                    self._clear()
                self._subject = subject
                self.signed_in = True
                self._generation += 1
                generation = self._generation
                self.loading = False
                self.error = ""
                self.notice = ""
                if product_id <= 0 or product_id > 2147483647:
                    self.error = "Produto inválido. Atualize o catálogo e tente novamente."
                    return
                self.pending_id = product_id
            async with rx.asession() as session:
                await session.execute(
                    text(
                        "SELECT pg_advisory_xact_lock(hashtextextended(:subject, 0))"
                    ),
                    {"subject": subject},
                )
                await session.execute(
                    text("SELECT pg_advisory_xact_lock(71420932)")
                )
                await session.execute(
                    text("SELECT id FROM products WHERE id = :id FOR SHARE"),
                    {"id": product_id},
                )
                exists = await eligible_product(session, product_id)
                if saved and not exists:
                    async with self:
                        if generation == self._generation:
                            self.saved_ids = [
                                i for i in self.saved_ids if i != product_id
                            ]
                            self.favorites = [
                                p
                                for p in self.favorites
                                if p["id"] != product_id
                            ]
                    raise ValueError(
                        "Este produto não está mais no catálogo e não pode ser salvo."
                    )
                if saved:
                    await session.execute(
                        text(
                            "INSERT INTO saved_lists (owner_sub, slug, title, visibility) VALUES (:subject, 'favorites', 'Favoritos', 'private') ON CONFLICT (owner_sub, slug) DO NOTHING"
                        ),
                        {"subject": subject},
                    )
                    await session.execute(
                        text("""
                        INSERT INTO saved_list_items (list_id, owner_sub, product_id, position)
                        SELECT id, owner_sub, :id, 0 FROM saved_lists
                        WHERE owner_sub = :subject AND slug = 'favorites'
                        ON CONFLICT (list_id, product_id) DO NOTHING
                    """),
                        {"subject": subject, "id": product_id},
                    )
                else:
                    await session.execute(
                        text("""
                        DELETE FROM saved_list_items i USING saved_lists l
                        WHERE i.list_id = l.id AND i.owner_sub = l.owner_sub
                          AND l.owner_sub = :subject AND l.slug = 'favorites' AND i.product_id = :id
                    """),
                        {"subject": subject, "id": product_id},
                    )
                await session.commit()
                committed = True
            current = await self._current_subject()
            async with self:
                if generation != self._generation:
                    return
                if current != subject:
                    self._clear()
                    return
                self.notice = (
                    "Produto salvo nos favoritos."
                    if saved
                    else "Produto removido dos favoritos."
                )
                if not exists:
                    self.notice = "O produto saiu do catálogo e foi removido da sua lista."
                if not saved:
                    self.saved_ids = [
                        i for i in self.saved_ids if i != product_id
                    ]
                    self.favorites = [
                        p for p in self.favorites if p["id"] != product_id
                    ]
                self.pending_id = 0
            yield FavoriteState.load_favorites
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                if generation == -1 or generation == self._generation:
                    self.error = (
                        str(e)
                        if isinstance(e, ValueError)
                        else (
                            "A alteração foi salva, mas não foi possível atualizar sua lista. Tente atualizar os favoritos."
                            if committed
                            else "Não foi possível alterar seus favoritos. Tente novamente."
                        )
                    )
        finally:
            async with self:
                if generation == self._generation:
                    self.pending_id = 0
