import reflex as rx
import reflex_enterprise as rxe

import logging
from datetime import datetime, timezone
from typing import Any, TypedDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.models import Coupon
from app.coupons import (
    normalize_code,
    parse_coupon_value,
    coupon_expiration,
    expiration_day,
)
from app.states.authorization import is_admin


class CouponRow(TypedDict):
    id: int
    code: str
    benefit: str
    active: bool
    validity: str
    expired: bool


class AdminCouponState(rx.State):
    rows: list[CouponRow] = rxe.field([], auth=is_admin)
    draft: dict[str, str] = rxe.field(
        {"code": "", "kind": "percent", "value": "", "expires": ""},
        auth=is_admin,
    )
    errors: dict[str, str] = rxe.field({}, auth=is_admin)
    error: str = rxe.field("", auth=is_admin)
    notice: str = rxe.field("", auth=is_admin)
    loading: bool = rxe.field(False, auth=is_admin)
    busy: bool = rxe.field(False, auth=is_admin)
    editing: bool = rxe.field(False, auth=is_admin)
    active: bool = rxe.field(True, auth=is_admin)
    revision: int = rxe.field(0, auth=is_admin)
    page: int = rxe.field(1, auth=is_admin)
    has_next: bool = rxe.field(False, auth=is_admin)
    _editing_id: int = 0

    @rxe.event(auth=is_admin, background=True)
    async def load_coupons(self, delta: int = 0):
        async with self:
            if (
                self.loading
                or self.busy
                or delta not in (-1, 0, 1)
                or (delta == 1 and not self.has_next)
            ):
                return
            self.loading = True
            self.error = ""
            page = max(1, self.page + delta)
        try:
            async with rx.asession() as session:
                coupons = (
                    await session.scalars(
                        select(Coupon)
                        .order_by(Coupon.id.desc())
                        .offset((page - 1) * 10)
                        .limit(11)
                    )
                ).all()
                now = datetime.now(timezone.utc)
                rows = [
                    CouponRow(
                        id=c.id,
                        code=c.code,
                        benefit=f"{c.discount_value}%"
                        if c.discount_kind == "percent"
                        else f"R$ {c.discount_value // 100},{c.discount_value % 100:02d}",
                        active=c.active,
                        validity=expiration_day(c.expires_at)
                        or "Sem vencimento",
                        expired=c.expires_at is not None
                        and (
                            c.expires_at
                            if c.expires_at.tzinfo
                            else c.expires_at.replace(tzinfo=timezone.utc)
                        )
                        <= now,
                    )
                    for c in coupons[:10]
                ]
            async with self:
                self.rows = rows
                self.page = page
                self.has_next = len(coupons) > 10
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.rows = []
                self.has_next = False
                self.error = "Não foi possível carregar os cupons. Tente atualizar novamente."
        finally:
            async with self:
                self.loading = False

    @rxe.event(auth=is_admin)
    def new_coupon(self):
        if self.busy or self.loading:
            return
        self._editing_id = 0
        self.editing = False
        self.active = True
        self.draft = {"code": "", "kind": "percent", "value": "", "expires": ""}
        self.errors = {}
        self.error = ""
        self.notice = ""
        self.revision += 1

    @rxe.event(auth=is_admin, background=True)
    async def edit_coupon(self, coupon_id: int):
        async with self:
            if self.busy or self.loading:
                return
            self.busy = True
            self.error = ""
            self.notice = ""
        try:
            async with rx.asession() as session:
                c = await session.scalar(
                    select(Coupon).where(Coupon.id == coupon_id).limit(1)
                )
                if c is None:
                    raise ValueError("Cupom não encontrado. Atualize a lista.")
                draft = {
                    "code": c.code,
                    "kind": c.discount_kind,
                    "value": str(c.discount_value)
                    if c.discount_kind == "percent"
                    else f"{c.discount_value // 100},{c.discount_value % 100:02d}",
                    "expires": expiration_day(c.expires_at),
                }
                active = c.active
            async with self:
                self._editing_id = coupon_id
                self.draft = draft
                self.active = active
                self.editing = True
                self.errors = {}
                self.revision += 1
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Não foi possível abrir o cupom. Tente novamente."
                )
        finally:
            async with self:
                self.busy = False

    @rxe.event(auth=is_admin, background=True)
    async def save_coupon(self, form_data: dict[str, Any]):
        async with self:
            if self.busy or self.loading:
                return
            draft = {
                k: str(form_data.get(k, "")).strip()[:200]
                for k in ("code", "kind", "value", "expires")
            }
            self.draft = draft
            self.active = form_data.get("active") in ("on", True, "true")
            active, editing_id = self.active, self._editing_id
            self.errors = {}
            self.error = ""
            self.notice = ""
            errors: dict[str, str] = {}
            code, value, expires = "", 0, None
            try:
                code = normalize_code(draft["code"])
            except ValueError as e:
                errors["code"] = str(e)
            try:
                value = parse_coupon_value(draft["kind"], draft["value"])
            except ValueError as e:
                errors["value"] = str(e)
            try:
                expires = coupon_expiration(draft["expires"])
            except ValueError as e:
                errors["expires"] = str(e)
            self.errors = errors
            if errors:
                self.error = (
                    "Revise os campos destacados. O formulário foi mantido."
                )
                return
            self.busy = True
        try:
            async with rx.asession() as session:
                async with session.begin():
                    if editing_id:
                        c = await session.scalar(
                            select(Coupon)
                            .where(Coupon.id == editing_id)
                            .with_for_update()
                        )
                        if c is None:
                            raise ValueError(
                                "Cupom não encontrado. Inicie um novo cadastro."
                            )
                    else:
                        c = Coupon(code=code)
                        session.add(c)
                    c.code = code
                    c.discount_kind = draft["kind"]
                    c.discount_value = value
                    c.expires_at = expires
                    c.active = active
                    await session.flush()
                    saved_id = c.id
            async with self:
                self._editing_id = saved_id
                self.editing = True
                self.draft["code"] = code
                self.revision += 1
                self.notice = "Cupom salvo. Pedidos anteriores mantêm seus códigos e descontos registrados."
        except IntegrityError as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.errors = {
                    "code": "Este código já existe, inclusive entre cupons desativados."
                }
                self.error = "Código já cadastrado. Edite o cupom existente ou escolha outro código."
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Não foi possível salvar. Nenhuma alteração foi confirmada; tente novamente."
                )
        finally:
            async with self:
                self.busy = False
        async with self:
            saved = not self.error
        if saved:
            yield AdminCouponState.load_coupons

    @rxe.event(auth=is_admin, background=True)
    async def set_active(self, coupon_id: int, active: bool):
        async with self:
            if self.busy or self.loading:
                return
            self.busy = True
            self.error = ""
            self.notice = ""
        try:
            async with rx.asession() as session:
                async with session.begin():
                    c = await session.scalar(
                        select(Coupon)
                        .where(Coupon.id == coupon_id)
                        .with_for_update()
                    )
                    if c is None:
                        raise ValueError(
                            "Cupom não encontrado. Atualize a lista."
                        )
                    c.active = active
            async with self:
                if self._editing_id == coupon_id:
                    self.active = active
                    self.revision += 1
                self.notice = (
                    "Cupom ativado. A validade ainda será conferida na sacola."
                    if active
                    else "Cupom desativado. O histórico dos pedidos foi preservado."
                )
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Não foi possível alterar o cupom. Tente novamente."
                )
        finally:
            async with self:
                self.busy = False
        yield AdminCouponState.load_coupons
