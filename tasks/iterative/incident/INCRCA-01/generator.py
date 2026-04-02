#!/usr/bin/env python3
"""
Generator for INCRCA-01: Cascading Timeout Misattribution.

Parameterizes surface details (service names, thresholds, connection counts)
from a seed value so each benchmark run has slightly different identifiers
while preserving the same logical structure and root cause.

Usage:
    python generator.py --seed 42 --output-dir ./workspace_generated
"""

import argparse
import os
import random
import shutil
import sys


# Parameterizable surface details
SERVICE_NAME_POOLS = {
    "checkout": ["CheckoutService", "OrderService", "PurchaseService", "CartService"],
    "user":     ["UserService", "AccountService", "ProfileService", "IdentityService"],
    "auth":     ["AuthService", "TokenService", "SessionService", "CredentialService"],
}

DB_NAME_POOL = ["users", "accounts", "members", "customers"]

SLO_THRESHOLD_POOL = [0.1, 0.05, 0.2]           # percent
BROKEN_POOL_SIZE_POOL = [3, 5, 8, 10]            # too-small pool sizes
CORRECT_POOL_SIZE_POOL = [50, 100, 75, 200]       # correct pool sizes
BASE_QUERY_LATENCY_POOL = [150, 180, 200, 220]    # ms without index


def generate(seed: int, output_dir: str):
    rng = random.Random(seed)

    def pick(pool):
        return rng.choice(pool)

    checkout_svc = pick(SERVICE_NAME_POOLS["checkout"])
    user_svc     = pick(SERVICE_NAME_POOLS["user"])
    auth_svc     = pick(SERVICE_NAME_POOLS["auth"])
    db_table     = pick(DB_NAME_POOL)
    slo_thresh   = pick(SLO_THRESHOLD_POOL)
    broken_pool  = pick(BROKEN_POOL_SIZE_POOL)
    correct_pool = pick(CORRECT_POOL_SIZE_POOL)
    base_latency = pick(BASE_QUERY_LATENCY_POOL)

    print(f"Seed: {seed}")
    print(f"  checkout_service  : {checkout_svc}")
    print(f"  user_service      : {user_svc}")
    print(f"  auth_service      : {auth_svc}")
    print(f"  db_table          : {db_table}")
    print(f"  slo_threshold     : {slo_thresh}%")
    print(f"  broken_pool_size  : {broken_pool}")
    print(f"  correct_pool_size : {correct_pool}")
    print(f"  base_query_latency: {base_latency}ms")

    # Copy workspace template
    src_dir = os.path.join(os.path.dirname(__file__), "workspace")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    shutil.copytree(src_dir, output_dir)

    # Patch auth_service.py
    auth_path = os.path.join(output_dir, "services", "auth_service.py")
    with open(auth_path) as f:
        content = f.read()
    content = content.replace("max_connections = 5", f"max_connections = {broken_pool}")
    content = content.replace(
        "_BASE_QUERY_LATENCY_MS = 180",
        f"_BASE_QUERY_LATENCY_MS = {base_latency}"
    )
    with open(auth_path, "w") as f:
        f.write(content)

    # Patch schema.sql — update table name
    schema_path = os.path.join(output_dir, "db", "schema.sql")
    with open(schema_path) as f:
        content = f.read()
    # Replace table name and index references
    content = content.replace(
        "CREATE TABLE IF NOT EXISTS users (",
        f"CREATE TABLE IF NOT EXISTS {db_table} ("
    )
    content = content.replace(
        "idx_users_email ON users(email)",
        f"idx_{db_table}_email ON {db_table}(email)"
    )
    content = content.replace(
        "REFERENCES users(id)",
        f"REFERENCES {db_table}(id)"
    )
    with open(schema_path, "w") as f:
        f.write(content)

    # Patch slo_test.py — update SLO threshold
    slo_path = os.path.join(output_dir, "test", "integration", "slo_test.py")
    with open(slo_path) as f:
        content = f.read()
    content = content.replace(
        "SLO_THRESHOLD = 0.1",
        f"SLO_THRESHOLD = {slo_thresh}"
    )
    with open(slo_path, "w") as f:
        f.write(content)

    # Write a params.json for downstream tooling
    import json
    params = {
        "seed": seed,
        "checkout_service": checkout_svc,
        "user_service": user_svc,
        "auth_service": auth_svc,
        "db_table": db_table,
        "slo_threshold_pct": slo_thresh,
        "broken_pool_size": broken_pool,
        "correct_pool_size": correct_pool,
        "base_query_latency_ms": base_latency,
    }
    with open(os.path.join(output_dir, "params.json"), "w") as f:
        json.dump(params, f, indent=2)

    print(f"\nGenerated workspace at: {output_dir}")
    print(f"params.json written.")


def main():
    parser = argparse.ArgumentParser(description="INCRCA-01 workspace generator")
    parser.add_argument("--seed", type=int, default=0, help="Random seed")
    parser.add_argument("--output-dir", default="./workspace_generated",
                        help="Output directory for generated workspace")
    args = parser.parse_args()
    generate(args.seed, args.output_dir)


if __name__ == "__main__":
    main()
