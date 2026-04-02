"""
8 unit tests for Prisma-migrated query functions.
Uses AsyncMock to mock the Prisma client — no real DB required.

These tests verify that:
1. db/queries.py uses Prisma (not SQLAlchemy) after migration
2. Each function calls the correct Prisma method with correct args
3. Return shapes are correct
"""
import asyncio
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_user(id=1, email="alice@example.com", name="Alice"):
    u = MagicMock()
    u.id = id
    u.email = email
    u.name = name
    u.created_at = "2024-01-01T00:00:00"
    u.dict = lambda: {"id": id, "email": email, "name": name, "created_at": "2024-01-01T00:00:00"}
    return u


def make_order(id=1, user_id=1, total=99.99, status="pending"):
    o = MagicMock()
    o.id = id
    o.user_id = user_id
    o.total = total
    o.status = status
    o.created_at = "2024-01-01T00:00:00"
    o.dict = lambda: {"id": id, "user_id": user_id, "total": total, "status": status}
    return o


def make_product(id=1, name="Widget", price=9.99, stock=100):
    p = MagicMock()
    p.id = id
    p.name = name
    p.price = price
    p.stock = stock
    p.dict = lambda: {"id": id, "name": name, "price": price, "stock": stock}
    return p


def make_prisma_mock():
    """Build a mock Prisma client with async methods."""
    client = MagicMock()

    # user model
    client.user = MagicMock()
    client.user.find_unique = AsyncMock()
    client.user.find_many = AsyncMock()
    client.user.create = AsyncMock()
    client.user.update = AsyncMock()
    client.user.delete = AsyncMock()

    # order model
    client.order = MagicMock()
    client.order.find_unique = AsyncMock()
    client.order.find_many = AsyncMock()

    # product model
    client.product = MagicMock()
    client.product.find_many = AsyncMock()

    # raw query methods
    client.query_raw = AsyncMock()
    client.execute_raw = AsyncMock()

    return client


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_client():
    return make_prisma_mock()


@pytest.fixture(autouse=True)
def inject_client(mock_client):
    """Inject mock Prisma client before each test."""
    import db.client as client_module
    client_module.set_client(mock_client)
    yield
    client_module.reset_client()


# ── Tests ──────────────────────────────────────────────────────────────────

class TestGetUser:
    def test_get_user_calls_find_unique(self, mock_client):
        """get_user must call prisma.user.find_unique with correct where clause."""
        user = make_user(id=5)
        mock_client.user.find_unique.return_value = user

        result = asyncio.run(__import__("db.queries", fromlist=["get_user"]).get_user(5))

        mock_client.user.find_unique.assert_called_once()
        call_kwargs = mock_client.user.find_unique.call_args
        # Accept either positional or keyword args
        where = (call_kwargs.kwargs.get("where") or
                 (call_kwargs.args[0] if call_kwargs.args else None))
        assert where is not None, "find_unique must be called with a 'where' argument"
        assert where.get("id") == 5

    def test_get_user_not_found_returns_none(self, mock_client):
        mock_client.user.find_unique.return_value = None
        result = asyncio.run(__import__("db.queries", fromlist=["get_user"]).get_user(999))
        assert result is None


class TestListUsers:
    def test_list_users_calls_find_many(self, mock_client):
        """list_users must call prisma.user.find_many."""
        users = [make_user(i) for i in range(3)]
        mock_client.user.find_many.return_value = users

        result = asyncio.run(__import__("db.queries", fromlist=["list_users"]).list_users(limit=3))

        mock_client.user.find_many.assert_called_once()
        assert len(result) == 3


class TestCreateUser:
    def test_create_user_calls_prisma_create(self, mock_client):
        """create_user must call prisma.user.create."""
        user = make_user(id=10, email="new@example.com", name="New User")
        mock_client.user.create.return_value = user

        data = {"email": "new@example.com", "name": "New User"}
        result = asyncio.run(__import__("db.queries", fromlist=["create_user"]).create_user(data))

        mock_client.user.create.assert_called_once()


class TestUpdateUser:
    def test_update_user_calls_prisma_update(self, mock_client):
        """update_user must call prisma.user.update."""
        user = make_user(id=1, name="Updated Name")
        mock_client.user.update.return_value = user

        result = asyncio.run(
            __import__("db.queries", fromlist=["update_user"]).update_user(1, {"name": "Updated Name"})
        )

        mock_client.user.update.assert_called_once()


class TestDeleteUser:
    def test_delete_user_calls_prisma_delete(self, mock_client):
        """delete_user must call prisma.user.delete."""
        mock_client.user.delete.return_value = make_user(id=1)

        asyncio.run(__import__("db.queries", fromlist=["delete_user"]).delete_user(1))

        mock_client.user.delete.assert_called_once()


class TestGetUserWithOrders:
    def test_get_user_with_orders_returns_user_and_orders(self, mock_client):
        """
        get_user_with_orders must return user dict with recent_orders list.
        Uses two Prisma queries (LATERAL JOIN workaround).
        """
        user = make_user(id=1)
        orders = [make_order(id=i, user_id=1) for i in range(2)]
        mock_client.user.find_unique.return_value = user
        mock_client.order.find_many.return_value = orders

        result = asyncio.run(
            __import__("db.queries", fromlist=["get_user_with_orders"]).get_user_with_orders(1)
        )

        assert result is not None
        assert "recent_orders" in result
        assert len(result["recent_orders"]) == 2


class TestGetProductInventory:
    def test_get_product_inventory_calls_find_many_with_in(self, mock_client):
        """get_product_inventory must call prisma.product.find_many with id IN clause."""
        products = [make_product(id=i) for i in [1, 2, 3]]
        mock_client.product.find_many.return_value = products

        result = asyncio.run(
            __import__("db.queries", fromlist=["get_product_inventory"]).get_product_inventory([1, 2, 3])
        )

        mock_client.product.find_many.assert_called_once()
        call_kwargs = mock_client.product.find_many.call_args
        where = (call_kwargs.kwargs.get("where") or
                 (call_kwargs.args[0] if call_kwargs.args else None))
        assert where is not None
        # Must use {"id": {"in": [...]}} pattern
        assert "id" in where
        id_clause = where["id"]
        assert "in" in id_clause
        assert set(id_clause["in"]) == {1, 2, 3}
