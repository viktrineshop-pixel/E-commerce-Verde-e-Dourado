import reflex as rx
import reflex_enterprise as rxe
import logging
import re
import secrets
from typing import Any, TypedDict
from datetime import datetime, timezone
from sqlalchemy import select, delete, func
from app.models import CartItem, Product, Order, OrderItem, Coupon
from app.coupons import normalize_code, coupon_discount
from reflex_enterprise.auth import User


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
    _applied_coupon_code: str = ""
    coupon: str = rxe.field("", auth=False)
    discount: str = rxe.field("R$ 0,00", auth=False)
    grand_total: str = rxe.field("R$ 0,00", auth=False)
    coupon_error: str = rxe.field("", auth=False)
    coupon_notice: str = rxe.field("", auth=False)
    order_coupon: str = rxe.field("", auth=False)
    order_discount: str = rxe.field("R$ 0,00", auth=False)
    order_subtotal: str = rxe.field("R$ 0,00", auth=False)
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
        whole = f"{cents // 100:,}".replace(",", ".")
        return f"R$ {whole},{cents % 100:02d}"

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
            subtotal = sum(c.quantity * p.price_centavos for c, p in rows)
            self.subtotal = self._brl(subtotal)
            discount = 0
            self.coupon_error = ""
            if not rows:
                self._applied_coupon_code = ""
                self.coupon_notice = ""
            if self._applied_coupon_code:
                coupon = await session.scalar(
                    select(Coupon)
                    .where(Coupon.code == self._applied_coupon_code)
                    .limit(1)
                )
                try:
                    discount = coupon_discount(
                        coupon, subtotal, datetime.now(timezone.utc)
                    )
                except ValueError as e:
                    self.coupon_error = str(e)
                    self.coupon_notice = ""
            self.coupon = self._applied_coupon_code
            self.discount = self._brl(discount)
            self.grand_total = self._brl(subtotal - discount)

    @rxe.event(auth=False, background=True)
    async def apply_coupon(self, form_data: dict[str, Any]):
        async with self:
            if self.busy or self.submitting or self.loading or self.confirmed:
                return
            self.coupon_error = ""
            self.coupon_notice = ""
            try:
                code = normalize_code(str(form_data.get("coupon_code", "")))
            except ValueError as e:
                self.coupon_error = str(e)
                return
            self.busy = True
            key = self._key()
        try:
            async with rx.asession() as session:
                subtotal = int(
                    await session.scalar(
                        select(
                            func.coalesce(
                                func.sum(
                                    CartItem.quantity * Product.price_centavos
                                ),
                                0,
                            )
                        )
                        .select_from(CartItem)
                        .join(Product, Product.id == CartItem.product_id)
                        .where(CartItem.cart_key == key)
                    )
                    or 0
                )
                coupon = await session.scalar(
                    select(Coupon).where(Coupon.code == code).limit(1)
                )
                discount = coupon_discount(
                    coupon, subtotal, datetime.now(timezone.utc)
                )
            async with self:
                self._applied_coupon_code = code
                self.coupon = code
                self.discount = self._brl(discount)
                self.grand_total = self._brl(subtotal - discount)
                self.coupon_notice = "Cupom aplicado. O desconto será conferido novamente ao enviar o pedido."
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.coupon_error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Não foi possível aplicar o cupom. Tente novamente."
                )
        finally:
            async with self:
                self.busy = False
        async with self:
            applied = not self.coupon_error
        if applied:
            yield CartState.load_cart

    @rxe.event(auth=False)
    def remove_coupon(self):
        if self.busy or self.submitting or self.loading:
            return
        self._applied_coupon_code = ""
        self.coupon = ""
        self.discount = "R$ 0,00"
        self.grand_total = self.subtotal
        self.coupon_error = ""
        self.coupon_notice = "Cupom removido."
        return CartState.load_cart

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
                    subtotal = sum(
                        c.quantity * by_id[c.product_id].price_centavos
                        for c in items
                    )
                    discount = 0
                    coupon_code = self._applied_coupon_code
                    if coupon_code:
                        coupon = await session.scalar(
                            select(Coupon)
                            .where(Coupon.code == coupon_code)
                            .with_for_update()
                        )
                        discount = coupon_discount(
                            coupon, subtotal, datetime.now(timezone.utc)
                        )
                    total = subtotal - discount
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
                        subtotal_centavos=subtotal,
                        shipping_centavos=0,
                        coupon_code=coupon_code or None,
                        discount_centavos=discount,
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
            self.order_subtotal = self._brl(subtotal)
            self.order_coupon = coupon_code
            self.order_discount = self._brl(discount)
            self._applied_coupon_code = ""
            self.coupon = ""
            self.discount = "R$ 0,00"
            self.grand_total = "R$ 0,00"
            self.coupon_error = ""
            self.coupon_notice = ""
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
