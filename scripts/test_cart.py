import reflex as rx
import unittest
from app.states.cart_state import CartState
from app.models import CartItem, Order, OrderItem


class CartValidationTests(unittest.TestCase):
    def setUp(self):
        self.state = CartState()
        self.data = {
            "recipient": "Maria Silva",
            "phone": "(11) 99999-9999",
            "email": "maria@example.com",
            "cep": "01310-100",
            "street": "Avenida Paulista",
            "number": "123",
            "complement": "",
            "neighborhood": "Bela Vista",
            "city": "São Paulo",
            "state": "SP",
        }

    def test_valid_address(self):
        values, errors = self.state._validate(self.data)
        self.assertEqual(errors, {})
        self.assertEqual(values["cep"], "01310100")
        self.assertEqual(values["phone"], "11999999999")

    def test_required_and_invalid_fields(self):
        for field in self.data:
            if field == "complement":
                continue
            with self.subTest(field=field):
                values, errors = self.state._validate({**self.data, field: ""})
                self.assertIn(field, errors)
        for field, value in (
            ("email", "invalid"),
            ("cep", "123"),
            ("phone", "999"),
            ("state", "XX"),
        ):
            with self.subTest(field=field):
                values, errors = self.state._validate(
                    {**self.data, field: value}
                )
                self.assertIn(field, errors)

    def test_client_totals_are_not_inputs(self):
        values, errors = self.state._validate(
            {
                **self.data,
                "total_centavos": 1,
                "price": 1,
                "cart_key": "another-cart",
            }
        )
        self.assertNotIn("total_centavos", values)
        self.assertNotIn("cart_key", values)
        self.assertEqual(errors, {})

    def test_cart_key_is_private_and_session_scoped(self):
        key = self.state._key()
        self.assertEqual(self.state._key(), key)
        self.assertNotEqual(CartState()._key(), key)
        self.assertGreaterEqual(len(key), 48)

    def test_existing_snapshot_schema(self):
        self.assertEqual(CartItem.__tablename__, "cart_items")
        self.assertIn("purchaser_sub", Order.__table__.columns)
        self.assertIn("unit_price_centavos", OrderItem.__table__.columns)


if __name__ == "__main__":
    unittest.main()
