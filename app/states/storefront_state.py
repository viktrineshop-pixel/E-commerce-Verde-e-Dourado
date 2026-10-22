import reflex as rx
import reflex_enterprise as rxe
import logging
from typing import Any
from decimal import Decimal, InvalidOperation
from app.public_catalog import ProductView, catalog_page, filter_options


class StorefrontState(rx.State):
    products: list[ProductView] = rxe.field([], auth=False)
    search: str = rxe.field("", auth=False)
    category: str = rxe.field("Todos", auth=False)
    sort: str = rxe.field("Mais recentes", auth=False)
    merchant: str = rxe.field("", auth=False)
    minimum: str = rxe.field("", auth=False)
    maximum: str = rxe.field("", auth=False)
    categories: list[str] = rxe.field(["Todos"], auth=False)
    merchants: list[str] = rxe.field([], auth=False)
    _generation: int = 0
    loading: bool = rxe.field(True, auth=False)
    error: str = rxe.field("", auth=False)
    total: int = rxe.field(0, auth=False)
    page_number: int = rxe.field(1, auth=False)
    mobile_menu: bool = rxe.field(False, auth=False)

    @rxe.var(auth=False, initial_value=1)
    def page_count(self) -> int:
        return max(1, (self.total + 11) // 12)

    @rxe.event(auth=False)
    def load_catalog(self):
        return StorefrontState.initialize_catalog

    @rxe.event(auth=False, background=True)
    async def initialize_catalog(self):
        try:
            categories, merchants = await filter_options()
            async with self:
                self.categories = categories
                self.merchants = merchants
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    "Não foi possível carregar os filtros. Tente novamente."
                )
                self.loading = False
            return
        yield StorefrontState.refresh_products

    @rxe.event(auth=False, background=True)
    async def refresh_products(self):
        async with self:
            self._generation += 1
            generation = self._generation
            search, category, merchant, sort, page = (
                self.search,
                self.category,
                self.merchant,
                self.sort,
                self.page_number,
            )
            minimum, maximum = self.minimum, self.maximum
            self.loading = True
            self.error = ""
        try:
            low, high = self._price(minimum), self._price(maximum)
            if high >= 0 and low > high:
                raise ValueError("Preço mínimo não pode exceder o máximo.")
            products, total, page = await catalog_page(
                search, category, merchant, low, high, sort, page
            )
            async with self:
                if generation != self._generation:
                    return
                self.products, self.total, self.page_number = (
                    products,
                    total,
                    page,
                )
                self.loading = False
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                if generation != self._generation:
                    return
                self.products = []
                self.total = 0
                self.loading = False
                self.error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Não foi possível carregar as ofertas. Tente novamente."
                )
        from app.states.favorite_state import FavoriteState

        yield FavoriteState.sync_auth

    def _price(self, value: str) -> int:
        if not value.strip():
            return -1
        try:
            amount = Decimal(value.replace(",", "."))
            if (
                not amount.is_finite()
                or amount < 0
                or amount > 100000000
                or amount * 100 != (amount * 100).to_integral_value()
            ):
                raise ValueError(
                    "Informe preços positivos com até duas casas decimais."
                )
            return int(amount * 100)
        except InvalidOperation as e:
            raise ValueError("Preço inválido. Use, por exemplo, 129,90.") from e

    @rxe.event(auth=False)
    def apply_filters(self, form_data: dict[str, Any]):
        self.category = str(form_data.get("category", "Todos"))
        self.merchant = str(form_data.get("merchant", ""))
        self.minimum = str(form_data.get("minimum", ""))
        self.maximum = str(form_data.get("maximum", ""))
        self.sort = str(form_data.get("sort", "Mais recentes"))
        self.page_number = 1
        return StorefrontState.refresh_products

    @rxe.event(auth=False)
    def set_search(self, value: str):
        self.search = value
        self.page_number = 1
        return StorefrontState.refresh_products

    @rxe.event(auth=False)
    def choose_category(self, value: str):
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
        self.sort = "Mais recentes"
        self.merchant = ""
        self.minimum = ""
        self.maximum = ""
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
    def clear_filters(self):
        self.search = ""
        self.category = "Todos"
        self.sort = "Mais recentes"
        self.merchant = ""
        self.minimum = ""
        self.maximum = ""
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
