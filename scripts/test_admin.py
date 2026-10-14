import reflex as rx
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from app.states.admin_state import parse_brl, safe_image_url
from app.states.authorization import is_admin


class ProductValidationTests(unittest.TestCase):
    def test_exact_money(self):
        for value, cents in [
            ("0", 0),
            ("0,01", 1),
            ("129,90", 12990),
            ("1.299,90", 129990),
            ("R$ 15,5", 1550),
            ("19.99", 1999),
        ]:
            self.assertEqual(parse_brl(value), cents)

    def test_invalid_money(self):
        for value in (
            "",
            "-1",
            "1,999",
            "NaN",
            "Infinity",
            "1e3",
            "1.2345",
            "999999999999999999",
        ):
            with self.assertRaises(ValueError):
                parse_brl(value)

    def test_image_urls(self):
        for value in (
            "https://example.com/photo.png",
            "/placeholder.svg",
            "/images/product.jpg",
        ):
            self.assertTrue(safe_image_url(value))
        for value in (
            "http://example.com/a",
            "javascript:alert(1)",
            "data:image/png,a",
            "//example.com/a",
            "/%2fexample.com/a",
            "/../a",
            "/%2e%2e/a",
            "/\\example.com",
            "https://user:pass@example.com/a",
            "/a%0ab",
        ):
            self.assertFalse(safe_image_url(value))


class AuthorizationTests(unittest.IsolatedAsyncioTestCase):
    async def test_subject_only_and_no_cache(self):
        session = AsyncMock()
        session.scalar.side_effect = [1, None]
        manager = AsyncMock()
        manager.__aenter__.return_value = session
        ctx = SimpleNamespace(
            auth_user_state=SimpleNamespace(
                userinfo={"sub": "stable-sub", "email": "display@example.com"}
            )
        )
        with patch.object(rx, "asession", return_value=manager):
            self.assertTrue(await is_admin(ctx))
            self.assertFalse(await is_admin(ctx))
        self.assertEqual(session.scalar.await_count, 2)

    async def test_blank_subject_fails_closed(self):
        ctx = SimpleNamespace(
            auth_user_state=SimpleNamespace(
                userinfo={"email": "display@example.com"}
            )
        )
        with patch.object(rx, "asession") as factory:
            self.assertFalse(await is_admin(ctx))
            factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
