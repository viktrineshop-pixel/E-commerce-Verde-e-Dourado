import reflex as rx

import unittest
from datetime import timezone
from app.discovery import (
    normalize_slug,
    normalize_gtin,
    safe_https,
    domains_value,
    date_value,
    json_value,
    parse_fields,
    blank,
    snapshot,
)
from app.models import Product, Offer


class DiscoveryValidationTests(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(
            normalize_slug("  Eletrônicos & Casa  "), "eletronicos-casa"
        )
        with self.assertRaises(ValueError):
            normalize_slug("!!!")

    def test_gtin(self):
        self.assertEqual(normalize_gtin("4006381333931"), "04006381333931")
        self.assertEqual(normalize_gtin("4006-3813 33931"), "04006381333931")
        self.assertIsNone(normalize_gtin(""))
        for invalid in ["4006381333932", "123", "000abc00000000"]:
            with self.assertRaises(ValueError):
                normalize_gtin(invalid)

    def test_https_and_merchant_match(self):
        allowed = ["amazon.com.br"]
        self.assertTrue(
            safe_https("https://www.amazon.com.br/item?id=123", allowed)
        )
        for bad in [
            "http://amazon.com.br/item",
            "https://amazon.com.br.evil.com/item",
            "https://evilamazon.com.br/item",
            "https://user@amazon.com.br/item",
            "https://amazon.com.br:8080/item",
            "https://127.0.0.1/item",
            "https://amazon.com.br/%250a",
            "https://amazon.com.br/\\item",
            "https://amazon.com.br/#fragment",
            "https://localhost/item",
        ]:
            self.assertFalse(safe_https(bad, allowed), bad)

    def test_domain_normalization(self):
        self.assertEqual(
            domains_value("Amazon.com.br\nwww.amazon.com.br amazon.com.br"),
            ["amazon.com.br", "www.amazon.com.br"],
        )
        for bad in ["https://amazon.com.br", "*.amazon.com.br", "localhost"]:
            with self.assertRaises(ValueError):
                domains_value(bad)

    def test_dates_require_timezone(self):
        self.assertEqual(
            date_value("2026-01-01T10:00:00-03:00").tzinfo, timezone.utc
        )
        self.assertIsNone(date_value(""))
        with self.assertRaises(ValueError):
            date_value("2026-01-01T10:00:00")

    def test_json_objects_only(self):
        self.assertEqual(json_value('{"cor": "azul"}'), {"cor": "azul"})
        for bad in ["[]", "{", '{"value": NaN}']:
            with self.assertRaises(ValueError):
                json_value(bad)

    def test_offer_has_no_editable_legacy_price(self):
        values = blank("offer")
        self.assertNotIn("price_centavos", values)
        self.assertNotIn("observed_at", values)
        offer = Offer()
        self.assertIsNone(offer.price_centavos)
        self.assertIsNone(offer.observed_at)

    def test_no_stock_in_editorial_form(self):
        values = blank("product")
        self.assertNotIn("stock", values)
        self.assertNotIn("price", values)
        values["title"] = "Produto real"
        self.assertEqual(parse_fields("product", values)["status"], "draft")

    def test_audit_snapshot_preserves_editorial_fields(self):
        product = Product(sku="VK-TEST", title="Antes")
        product.id = 1
        before = snapshot(product)
        product.title = "Depois"
        self.assertEqual(before["title"], "Antes")
        self.assertEqual(snapshot(product)["title"], "Depois")
        self.assertEqual(product.status, "draft")


if __name__ == "__main__":
    unittest.main()
