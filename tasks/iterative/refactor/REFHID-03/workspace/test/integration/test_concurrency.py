"""
2 integration tests that verify lock_and_get_order uses SELECT FOR UPDATE.

These tests will FAIL in round 1 if lock_and_get_order does NOT use
Prisma's query_raw with 'FOR UPDATE' in the SQL string.

The tests:
1. Verify that query_raw is called (not just find_unique)
2. Verify that the SQL contains 'FOR UPDATE'

Without the workaround, the function might silently succeed using
prisma.order.find_unique() which drops the lock — detected here.
"""
import asyncio
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, call, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def make_prisma_mock():
    client = MagicMock()
    client.user = MagicMock()
    client.order = MagicMock()
    client.order.find_unique = AsyncMock()
    client.order.find_many = AsyncMock()
    client.product = MagicMock()
    client.query_raw = AsyncMock(return_value=[{
        "id": 42, "user_id": 1, "total": 150.0, "status": "pending"
    }])
    client.execute_raw = AsyncMock(return_value=1)
    return client


@pytest.fixture
def mock_client():
    return make_prisma_mock()


@pytest.fixture(autouse=True)
def inject_client(mock_client):
    import db.client as client_module
    client_module.set_client(mock_client)
    yield
    client_module.reset_client()


class TestLockAndGetOrder:
    def test_lock_and_get_order_uses_query_raw(self, mock_client):
        """
        lock_and_get_order MUST call query_raw (not find_unique).
        Using find_unique silently drops the pessimistic lock.
        The Verifier detects this omission; the Executor's brief does not warn about it.
        """
        from db.queries import lock_and_get_order

        result = asyncio.run(lock_and_get_order(42))

        assert mock_client.query_raw.called, (
            "lock_and_get_order must use prisma.query_raw() to issue SELECT FOR UPDATE. "
            "Using prisma.order.find_unique() drops the pessimistic lock silently. "
            "Fix: await db.query_raw('SELECT * FROM \"orders\" WHERE id = $1 FOR UPDATE', order_id)"
        )
        # find_unique should NOT have been called (it doesn't support FOR UPDATE)
        assert not mock_client.order.find_unique.called, (
            "lock_and_get_order must not use find_unique — it cannot issue FOR UPDATE."
        )

    def test_lock_and_get_order_sql_contains_for_update(self, mock_client):
        """
        The SQL passed to query_raw must contain 'FOR UPDATE'.
        Prisma has no native pessimistic locking — it must be expressed in raw SQL.
        """
        from db.queries import lock_and_get_order

        asyncio.run(lock_and_get_order(42))

        assert mock_client.query_raw.called, (
            "query_raw was not called — cannot verify FOR UPDATE clause."
        )

        # Get the SQL string from the call
        call_args = mock_client.query_raw.call_args
        sql_arg = None
        if call_args.args:
            sql_arg = call_args.args[0]
        elif call_args.kwargs:
            sql_arg = next(iter(call_args.kwargs.values()), None)

        assert sql_arg is not None, "query_raw must be called with a SQL string as first argument"
        assert "FOR UPDATE" in str(sql_arg).upper(), (
            f"SQL passed to query_raw must contain 'FOR UPDATE'. Got: {sql_arg!r}\n"
            "Prisma has no native SELECT FOR UPDATE. "
            "Use: await db.query_raw('SELECT * FROM \"orders\" WHERE id = $1 FOR UPDATE', order_id)"
        )
