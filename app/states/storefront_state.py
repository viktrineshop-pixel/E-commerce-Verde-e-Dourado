import reflex as rx
import reflex_enterprise as rxe
import logging
from typing import TypedDict
from sqlalchemy import select, func, or_
from app.models import Product
from app.catalog_seed import seed_catalog


class ProductView(TypedDict):
    id: int
    title: str
    description: str
    category: str
    image_url: str
    price: str
    compare_price: str
    badge: str
    stock: int


class StorefrontState(rx.State):
    products: list[ProductView] = rxe.field([], auth=False)
    search: str = rxe.field("", auth=False)
    category: str = rxe.field("Todos", auth=False)
    sort: str = rxe.field("Destaques", auth=False)
    price_filter: str = rxe.field("Todos os preços", auth=False)
    available_only: bool = rxe.field(False, auth=False)
    loading: bool = rxe.field(True, auth=False)
    error: str = rxe.field("", auth=False)
    total: int = rxe.field(0, auth=False)
    page_number: int = rxe.field(1, auth=False)
    mobile_menu: bool = rxe.field(False, auth=False)

    @rxe.var(auth=False)
    def page_count(self) -> int:
        return max(1, (self.total + 11) // 12)

    @rxe.event(auth=False)
    async def load_catalog(self):
        self.loading = True
        self.error = ""
        yield
        try:
            await seed_catalog()
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.loading = False
            self.error = (
                "Não foi possível carregar o catálogo. Tente novamente."
            )
            return
        yield StorefrontState.refresh_products

    @rxe.event(auth=False)
    async def refresh_products(self):
        self.loading = True
        self.error = ""
        yield
        filters = []
        term = self.search.strip()
        if term:
            escaped = (
                term.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            pattern = f"%{escaped}%"
            filters.append(
                or_(
                    Product.title.ilike(pattern, escape="\\"),
                    Product.description.ilike(pattern, escape="\\"),
                    Product.category.ilike(pattern, escape="\\"),
                )
            )
        if self.category in ("Feminino", "Masculino", "Acessórios"):
            filters.append(Product.category == self.category)
        elif self.category == "Novidades":
            filters.append(Product.badge == "Novidade")
        elif self.category == "Promoções":
            filters.append(
                Product.compare_at_price_centavos > Product.price_centavos
            )
        elif self.category != "Todos":
            filters.append(Product.category == self.category)
        if self.price_filter == "Até R$ 200":
            filters.append(Product.price_centavos <= 20000)
        elif self.price_filter == "R$ 200 a R$ 400":
            filters.extend(
                [
                    Product.price_centavos > 20000,
                    Product.price_centavos <= 40000,
                ]
            )
        elif self.price_filter == "Acima de R$ 400":
            filters.append(Product.price_centavos > 40000)
        if self.available_only:
            filters.append(Product.stock > 0)
        ordering = {
            "Destaques": (Product.featured.desc(), Product.id.asc()),
            "Menor preço": (Product.price_centavos.asc(), Product.id.asc()),
            "Maior preço": (Product.price_centavos.desc(), Product.id.asc()),
            "Mais recentes": (Product.created_at.desc(), Product.id.desc()),
        }
        try:
            async with rx.asession() as session:
                total = await session.scalar(
                    select(func.count()).select_from(Product).where(*filters)
                )
                rows = (
                    await session.scalars(
                        select(Product)
                        .where(*filters)
                        .order_by(
                            *ordering.get(self.sort, ordering["Destaques"])
                        )
                        .offset((self.page_number - 1) * 12)
                        .limit(12)
                    )
                ).all()
                self.products = [
                    ProductView(
                        id=p.id,
                        title=p.title,
                        description=p.description,
                        category=p.category,
                        image_url=p.image_url or "/placeholder.svg",
                        price=self._brl(p.price_centavos),
                        compare_price=self._brl(p.compare_at_price_centavos)
                        if p.compare_at_price_centavos
                        else "",
                        badge=p.badge,
                        stock=p.stock,
                    )
                    for p in rows
                ]
                self.total = int(total or 0)
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.products = []
            self.total = 0
            self.error = (
                "Não foi possível carregar os produtos. Tente novamente."
            )
        finally:
            self.loading = False

    def _brl(self, cents: int) -> str:
        value = f"{cents / 100:,.2f}"
        return (
            f"R$ {value.replace(',', '|').replace('.', ',').replace('|', '.')}"
        )

    @rxe.event(auth=False)
    def set_search(self, value: str):
        self.search = value[:150]
        self.page_number = 1
        return StorefrontState.refresh_products

    @rxe.event(auth=False)
    def choose_category(self, value: str):
        if value not in (
            "Todos",
            "Feminino",
            "Masculino",
            "Acessórios",
            "Novidades",
            "Promoções",
        ):
            return
        self.category = value
        self.page_number = 1
        self.mobile_menu = False
        return StorefrontState.refresh_products

    @rxe.event(auth=False)
    def choose_home_category(self, label: str):
        if label not in (
            "Camining",
            "Destaques",
            "Infantil",
            "Masculino",
            "Vestidos",
            "Papaya",
            "Makeup",
        ):
            return
        self.search = "Vestido" if label == "Vestidos" else ""
        self.category = "Todos" if label in ("Destaques", "Vestidos") else label
        self.sort = "Destaques"
        self.price_filter = "Todos os preços"
        self.available_only = False
        self.page_number = 1
        self.mobile_menu = False
        return StorefrontState.refresh_products

    @rxe.event(auth=False)
    def choose_sort(self, value: str):
        if value in (
            "Destaques",
            "Menor preço",
            "Maior preço",
            "Mais recentes",
        ):
            self.sort = value
            self.page_number = 1
            return StorefrontState.refresh_products

    @rxe.event(auth=False)
    def choose_price(self, value: str):
        if value in (
            "Todos os preços",
            "Até R$ 200",
            "R$ 200 a R$ 400",
            "Acima de R$ 400",
        ):
            self.price_filter = value
            self.page_number = 1
            return StorefrontState.refresh_products

    @rxe.event(auth=False)
    def toggle_available(self):
        self.available_only = not self.available_only
        self.page_number = 1
        return StorefrontState.refresh_products

    @rxe.event(auth=False)
    def clear_filters(self):
        self.search = ""
        self.category = "Todos"
        self.sort = "Destaques"
        self.price_filter = "Todos os preços"
        self.available_only = False
        self.page_number = 1
        return StorefrontState.refresh_products

    @rxe.event(auth=False)
    def change_page(self, direction: int):
        self.page_number = min(
            self.page_count, max(1, self.page_number + direction)
        )
        return StorefrontState.refresh_products

    @rxe.event(auth=False)
    def toggle_menu(self):
        self.mobile_menu = not self.mobile_menu
