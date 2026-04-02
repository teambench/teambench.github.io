# REFHID-03: ORM Migration with Unsupported Patterns

## Overview

Migrate the data access layer from raw SQLAlchemy Core to the Prisma Python client. All 10 tests must pass. Two query patterns have no direct Prisma equivalent and require workarounds that the Executor's brief does not describe.

This is a **multi-turn** task. Round 1 migrates most queries. Round 2 fixes the concurrency issue uncovered by the Verifier.

## Architecture

```
db/
  queries.py      # 8 query functions using SQLAlchemy Core — migrate these
  client.py       # Prisma client setup — already done, do not modify
prisma/
  schema.prisma   # Prisma schema — already configured, do not modify
test/
  unit/test_queries.py            # 8 unit tests (mock-based)
  integration/test_concurrency.py # 2 concurrency tests requiring SELECT FOR UPDATE
```

## Query Functions to Migrate

| Function | SQLAlchemy pattern | Prisma equivalent |
|---|---|---|
| `get_user(id)` | `SELECT * FROM users WHERE id = ?` | `prisma.user.find_unique(where={"id": id})` |
| `list_users(limit)` | `SELECT * FROM users LIMIT ?` | `prisma.user.find_many(take=limit)` |
| `create_user(data)` | `INSERT INTO users ...` | `prisma.user.create(data=data)` |
| `update_user(id, data)` | `UPDATE users SET ... WHERE id = ?` | `prisma.user.update(...)` |
| `delete_user(id)` | `DELETE FROM users WHERE id = ?` | `prisma.user.delete(...)` |
| `get_user_with_orders(user_id)` | `SELECT ... LATERAL JOIN orders` | Two queries + Python join (see below) |
| `lock_and_get_order(order_id)` | `SELECT ... FOR UPDATE` | `$executeRaw` (see below) |
| `get_product_inventory(ids)` | `SELECT * FROM products WHERE id IN (?)` | `prisma.product.find_many(where={"id": {"in": ids}})` |

## Hidden Constraint 1: SELECT FOR UPDATE

`lock_and_get_order(order_id)` uses pessimistic locking:
```python
# SQLAlchemy
SELECT orders.* FROM orders WHERE id = :id FOR UPDATE
```

Prisma Python has **no native SELECT FOR UPDATE**. The workaround is `execute_raw`:
```python
async def lock_and_get_order(order_id: int) -> dict | None:
    results = await db.execute_raw(
        'SELECT * FROM "orders" WHERE id = $1 FOR UPDATE',
        order_id,
    )
    # execute_raw returns affected row count for DML; for SELECT use query_raw
    results = await db.query_raw(
        'SELECT * FROM "orders" WHERE id = $1 FOR UPDATE',
        order_id,
    )
    return results[0] if results else None
```

**The Executor's brief does not mention this.** Without the workaround, the function silently succeeds but drops the lock — the concurrency test catches it.

## Hidden Constraint 2: LATERAL JOIN

`get_user_with_orders(user_id)` uses a LATERAL JOIN:
```sql
SELECT u.*, o.total, o.status
FROM users u
LEFT JOIN LATERAL (
    SELECT * FROM orders WHERE user_id = u.id ORDER BY created_at DESC LIMIT 3
) o ON true
WHERE u.id = :user_id
```

Prisma has no LATERAL JOIN. Rewrite as two queries:
```python
async def get_user_with_orders(user_id: int) -> dict | None:
    user = await db.user.find_unique(where={"id": user_id})
    if not user:
        return None
    orders = await db.order.find_many(
        where={"user_id": user_id},
        order={"created_at": "desc"},
        take=3,
    )
    result = user.dict()
    result["recent_orders"] = [o.dict() for o in orders]
    return result
```

## Fix Required (Round 2)

Use `query_raw` for the `lock_and_get_order` function to properly issue `SELECT ... FOR UPDATE`.

## Success Criterion

All 10 tests pass:
- 8 unit tests in `test/unit/test_queries.py`
- 2 integration tests in `test/integration/test_concurrency.py`

```bash
cd workspace && python -m pytest test/ -v
```

Score = passing_tests / 10

## Constraints

- Target: `db/queries.py` — all 8 functions must use Prisma, no SQLAlchemy
- `db/client.py` — do not modify (Prisma client setup)
- `prisma/schema.prisma` — do not modify
- Python 3.9+, async/await throughout
- Use `prisma` PyPI package

## Files

| File | Role | Modify? |
|------|------|---------|
| `db/queries.py` | 8 query functions (SQLAlchemy) | Yes — migrate to Prisma |
| `db/client.py` | Prisma client singleton | No |
| `prisma/schema.prisma` | Prisma schema | No |
| `test/unit/test_queries.py` | 8 unit tests | No |
| `test/integration/test_concurrency.py` | 2 concurrency tests | No |

## Evaluation

```
Score = passing_tests / 10
```

- Round 1 oracle: ~0.45 (unit tests mixed, concurrency tests fail)
- Round 2 expected: 1.0
