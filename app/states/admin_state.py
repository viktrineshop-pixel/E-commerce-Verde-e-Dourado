import reflex as rx
import reflex_enterprise as rxe
import logging
import re
from decimal import Decimal
from typing import Any, TypedDict
from urllib.parse import urlsplit, unquote
from uuid import uuid4
from sqlalchemy import select, func, text
from app.models import Product, StoreMember
from app.affiliate import PARTNER_ROUTES, safe_affiliate_url


def parse_brl(value: str) -> int:
    raw = value.strip().removeprefix("R$").strip()
    if len(raw) > 24:
        raise ValueError("Valor muito longo.")
    if not re.fullmatch(
        r"(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d{1,2})?|\d+(?:\.\d{1,2})?", raw
    ):
        raise ValueError(
            "Use um valor positivo como 129,90 ou 1.299,90, com até duas casas decimais."
        )
    normalized = raw.replace(".", "").replace(",", ".") if "," in raw else raw
    cents = int(Decimal(normalized) * 100)
    if cents > 99999999999:
        raise ValueError("Preço máximo: R$ 999.999.999,99.")
    return cents


def safe_image_url(value: str) -> bool:
    if not value or len(value) > 2048:
        return False
    decoded = unquote(value)
    if any(c.isspace() or ord(c) < 32 for c in decoded) or "\\" in decoded:
        return False
    try:
        parts = urlsplit(value)
        if value.startswith("/"):
            return (
                not decoded.startswith("//")
                and not parts.netloc
                and not parts.scheme
                and not parts.fragment
                and ".." not in unquote(parts.path).split("/")
            )
        return (
            parts.scheme == "https"
            and bool(parts.hostname)
            and parts.username is None
            and parts.password is None
        )
    except ValueError:
        return False


def empty_draft() -> dict[str, str]:
    return {
        "title": "",
        "description": "",
        "category": "",
        "image_url": "",
        "price": "",
        "compare_price": "",
        "stock": "0",
        "badge": "",
        "partner_name": "Amazon",
        "affiliate_url": "",
    }


class AdminProduct(TypedDict):
    id: int
    title: str
    sku: str
    category: str
    image_url: str
    price: str
    stock: int
    partner_name: str


