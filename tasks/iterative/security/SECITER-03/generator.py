#!/usr/bin/env python3
"""
SECITER-03 Generator
Parameterizes surface details (package versions, JWT algorithm, upload dir, etc.)
from a seed so different seeds produce different surface instances of the same task.

Usage:
  python generator.py <seed> [output_dir]
"""

import random
import os
import sys
import shutil
import json
import re


def make_rng(seed: int) -> random.Random:
    return random.Random(seed)


def generate(seed: int, output_dir: str):
    rng = make_rng(seed)

    # ── Parameterized values ──────────────────────────────────────────────────

    # Lodash vulnerable version (all < 4.17.21 are vulnerable)
    lodash_vuln = rng.choice(["4.17.15", "4.17.14", "4.17.11", "4.17.4"])

    # jsonwebtoken vulnerable version (all < 9.0.0 are vulnerable)
    jwt_vuln = rng.choice(["8.5.1", "8.4.0", "8.3.0", "7.4.3"])

    # express-fileupload vulnerable version (all < 1.4.0 are vulnerable)
    fileupload_vuln = rng.choice(["1.2.1", "1.1.7", "1.0.0", "0.4.0"])

    # JWT algorithm
    jwt_algo = rng.choice(["HS256", "HS384", "HS512"])

    # JWT expiry
    jwt_expiry = rng.choice(["1h", "2h", "30m", "24h"])

    # Upload directory name
    upload_dir_name = rng.choice(["uploads", "files", "attachments", "media"])

    # Environment variable names
    jwt_secret_env = rng.choice(["JWT_SECRET", "APP_JWT_SECRET", "TOKEN_SECRET"])

    params = {
        "lodash_vuln": lodash_vuln,
        "jwt_vuln": jwt_vuln,
        "fileupload_vuln": fileupload_vuln,
        "jwt_algo": jwt_algo,
        "jwt_expiry": jwt_expiry,
        "upload_dir_name": upload_dir_name,
        "jwt_secret_env": jwt_secret_env,
    }

    print(f"[generator] seed={seed}")
    print(f"[generator] parameters:")
    for k, v in params.items():
        print(f"  {k} = {v!r}")

    # ── Output directory ──────────────────────────────────────────────────────
    src_dir = os.path.join(os.path.dirname(__file__), "workspace")
    if os.path.abspath(output_dir) != os.path.abspath(src_dir):
        shutil.copytree(src_dir, output_dir, dirs_exist_ok=True)

    # ── Substitutions ─────────────────────────────────────────────────────────

    substitutions = {
        # Vulnerable versions in package.json
        '"lodash": "4.17.15"': f'"lodash": "{lodash_vuln}"',
        '"jsonwebtoken": "8.5.1"': f'"jsonwebtoken": "{jwt_vuln}"',
        '"express-fileupload": "1.2.1"': f'"express-fileupload": "{fileupload_vuln}"',
        # JWT algorithm
        "HS256": jwt_algo,
        # JWT expiry
        "'1h'": f"'{jwt_expiry}'",
        # Upload dir
        "'uploads'": f"'{upload_dir_name}'",
        '"uploads"': f'"{upload_dir_name}"',
        # JWT secret env var
        "JWT_SECRET": jwt_secret_env,
    }

    files_to_patch = [
        os.path.join(output_dir, "package.json"),
        os.path.join(output_dir, "src", "auth", "jwt.js"),
        os.path.join(output_dir, "src", "auth", "middleware.js"),
        os.path.join(output_dir, "src", "auth", "refresh.js"),
        os.path.join(output_dir, "src", "upload", "handler.js"),
        os.path.join(output_dir, "src", "utils", "transform.js"),
        os.path.join(output_dir, "test", "integration", "auth.test.js"),
        os.path.join(output_dir, "test", "integration", "upload.test.js"),
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

    # Patch spec.md and brief.md
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

    # Write params.json
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
