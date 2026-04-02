"""
Data access layer — currently uses SQLAlchemy Core.
Migrate all 8 functions to use the Prisma Python client from db.client.

NOTE: All functions are async. Use `await` with every Prisma call.
"""
from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Optional

# SQLAlchemy imports — to be removed after migration
from sqlalchemy import create_engine, text, MetaData, Table, Column
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.pool import StaticPool

# In-memory SQLite engine for the pre-migration implementation
_engine = None
_metadata = MetaData()

users_table = Table(
    "users", _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("email", String, unique=True, nullable=False),
    Column("name", String, nullable=False),
    Column("created_at", String),
)

orders_table = Table(
    "orders", _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("total", Float, nullable=False),
    Column("status", String, nullable=False, default="pending"),
    Column("created_at", String),
)

products_table = Table(
    "products", _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String, nullable=False),
    Column("price", Float, nullable=False),
    Column("stock", Integer, nullable=False, default=0),
)


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        _metadata.create_all(_engine)
    return _engine


def _row_to_dict(row) -> dict:
    return dict(row._mapping) if row else None


# ─── Query functions (SQLAlchemy Core — to be migrated to Prisma) ────────────

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single user by ID."""
    engine = _get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": user_id},
        )
        row = result.fetchone()
        return _row_to_dict(row)


async def list_users(limit: int = 10) -> List[Dict[str, Any]]:
    """List users with a limit."""
    engine = _get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM users LIMIT :limit"),
            {"limit": limit},
        )
        return [_row_to_dict(r) for r in result.fetchall()]


async def create_user(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new user."""
    engine = _get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "INSERT INTO users (email, name, created_at) "
                "VALUES (:email, :name, datetime('now')) RETURNING *"
            ),
            data,
        )
        conn.commit()
        row = result.fetchone()
        return _row_to_dict(row)


async def update_user(user_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update user fields by ID."""
    engine = _get_engine()
    set_clauses = ", ".join(f"{k} = :{k}" for k in data)
    params = {**data, "id": user_id}
    with engine.connect() as conn:
        conn.execute(
            text(f"UPDATE users SET {set_clauses} WHERE id = :id"),
            params,
        )
        conn.commit()
        result = conn.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": user_id},
        )
        row = result.fetchone()
        return _row_to_dict(row)


async def delete_user(user_id: int) -> bool:
    """Delete a user by ID. Returns True if deleted."""
    engine = _get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM users WHERE id = :id"),
            {"id": user_id},
        )
        conn.commit()
        return result.rowcount > 0


async def get_user_with_orders(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a user with their 3 most recent orders.
    SQLAlchemy uses a LATERAL JOIN — no direct Prisma equivalent.
    Migration requires two separate queries + Python-level join.
    """
    engine = _get_engine()
    with engine.connect() as conn:
        # SQLite doesn't support LATERAL JOIN, simulate with subquery
        user_result = conn.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": user_id},
        )
        user_row = user_result.fetchone()
        if not user_row:
            return None
        user = _row_to_dict(user_row)

        orders_result = conn.execute(
            text(
                "SELECT * FROM orders WHERE user_id = :uid "
                "ORDER BY created_at DESC LIMIT 3"
            ),
            {"uid": user_id},
        )
        user["recent_orders"] = [_row_to_dict(r) for r in orders_result.fetchall()]
        return user


async def lock_and_get_order(order_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch an order with a pessimistic lock (SELECT FOR UPDATE).
    SQLAlchemy: SELECT * FROM orders WHERE id = :id FOR UPDATE
    Prisma migration requires query_raw — no native FOR UPDATE support.
    """
    engine = _get_engine()
    with engine.connect() as conn:
        # SQLite doesn't support FOR UPDATE; this simulates the pattern
        result = conn.execute(
            text("SELECT * FROM orders WHERE id = :id"),
            {"id": order_id},
        )
        row = result.fetchone()
        return _row_to_dict(row)


async def get_product_inventory(product_ids: List[int]) -> List[Dict[str, Any]]:
    """Fetch products by a list of IDs."""
    if not product_ids:
        return []
    engine = _get_engine()
    placeholders = ", ".join(f":id{i}" for i in range(len(product_ids)))
    params = {f"id{i}": pid for i, pid in enumerate(product_ids)}
    with engine.connect() as conn:
        result = conn.execute(
            text(f"SELECT * FROM products WHERE id IN ({placeholders})"),
            params,
        )
        return [_row_to_dict(r) for r in result.fetchall()]
