import reflex as rx
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from app.states.admin_order_state import (
    AdminOrderState,
    EDITABLE_STATUSES,
    STATUS_LABELS,
    order_money,
    order_date,
)


class OrderPresentationTests(unittest.TestCase):
    def test_brl_and_local_date(self):
        self.assertEqual(order_money(129990), "R$ 1.299,90")
        self.assertEqual(order_money(0), "R$ 0,00")
        self.assertEqual(order_money(1), "R$ 0,01")
        self.assertEqual(
            order_date(datetime(2026, 1, 2, 1, 30, tzinfo=timezone.utc)),
            "01/01/2026 · 22:30",
        )

    def test_status_options_and_history(self):
        self.assertEqual(
            EDITABLE_STATUSES, {"pending", "processing", "shipped", "cancelled"}
        )
        self.assertEqual(STATUS_LABELS["paid"], "Pago")
        self.assertEqual(STATUS_LABELS["delivered"], "Entregue")
        self.assertEqual(STATUS_LABELS["refunded"], "Reembolsado")


class OrderWriteTests(unittest.IsolatedAsyncioTestCase):
    async def _write(self, row, status, expected="pending"):
        session = MagicMock()
        session.scalar = AsyncMock(return_value=row)
        transaction = AsyncMock()
        session.begin.return_value = transaction
        manager = AsyncMock()
        manager.__aenter__.return_value = session
        with patch.object(rx, "asession", return_value=manager):
            changed = await AdminOrderState._persist_status(
                SimpleNamespace(), 1, status, expected
            )
        self.assertIn("FOR UPDATE", str(session.scalar.call_args.args[0]))
        transaction.__aexit__.assert_awaited_once()
        return changed

    async def test_shipping_and_cancellation_timestamps(self):
        row = SimpleNamespace(
            status="pending", shipped_at=None, cancelled_at=None
        )
        self.assertTrue(await self._write(row, "shipped"))
        self.assertIsNotNone(row.shipped_at)
        self.assertIsNone(row.cancelled_at)
        self.assertTrue(await self._write(row, "cancelled", "shipped"))
        self.assertIsNone(row.shipped_at)
        self.assertIsNotNone(row.cancelled_at)
        self.assertTrue(await self._write(row, "processing", "cancelled"))
        self.assertIsNone(row.shipped_at)
        self.assertIsNone(row.cancelled_at)

    async def test_no_duplicate_write(self):
        stamp = datetime.now(timezone.utc)
        row = SimpleNamespace(
            status="shipped", shipped_at=stamp, cancelled_at=None
        )
        self.assertFalse(await self._write(row, "shipped"))
        self.assertEqual(row.shipped_at, stamp)

    async def test_allowlist_before_database(self):
        with patch.object(rx, "asession") as factory:
            for status in ("paid", "delivered", "refunded", "unknown", ""):
                with self.assertRaises(ValueError):
                    await AdminOrderState._persist_status(
                        SimpleNamespace(), 1, status, "pending"
                    )
            factory.assert_not_called()

    async def test_missing_and_concurrent_orders(self):
        with self.assertRaises(ValueError):
            await self._write(None, "processing")
        row = SimpleNamespace(
            status="cancelled", shipped_at=None, cancelled_at=None
        )
        with self.assertRaises(ValueError):
            await self._write(row, "processing")
        self.assertEqual(row.status, "cancelled")

    async def test_transaction_failure_propagates(self):
        session = MagicMock()
        session.scalar = AsyncMock(
            return_value=SimpleNamespace(
                status="pending", shipped_at=None, cancelled_at=None
            )
        )
        transaction = AsyncMock()
        transaction.__aexit__.side_effect = RuntimeError("commit failed")
        session.begin.return_value = transaction
        manager = AsyncMock()
        manager.__aenter__.return_value = session
        with patch.object(rx, "asession", return_value=manager):
            with self.assertRaises(RuntimeError):
                await AdminOrderState._persist_status(
                    SimpleNamespace(), 1, "shipped", "pending"
                )


if __name__ == "__main__":
    unittest.main()
