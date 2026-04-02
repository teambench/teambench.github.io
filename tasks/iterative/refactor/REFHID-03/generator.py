"""
Generator for REFHID-03: ORM Migration with Unsupported Patterns.
Parameterizes table names, field names, and query patterns from a seed.

Usage:
    python generator.py --seed 42 --output-dir ./generated/
"""
import argparse
import json
import os
import random
import textwrap

TABLE_NAME_SETS = [
    {"users": "users", "orders": "orders", "products": "products"},
    {"users": "accounts", "orders": "purchases", "products": "items"},
    {"users": "members", "orders": "transactions", "products": "catalog"},
]

USER_ID_FIELD_VARIANTS = ["id", "user_id", "account_id"]
ORDER_TOTAL_FIELD_VARIANTS = ["total", "amount", "price_total"]
PRODUCT_STOCK_FIELD_VARIANTS = ["stock", "inventory", "quantity"]

LOCK_TIMEOUT_VARIANTS = [None, 5000, 10000]


def seed_random(seed: int) -> random.Random:
    rng = random.Random()
    rng.seed(seed)
    return rng


def pick(rng, lst):
    return lst[rng.randint(0, len(lst) - 1)]


def generate_params(seed: int) -> dict:
    rng = seed_random(seed)
    tables = pick(rng, TABLE_NAME_SETS)
    return {
        "seed": seed,
        "tables": tables,
        "order_total_field": pick(rng, ORDER_TOTAL_FIELD_VARIANTS),
        "product_stock_field": pick(rng, PRODUCT_STOCK_FIELD_VARIANTS),
        "lock_timeout_ms": pick(rng, LOCK_TIMEOUT_VARIANTS),
        "lateral_limit": rng.randint(2, 5),
    }


def render_queries_py(p: dict) -> str:
    t = p["tables"]
    total_f = p["order_total_field"]
    stock_f = p["product_stock_field"]
    limit = p["lateral_limit"]
    return textwrap.dedent(f"""\
        \"\"\"
        Data access layer — SQLAlchemy Core.
        Migrate to Prisma Python client.
        Table names: users={t['users']}, orders={t['orders']}, products={t['products']}
        \"\"\"
        from __future__ import annotations
        from typing import Any, Dict, List, Optional
        from db.client import get_client


        async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
            db = get_client()
            user = await db.{t['users'][:-1] if t['users'].endswith('s') else t['users']}.find_unique(where={{"id": user_id}})
            return user.dict() if user else None


        async def lock_and_get_order(order_id: int) -> Optional[Dict[str, Any]]:
            db = get_client()
            # Must use query_raw for SELECT FOR UPDATE
            results = await db.query_raw(
                'SELECT * FROM "{t['orders']}" WHERE id = $1 FOR UPDATE',
                order_id,
            )
            return results[0] if results else None
        """)


def generate(seed: int, output_dir: str) -> None:
    p = generate_params(seed)
    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "params.json"), "w") as f:
        json.dump(p, f, indent=2)

    with open(os.path.join(output_dir, "queries_snippet.py"), "w") as f:
        f.write(render_queries_py(p))

    print(f"Generated REFHID-03 variant for seed={seed}")
    print(f"  tables:       {p['tables']}")
    print(f"  total field:  {p['order_total_field']}")
    print(f"  stock field:  {p['product_stock_field']}")
    print(f"  lateral limit: {p['lateral_limit']}")
    print(f"Output: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Generate REFHID-03 task variants")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="./generated")
    args = parser.parse_args()
    generate(args.seed, args.output_dir)


if __name__ == "__main__":
    main()
