import reflex as rx
import reflex_enterprise as rxe
import logging
import re
from app.public_catalog import ProductView, product_detail


class ProductDetailState(rx.State):
    groups: list[ProductView] = rxe.field([], auth=False)
    loading: bool = rxe.field(True, auth=False)
    error: str = rxe.field("", auth=False)
    _generation: int = 0

    @rxe.event(auth=False, background=True)
    async def load_detail(self):
        async with self:
            raw = self.router.page.params.get("product_id", "")
            self._generation += 1
            generation = self._generation
            self.loading = True
            self.error = ""
            self.groups = []
        try:
            groups = []
            if (
                isinstance(raw, str)
                and re.fullmatch(r"[0-9]{1,10}", raw)
                and 0 < int(raw) <= 2147483647
            ):
                groups = await product_detail(int(raw))
            async with self:
                if generation != self._generation:
                    return
                self.groups = groups
                self.loading = False
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                if generation == self._generation:
                    self.loading = False
                    self.error = "Não foi possível carregar este produto. Tente novamente."
        from app.states.favorite_state import FavoriteState

        yield FavoriteState.sync_auth