class AdminState(rx.State):
    can_manage: bool = False
    role_loading: bool = True
    role_error: str = ""
    products: list[AdminProduct] = []
    draft: dict[str, str] = empty_draft()
    errors: dict[str, str] = {}
    error: str = rxe.field("", auth=True)
    notice: str = rxe.field("", auth=True)
    sku: str = "Gerado automaticamente ao salvar"
    editing: bool = rxe.field(False, auth=True)
    featured: bool = rxe.field(False, auth=True)
    delete_title: str = rxe.field("", auth=True)
    loading: bool = rxe.field(False, auth=True)
    busy: bool = rxe.field(False, auth=True)
    page: int = 1
    total: int = 0
    _editing_id: int = 0
    _delete_id: int = 0

    @rx.var
    def preview_url(self) -> str:
        url = self.draft["image_url"].strip()
        return url if safe_image_url(url) else "/placeholder.svg"

    async def _bootstrap(self):
        self.can_manage = False
        self.role_error = ""
        self.role_loading = True
        try:
            subject = ""
            user: dict[str, str] = {}
            if (
                not isinstance(subject, str)
                or not subject.strip()
                or len(subject) > 255
            ):
                self.products = []
                self._clear_draft()
                return
            values = {
                "subject": subject,
                "email": str(user.get("email", ""))[:320],
                "name": str(user.get("name", ""))[:250],
            }
            async with rx.asession() as session:
                async with session.begin():
                    await session.execute(
                        text("""
                        INSERT INTO store_members (subject, role, admin_slot, email, name)
                        VALUES (:subject, 'admin', 1, :email, :name)
                        ON CONFLICT DO NOTHING
                    """),
                        values,
                    )
                    await session.execute(
                        text("""
                        INSERT INTO store_members (subject, role, admin_slot, email, name)
                        VALUES (:subject, 'member', NULL, :email, :name)
                        ON CONFLICT DO NOTHING
                    """),
                        values,
                    )
                    self.can_manage = (
                        await session.scalar(
                            select(StoreMember.id)
                            .where(
                                StoreMember.subject == subject,
                                StoreMember.role == "admin",
                                StoreMember.admin_slot == 1,
                            )
                            .limit(1)
                        )
                        is not None
                    )
            if not self.can_manage:
                self.products = []
                self._clear_draft()
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.can_manage = False
            self.products = []
            self.role_error = (
                "Não foi possível verificar seu acesso. Tente novamente."
            )
        finally:
            self.role_loading = False

    @rx.event
    async def load_role(self):
        await self._bootstrap()

    @rx.event
    async def load_dashboard(self):
        await self._bootstrap()
        if self.can_manage:
            from app.states.admin_order_state import AdminOrderState

            yield AdminOrderState.load_orders
            yield AdminState.load_products

    @rx.event
    async def load_products(self):
        self.loading = True
        try:
            async with rx.asession() as session:
                self.total = int(
                    await session.scalar(
                        select(func.count()).select_from(Product)
                    )
                    or 0
                )
                self.page = min(self.page, max(1, (self.total + 19) // 20))
                rows = (
                    await session.scalars(
                        select(Product)
                        .order_by(Product.id.desc())
                        .offset((self.page - 1) * 20)
                        .limit(20)
                    )
                ).all()
                self.products = [
                    AdminProduct(
                        id=p.id,
                        title=p.title,
                        sku=p.sku,
                        category=p.category,
                        image_url=p.image_url
                        if safe_image_url(p.image_url)
                        else "/placeholder.svg",
                        price=f"R$ {self._amount(p.price_centavos)}",
                        stock=p.stock,
                        partner_name=p.partner_name,
                    )
                    for p in rows
                ]
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.products = []
            self.error = "Não foi possível atualizar a lista. Use Atualizar; alterações já confirmadas foram mantidas."
        finally:
            self.loading = False

    def _amount(self, cents: int) -> str:
        return f"{cents // 100},{cents % 100:02d}"

    def _clear_draft(self):
        self._editing_id = 0
        self._delete_id = 0
        self.editing = False
        self.delete_title = ""
        self.sku = "Gerado automaticamente ao salvar"
        self.draft = empty_draft()
        self.featured = False
        self.errors = {}

    @rxe.event(auth=True)
    def new_product(self):
        self._clear_draft()
        self.notice = ""
        self.error = ""

    @rxe.event(auth=True)
    def set_field(self, field: str, value: str):
        if field in self.draft:
            self.draft[field] = value[:10001]
            self.errors.pop(field, None)

    @rxe.event(auth=True)
    def toggle_featured(self):
        self.featured = not self.featured

    @rxe.event(auth=True)
    async def edit_product(self, product_id: int):
        self.error = ""
        self.notice = ""
        try:
            async with rx.asession() as session:
                p = await session.scalar(
                    select(Product).where(Product.id == product_id).limit(1)
                )
                if p is None:
                    raise ValueError(
                        "Produto não encontrado. Atualize a lista."
                    )
                self._clear_draft()
                self._editing_id = p.id
                self.editing = True
                self.sku = p.sku
                self.featured = p.featured
                self.draft = {
                    "title": p.title,
                    "description": p.description,
                    "category": p.category,
                    "image_url": p.image_url,
                    "price": self._amount(p.price_centavos),
                    "compare_price": self._amount(p.compare_at_price_centavos)
                    if p.compare_at_price_centavos is not None
                    else "",
                    "stock": str(p.stock),
                    "badge": p.badge,
                    "partner_name": p.partner_name,
                    "affiliate_url": p.affiliate_url,
                }
            return rx.call_script(
                "document.getElementById('product-editor')?.scrollIntoView({behavior:'smooth', block:'start'}); document.getElementById('admin-title')?.focus({preventScroll:true});"
            )
        except ValueError as e:
            logging.exception(f"Error: {e}")
            self.error = str(e)
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "Não foi possível abrir o produto. Tente novamente."

    def _validate(self) -> tuple[int, int | None, int]:
        self.errors = {}
        for field, limit in {
            "title": 250,
            "description": 10000,
            "category": 120,
            "image_url": 2048,
            "badge": 80,
        }.items():
            self.draft[field] = self.draft[field].strip()
            if field != "badge" and not self.draft[field]:
                self.errors[field] = "Preencha este campo."
            elif len(self.draft[field]) > limit:
                self.errors[field] = f"Use até {limit} caracteres."
        if self.draft["partner_name"] not in PARTNER_ROUTES:
            self.errors["partner_name"] = (
                "Escolha Amazon, Mercado Livre ou Shopee."
            )
        affiliate_url = self.draft["affiliate_url"]
        if affiliate_url and not safe_affiliate_url(affiliate_url):
            self.errors["affiliate_url"] = (
                "Use uma URL absoluta https:// segura, sem credenciais, espaços ou caracteres de controle, com até 2048 caracteres. Ou deixe em branco."
            )
        if not safe_image_url(self.draft["image_url"]):
            self.errors["image_url"] = (
                "Use https:// ou um caminho local seguro iniciado por / (sem uploads temporários)."
            )
        if self.draft["image_url"].startswith(("/_upload", "/_upload/")):
            self.errors["image_url"] = (
                "Use uma imagem permanente, não um upload temporário."
            )
        price = 0
        compare = None
        for field in ("price", "compare_price"):
            if field == "compare_price" and not self.draft[field].strip():
                continue
            try:
                value = parse_brl(self.draft[field])
                if field == "price":
                    price = value
                else:
                    compare = value
            except ValueError as e:
                self.errors[field] = str(e)
        if compare is not None and compare < price:
            self.errors["compare_price"] = (
                "O preço anterior deve ser maior ou igual ao preço atual."
            )
        stock = 0
        if not re.fullmatch(r"\d{1,10}", self.draft["stock"].strip()):
            self.errors["stock"] = "Informe um número inteiro não negativo."
        else:
            stock = int(self.draft["stock"])
            if stock > 2147483647:
                self.errors["stock"] = "Estoque acima do limite permitido."
        return price, compare, stock

    @rxe.event(auth=True)
    async def save_product(self, fields: dict[str, Any]):
        if self.busy:
            return
        for field in self.draft:
            if field in fields and isinstance(fields[field], str):
                self.draft[field] = fields[field][:10001]
        self.notice = ""
        self.error = ""
        price, compare, stock = self._validate()
        if self.errors:
            self.error = "Revise os campos indicados. O formulário foi mantido."
            return
        self.busy = True
        try:
            async with rx.asession() as session:
                async with session.begin():
                    if self._editing_id:
                        p = await session.scalar(
                            select(Product)
                            .where(Product.id == self._editing_id)
                            .with_for_update()
                        )
                        if p is None:
                            raise ValueError(
                                "Este produto foi excluído. Copie os dados ou inicie um novo cadastro."
                            )
                    else:
                        p = Product(sku=f"VK-{uuid4().hex.upper()}")
                        session.add(p)
                    for field in (
                        "title",
                        "description",
                        "category",
                        "image_url",
                        "badge",
                        "partner_name",
                        "affiliate_url",
                    ):
                        setattr(p, field, self.draft[field])
                    p.price_centavos = price
                    p.compare_at_price_centavos = compare
                    p.stock = stock
                    p.featured = self.featured
                    await session.flush()
                    saved_id, saved_sku = p.id, p.sku
            self._editing_id = saved_id
            self.sku = saved_sku
            self.editing = True
            self.notice = (
                "Produto salvo. As informações estão disponíveis na vitrine."
            )
            yield AdminState.load_products
            from app.states.storefront_state import StorefrontState

            yield StorefrontState.refresh_products
        except ValueError as e:
            logging.exception(f"Error: {e}")
            self.error = str(e)
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "Não foi possível salvar o produto. Os campos foram mantidos; tente novamente."
        finally:
            self.busy = False

    @rxe.event(auth=True)
    async def request_delete(self, product_id: int):
        self.error = ""
        self.notice = ""
        self._delete_id = 0
        self.delete_title = ""
        try:
            async with rx.asession() as session:
                p = await session.scalar(
                    select(Product).where(Product.id == product_id).limit(1)
                )
                if p is None:
                    raise ValueError(
                        "Produto não encontrado. Atualize a lista."
                    )
                self._delete_id = p.id
                self.delete_title = p.title
        except ValueError as e:
            logging.exception(f"Error: {e}")
            self.error = str(e)
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = (
                "Não foi possível preparar a exclusão. Tente novamente."
            )

    @rxe.event(auth=True)
    def cancel_delete(self):
        self._delete_id = 0
        self.delete_title = ""

    @rxe.event(auth=True)
    async def confirm_delete(self):
        if not self._delete_id or self.busy:
            return
        self.busy = True
        self.error = ""
        self.notice = ""
        try:
            async with rx.asession() as session:
                async with session.begin():
                    p = await session.scalar(
                        select(Product)
                        .where(Product.id == self._delete_id)
                        .with_for_update()
                    )
                    if p is None:
                        raise ValueError(
                            "O produto já foi excluído. Atualize a lista."
                        )
                    await session.delete(p)
            if self._editing_id == self._delete_id:
                self._clear_draft()
            self._delete_id = 0
            self.delete_title = ""
            self.notice = "Produto excluído. Sacolas foram ajustadas e o histórico dos pedidos foi preservado."
            yield AdminState.load_products
            from app.states.storefront_state import StorefrontState
            from app.states.cart_state import CartState

            yield StorefrontState.refresh_products
            yield CartState.load_cart
        except ValueError as e:
            logging.exception(f"Error: {e}")
            self._delete_id = 0
            self.delete_title = ""
            self.error = str(e)
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "Não foi possível excluir. Nenhuma exclusão foi confirmada; tente novamente."
        finally:
            self.busy = False

    @rxe.event(auth=True)
    def change_page(self, delta: int):
        self.page = min(
            max(1, (self.total + 19) // 20), max(1, self.page + delta)
        )
        return AdminState.load_products
