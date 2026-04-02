#!/usr/bin/env python3
"""
SECITER-02 Generator
Parameterizes surface details (allowed origins, CSP CDN domains, analytics ID, etc.)
from a seed so different seeds produce different surface instances of the same task.

Usage:
  python generator.py <seed> [output_dir]
"""

import random
import os
import sys
import shutil
import json


def make_rng(seed: int) -> random.Random:
    return random.Random(seed)


def generate(seed: int, output_dir: str):
    rng = make_rng(seed)

    # ── Parameterized values ──────────────────────────────────────────────────

    # Allowed origins
    app_subdomain = rng.choice(["app", "dashboard", "portal", "ui"])
    admin_subdomain = rng.choice(["admin", "manage", "control", "ops"])
    base_domain = rng.choice(["example.com", "myapp.io", "platform.dev"])
    allowed_origin_1 = f"https://{app_subdomain}.{base_domain}"
    allowed_origin_2 = f"https://{admin_subdomain}.{base_domain}"

    # CDN domain
    cdn_domain = rng.choice([
        f"https://cdn.{base_domain}",
        "https://cdnjs.cloudflare.com",
        "https://unpkg.com",
    ])

    # WebSocket domain
    ws_domain = rng.choice([
        f"wss://realtime.{base_domain}",
        f"wss://ws.{base_domain}",
        "wss://socket.example.com",
    ])

    # Analytics ID
    analytics_id = f"UA-{rng.randint(10000, 99999)}-{rng.randint(1, 9)}"

    # Cookie name for nonce storage
    nonce_placeholder = rng.choice(["{{NONCE}}", "%%NONCE%%", "__NONCE__"])

    params = {
        "allowed_origin_1": allowed_origin_1,
        "allowed_origin_2": allowed_origin_2,
        "cdn_domain": cdn_domain,
        "ws_domain": ws_domain,
        "analytics_id": analytics_id,
        "nonce_placeholder": nonce_placeholder,
        "base_domain": base_domain,
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
        "https://app.example.com": allowed_origin_1,
        "https://admin.example.com": allowed_origin_2,
        "https://cdn.example.com": cdn_domain,
        "wss://realtime.example.com": ws_domain,
        "UA-12345-1": analytics_id,
        "{{NONCE}}": nonce_placeholder,
    }

    files_to_patch = [
        os.path.join(output_dir, "src", "middleware", "security.js"),
        os.path.join(output_dir, "src", "app.js"),
        os.path.join(output_dir, "public", "index.html"),
        os.path.join(output_dir, "test", "security", "headers.test.js"),
        os.path.join(output_dir, "test", "functional", "app.test.js"),
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

    # Update nonce regex in test if placeholder changed
    if nonce_placeholder != "{{NONCE}}":
        escaped = nonce_placeholder.replace("{", "\\{").replace("}", "\\}").replace("%", "\\%").replace("_", "\\_")
        test_path = os.path.join(output_dir, "test", "functional", "app.test.js")
        if os.path.exists(test_path):
            with open(test_path, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace(
                "res.text).not.toContain('{{NONCE}}')",
                f"res.text).not.toContain('{nonce_placeholder}')"
            )
            with open(test_path, "w", encoding="utf-8") as f:
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
