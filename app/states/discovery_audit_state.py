import reflex as rx
import reflex_enterprise as rxe

import logging
from typing import Any
from app.states.authorization import is_admin
from app.discovery import read_page


class DiscoveryAuditState(rx.State):
    rows: list[dict[str, str]] = rxe.field([], auth=is_admin)
    page: int = rxe.field(1, auth=is_admin)
    total: int = rxe.field(0, auth=is_admin)
    product_id: int = rxe.field(0, auth=is_admin)
    loading: bool = rxe.field(False, auth=is_admin)
    error: str = rxe.field("", auth=is_admin)

    @rxe.event(auth=is_admin)
    def change_page(self, delta: int):
        if self.loading or delta not in (-1, 1):
            return
        self.page = min(
            max(1, (self.total + 14) // 15), max(1, self.page + delta)
        )
        return DiscoveryAuditState.load

    @rxe.event(auth=is_admin)
    def filter_history(self, form_data: dict[str, Any]):
        try:
            raw = str(form_data.get("product_id", "")).strip()
            if raw and (not raw.isdigit() or not 0 < int(raw) <= 2147483647):
                raise ValueError(
                    "Informe um ID de produto positivo ou deixe vazio para todos."
                )
            self.product_id = int(raw) if raw else 0
            self.page = 1
            return DiscoveryAuditState.load
        except ValueError as e:
            logging.exception(f"Error: {e}")
            self.error = str(e)

    @rxe.event(auth=is_admin, background=True)
    async def load(self):
        async with self:
            if self.loading:
                return
            self.loading, self.error = True, ""
            page, product_id = self.page, self.product_id
        try:
            rows, total = await read_page("audit", page, product_id=product_id)
            async with self:
                self.rows, self.total = rows, total
                self.page = min(page, max(1, (total + 14) // 15))
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.rows = []
                self.error = "Não foi possível carregar a auditoria. Use Atualizar histórico."
        finally:
            async with self:
                self.loading = False
