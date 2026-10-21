import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text()


class AffiliateOnlyTests(unittest.TestCase):
    def test_legacy_mutations_deny_and_return_before_work(self):
        tree = ast.parse(source("app/states/cart_state.py"))
        state = next(
            n
            for n in tree.body
            if isinstance(n, ast.ClassDef) and n.name == "CartState"
        )
        mutations = {
            "add_product",
            "change_quantity",
            "remove_product",
            "apply_coupon",
            "remove_coupon",
            "place_order",
        }
        found = set()
        for node in state.body:
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name in mutations
            ):
                found.add(node.name)
                self.assertIsInstance(node.body[0], ast.Return)
                decorator = node.decorator_list[0]
                gate = next(
                    k.value for k in decorator.keywords if k.arg == "auth"
                )
                self.assertEqual(gate.id, "legacy_commerce_disabled")
        self.assertEqual(found, mutations)
        gate = next(
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef)
            and n.name == "legacy_commerce_disabled"
        )
        self.assertIs(gate.body[0].value.value, False)

    def test_archive_write_paths_disabled(self):
        tree = ast.parse(source("app/states/admin_order_state.py"))
        state = next(
            n
            for n in tree.body
            if isinstance(n, ast.ClassDef) and n.name == "AdminOrderState"
        )
        persist = next(
            n
            for n in state.body
            if isinstance(n, ast.AsyncFunctionDef)
            and n.name == "_persist_status"
        )
        self.assertIsInstance(persist.body[0], ast.Raise)
        save = next(
            n
            for n in state.body
            if isinstance(n, ast.AsyncFunctionDef) and n.name == "save_status"
        )
        self.assertIsInstance(save.body[1], ast.Return)
        self.assertNotIn(
            "order_status_form(order),",
            source("app/components/admin_orders.py"),
        )
        self.assertIn(
            "WHERE purchaser_sub = :subject",
            source("app/states/account_state.py"),
        )
        self.assertIn(
            "o.purchaser_sub = :subject", source("app/states/account_state.py")
        )

    def test_routes_and_public_copy(self):
        entry = source("app/app.py")
        self.assertNotIn("CartState", entry)
        self.assertNotIn("cart_content", entry)
        self.assertIn('route="/privacidade"', entry)
        self.assertIn('route="/carrinho"', entry)
        self.assertIn(
            'rx.redirect("/")', source("app/states/legacy_navigation_state.py")
        )
        for path in (
            "app/components/header.py",
            "app/components/hero.py",
            "app/pages/marketplaces.py",
            "app/pages/auth_login.py",
        ):
            self.assertNotIn("VIKTRINE SHOP", source(path))
        self.assertIn('href="/privacidade"', source("app/components/hero.py"))
        self.assertNotIn(
            "CartState.load_cart", source("app/components/marketplace.py")
        )
        self.assertNotIn("catalog(),", source("app/components/marketplace.py"))


if __name__ == "__main__":
    unittest.main()
