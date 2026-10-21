import reflex as rx
import reflex_enterprise as rxe

import logging
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from sqlalchemy import text
from reflex_enterprise.auth import User
from app.states.authorization import is_admin
from app.link_health import verify_offer

REPORT_CTE = """WITH filtered AS (
 SELECT c.offer_id, c.created_at, c.marketplace FROM product_link_clicks c
 WHERE (CAST(:start AS timestamptz) IS NULL OR c.created_at >= CAST(:start AS timestamptz))
 AND (CAST(:end AS timestamptz) IS NULL OR c.created_at < CAST(:end AS timestamptz))
), groups AS (
 SELECT o.id AS offer_id, m.id AS merchant_id, m.name AS merchant, p.title,
 COUNT(*) AS clicks, MAX(c.created_at) AS latest
 FROM filtered c JOIN offers o ON o.id=c.offer_id
 JOIN merchants m ON m.id=o.merchant_id JOIN products p ON p.id=o.product_id
 WHERE (:merchant = 0 OR m.id=:merchant)
 GROUP BY o.id, m.id, m.name, p.title
) """


class OperationsState(rx.State):
    loading: bool = rxe.field(False, auth=is_admin)
    checking: bool = rxe.field(False, auth=is_admin)
    checking_id: int = rxe.field(0, auth=is_admin)
    error: str = rxe.field("", auth=is_admin)
    notice: str = rxe.field("", auth=is_admin)
    start: str = rxe.field("", auth=is_admin)
    end: str = rxe.field("", auth=is_admin)
    merchant: int = rxe.field(0, auth=is_admin)
    page: int = rxe.field(1, auth=is_admin)
    total: int = rxe.field(0, auth=is_admin)
    reports: list[dict[str, str]] = rxe.field([], auth=is_admin)
    stores: list[dict[str, str]] = rxe.field([], auth=is_admin)
    legacy: int = rxe.field(0, auth=is_admin)
    links: list[dict[str, str]] = rxe.field([], auth=is_admin)
    link_page: int = rxe.field(1, auth=is_admin)
    link_total: int = rxe.field(0, auth=is_admin)

    @rxe.event(auth=is_admin)
    def filter_report(self, form_data: dict[str, Any]):
        if self.loading:
            return
        try:
            start, end = (
                str(form_data.get("start", "")),
                str(form_data.get("end", "")),
            )
            for value in (start, end):
                if value:
                    date.fromisoformat(value)
            if start and end and start > end:
                raise ValueError(
                    "Data inicial deve ser anterior ou igual à final."
                )
            raw = str(form_data.get("merchant", "")).strip()
            if raw and (not raw.isdigit() or not 0 < int(raw) <= 2147483647):
                raise ValueError("Loja: ID positivo ou vazio para todas.")
            self.start, self.end = start, end
            self.merchant = int(raw) if raw else 0
            self.page = 1
            return OperationsState.load
        except ValueError as e:
            logging.exception(f"Error: {e}")
            self.error = str(e)

    @rxe.event(auth=is_admin)
    def paginate(self, delta: int, links: bool):
        if self.loading or delta not in (-1, 1):
            return
        if links:
            self.link_page = min(
                max(1, (self.link_total + 14) // 15),
                max(1, self.link_page + delta),
            )
        else:
            self.page = min(
                max(1, (self.total + 14) // 15), max(1, self.page + delta)
            )
        return OperationsState.load

    @rxe.event(auth=is_admin, background=True)
    async def load(self):
        async with self:
            if self.loading:
                return
            self.loading = True
            self.error = ""
            start, end, merchant, page, link_page = (
                self.start,
                self.end,
                self.merchant,
                self.page,
                self.link_page,
            )
        try:
            params = {
                "start": datetime.combine(
                    date.fromisoformat(start), time.min, timezone.utc
                )
                if start
                else None,
                "end": datetime.combine(
                    date.fromisoformat(end) + timedelta(days=1),
                    time.min,
                    timezone.utc,
                )
                if end
                else None,
                "merchant": merchant,
                "offset": (page - 1) * 15,
            }
            async with rx.asession() as session:
                total = int(
                    await session.scalar(
                        text(f"{REPORT_CTE} SELECT COUNT(*) FROM groups"),
                        params,
                    )
                    or 0
                )
                reports = (
                    (
                        await session.execute(
                            text(
                                f"{REPORT_CTE} SELECT offer_id, merchant_id, merchant, title, clicks, latest FROM groups ORDER BY clicks DESC, offer_id LIMIT 15 OFFSET :offset"
                            ),
                            params,
                        )
                    )
                    .mappings()
                    .all()
                )
                stores = (
                    (
                        await session.execute(
                            text(
                                f"{REPORT_CTE} SELECT merchant_id, merchant, SUM(clicks) AS clicks FROM groups GROUP BY merchant_id, merchant ORDER BY clicks DESC, merchant_id LIMIT 15"
                            ),
                            params,
                        )
                    )
                    .mappings()
                    .all()
                )
                legacy = int(
                    await session.scalar(
                        text(
                            f"{REPORT_CTE} SELECT COUNT(*) FROM filtered WHERE offer_id IS NULL"
                        ),
                        params,
                    )
                    or 0
                )
                link_total = int(
                    await session.scalar(
                        text("SELECT COUNT(*) FROM affiliate_links")
                    )
                    or 0
                )
                links = (
                    (
                        await session.execute(
                            text("""SELECT l.offer_id, m.name AS merchant, p.title, l.validation_status,
                l.last_checked_at, l.http_status, l.resolved_url, l.validation_error,
                l.validation_metadata ->> 'network_health' AS network_health
                FROM affiliate_links l JOIN offers o ON o.id=l.offer_id
                JOIN merchants m ON m.id=o.merchant_id JOIN products p ON p.id=o.product_id
                ORDER BY l.id DESC LIMIT 15 OFFSET :offset"""),
                            {"offset": (link_page - 1) * 15},
                        )
                    )
                    .mappings()
                    .all()
                )
            async with self:
                self.total, self.link_total, self.legacy = (
                    total,
                    link_total,
                    legacy,
                )
                self.reports = [
                    {key: str(value or "") for key, value in row.items()}
                    for row in reports
                ]
                self.stores = [
                    {key: str(value or "") for key, value in row.items()}
                    for row in stores
                ]
                self.links = [
                    {key: str(value or "") for key, value in row.items()}
                    for row in links
                ]
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.reports, self.stores, self.links = [], [], []
                self.error = "Falha ao carregar operações. Atualize para tentar novamente; métricas não foram estimadas."
        finally:
            async with self:
                self.loading = False

    @rxe.event(auth=is_admin, background=True)
    async def check(self, offer_id: str):
        async with self:
            if self.checking:
                return
            self.checking = True
            self.error, self.notice = "", ""
        try:
            if not offer_id.isdigit() or not 0 < int(offer_id) <= 2147483647:
                raise ValueError("ID de oferta inválido.")
            async with self:
                self.checking_id = int(offer_id)
            actor = str((await User.current() or {}).get("sub", ""))
            notice = await verify_offer(int(offer_id), actor)
            async with self:
                self.notice = notice
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Não foi possível confirmar a checagem; atualize antes de repetir."
                )
        finally:
            async with self:
                self.checking = False
                self.checking_id = 0
        yield OperationsState.load
        from app.states.discovery_state import DiscoveryState
        from app.states.discovery_audit_state import DiscoveryAuditState

        yield DiscoveryState.load
        yield DiscoveryAuditState.load
