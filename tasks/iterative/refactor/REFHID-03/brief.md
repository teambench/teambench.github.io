# REFHID-03: Migrate ORM from SQLAlchemy Core to Prisma

## Your Task

Migrate `db/queries.py` from raw SQLAlchemy Core queries to the Prisma Python client. All 10 tests must pass.

## Files to Work With

```
workspace/
  db/queries.py                       # 8 query functions — migrate these
  db/client.py                        # Prisma client setup (already done, do not modify)
  prisma/schema.prisma                # Prisma schema (do not modify)
  test/unit/test_queries.py           # 8 unit tests
  test/integration/test_concurrency.py # 2 concurrency tests
  requirements.txt
```

## Quick Start

```bash
cd workspace
pip install -r requirements.txt
python -m pytest test/ -v
```

## What to Change

Replace all 8 functions in `db/queries.py` to use the Prisma client from `db/client.py`:
- `get_user(id)` → `prisma.user.find_unique(...)`
- `list_users(limit)` → `prisma.user.find_many(...)`
- `create_user(data)` → `prisma.user.create(...)`
- `update_user(id, data)` → `prisma.user.update(...)`
- `delete_user(id)` → `prisma.user.delete(...)`
- `get_user_with_orders(user_id)` → use Prisma relations
- `lock_and_get_order(order_id)` → use Prisma query API
- `get_product_inventory(ids)` → `prisma.product.find_many(...)`

## Note

All functions are async. The Prisma client must be connected before use — see `db/client.py` for the setup pattern.

## Target

```
python -m pytest test/ -v
# 10 passed
```

## Real-World Provenance

This task is based on two real Prisma GitHub issues documenting missing SQL primitives that affect ORM migration completeness:

- **prisma/prisma#7252** — `SELECT FOR UPDATE` (row-level locking) not supported in Prisma query API, requiring `$queryRaw` fallback:
  https://github.com/prisma/prisma/issues/7252
- **prisma/prisma#5068** — `LATERAL JOIN` unsupported in Prisma, requiring raw query fallback:
  https://github.com/prisma/prisma/issues/5068

The `lock_and_get_order(order_id)` function targets the `SELECT FOR UPDATE` gap from prisma/prisma#7252. The `get_product_inventory(ids)` function touches the lateral-join pattern from prisma/prisma#5068. These two functions are the hidden breaks in an otherwise straightforward migration — naively translating the other six functions to Prisma query API works, but these two require awareness of Prisma's documented limitations.

See [`../PROVENANCE.md`](../PROVENANCE.md) for full details.
