import reflex as rx
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from app.click_tracking import click_api
from app.states.admin_click_state import REPORT_SQL


class ClickEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def request_click(
        self, product, path="/api/product-click/7", failure=False
    ):
        session = MagicMock()
        session.get = AsyncMock(return_value=product)
        session.commit = AsyncMock()
        if failure:
            session.commit.side_effect = RuntimeError("commit failed")
        manager = AsyncMock()
        manager.__aenter__.return_value = session
        config = SimpleNamespace(
            deploy_url="https://shop.example", frontend_port=3000
        )
        with (
            patch.object(rx, "asession", return_value=manager),
            patch(
                "app.click_tracking.rx.config.get_config", return_value=config
            ),
        ):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=click_api),
                base_url="https://shop.example",
            ) as client:
                response = await client.get(path, follow_redirects=False)
        return response, session

    def product(
        self, partner="Amazon", url="https://partner.example/item?tag=real"
    ):
        return SimpleNamespace(
            id=7,
            title="Título atual",
            sku="VK-CURRENT",
            partner_name=partner,
            affiliate_url=url,
        )

    async def test_public_get_commits_snapshot_before_returning_redirect(self):
        response, session = await self.request_click(self.product())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.headers["location"],
            "https://partner.example/item?tag=real",
        )
        self.assertEqual(response.headers["cache-control"], "no-store")
        session.get.assert_awaited_once()
        session.commit.assert_awaited_once()
        snapshot = session.add.call_args.args[0]
        self.assertEqual(
            (
                snapshot.product_id,
                snapshot.title,
                snapshot.sku,
                snapshot.marketplace,
            ),
            (7, "Título atual", "VK-CURRENT", "Amazon"),
        )

    async def test_fresh_product_link_and_query_redirect_is_ignored(self):
        response, _ = await self.request_click(
            self.product(url="https://partner.example/changed"),
            "/api/product-click/7?redirect=https://evil.example",
        )
        self.assertEqual(
            response.headers["location"], "https://partner.example/changed"
        )

    async def test_each_internal_fallback_is_frontend_route(self):
        for partner, slug in (
            ("Amazon", "amazon"),
            ("Shopee", "shopee"),
            ("Mercado Livre", "mercado-livre"),
        ):
            response, session = await self.request_click(
                self.product(partner, "javascript:alert(1)")
            )
            self.assertEqual(
                response.headers["location"],
                f"https://shop.example/lojas/{slug}",
            )
            session.commit.assert_awaited_once()

    async def test_missing_invalid_and_deleted_products_do_not_count(self):
        for value in ("7", "invalid", "-1", "99999999999999999999"):
            response, session = await self.request_click(
                None, f"/api/product-click/{value}"
            )
            self.assertEqual(
                response.headers["location"], "https://shop.example/#catalogo"
            )
            session.add.assert_not_called()
            session.commit.assert_not_awaited()

    async def test_failed_insert_keeps_safe_destination_and_logs(self):
        with patch("app.click_tracking.logging.exception") as log:
            response, session = await self.request_click(
                self.product(), failure=True
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.headers["location"],
            "https://partner.example/item?tag=real",
        )
        session.commit.assert_awaited_once()
        log.assert_called_once()


class ReportWiringTests(unittest.TestCase):
    def test_report_aggregates_snapshots_without_live_product_join(self):
        sql = str(REPORT_SQL)
        self.assertIn("GROUP BY sku, title, marketplace", sql)
        self.assertIn("GROUP BY marketplace", sql)
        self.assertIn("rank <= 20", sql)
        self.assertNotIn("JOIN products", sql)

    def test_authorized_background_report_and_wiring(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "app/states/admin_click_state.py").read_text()
        tree = ast.parse(source)
        method = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef)
            and node.name == "load_report"
        )
        decorator = method.decorator_list[0]
        keywords = {kw.arg: ast.unparse(kw.value) for kw in decorator.keywords}
        self.assertEqual(keywords["auth"], "is_admin")
        self.assertEqual(keywords["background"], "True")
        self.assertIn(
            "yield AdminClickState.load_report",
            (root / "app/states/admin_state.py").read_text(),
        )
        self.assertIn(
            "admin_clicks(),", (root / "app/components/admin.py").read_text()
        )
        self.assertIn(
            "api_transformer=click_api", (root / "app/app.py").read_text()
        )
        catalog = (root / "app/components/catalog.py").read_text()
        self.assertIn('href=tracking_url(product["id"])', catalog)
        self.assertNotIn('href=product["destination_url"]', catalog)


if __name__ == "__main__":
    unittest.main()
