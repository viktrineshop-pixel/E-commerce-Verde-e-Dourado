import reflex as rx

import asyncio
import unittest
from unittest.mock import patch
from starlette.requests import Request
from app.public_catalog import PUBLIC_CTE, catalog_page, money
from app.discovery import safe_https
from app.click_tracking import track_offer_click, track_product_click


class PublicDiscoveryTests(unittest.TestCase):
    def test_money_has_two_places(self):
        self.assertEqual(money(12990, "BRL"), "R$ 129,90")
        self.assertEqual(money(1, "USD"), "USD 0,01")

    def test_domain_and_protocol_guards(self):
        allowed = ["amazon.com.br"]
        self.assertTrue(
            safe_https("https://www.amazon.com.br/item?tag=viktrine", allowed)
        )
        for url in (
            "https://amazon.com.br.evil.example/item",
            "http://amazon.com.br/item",
            "https://evil.example/item",
            "https://amazon.com.br@evil.example/item",
            "https://amazon.com.br/%250a",
            "https://amazon.com.br:444/item",
        ):
            self.assertFalse(safe_https(url, allowed))

    def test_eligibility_has_all_required_joins(self):
        for fragment in (
            "p.status = 'published'",
            "o.status = 'published'",
            "m.status = 'active'",
            "l.validation_status = 'valid'",
            "p.sku NOT LIKE 'DEMO-%'",
            "price_observations po",
            "active_categories",
            "l.expires_at > CURRENT_TIMESTAMP",
            "po.currency = o.currency",
            "po.observed_at = o.observed_at",
        ):
            self.assertIn(fragment, PUBLIC_CTE)

    def test_bad_ids_never_query_or_refer(self):
        for handler, key in (
            (track_offer_click, "offer_id"),
            (track_product_click, "product_id"),
        ):
            for value in (
                "0",
                "-1",
                "2147483648",
                "1?url=https://evil.example",
                "abc",
                "1.0",
            ):
                request = Request(
                    {
                        "type": "http",
                        "method": "GET",
                        "path": "/",
                        "headers": [],
                        "path_params": {key: value},
                    }
                )
                with (
                    patch("app.click_tracking.rx.asession") as session,
                    patch(
                        "app.click_tracking.frontend_destination",
                        return_value="/#catalogo",
                    ),
                ):
                    response = asyncio.run(handler(request))
                    session.assert_not_called()
                    self.assertEqual(response.headers["location"], "/#catalogo")
                    self.assertEqual(
                        response.headers["cache-control"], "no-store"
                    )


async def database_contract():
    products, total, page = await catalog_page(
        "", "Todos", "", -1, -1, "Mais recentes", 1
    )
    assert len(products) <= 12
    assert total >= 0 and page >= 1
    for product in products:
        assert product["offers"]
        for offer in product["offers"]:
            assert offer["source"] and offer["observed"]
    return total


if __name__ == "__main__":
    unittest.main()
