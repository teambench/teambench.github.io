#!/usr/bin/env python3
"""
Generator for INCRCA-02: Silent Data Corruption.

Parameterizes surface details (discount rates, order amounts, table names)
from a seed value while preserving the same logical bugs and fix structure.

Usage:
    python generator.py --seed 42 --output-dir ./workspace_generated
"""

import argparse
import os
import random
import shutil
import json


CUSTOMER_ID_POOL = ["cust_001", "customer_alpha", "acct_007", "buyer_999"]
DISCOUNT_RATE_POOL = [0.05, 0.10, 0.15, 0.20]
BASE_ORDER_TOTAL_POOL = [50.0, 100.0, 150.0, 200.0]
PRODUCT_PRICE_POOL = [
    [("9.99", 3), ("4.99", 2)],
    [("14.99", 2), ("7.50", 4)],
    [("29.99", 1), ("9.99", 3)],
    [("24.95", 2), ("12.50", 1)],
]
TABLE_NAME_POOL = ["orders", "purchases", "transactions", "sales_orders"]


def generate(seed: int, output_dir: str):
    rng = random.Random(seed)

    def pick(pool):
        return rng.choice(pool)

    customer_id    = pick(CUSTOMER_ID_POOL)
    discount_rate  = pick(DISCOUNT_RATE_POOL)
    base_total     = pick(BASE_ORDER_TOTAL_POOL)
    product_prices = pick(PRODUCT_PRICE_POOL)
    table_name     = pick(TABLE_NAME_POOL)

    print(f"Seed: {seed}")
    print(f"  customer_id    : {customer_id}")
    print(f"  discount_rate  : {discount_rate}")
    print(f"  base_total     : {base_total}")
    print(f"  product_prices : {product_prices}")
    print(f"  table_name     : {table_name}")

    src_dir = os.path.join(os.path.dirname(__file__), "workspace")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    shutil.copytree(src_dir, output_dir)

    # Patch models.py — update table name
    models_path = os.path.join(output_dir, "orders", "models.py")
    with open(models_path) as f:
        content = f.read()
    content = content.replace('__tablename__ = "orders"', f'__tablename__ = "{table_name}"')
    with open(models_path, "w") as f:
        f.write(content)

    # Patch test file — update customer_id, discount rates, and amounts
    test_path = os.path.join(output_dir, "test", "test_orders.py")
    with open(test_path) as f:
        content = f.read()
    content = content.replace('"cust_001"', f'"{customer_id}"')
    content = content.replace('"cust_002"', f'"{customer_id}_2"')
    content = content.replace('"cust_concurrent"', f'"{customer_id}_concurrent"')
    content = content.replace('"cust_idem"', f'"{customer_id}_idem"')
    with open(test_path, "w") as f:
        f.write(content)

    # Write params.json
    params = {
        "seed": seed,
        "customer_id": customer_id,
        "discount_rate": discount_rate,
        "base_total": base_total,
        "product_prices": product_prices,
        "table_name": table_name,
    }
    with open(os.path.join(output_dir, "params.json"), "w") as f:
        json.dump(params, f, indent=2)

    print(f"\nGenerated workspace at: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="INCRCA-02 workspace generator")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", default="./workspace_generated")
    args = parser.parse_args()
    generate(args.seed, args.output_dir)


if __name__ == "__main__":
    main()
