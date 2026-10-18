import reflex as rx
import reflex_enterprise as rxe
import logging
from typing import TypedDict
from sqlalchemy import text
from app.states.authorization import is_admin


class MarketplaceClicks(TypedDict):
    marketplace: str
    clicks: int


class ProductClicks(TypedDict):
    sku: str
    title: str
    marketplace: str
    clicks: int
    rank: int


REPORT_SQL = text("""
    WITH product_counts AS (
        SELECT sku, title, marketplace, COUNT(*) AS clicks
        FROM product_link_clicks
        GROUP BY sku, title, marketplace
    ), ranked AS (
        SELECT sku, title, marketplace, clicks,
            ROW_NUMBER() OVER (
                ORDER BY clicks DESC, sku, title, marketplace
            ) AS rank
        FROM product_counts
    )
    SELECT 'total' AS kind, '' AS sku, '' AS title, '' AS marketplace,
        COUNT(*) AS clicks, 0 AS rank
    FROM product_link_clicks
    UNION ALL
    SELECT 'marketplace', '', '', marketplace, COUNT(*), 0
    FROM product_link_clicks
    GROUP BY marketplace
    UNION ALL
    SELECT 'product', sku, title, marketplace, clicks, rank
    FROM ranked WHERE rank <= 20
    ORDER BY kind, rank, marketplace
""")


class AdminClickState(rx.State):
    marketplaces: list[MarketplaceClicks] = rxe.field([], auth=is_admin)
    products: list[ProductClicks] = rxe.field([], auth=is_admin)
    total: int = rxe.field(0, auth=is_admin)
    loading: bool = rxe.field(False, auth=is_admin)
    error: str = rxe.field("", auth=is_admin)

    @rxe.event(auth=is_admin, background=True)
    async def load_report(self):
        async with self:
            if self.loading:
                return
            self.loading = True
            self.error = ""
        try:
            async with rx.asession() as session:
                rows = (await session.execute(REPORT_SQL)).mappings().all()
            total = 0
            marketplaces: list[MarketplaceClicks] = []
            products: list[ProductClicks] = []
            for row in rows:
                if row["kind"] == "total":
                    total = int(row["clicks"])
                elif row["kind"] == "marketplace":
                    marketplaces.append(
                        MarketplaceClicks(
                            marketplace=str(row["marketplace"]),
                            clicks=int(row["clicks"]),
                        )
                    )
                elif row["kind"] == "product":
                    products.append(
                        ProductClicks(
                            sku=str(row["sku"]),
                            title=str(row["title"]),
                            marketplace=str(row["marketplace"]),
                            clicks=int(row["clicks"]),
                            rank=int(row["rank"]),
                        )
                    )
            async with self:
                self.total = total
                self.marketplaces = marketplaces
                self.products = products
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.total = 0
                self.marketplaces = []
                self.products = []
                self.error = "Não foi possível carregar os cliques. Use Atualizar relatório para tentar novamente."
        finally:
            async with self:
                self.loading = False
