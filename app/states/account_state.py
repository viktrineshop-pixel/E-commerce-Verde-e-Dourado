import reflex as rx
import reflex_enterprise as rxe
import logging
from typing import TypedDict
from zoneinfo import ZoneInfo
from sqlalchemy import text, bindparam
from reflex_enterprise.auth import User


class PurchasedItem(TypedDict):
    id: int
    title: str
    sku: str
    description: str
    category: str
    image_url: str
    quantity: int
    unit_price: str
    discount: str
    total: str


class CustomerOrder(TypedDict):
    id: int
    number: str
    date: str
    status: str
    status_label: str
    subtotal: str
    shipping: str
    discount: str
    total: str
    recipient: str
    street: str
    complement: str
    neighborhood: str
    city: str
    postal_code: str
    country: str
    phone: str
    email: str
    items: list[PurchasedItem]


class AccountState(rx.State):
    orders: list[CustomerOrder] = rxe.field([], auth=True)
    loading: bool = rxe.field(True, auth=True)
    error: str = rxe.field("", auth=True)
    page_number: int = rxe.field(1, auth=True)
    has_next: bool = rxe.field(False, auth=True)
    _offset: int = 0

    def _money(self, cents: int, currency: str = "BRL") -> str:
        value = f"{cents / 100:,.2f}"
        formatted = value.replace(",", "|").replace(".", ",").replace("|", ".")
        prefix = "R$" if currency == "BRL" else currency
        return f"{prefix} {formatted}"

    @rxe.event(auth=True)
    async def load_orders(self):
        self._offset = 0
        self.page_number = 1
        async for update in self._fetch():
            yield update

    @rxe.event(auth=True)
    async def refresh_orders(self):
        async for update in self._fetch():
            yield update

    @rxe.event(auth=True)
    async def next_page(self):
        if self.loading or not self.has_next:
            return
        self._offset += 10
        self.page_number = self._offset // 10 + 1
        async for update in self._fetch():
            yield update

    @rxe.event(auth=True)
    async def previous_page(self):
        if self.loading or self._offset == 0:
            return
        self._offset = max(0, self._offset - 10)
        self.page_number = self._offset // 10 + 1
        async for update in self._fetch():
            yield update

    async def _fetch(self):
        self.loading = True
        self.error = ""
        self.orders = []
        self.has_next = False
        yield
        try:
            user = await User.current() or {}
            subject = user.get("sub")
            if not isinstance(subject, str) or not subject.strip():
                self.error = "Sua sessão não está disponível. Entre novamente para consultar seus pedidos."
                yield rx.redirect("/login?redirect_to=/minha-conta")
                return
            async with rx.asession() as session:
                rows = (
                    (
                        await session.execute(
                            text("""
                    SELECT id, created_at, status, currency,
                           COALESCE(subtotal_centavos, 0) AS subtotal,
                           COALESCE(shipping_centavos, 0) AS shipping,
                           COALESCE(discount_centavos, 0) AS discount,
                           COALESCE(total_centavos, 0) AS total,
                           shipping_recipient, shipping_street, shipping_number,
                           shipping_complement, shipping_neighborhood, shipping_city,
                           shipping_state, shipping_postal_code, shipping_country_code,
                           contact_phone, contact_email
                    FROM orders
                    WHERE purchaser_sub = :subject
                    ORDER BY created_at DESC, id DESC
                    LIMIT 11 OFFSET :offset
                """),
                            {"subject": subject, "offset": self._offset},
                        )
                    )
                    .mappings()
                    .all()
                )
                self.has_next = len(rows) > 10
                rows = rows[:10]
                item_rows = []
                if rows:
                    item_rows = (
                        (
                            await session.execute(
                                text("""
                        SELECT i.id, i.order_id, i.title, i.sku, i.description,
                               i.category, i.image_url, i.quantity,
                               COALESCE(i.unit_price_centavos, 0) AS unit_price,
                               COALESCE(i.discount_centavos, 0) AS discount,
                               COALESCE(i.total_centavos, 0) AS total
                        FROM order_items i JOIN orders o ON o.id = i.order_id
                        WHERE o.purchaser_sub = :subject AND o.id IN :order_ids
                        ORDER BY o.created_at DESC, o.id DESC, i.line_number
                        LIMIT 1000
                    """).bindparams(bindparam("order_ids", expanding=True)),
                                {
                                    "subject": subject,
                                    "order_ids": [row["id"] for row in rows],
                                },
                            )
                        )
                        .mappings()
                        .all()
                    )
            labels = {
                "pending": "Pedido recebido",
                "paid": "Pago",
                "processing": "Em preparação",
                "shipped": "Enviado",
                "delivered": "Entregue",
                "cancelled": "Cancelado",
                "refunded": "Reembolsado",
            }
            currencies = {row["id"]: row["currency"] for row in rows}
            items: dict[int, list[PurchasedItem]] = {
                row["id"]: [] for row in rows
            }
            for item in item_rows:
                currency = currencies[item["order_id"]]
                items[item["order_id"]].append(
                    PurchasedItem(
                        id=item["id"],
                        title=item["title"],
                        sku=item["sku"],
                        description=item["description"],
                        category=item["category"],
                        image_url=item["image_url"] or "/placeholder.svg",
                        quantity=item["quantity"],
                        unit_price=self._money(item["unit_price"], currency),
                        discount=self._money(item["discount"], currency),
                        total=self._money(item["total"], currency),
                    )
                )
            for row in rows:
                date = row["created_at"]
                if date.tzinfo:
                    date = date.astimezone(ZoneInfo("America/Sao_Paulo"))
                self.orders.append(
                    CustomerOrder(
                        id=row["id"],
                        number=f"ML-{row['id']:06d}",
                        date=date.strftime("%d/%m/%Y · %H:%M"),
                        status=row["status"],
                        status_label=labels.get(
                            row["status"], "Pedido registrado"
                        ),
                        subtotal=self._money(row["subtotal"], row["currency"]),
                        shipping=self._money(row["shipping"], row["currency"]),
                        discount=self._money(row["discount"], row["currency"]),
                        total=self._money(row["total"], row["currency"]),
                        recipient=row["shipping_recipient"],
                        street=f"{row['shipping_street']}, {row['shipping_number']}",
                        complement=row["shipping_complement"],
                        neighborhood=row["shipping_neighborhood"],
                        city=f"{row['shipping_city']} / {row['shipping_state']}",
                        postal_code=row["shipping_postal_code"],
                        country=row["shipping_country_code"],
                        phone=row["contact_phone"],
                        email=row["contact_email"],
                        items=items[row["id"]],
                    )
                )
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.orders = []
            self.has_next = False
            self.error = "Não foi possível carregar seus pedidos. Tente novamente em instantes."
        finally:
            self.loading = False
