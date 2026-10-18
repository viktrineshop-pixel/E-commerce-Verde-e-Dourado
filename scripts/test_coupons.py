import reflex as rx

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from app.coupons import (
    normalize_code,
    parse_coupon_value,
    coupon_expiration,
    expiration_day,
    coupon_discount,
)
from app.models import Coupon, Order
from app.states.cart_state import CartState


class CouponValidationTests(unittest.TestCase):
    def test_normalized_codes(self):
        self.assertEqual(normalize_code("  boas-vindas10  "), "BOAS-VINDAS10")
        self.assertEqual(normalize_code("a" * 100), "A" * 100)
        for code in ("", "a" * 101, "A B", "A_B", "<script>", "A/B"):
            with self.subTest(code=code), self.assertRaises(ValueError):
                normalize_code(code)

    def test_exact_values(self):
        for raw, value in (
            ("0,01", 1),
            ("19.99", 1999),
            ("R$ 20,5", 2050),
            ("10", 1000),
        ):
            self.assertEqual(parse_coupon_value("fixed", raw), value)
        for raw in ("1", "10", "100"):
            self.assertEqual(parse_coupon_value("percent", raw), int(raw))
        for kind, raw in (
            ("percent", "0"),
            ("percent", "101"),
            ("percent", "1.5"),
            ("percent", "-1"),
            ("fixed", "0"),
            ("fixed", "NaN"),
            ("fixed", "Infinity"),
            ("fixed", "1e3"),
            ("fixed", "1,234"),
            ("fixed", "1.000,00"),
            ("fixed", "-5"),
            ("unknown", "10"),
        ):
            with (
                self.subTest(kind=kind, raw=raw),
                self.assertRaises(ValueError),
            ):
                parse_coupon_value(kind, raw)

    def test_expiration_end_of_local_day(self):
        self.assertIsNone(coupon_expiration(""))
        expiry = coupon_expiration("2030-01-20")
        self.assertEqual(expiry, datetime(2030, 1, 21, 3, tzinfo=timezone.utc))
        self.assertEqual(expiration_day(expiry), "2030-01-20")
        self.assertEqual(expiration_day(None), "")
        with self.assertRaises(ValueError):
            coupon_expiration("2030-02-30")

    def test_integer_rounding_and_clamping(self):
        now = datetime.now(timezone.utc)
        self.assertEqual(
            coupon_discount(
                Coupon(code="P", active=True, discount_value=33), 101, now
            ),
            33,
        )
        self.assertEqual(
            coupon_discount(
                Coupon(code="P", active=True, discount_value=100), 101, now
            ),
            101,
        )
        self.assertEqual(
            coupon_discount(
                Coupon(
                    code="F",
                    active=True,
                    discount_kind="fixed",
                    discount_value=5000,
                ),
                101,
                now,
            ),
            101,
        )
        self.assertEqual(
            coupon_discount(
                Coupon(
                    code="F",
                    active=True,
                    discount_kind="fixed",
                    discount_value=1,
                ),
                101,
                now,
            ),
            1,
        )

    def test_invalid_coupons(self):
        now = datetime.now(timezone.utc)
        for coupon, subtotal in (
            (None, 100),
            (Coupon(code="OFF", active=False), 100),
            (Coupon(code="OLD", active=True, expires_at=now), 100),
            (Coupon(code="P", active=True), 0),
            (Coupon(code="P", active=True), 1),
        ):
            with self.subTest(coupon=coupon), self.assertRaises(ValueError):
                coupon_discount(coupon, subtotal, now)
        c = Coupon(
            code="VALID",
            active=True,
            discount_value=10,
            expires_at=now + timedelta(seconds=1),
        )
        self.assertEqual(coupon_discount(c, 100, now), 10)

    def test_private_coupon_and_untrusted_checkout_inputs(self):
        state = CartState()
        self.assertEqual(state._applied_coupon_code, "")
        self.assertEqual(state.grand_total, "R$ 0,00")
        values, _ = state._validate(
            {
                "coupon_code": "FAKE",
                "discount_centavos": 999,
                "total_centavos": 0,
            }
        )
        self.assertNotIn("coupon_code", values)
        self.assertNotIn("discount_centavos", values)
        self.assertNotIn("total_centavos", values)


class CheckoutCouponTests(unittest.IsolatedAsyncioTestCase):
    async def _checkout(self, coupon: Coupon):
        state = CartState()
        state._applied_coupon_code = coupon.code
        product = SimpleNamespace(
            id=1,
            title="Peça",
            stock=3,
            price_centavos=101,
            sku="T",
            description="",
            category="",
            image_url="",
            compare_at_price_centavos=None,
        )
        item = SimpleNamespace(product_id=1, quantity=2)
        session = AsyncMock()
        session.add = MagicMock()
        session.begin = MagicMock(return_value=AsyncMock())
        session.scalars.side_effect = [
            SimpleNamespace(all=lambda: [1]),
            SimpleNamespace(all=lambda: [product]),
            SimpleNamespace(all=lambda: [item]),
        ]
        session.scalar.return_value = coupon

        async def flush():
            for call in session.add.call_args_list:
                obj = call.args[0]
                if isinstance(obj, Order):
                    obj.id = 123

        session.flush.side_effect = flush
        manager = AsyncMock()
        manager.__aenter__.return_value = session
        data = {
            "recipient": "Cliente",
            "phone": "11999999999",
            "email": "cliente@example.com",
            "cep": "01310100",
            "street": "Rua",
            "number": "1",
            "complement": "",
            "neighborhood": "Centro",
            "city": "São Paulo",
            "state": "SP",
            "total_centavos": 0,
            "discount_centavos": 999999,
            "coupon_code": "FORGED",
        }
        with (
            patch.object(rx, "asession", return_value=manager),
            patch(
                "app.states.cart_state.User.current",
                new=AsyncMock(return_value={}),
            ),
            patch.object(
                CartState,
                "get_state",
                new=AsyncMock(return_value=SimpleNamespace(loading=False)),
            ),
            patch.object(CartState, "_refresh", new=AsyncMock()),
        ):
            async for _ in CartState.place_order.fn(state, data):
                pass
        return state, session, product

    async def test_checkout_uses_locked_price_and_coupon(self):
        state, session, product = await self._checkout(
            Coupon(code="TEN", active=True, discount_value=10)
        )
        orders = [
            call.args[0]
            for call in session.add.call_args_list
            if isinstance(call.args[0], Order)
        ]
        self.assertEqual(len(orders), 1, state.error)
        order = orders[0]
        self.assertEqual(
            (
                order.subtotal_centavos,
                order.discount_centavos,
                order.total_centavos,
                order.coupon_code,
            ),
            (202, 20, 182, "TEN"),
        )
        self.assertEqual(product.stock, 1)
        self.assertTrue(state.confirmed)
        self.assertEqual(state.order_coupon, "TEN")
        self.assertEqual(state.order_discount, "R$ 0,20")
        self.assertEqual(state._applied_coupon_code, "")
        self.assertIn("FOR UPDATE", str(session.scalar.call_args.args[0]))

    async def test_checkout_rejects_disabled_or_expired_without_writes(self):
        for coupon in (
            Coupon(code="OFF", active=False),
            Coupon(
                code="OLD",
                active=True,
                expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            ),
        ):
            state, session, product = await self._checkout(coupon)
            self.assertFalse(state.confirmed)
            self.assertTrue(state.error)
            session.add.assert_not_called()
            self.assertEqual(product.stock, 3)
            self.assertTrue(
                session.begin.return_value.__aexit__.call_args.args[0]
                is ValueError
            )


if __name__ == "__main__":
    unittest.main()
