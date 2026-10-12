import reflex as rx
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from app.states.account_state import AccountState


class AccountHistoryTests(unittest.IsolatedAsyncioTestCase):
    async def load(self, state):
        async for _ in AccountState.load_orders.fn(state):
            pass

    async def test_missing_subject_does_not_query(self):
        state = AccountState()
        with (
            patch(
                "app.states.account_state.User.current",
                new=AsyncMock(return_value={"email": "customer@example.com"}),
            ),
            patch("app.states.account_state.rx.asession") as session,
        ):
            await self.load(state)
        session.assert_not_called()
        self.assertEqual(state.orders, [])
        self.assertFalse(state.loading)
        self.assertTrue(state.error)

    async def test_history_uses_subject_and_saved_snapshots(self):
        state = AccountState()
        row = {
            "id": 42,
            "created_at": datetime(2026, 1, 10, 15, tzinfo=timezone.utc),
            "status": "pending",
            "currency": "BRL",
            "subtotal": 12345,
            "shipping": 0,
            "discount": 0,
            "total": 12345,
            "shipping_recipient": "Cliente",
            "shipping_street": "Rua das Flores",
            "shipping_number": "10",
            "shipping_complement": "Apto 2",
            "shipping_neighborhood": "Centro",
            "shipping_city": "São Paulo",
            "shipping_state": "SP",
            "shipping_postal_code": "01310100",
            "shipping_country_code": "BR",
            "contact_phone": "11999999999",
            "contact_email": "delivery@example.com",
        }
        item = {
            "id": 7,
            "order_id": 42,
            "title": "Título histórico",
            "sku": "SNAPSHOT",
            "description": "Descrição histórica",
            "category": "Acessórios",
            "image_url": "",
            "quantity": 1,
            "unit_price": 12345,
            "discount": 0,
            "total": 12345,
        }
        order_result = MagicMock()
        order_result.mappings.return_value.all.return_value = [row]
        item_result = MagicMock()
        item_result.mappings.return_value.all.return_value = [item]
        session = AsyncMock()
        session.execute.side_effect = [order_result, item_result]
        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=session)
        context.__aexit__ = AsyncMock(return_value=False)
        with (
            patch(
                "app.states.account_state.User.current",
                new=AsyncMock(
                    return_value={
                        "sub": "authenticated-subject",
                        "email": "different@example.com",
                    }
                ),
            ),
            patch("app.states.account_state.rx.asession", return_value=context),
        ):
            await self.load(state)
        for call in session.execute.call_args_list:
            statement, parameters = call.args
            self.assertIn("purchaser_sub = :subject", str(statement))
            self.assertEqual(parameters["subject"], "authenticated-subject")
            self.assertNotIn("email", parameters)
        self.assertEqual(
            session.execute.call_args_list[1].args[1]["order_ids"], [42]
        )
        self.assertEqual(state.orders[0]["number"], "ML-000042")
        self.assertEqual(state.orders[0]["total"], "R$ 123,45")
        self.assertEqual(
            state.orders[0]["items"][0]["title"], "Título histórico"
        )
        self.assertEqual(
            state.orders[0]["items"][0]["image_url"], "/placeholder.svg"
        )
        self.assertFalse(state.loading)
        self.assertEqual(state.error, "")

    async def test_failure_clears_history_and_finishes_loading(self):
        state = AccountState()
        with (
            patch(
                "app.states.account_state.User.current",
                new=AsyncMock(side_effect=RuntimeError("Unavailable")),
            ),
            patch("app.states.account_state.logging.exception") as log,
        ):
            await self.load(state)
        log.assert_called_once()
        self.assertFalse(state.loading)
        self.assertEqual(state.orders, [])
        self.assertTrue(state.error)


if __name__ == "__main__":
    unittest.main()
