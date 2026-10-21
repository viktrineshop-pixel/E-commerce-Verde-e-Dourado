import reflex as rx
import reflex_enterprise as rxe

import logging
from typing import Any
from reflex_enterprise.auth import User
from sqlalchemy.exc import IntegrityError
from app.states.authorization import is_admin
from app.discovery import (
    LABELS,
    FIELDS,
    blank,
    read_page,
    read_editor,
    save_record,
)


class DiscoveryState(rx.State):
    kind: str = rxe.field("product", auth=is_admin)
    heading: str = rxe.field("Produtos editoriais", auth=is_admin)
    rows: list[dict[str, str]] = rxe.field([], auth=is_admin)
    definitions: list[dict[str, str]] = rxe.field(
        [
            {
                "name": name,
                "label": label,
                "control": control,
                "choices": choices,
            }
            for name, label, control, choices in FIELDS["product"]
        ],
        auth=is_admin,
    )
    draft: dict[str, str] = rxe.field(blank("product"), auth=is_admin)
    record_id: int = rxe.field(0, auth=is_admin)
    version: int = rxe.field(0, auth=is_admin)
    page: int = rxe.field(1, auth=is_admin)
    total: int = rxe.field(0, auth=is_admin)
    query: str = rxe.field("", auth=is_admin)
    status_filter: str = rxe.field("", auth=is_admin)
    product_filter: int = rxe.field(0, auth=is_admin)
    loading: bool = rxe.field(False, auth=is_admin)
    saving: bool = rxe.field(False, auth=is_admin)
    error: str = rxe.field("", auth=is_admin)
    notice: str = rxe.field("", auth=is_admin)
    context: str = rxe.field("", auth=is_admin)
    _expected: str = ""

    def _new_editor(self):
        self.record_id = 0
        self._expected = ""
        self.draft = blank(self.kind)
        if self.product_filter and "product_id" in self.draft:
            self.draft["product_id"] = str(self.product_filter)
        self.definitions = [
            {
                "name": name,
                "label": label,
                "control": control,
                "choices": choices,
            }
            for name, label, control, choices in FIELDS[self.kind]
        ]
        self.version += 1

    @rxe.event(auth=is_admin)
    def new_record(self):
        self._new_editor()
        self.error, self.notice = "", ""

    @rxe.event(auth=is_admin)
    def choose_panel(self, kind: str):
        if kind not in LABELS or kind == "audit" or self.saving or self.loading:
            return
        self.kind, self.heading = kind, LABELS[kind]
        self.page, self.total = 1, 0
        self.query, self.status_filter = "", ""
        self.error, self.notice = "", ""
        self.rows = []
        self._new_editor()
        return DiscoveryState.load

    @rxe.event(auth=is_admin)
    async def filter_records(self, form_data: dict[str, Any]):
        if self.loading or self.saving:
            return
        try:
            self.query = str(form_data.get("query", "")).strip()[:250]
            self.status_filter = str(form_data.get("status", "")).strip()
            raw = str(form_data.get("product_filter", "")).strip()
            if raw and (not raw.isdigit() or not 0 < int(raw) <= 2147483647):
                raise ValueError(
                    "Filtro de produto: informe um ID positivo ou deixe vazio."
                )
            self.product_filter = int(raw) if raw else 0
            self.page = 1
            self.context = (
                f"Contexto: produto #{self.product_filter}"
                if self.product_filter
                else ""
            )
            self.error = ""
            self._new_editor()
            yield DiscoveryState.load
        except ValueError as e:
            logging.exception(f"Error: {e}")
            self.error = str(e)

    @rxe.event(auth=is_admin)
    def change_page(self, delta: int):
        if self.loading or self.saving or delta not in (-1, 1):
            return
        self.page = min(
            max(1, (self.total + 14) // 15), max(1, self.page + delta)
        )
        return DiscoveryState.load

    @rxe.event(auth=is_admin, background=True)
    async def load(self):
        async with self:
            if self.loading or self.saving:
                return
            self.loading = True
            kind, page, query, status, product_id = (
                self.kind,
                self.page,
                self.query,
                self.status_filter,
                self.product_filter,
            )
        try:
            rows, total = await read_page(kind, page, query, status, product_id)
            async with self:
                self.rows, self.total = rows, total
                self.page = min(page, max(1, (total + 14) // 15))
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.rows = []
                self.error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Não foi possível carregar este painel. Use Atualizar para tentar novamente."
                )
        finally:
            async with self:
                self.loading = False

    @rxe.event(auth=is_admin, background=True)
    async def edit(self, record_id: str):
        async with self:
            if (
                self.loading
                or self.saving
                or self.kind in ("audit", "observation")
            ):
                return
            kind = self.kind
            self.loading = True
            self.error, self.notice = "", ""
        try:
            values, expected = await read_editor(kind, int(record_id))
            async with self:
                self.draft, self._expected, self.record_id = (
                    values,
                    expected,
                    int(record_id),
                )
                self.version += 1
            yield rx.call_script(
                "document.getElementById('discovery-editor')?.scrollIntoView({behavior:'smooth',block:'start'})"
            )
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Não foi possível abrir o registro. Atualize o painel."
                )
        finally:
            async with self:
                self.loading = False

    @rxe.event(auth=is_admin)
    def save(self, form_data: dict[str, Any]):
        if self.saving or self.loading:
            return
        fields = {
            str(k): str(v)
            for k, v in form_data.items()
            if isinstance(v, (str, int, float, bool))
        }
        for key in self.draft:
            if key in fields:
                self.draft[key] = fields[key][:10001]
        self.error, self.notice = "", ""
        self.saving = True
        return DiscoveryState.persist(fields)

    @rxe.event(auth=is_admin, background=True)
    async def persist(self, fields: dict[str, str]):
        async with self:
            kind, record_id, expected = (
                self.kind,
                self.record_id,
                self._expected,
            )
        try:
            user = await User.current() or {}
            actor = str(user.get("sub", ""))
            saved_id = await save_record(
                kind, record_id, fields, expected, actor
            )
            async with self:
                self.error = ""
                self.notice = f"Registro #{saved_id} salvo com auditoria. Revisão manual não comprova API, venda, comissão ou saúde do redirecionamento."
                self._new_editor()
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                if isinstance(e, ValueError):
                    self.error = str(e)
                elif isinstance(e, IntegrityError):
                    self.error = "Conflito de identificador/slug ou vínculo: já existe um registro com esta chave (incluindo link único por oferta). Nenhuma alteração foi confirmada."
                else:
                    self.error = "Não foi possível confirmar o salvamento. O formulário foi mantido; atualize a lista antes de tentar novamente."
        finally:
            async with self:
                self.saving = False
        yield DiscoveryState.load
        from app.states.discovery_audit_state import DiscoveryAuditState

        yield DiscoveryAuditState.load
