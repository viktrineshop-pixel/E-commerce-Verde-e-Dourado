import reflex as rx
import reflex_enterprise as rxe
import logging
from datetime import datetime, timezone
from typing import Any, TypedDict
from zoneinfo import ZoneInfo
from sqlalchemy import select
from app.models import Order, OrderItem


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

    async def _read_page(self, page: int) -> tuple[list[AdminOrder], bool, int]:
        async with rx.asession() as session:
            rows = (
                await session.execute(
                    select(
                        Order.id,
                        Order.created_at,
                        Order.contact_name,
                        Order.contact_email,
                        Order.total_centavos,
                        Order.status,
                    )
                    .order_by(Order.created_at.desc(), Order.id.desc())
                    .offset((page - 1) * PAGE_SIZE)
                    .limit(PAGE_SIZE + 1)
                )
            ).all()
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
                    status_label=STATUS_LABELS.get(row.status, row.status),
                    items=items[row.id],
                )
                for row in rows
            ]
        return orders, has_next, page

    @rx.event
    async def load_orders(self, delta: int = 0):
        if self.loading or self.saving:
            return
        if delta not in (-1, 0, 1) or (delta == 1 and not self.has_next):
            return
        page = max(1, self.page + delta)
        self.loading = True
        self.error = ""
        self.notice = ""
        try:
            orders, has_next, page = await self._read_page(page)
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

    async def _persist_status(
        self, order_id: int, status: str, expected: str
    ) -> bool:
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

    @rxe.event(auth=True)
    async def save_status(self, fields: dict[str, Any]):
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
                orders, has_next, page = await self._read_page(page)
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
