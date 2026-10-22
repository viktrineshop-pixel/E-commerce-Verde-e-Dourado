import reflex as rx
import reflex_enterprise as rxe
import logging
import re
from datetime import datetime, timezone
from typing import Any, TypedDict
from zoneinfo import ZoneInfo
from sqlalchemy import Select, func, select
from sqlalchemy.sql.elements import ColumnElement
from app.models import Order, OrderItem
from app.states.authorization import is_admin


PAGE_SIZE = 10
STATUS_LABELS = {
    "pending": "Recebido",
    "processing": "Em preparação",
    "shipped": "Enviado",
    "cancelled": "Cancelado",
    "paid": "Pago",
    "delivered": "Entregue",
    "refunded": "Reembolsado",
}
EDITABLE_STATUSES = frozenset({"pending", "processing", "shipped", "cancelled"})
SEARCH_MAX_LENGTH = 320
SEARCH_EMAIL_MIN_LENGTH = 3
MAX_ORDER_ID = 2_147_483_647
_ORDER_NUMBER_RE = re.compile(r"^(?:ml[-\s]?)?(\d{1,12})$")
_EMAIL_FRAGMENT_RE = re.compile(r"^[a-z0-9.!#$%&'*+/=?^_`{|}~@-]+$")


def escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def parse_order_query(raw: str) -> tuple[str, str, str]:
    """Return (kind, value, label); kind is '', 'id' or 'email'."""
    if not isinstance(raw, str):
        raise ValueError("Digite um número de pedido ou um e-mail válido.")
    text = raw.strip()
    if not text:
        return "", "", ""
    if len(text) > SEARCH_MAX_LENGTH:
        raise ValueError(
            f"A busca aceita no máximo {SEARCH_MAX_LENGTH} caracteres."
        )
    lowered = text.lower()
    number = _ORDER_NUMBER_RE.match(lowered)
    if number:
        order_id = int(number.group(1))
        if order_id <= 0 or order_id > MAX_ORDER_ID:
            raise ValueError(
                "Número de pedido inválido. Use o formato ML-000123 ou apenas o número."
            )
        return "id", str(order_id), f"Pedido ML-{order_id:06d}"
    if len(lowered) < SEARCH_EMAIL_MIN_LENGTH:
        raise ValueError(
            f"Para buscar por e-mail, digite pelo menos {SEARCH_EMAIL_MIN_LENGTH} caracteres."
        )
    if not _EMAIL_FRAGMENT_RE.match(lowered):
        raise ValueError(
            "Use um número de pedido (ML-000123) ou parte de um e-mail, sem espaços ou acentos."
        )
    return "email", lowered, f"E-mail contendo “{lowered}”"


def order_search_filter(kind: str, value: str) -> ColumnElement[bool] | None:
    if kind == "id":
        order_id = int(value)
        if order_id <= 0 or order_id > MAX_ORDER_ID:
            raise ValueError("Número de pedido inválido.")
        return Order.id == order_id
    if kind == "email":
        if not value:
            raise ValueError("E-mail de busca vazio.")
        return func.lower(Order.contact_email).like(
            f"%{escape_like(value)}%", escape="\\"
        )
    if kind == "":
        return None
    raise ValueError("Tipo de busca desconhecido.")


