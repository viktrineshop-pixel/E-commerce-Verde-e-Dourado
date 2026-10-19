import reflex as rx
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from app.models import CustomerFavorite
from app.states.favorite_state import FavoriteState


class FavoriteHarness:
    _current_subject = FavoriteState._current_subject
    _clear = FavoriteState._clear
    _money = FavoriteState._money

    def __init__(self):
        self._generation = 0
        self._clear()
        self.get_state = AsyncMock(
            return_value=SimpleNamespace(products=[{"id": 7}])
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class FavoritesTests(unittest.IsolatedAsyncioTestCase):
    async def run_handler(self, handler, state, *args):
        updates = []
        async for update in handler.fn(state, *args):
            updates.append(update)
        return updates

    def session(self, rows=()):
        session = AsyncMock()
        session.scalar.return_value = 7
        result = MagicMock()
        result.mappings.return_value.all.return_value = list(rows)
        session.execute.return_value = result
        scalar_result = MagicMock()
        scalar_result.all.return_value = [7]
        session.scalars.return_value = scalar_result
        context = AsyncMock()
        context.__aenter__.return_value = session
        return session, context

    async def test_invalid_identity_never_queries_and_clears_stale_data(self):
        for user in (
            {},
            {"email": "same@example.com"},
            {"sub": " "},
            {"sub": 7},
        ):
            state = FavoriteHarness()
            state.saved_ids = [7]
            state.signed_in = True
            with (
                patch(
                    "app.states.favorite_state.User.current",
                    AsyncMock(return_value=user),
                ),
                patch("app.states.favorite_state.rx.asession") as db,
            ):
                await self.run_handler(FavoriteState.load_favorites, state)
            db.assert_not_called()
            self.assertFalse(state.signed_in)
            self.assertFalse(state.ready)
            self.assertEqual(state.saved_ids, [])

    async def test_load_filters_verified_identity_and_formats_products(self):
        state = FavoriteHarness()
        session, context = self.session(
            [
                {
                    "id": 7,
                    "title": "Peça",
                    "image_url": "",
                    "price_centavos": 12345,
                    "partner_name": "Amazon",
                }
            ]
        )
        with (
            patch(
                "app.states.favorite_state.User.current",
                AsyncMock(
                    return_value={
                        "sub": "verified-A",
                        "email": "ignored@example.com",
                    }
                ),
            ),
            patch(
                "app.states.favorite_state.rx.asession", return_value=context
            ),
        ):
            await self.run_handler(FavoriteState.load_favorites, state)
        for call in (
            session.execute.call_args_list + session.scalars.call_args_list
        ):
            self.assertEqual(call.args[1]["subject"], "verified-A")
            self.assertIn("f.subject = :subject", str(call.args[0]))
        self.assertEqual(state.saved_ids, [7])
        self.assertEqual(state.favorites[0]["price"], "R$ 123,45")
        self.assertEqual(state.favorites[0]["image_url"], "/placeholder.svg")
        self.assertTrue(state.ready)
        self.assertFalse(state.loading)

    async def test_save_is_idempotent_and_remove_is_owner_scoped(self):
        for saved in (True, False):
            state = FavoriteHarness()
            session, context = self.session()
            with (
                patch(
                    "app.states.favorite_state.User.current",
                    AsyncMock(return_value={"sub": "verified-B"}),
                ),
                patch(
                    "app.states.favorite_state.rx.asession",
                    return_value=context,
                ),
            ):
                await self.run_handler(FavoriteState.set_saved, state, 7, saved)
            statement, parameters = session.execute.call_args.args
            self.assertEqual(parameters, {"subject": "verified-B", "id": 7})
            if saved:
                self.assertIn(
                    "ON CONFLICT (subject, product_id) DO NOTHING",
                    str(statement),
                )
            else:
                self.assertIn(
                    "subject = :subject AND product_id = :id", str(statement)
                )
            session.commit.assert_awaited_once()
            self.assertEqual(state.pending_id, 0)
            self.assertFalse(state.error)

    async def test_missing_product_cannot_be_saved_but_can_be_removed(self):
        for saved in (True, False):
            state = FavoriteHarness()
            session, context = self.session()
            session.scalar.return_value = None
            with (
                patch(
                    "app.states.favorite_state.User.current",
                    AsyncMock(return_value={"sub": "verified"}),
                ),
                patch(
                    "app.states.favorite_state.rx.asession",
                    return_value=context,
                ),
                patch("app.states.favorite_state.logging.exception"),
            ):
                await self.run_handler(FavoriteState.set_saved, state, 7, saved)
            if saved:
                session.commit.assert_not_awaited()
                self.assertIn("não está mais", state.error)
            else:
                session.commit.assert_awaited_once()
            self.assertEqual(state.pending_id, 0)

    async def test_identity_switch_during_load_does_not_deliver_old_list(self):
        state = FavoriteHarness()
        session, context = self.session()
        with (
            patch(
                "app.states.favorite_state.User.current",
                AsyncMock(side_effect=[{"sub": "A"}, {"sub": "B"}]),
            ),
            patch(
                "app.states.favorite_state.rx.asession", return_value=context
            ),
        ):
            await self.run_handler(FavoriteState.load_favorites, state)
        self.assertEqual(state.saved_ids, [])
        self.assertEqual(state.favorites, [])
        self.assertFalse(state.signed_in)

    async def test_failure_has_error_and_loading_finishes(self):
        state = FavoriteHarness()
        session, context = self.session()
        session.scalars.side_effect = RuntimeError("Database unavailable")
        with (
            patch(
                "app.states.favorite_state.User.current",
                AsyncMock(return_value={"sub": "verified"}),
            ),
            patch(
                "app.states.favorite_state.rx.asession", return_value=context
            ),
            patch("app.states.favorite_state.logging.exception") as log,
        ):
            await self.run_handler(FavoriteState.load_favorites, state)
        log.assert_called_once()
        self.assertTrue(state.error)
        self.assertFalse(state.loading)
        self.assertFalse(state.ready)

    def test_existing_schema_has_unique_owner_product_and_delete_cascade(self):
        table = CustomerFavorite.__table__
        unique = next(
            c
            for c in table.constraints
            if c.name == "uq_customer_favorites_subject_product"
        )
        self.assertEqual(
            [c.name for c in unique.columns], ["subject", "product_id"]
        )
        self.assertEqual(
            next(iter(table.c.product_id.foreign_keys)).ondelete, "CASCADE"
        )


if __name__ == "__main__":
    unittest.main()
