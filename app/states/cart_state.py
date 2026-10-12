import reflex as rx
import reflex_enterprise as rxe
import logging
import re
import secrets
from typing import Any, TypedDict
from sqlalchemy import select, delete
from reflex_enterprise.auth import User
from app.models import CartItem, Product, Order, OrderItem


class CartLine(TypedDict):
    product_id: int
    title: str
    image_url: str
    quantity: int
    stock: int
    unit_price: str
    line_total: str


class CartState(rx.State):
    _cart_key: str = ""
    _last_order_id: int = 0
    lines: list[CartLine] = rxe.field([], auth=False)
    count: int = rxe.field(0, auth=False)
    subtotal: str = rxe.field("R$ 0,00", auth=False)
    loading: bool = rxe.field(True, auth=False)
    busy: bool = rxe.field(False, auth=False)
    submitting: bool = rxe.field(False, auth=False)
    error: str = rxe.field("", auth=False)
    notice: str = rxe.field("", auth=False)
    errors: dict[str, str] = rxe.field({}, auth=False)
    draft: dict[str, str] = rxe.field({}, auth=False)
    confirmed: bool = rxe.field(False, auth=False)
    order_number: str = rxe.field("", auth=False)
    order_total: str = rxe.field("R$ 0,00", auth=False)

    def _key(self) -> str:
        # Backend-only: never accept a cart identifier from the browser.
        if not self._cart_key:
            self._cart_key = secrets.token_urlsafe(48)
        return self._cart_key

    def _brl(self, cents: int) -> str:
        value = f"{cents / 100:,.2f}"
        return (
            f"R$ {value.replace(',', '|').replace('.', ',').replace('|', '.')}"
        )

    async def _refresh(self):
        async with rx.asession() as session:
            rows = (
                await session.execute(
                    select(CartItem, Product)
                    .join(Product, Product.id == CartItem.product_id)
                    .where(CartItem.cart_key == self._key())
                    .order_by(Product.id)
                    .limit(100)
                )
            ).all()
            self.lines = [
                CartLine(
                    product_id=p.id,
                    title=p.title,
                    image_url=p.image_url or "/placeholder.svg",
                    quantity=c.quantity,
                    stock=p.stock,
                    unit_price=self._brl(p.price_centavos),
                    line_total=self._brl(c.quantity * p.price_centavos),
                )
                for c, p in rows
            ]
            self.count = sum(c.quantity for c, p in rows)
            self.subtotal = self._brl(
                sum(c.quantity * p.price_centavos for c, p in rows)
            )

    @rxe.event(auth=False)
    async def load_cart(self):
        self.loading = True
        self.error = ""
        yield
        try:
            await self._refresh()
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = (
                "Não foi possível carregar sua sacola. Tente novamente."
            )
        finally:
            self.loading = False

    @rxe.event(auth=False)
    async def add_product(self, product_id: int):
        if self.busy or self.submitting:
            return
        self.busy = True
        self.error = ""
        self.notice = ""
        yield
        try:
            user = await User.current() or {}
            async with rx.asession() as session:
                async with session.begin():
                    product = await session.scalar(
                        select(Product)
                        .where(Product.id == product_id)
                        .with_for_update()
                    )
                    if not product or product.stock <= 0:
                        raise ValueError(
                            "Esta peça está indisponível no momento."
                        )
                    item = await session.scalar(
                        select(CartItem)
                        .where(
                            CartItem.cart_key == self._key(),
                            CartItem.product_id == product_id,
                        )
                        .with_for_update()
                    )
                    quantity = item.quantity if item else 0
                    if quantity >= product.stock:
                        raise ValueError(
                            "A quantidade na sacola já atingiu o estoque disponível."
                        )
                    if item:
                        item.quantity += 1
                        item.owner_sub = str(user.get("sub", "")) or None
                    else:
                        existing = (
                            await session.scalars(
                                select(CartItem.id)
                                .where(CartItem.cart_key == self._key())
                                .limit(100)
                            )
                        ).all()
                        if len(existing) >= 100:
                            raise ValueError(
                                "Sua sacola atingiu o limite de 100 peças diferentes."
                            )
                        session.add(
                            CartItem(
                                cart_key=self._key(),
                                product_id=product_id,
                                owner_sub=str(user.get("sub", "")) or None,
                            )
                        )
            self.confirmed = False
            await self._refresh()
            self.notice = "Peça adicionada à sacola."
            yield rx.toast("Peça adicionada à sacola", duration=3000)
        except ValueError as e:
            logging.exception(f"Error: {e}")
            self.error = str(e)
            yield rx.toast(str(e), duration=4000)
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "Não foi possível adicionar a peça. Tente novamente."
            yield rx.toast(self.error, duration=4000)
        finally:
            self.busy = False

    @rxe.event(auth=False)
    async def change_quantity(self, product_id: int, delta: int):
        if delta not in (-1, 1) or self.busy or self.submitting:
            return
        self.busy = True
        self.error = ""
        self.notice = ""
        yield
        try:
            async with rx.asession() as session:
                async with session.begin():
                    product = await session.scalar(
                        select(Product)
                        .where(Product.id == product_id)
                        .with_for_update()
                    )
                    item = await session.scalar(
                        select(CartItem)
                        .where(
                            CartItem.cart_key == self._key(),
                            CartItem.product_id == product_id,
                        )
                        .with_for_update()
                    )
                    if item and product:
                        quantity = item.quantity + delta
                        if quantity < 1:
                            raise ValueError(
                                "Para retirar esta peça, use Remover."
                            )
                        if delta > 0 and quantity > product.stock:
                            raise ValueError(
                                "Não há mais unidades disponíveis desta peça."
                            )
                        item.quantity = quantity
            await self._refresh()
        except ValueError as e:
            logging.exception(f"Error: {e}")
            self.error = str(e)
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = (
                "Não foi possível alterar a quantidade. Tente novamente."
            )
        finally:
            self.busy = False

    @rxe.event(auth=False)
    async def remove_product(self, product_id: int):
        if self.busy or self.submitting:
            return
        self.busy = True
        self.error = ""
        yield
        try:
            async with rx.asession() as session:
                async with session.begin():
                    await session.execute(
                        delete(CartItem).where(
                            CartItem.cart_key == self._key(),
                            CartItem.product_id == product_id,
                        )
                    )
            await self._refresh()
            self.notice = "Peça removida da sacola."
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "Não foi possível remover a peça. Tente novamente."
        finally:
            self.busy = False

    def _validate(
        self, data: dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, str]]:
        limits = {
            "recipient": 250,
            "phone": 40,
            "email": 320,
            "cep": 24,
            "street": 250,
            "number": 40,
            "complement": 250,
            "neighborhood": 120,
            "city": 120,
            "state": 2,
        }
        values = {key: str(data.get(key, "")).strip() for key in limits}
        errors: dict[str, str] = {}
        for key, limit in limits.items():
            if key != "complement" and not values[key]:
                errors[key] = "Preencha este campo."
            elif len(values[key]) > limit:
                errors[key] = f"Use no máximo {limit} caracteres."
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", values["email"]):
            errors["email"] = "Informe um e-mail válido."
        phone = re.sub(r"\D", "", values["phone"])
        if phone.startswith("55") and len(phone) in (12, 13):
            phone = phone[2:]
        if len(phone) not in (10, 11):
            errors["phone"] = "Informe o telefone com DDD (10 ou 11 dígitos)."
        cep = re.sub(r"\D", "", values["cep"])
        if len(cep) != 8 or not re.fullmatch(r"[\d\s-]+", values["cep"]):
            errors["cep"] = "Informe um CEP com 8 dígitos."
        values["state"] = values["state"].upper()
        if (
            values["state"]
            not in "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()
        ):
            errors["state"] = "Selecione uma UF válida."
        values["phone"] = phone
        values["cep"] = cep
        return values, errors

    @rxe.event(auth=False)
    async def place_order(self, form_data: dict[str, Any]):
        if self.submitting or self.busy or self.confirmed:
            return
        values, errors = self._validate(form_data)
        self.draft = {
            key: str(form_data.get(key, "")).strip()[:320] for key in values
        }
        self.errors = errors
        self.error = ""
        if errors:
            self.error = "Revise os campos destacados antes de enviar o pedido."
            return
        self.submitting = True
        yield
        committed = False
        try:
            user = await User.current() or {}
            async with rx.asession() as session:
                async with session.begin():
                    ids = (
                        await session.scalars(
                            select(CartItem.product_id)
                            .where(CartItem.cart_key == self._key())
                            .order_by(CartItem.product_id)
                            .limit(100)
                        )
                    ).all()
                    if not ids:
                        raise ValueError(
                            "Sua sacola está vazia. Adicione uma peça para continuar."
                        )
                    products = (
                        await session.scalars(
                            select(Product)
                            .where(Product.id.in_(ids))
                            .order_by(Product.id)
                            .with_for_update()
                        )
                    ).all()
                    items = (
                        await session.scalars(
                            select(CartItem)
                            .where(CartItem.cart_key == self._key())
                            .order_by(CartItem.product_id)
                            .with_for_update()
                        )
                    ).all()
                    by_id = {p.id: p for p in products}
                    if not items:
                        raise ValueError(
                            "Sua sacola já foi finalizada ou está vazia."
                        )
                    for item in items:
                        p = by_id.get(item.product_id)
                        if not p or item.quantity > p.stock:
                            title = p.title if p else "Uma peça"
                            raise ValueError(
                                f"{title}: estoque insuficiente. Ajuste a sacola antes de continuar."
                            )
                    total = sum(
                        c.quantity * by_id[c.product_id].price_centavos
                        for c in items
                    )
                    order = Order(
                        purchaser_sub=str(user.get("sub", "")),
                        contact_name=values["recipient"],
                        contact_email=values["email"],
                        contact_phone=values["phone"],
                        shipping_recipient=values["recipient"],
                        shipping_street=values["street"],
                        shipping_number=values["number"],
                        shipping_complement=values["complement"],
                        shipping_neighborhood=values["neighborhood"],
                        shipping_city=values["city"],
                        shipping_state=values["state"],
                        shipping_postal_code=values["cep"],
                        subtotal_centavos=total,
                        shipping_centavos=0,
                        total_centavos=total,
                        status="pending",
                    )
                    session.add(order)
                    await session.flush()
                    order_id = order.id
                    for index, item in enumerate(items, start=1):
                        p = by_id[item.product_id]
                        session.add(
                            OrderItem(
                                order_id=order_id,
                                line_number=index,
                                product_id=p.id,
                                sku=p.sku,
                                title=p.title,
                                description=p.description,
                                category=p.category,
                                image_url=p.image_url,
                                quantity=item.quantity,
                                unit_price_centavos=p.price_centavos,
                                compare_at_price_centavos=p.compare_at_price_centavos,
                                total_centavos=item.quantity * p.price_centavos,
                            )
                        )
                        p.stock -= item.quantity
                    await session.execute(
                        delete(CartItem).where(CartItem.cart_key == self._key())
                    )
            committed = True
            self._last_order_id = order_id
            self.order_number = f"ML-{order_id:06d}"
            self.order_total = self._brl(total)
            self.confirmed = True
            self.lines = []
            self.count = 0
            self.subtotal = "R$ 0,00"
            self.draft = {}
            self.errors = {}
            self.notice = ""
            from app.states.storefront_state import StorefrontState

            storefront = await self.get_state(StorefrontState)
            storefront.loading = True
            yield StorefrontState.refresh_products
            yield rx.redirect("/carrinho#pedido-recebido")
        except ValueError as e:
            logging.exception(f"Error: {e}")
            self.error = str(e)
            await self._refresh()
        except Exception as e:
            logging.exception(f"Error: {e}")
            if not committed:
                self.error = "Não foi possível enviar o pedido. Sua sacola foi mantida; tente novamente."
        finally:
            self.submitting = False
