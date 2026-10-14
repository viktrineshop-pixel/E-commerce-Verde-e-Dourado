import reflex as rx
import ast
import unittest
from pathlib import Path
from app.affiliate import (
    PARTNER_ROUTES,
    effective_destination,
    safe_affiliate_url,
)
from app.states.admin_state import empty_draft


class AffiliateTests(unittest.TestCase):
    def test_secure_destinations_are_preserved(self):
        for url in (
            "https://example.com/product?tag=shop&item=1#details",
            "https://example.com:443/p",
            "https://example.com/p%20name",
        ):
            if "%20" in url:
                self.assertFalse(safe_affiliate_url(url))
            else:
                self.assertTrue(safe_affiliate_url(url))
                self.assertEqual(effective_destination("Shopee", url), url)

    def test_unsafe_urls_fall_back_to_each_partner(self):
        for partner, route in PARTNER_ROUTES.items():
            for url in (
                "",
                "http://example.com",
                "//example.com",
                "/product",
                "javascript:alert(1)",
                "data:text/html,hi",
                "https:///product",
                "https://user:password@example.com",
                "https://example.com:bad",
                "https://example.com:99999",
                "https://example.com\\evil",
                "https://example.com/\nnext",
                "https://example.com/%0anext",
                "https://example.com/%7fnext",
                "https://example.com/ next",
                " https://example.com",
                "https://example.com/%5cnext",
            ):
                with self.subTest(partner=partner, url=url):
                    self.assertFalse(safe_affiliate_url(url))
                    self.assertEqual(effective_destination(partner, url), route)

    def test_new_draft_has_optional_url_and_valid_partner(self):
        draft = empty_draft()
        self.assertEqual(draft["affiliate_url"], "")
        self.assertEqual(draft["partner_name"], "Amazon")

    def test_admin_mutations_keep_authorization(self):
        root = Path(__file__).resolve().parents[1]
        tree = ast.parse((root / "app/states/admin_state.py").read_text())
        methods = {
            node.name: node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        for name in (
            "save_product",
            "confirm_delete",
            "set_field",
            "edit_product",
            "new_product",
        ):
            self.assertTrue(
                any(
                    isinstance(decorator, ast.Call)
                    and any(
                        keyword.arg == "auth"
                        and isinstance(keyword.value, ast.Name)
                        and keyword.value.id == "is_admin"
                        for keyword in decorator.keywords
                    )
                    for decorator in methods[name].decorator_list
                ),
                name,
            )

    def test_cards_use_real_links_without_cart_actions(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "app/components/catalog.py").read_text()
        self.assertNotIn("CartState", source)
        self.assertIn('href=product["destination_url"]', source)
        self.assertIn('"Ir para a loja"', source)
        self.assertIn('product["partner_name"]', source)


if __name__ == "__main__":
    unittest.main()
