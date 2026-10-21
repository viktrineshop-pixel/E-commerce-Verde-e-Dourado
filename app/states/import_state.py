import reflex as rx
import reflex_enterprise as rxe

import logging
from typing import Any
from reflex_enterprise.auth import User
from app.states.authorization import is_admin
from app.catalog_import import (
    KINDS,
    MAX_BYTES,
    parse_csv,
    preview_import,
    commit_import,
    template,
    columns,
)


class ImportState(rx.State):
    kind: str = rxe.field("category", auth=is_admin)
    busy: bool = rxe.field(False, auth=is_admin)
    ready: bool = rxe.field(False, auth=is_admin)
    errors: list[str] = rxe.field([], auth=is_admin)
    preview: list[str] = rxe.field([], auth=is_admin)
    count: int = rxe.field(0, auth=is_admin)
    notice: str = rxe.field("", auth=is_admin)
    _rows: list[dict[str, str]] = []
    _data: bytes = b""
    _confirmed: bool = False

    @rxe.var(auth=is_admin, initial_value="")
    def header_template(self) -> str:
        return template(self.kind)

    @rxe.event(auth=is_admin)
    def choose(self, kind: str):
        if kind in KINDS and not self.busy:
            self.kind = kind
            self.ready = False
            self._rows = []
            self._data = b""
            self.preview = []
            self.errors = []
            self.count = 0
            self.notice = ""

    @rxe.event(auth=is_admin)
    def download_template(self):
        return rx.download(
            data=template(self.kind), filename=f"viktrine-{self.kind}.csv"
        )

    @rxe.event(auth=is_admin)
    async def upload(self, files: list[rx.UploadFile]):
        if self.busy:
            return
        self.ready = False
        self.errors = []
        self.preview = []
        self._rows = []
        self.count = 0
        self.notice = ""
        try:
            if len(files) != 1 or not (files[0].name or "").lower().endswith(
                ".csv"
            ):
                raise ValueError("Selecione exatamente um arquivo .csv.")
            data = await files[0].read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ValueError("Arquivo maior que 512 KiB; divida em lotes.")
            self._data = data
            self.busy = True
            yield ImportState.validate_upload
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.errors = [
                str(e)
                if isinstance(e, ValueError)
                else "Falha no upload; selecione novamente."
            ]
        finally:
            for file in files:
                await file.close()

    @rxe.event(auth=is_admin, background=True)
    async def validate_upload(self):
        async with self:
            kind, data = self.kind, self._data
            self._data = b""
        try:
            rows = parse_csv(kind, data)
            actor = str((await User.current() or {}).get("sub", ""))
            errors = await preview_import(kind, rows, actor)
            async with self:
                self.errors = errors
                self.count = len(rows)
                self.ready = not errors
                self._rows = rows if not errors else []
                self.preview = [
                    f"Registro {i}: {' · '.join(f'{key}={row[key]}' for key in columns(kind) if row.get(key))}"
                    for i, row in enumerate(rows[:20], 2)
                ]
                self.notice = (
                    "Prévia sem escrita: até 20 registros exibidos. Todos os registros foram validados."
                    if not errors
                    else "Nenhuma escrita. Corrija os registros indicados e envie novamente."
                )
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.errors = [
                    str(e)
                    if isinstance(e, ValueError)
                    else "Falha ao validar vínculos; tente novamente."
                ]
                self.ready = False
        finally:
            async with self:
                self.busy = False

    @rxe.event(auth=is_admin)
    def confirm(self, form_data: dict[str, Any]):
        if self.busy or not self.ready or not self._rows:
            return
        reason = str(form_data.get("reason", "")).strip()
        if form_data.get("confirm") != "on" or not reason or len(reason) > 2000:
            self.errors = [
                "Confirme o lote e informe um motivo de até 2.000 caracteres."
            ]
            return
        self.busy = True
        self.ready = False
        self._confirmed = True
        return ImportState.persist(reason)

    @rxe.event(auth=is_admin, background=True)
    async def persist(self, reason: str):
        async with self:
            if not self._confirmed or not self.busy or not self._rows:
                return
            self._confirmed = False
            kind, rows = self.kind, self._rows
            self._rows = []
        try:
            actor = str((await User.current() or {}).get("sub", ""))
            ids = await commit_import(kind, rows, actor, reason)
            async with self:
                self.errors = []
                self.preview = []
                self.notice = f"Lote confirmado atomicamente: {len(ids)} registros. IDs: {', '.join(str(value) for value in ids)}. Revisão/publicação não realizada."
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.errors = [
                    str(e)
                    if isinstance(e, ValueError)
                    else "Lote não confirmado; transação revertida. Confira a lista antes de reenviar."
                ]
                self.notice = "Nenhum registro deste lote foi confirmado; envie novamente para uma nova prévia."
        finally:
            async with self:
                self.busy = False
        from app.states.discovery_state import DiscoveryState
        from app.states.discovery_audit_state import DiscoveryAuditState

        yield DiscoveryState.load
        yield DiscoveryAuditState.load
