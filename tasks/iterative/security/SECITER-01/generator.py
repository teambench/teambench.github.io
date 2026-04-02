#!/usr/bin/env python3
"""
SECITER-01 Generator
Parameterizes surface details (route paths, variable names, numeric values)
from a seed so different seeds produce different surface instances of the same task.

Usage:
  python generator.py <seed> [output_dir]

Example:
  python generator.py 42 ./workspace_42
  python generator.py 99 ./workspace_99
"""

import random
import os
import sys
import shutil
import re


def make_rng(seed: int) -> random.Random:
    return random.Random(seed)


def generate(seed: int, output_dir: str):
    rng = make_rng(seed)

    # ── Parameterized values ──────────────────────────────────────────────────

    # Route prefix variant (always /api/vN/auth)
    api_version = rng.choice(["v1", "v2"])

    # Rate limit window (minutes) and max attempts
    rate_window_minutes = rng.choice([10, 15, 20])
    rate_max_attempts = rng.choice([3, 5, 10])

    # JWT expiry
    jwt_expiry = rng.choice(["1h", "2h", "30m"])

    # bcrypt salt rounds
    bcrypt_rounds = rng.choice([10, 12, 14])

    # Table name variant
    table_name = rng.choice(["users", "accounts", "members"])

    # Username field name
    username_field = rng.choice(["username", "login", "handle"])

    # Cookie name for JWT
    cookie_name = rng.choice(["token", "auth_token", "jwt"])

    # Session cookie name
    session_cookie = rng.choice(["sessionId", "sid", "connect.sid"])

    params = {
        "api_version": api_version,
        "rate_window_ms": rate_window_minutes * 60 * 1000,
        "rate_window_minutes": rate_window_minutes,
        "rate_max_attempts": rate_max_attempts,
        "jwt_expiry": jwt_expiry,
        "bcrypt_rounds": bcrypt_rounds,
        "table_name": table_name,
        "username_field": username_field,
        "cookie_name": cookie_name,
        "session_cookie": session_cookie,
        "route_prefix": f"/api/{api_version}/auth",
    }

    print(f"[generator] seed={seed}")
    print(f"[generator] parameters:")
    for k, v in params.items():
        print(f"  {k} = {v!r}")

    # ── Output directory ──────────────────────────────────────────────────────
    src_dir = os.path.join(os.path.dirname(__file__), "workspace")
    if os.path.abspath(output_dir) != os.path.abspath(src_dir):
        shutil.copytree(src_dir, output_dir, dirs_exist_ok=True)

    # ── Apply substitutions ───────────────────────────────────────────────────

    substitutions = {
        # Route prefix
        "/api/v1/auth": params["route_prefix"],
        # Rate limit window
        "15 * 60 * 1000": f"{rate_window_minutes} * 60 * 1000",
        "5 requests per 15 minutes": f"{rate_max_attempts} requests per {rate_window_minutes} minutes",
        "max: 5": f"max: {rate_max_attempts}",
        # JWT expiry
        "'1h'": f"'{jwt_expiry}'",
        # bcrypt rounds
        "salt rounds = 12": f"salt rounds = {bcrypt_rounds}",
        "saltRounds = 12": f"saltRounds = {bcrypt_rounds}",
        # Table name (in model)
        "tableName: 'users'": f"tableName: '{table_name}'",
        # Cookie name
        "'token'": f"'{cookie_name}'",
        # Session cookie name
        "name: 'sessionId'": f"name: '{session_cookie}'",
        "sessionId=": f"{session_cookie}=",
    }

    files_to_patch = [
        os.path.join(output_dir, "src", "auth", "login.js"),
        os.path.join(output_dir, "src", "middleware", "rateLimit.js"),
        os.path.join(output_dir, "src", "models", "User.js"),
        os.path.join(output_dir, "src", "app.js"),
        os.path.join(output_dir, "test", "security", "auth.test.js"),
        os.path.join(output_dir, "package.json"),
    ]

    for filepath in files_to_patch:
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        for old, new in substitutions.items():
            content = content.replace(old, new)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    # ── Patch spec.md and brief.md ────────────────────────────────────────────
    for doc in ["spec.md", "brief.md"]:
        doc_path = os.path.join(os.path.dirname(__file__), doc)
        out_doc_path = os.path.join(output_dir, "..", doc)
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()
            for old, new in substitutions.items():
                content = content.replace(old, new)
            with open(out_doc_path, "w", encoding="utf-8") as f:
                f.write(content)

    # ── Write params.json for reproducibility ─────────────────────────────────
    import json
    params_path = os.path.join(output_dir, "..", "params.json")
    with open(params_path, "w", encoding="utf-8") as f:
        json.dump({"seed": seed, **params}, f, indent=2)

    print(f"[generator] Written to: {output_dir}")
    print(f"[generator] Params saved to: {params_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <seed> [output_dir]")
        sys.exit(1)

    seed = int(sys.argv[1])
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(__file__), f"workspace_seed{seed}"
    )
    generate(seed, output_dir)