def orders_page_statement(page: int, kind: str = "", value: str = "") -> Select:
    statement = select(
        Order.id,
        Order.created_at,
        Order.contact_name,
        Order.contact_email,
        Order.total_centavos,
        Order.status,
    )
    condition = order_search_filter(kind, value)
    if condition is not None:
        statement = statement.where(condition)
    return (
        statement.order_by(Order.created_at.desc(), Order.id.desc())
        .offset((max(1, page) - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE + 1)
    )


def order_money(cents: int) -> str:
    whole = f"{cents // 100:,}".replace(",", ".")
    return f"R$ {whole},{cents % 100:02d}"


def order_date(value: datetime) -> str:
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return aware.astimezone(ZoneInfo("America/Sao_Paulo")).strftime(
        "%d/%m/%Y · %H:%M"
    )


class AdminOrderItem(TypedDict):
    id: int
    title: str
    quantity: int


class AdminOrder(TypedDict):
    id: int
    number: str
    date: str
    contact_name: str
    contact_email: str
    total: str
    status: str
    status_label: str
    items: list[AdminOrderItem]


class AdminOrderState(rx.State):
    orders: list[AdminOrder] = []
    loading: bool = False
    saving: bool = False
    saving_id: int = 0
    page: int = 1
    has_next: bool = False
    error: str = ""
    notice: str = ""
    query_text: str = ""
    search_kind: str = ""
    search_value: str = ""
    search_label: str = ""
    search_error: str = ""
    form_version: int = 0

    async def _read_page(
        self, page: int, kind: str = "", value: str = ""
    ) -> tuple[list[AdminOrder], bool, int]:
        page = max(1, page)
        statement = orders_page_statement(page, kind, value)
        async with rx.asession() as session:
            rows = (await session.execute(statement)).all()
            has_next = len(rows) > PAGE_SIZE
            rows = rows[:PAGE_SIZE]
            items: dict[int, list[AdminOrderItem]] = {
                row.id: [] for row in rows
            }
            if rows:
                item_rows = (
                    await session.execute(
                        select(
                            OrderItem.id,
                            OrderItem.order_id,
                            OrderItem.title,
                            OrderItem.quantity,
                        )
                        .where(OrderItem.order_id.in_(list(items)))
                        .order_by(
                            OrderItem.order_id,
                            OrderItem.line_number,
                            OrderItem.id,
                        )
                    )
                ).all()
                for item in item_rows:
                    items[item.order_id].append(
                        AdminOrderItem(
                            id=item.id,
                            title=item.title,
                            quantity=item.quantity,
                        )
                    )
            orders = [
                AdminOrder(
                    id=row.id,
                    number=f"ML-{row.id:06d}",
                    date=order_date(row.created_at),
                    contact_name=row.contact_name,
                    contact_email=row.contact_email,
                    total=order_money(row.total_centavos),
                    status=row.status,
                    status_label=f"Status histórico: {STATUS_LABELS.get(row.status, row.status)}",
                    items=items[row.id],
                )
                for row in rows
            ]
        return orders, has_next, page

    async def _load_page(self, page: int):
        self.loading = True
        self.error = ""
        self.notice = ""
        try:
            kind, value = self.search_kind, self.search_value
            orders, has_next, page = await self._read_page(page, kind, value)
            if not orders and page > 1:
                orders, has_next, page = await self._read_page(1, kind, value)
            self.orders = orders
            self.has_next = has_next
            self.page = page
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.orders = []
            self.has_next = False
            self.error = "Não foi possível carregar os pedidos. Use Atualizar pedidos para tentar novamente."
        finally:
            self.loading = False

    @rx.event
    async def load_orders(self, delta: int = 0):
        if self.loading or self.saving:
            return
        if delta not in (-1, 0, 1) or (delta == 1 and not self.has_next):
            return
        await self._load_page(max(1, self.page + delta))

    @rx.event
    async def search_orders(self, form_data: dict[str, Any]):
        if self.loading or self.saving:
            return
        raw = form_data.get("query", "")
        raw = raw if isinstance(raw, str) else ""
        self.query_text = raw.strip()[:SEARCH_MAX_LENGTH]
        self.search_error = ""
        try:
            kind, value, label = parse_order_query(raw)
            if not kind:
                raise ValueError(
                    "Digite um número de pedido ou um e-mail para buscar, ou use Limpar para ver todos."
                )
        except ValueError as e:
            logging.exception(f"Error: {e}")
            self.search_error = str(e)
            return
        self.query_text = raw.strip()
        self.search_kind = kind
        self.search_value = value
        self.search_label = label
        self.form_version += 1
        await self._load_page(1)

    @rxe.event(auth=is_admin)
    async def clear_search(self):
        if self.loading or self.saving:
            return
        self.query_text = ""
        self.search_kind = ""
        self.search_value = ""
        self.search_label = ""
        self.search_error = ""
        self.form_version += 1
        await self._load_page(1)

    async def _persist_status(
        self, order_id: int, status: str, expected: str
    ) -> bool:
        raise ValueError(
            "Arquivo demonstrativo somente leitura. Alterações de status estão desativadas."
        )
        if (
            order_id <= 0
            or status not in EDITABLE_STATUSES
            or expected not in STATUS_LABELS
        ):
            raise ValueError(
                "Escolha um dos quatro status permitidos para um pedido válido."
            )
        async with rx.asession() as session:
            async with session.begin():
                order = await session.scalar(
                    select(Order).where(Order.id == order_id).with_for_update()
                )
                if order is None:
                    raise ValueError("Pedido não encontrado. Atualize a lista.")
                if order.status == status:
                    return False
                if order.status != expected:
                    raise ValueError(
                        "O status foi alterado por outra sessão. Atualize os pedidos antes de salvar novamente."
                    )
                now = datetime.now(timezone.utc)
                order.status = status
                order.shipped_at = now if status == "shipped" else None
                order.cancelled_at = now if status == "cancelled" else None
        return True

    @rxe.event(auth=is_admin)
    async def save_status(self, fields: dict[str, Any]):
        self.error = "Arquivo demonstrativo somente leitura. Nenhum status pode ser alterado."
        return
        if self.loading or self.saving:
            return
        self.error = ""
        self.notice = ""
        try:
            order_id = int(str(fields.get("order_id", "")))
            status = str(fields.get("status", ""))
            expected = str(fields.get("expected", ""))
            if (
                order_id <= 0
                or status not in EDITABLE_STATUSES
                or expected not in STATUS_LABELS
            ):
                raise ValueError(
                    "Escolha um dos quatro status disponíveis antes de salvar."
                )
        except (ValueError, TypeError) as e:
            logging.exception(f"Error: {e}")
            self.error = "Escolha um dos quatro status disponíveis para um pedido válido."
            return
        self.saving = True
        self.saving_id = order_id
        page = self.page
        try:
            changed = await self._persist_status(order_id, status, expected)
        except ValueError as e:
            logging.exception(f"Error: {e}")
            self.error = str(e)
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "Não foi possível confirmar a alteração. Atualize os pedidos para verificar o status antes de tentar novamente."
        else:
            self.notice = (
                f"Pedido ML-{order_id:06d}: status salvo como {STATUS_LABELS[status]}."
                if changed
                else f"Pedido ML-{order_id:06d} já está com o status {STATUS_LABELS[status]}."
            )
            try:
                orders, has_next, page = await self._read_page(
                    page, self.search_kind, self.search_value
                )
                self.orders = orders
                self.has_next = has_next
                self.page = page
            except Exception as e:
                logging.exception(f"Error: {e}")
                self.orders = []
                self.has_next = False
                self.error = "O status foi confirmado, mas não foi possível recarregar a lista. Use Atualizar pedidos; não é necessário salvar novamente."
        finally:
            self.saving = False
            self.saving_id = 0
