import reflex as rx
import reflex_enterprise as rxe
import logging
from typing import TypedDict
from reflex_enterprise.auth import User
from sqlalchemy import bindparam, text


class FavoriteProduct(TypedDict):
    id: int
    title: str
    image_url: str
    price: str
    partner_name: str


class FavoriteState(rx.State):
    signed_in: bool = rxe.field(False, auth=False)
    ready: bool = rxe.field(False, auth=False)
    saved_ids: list[int] = rxe.field([], auth=True)
    favorites: list[FavoriteProduct] = rxe.field([], auth=True)
    loading: bool = rxe.field(True, auth=True)
    pending_id: int = rxe.field(0, auth=True)
    error: str = rxe.field("", auth=True)
    notice: str = rxe.field("", auth=True)
    page_number: int = rxe.field(1, auth=True)
    has_next: bool = rxe.field(False, auth=True)
    _subject: str = ""
    _generation: int = 0

    async def _current_subject(self) -> str:
        user = await User.current() or {}
        subject = user.get("sub", "")
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

    @rxe.event(auth=False)
    def clear_presentation(self):
        self._clear()

    @rxe.event(auth=False)
    async def sync_auth(self):
        self.ready = False
        try:
            subject = await self._current_subject()
            if not subject:
                self._clear()
                return
            if subject != self._subject:
                self._clear()
            self._subject = subject
            self.signed_in = True
            yield FavoriteState.load_favorites
        except Exception as e:
            logging.exception(f"Error: {e}")
            self._clear()
            yield rx.toast(
                "Não foi possível verificar sua conta. Tente atualizar a página."
            )

    @rxe.event(auth=True, background=True)
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
                catalog_ids = [product["id"] for product in storefront.products]
                page = self.page_number
            async with rx.asession() as session:
                saved_ids = []
                if catalog_ids:
                    saved_ids = list(
                        (
                            await session.scalars(
                                text("""
                            SELECT f.product_id FROM customer_favorites f
                            JOIN products p ON p.id = f.product_id
                            WHERE f.subject = :subject AND f.product_id IN :ids
                            LIMIT 12
                        """).bindparams(bindparam("ids", expanding=True)),
                                {"subject": subject, "ids": catalog_ids},
                            )
                        ).all()
                    )
                rows = (
                    (
                        await session.execute(
                            text("""
                        SELECT p.id, p.title, p.image_url,
                               COALESCE(p.price_centavos, 0) AS price_centavos,
                               p.partner_name
                        FROM customer_favorites f JOIN products p ON p.id = f.product_id
                        WHERE f.subject = :subject
                        ORDER BY f.created_at DESC, f.id DESC
                        LIMIT 13 OFFSET :offset
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
                    price=self._money(row["price_centavos"]),
                    partner_name=row["partner_name"],
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

    def _money(self, cents: int) -> str:
        value = f"{cents / 100:,.2f}"
        return (
            f"R$ {value.replace(',', '|').replace('.', ',').replace('|', '.')}"
        )

    @rxe.event(auth=True)
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
                exists = await session.scalar(
                    text(
                        "SELECT id FROM products WHERE id = :id FOR KEY SHARE"
                    ),
                    {"id": product_id},
                )
                if saved and exists is None:
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
                        text("""
                        INSERT INTO customer_favorites (subject, product_id)
                        VALUES (:subject, :id)
                        ON CONFLICT (subject, product_id) DO NOTHING
                    """),
                        {"subject": subject, "id": product_id},
                    )
                else:
                    await session.execute(
                        text("""
                        DELETE FROM customer_favorites
                        WHERE subject = :subject AND product_id = :id
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
                if exists is None:
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
