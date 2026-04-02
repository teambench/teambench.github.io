#!/usr/bin/env python3
"""
Generator for INCRCA-03: Memory Leak.

Parameterizes surface details (cache sizes, file counts, record IDs)
from a seed value while preserving the same logical bugs.

Usage:
    python generator.py --seed 42 --output-dir ./workspace_generated
"""

import argparse
import os
import random
import shutil
import json


BROKEN_CACHE_SIZE_POOL = [None, None, None]   # always None (the bug)
FIXED_CACHE_SIZE_POOL  = [500, 1000, 2000, 5000]
SOURCE_NAME_POOL       = ["test", "ingestion", "pipeline_alpha", "etl_batch"]
RECORD_PREFIX_POOL     = ["rec_", "record_", "item_", "event_"]
N_CALLS_POOL           = [3000, 5000, 8000, 10000]


def generate(seed: int, output_dir: str):
    rng = random.Random(seed)

    def pick(pool):
        return rng.choice(pool)

    fixed_cache_size = pick(FIXED_CACHE_SIZE_POOL)
    source_name      = pick(SOURCE_NAME_POOL)
    record_prefix    = pick(RECORD_PREFIX_POOL)
    n_calls          = pick(N_CALLS_POOL)

    print(f"Seed: {seed}")
    print(f"  fixed_cache_size : {fixed_cache_size}")
    print(f"  source_name      : {source_name}")
    print(f"  record_prefix    : {record_prefix}")
    print(f"  n_calls_test     : {n_calls}")

    src_dir = os.path.join(os.path.dirname(__file__), "workspace")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    shutil.copytree(src_dir, output_dir)

    # Patch test file — update n_calls and record prefix
    test_path = os.path.join(output_dir, "test", "test_memory.py")
    with open(test_path) as f:
        content = f.read()
    content = content.replace("n_calls = 5000", f"n_calls = {n_calls}")
    content = content.replace('"unique_key_"', f'"unique_{record_prefix}"')
    content = content.replace(
        "assert info[\"currsize\"] <= 1500",
        f"assert info[\"currsize\"] <= {int(fixed_cache_size * 1.5)}"
    )
    with open(test_path, "w") as f:
        f.write(content)

    # Patch pipeline.py — update source name
    pipeline_path = os.path.join(output_dir, "processor", "pipeline.py")
    with open(pipeline_path) as f:
        content = f.read()
    content = content.replace('source="test"', f'source="{source_name}"')
    content = content.replace('source="batch_test"', f'source="{source_name}_batch"')
    with open(pipeline_path, "w") as f:
        f.write(content)

    # Write params.json
    params = {
        "seed": seed,
        "fixed_cache_size": fixed_cache_size,
        "source_name": source_name,
        "record_prefix": record_prefix,
        "n_calls_test": n_calls,
    }
    with open(os.path.join(output_dir, "params.json"), "w") as f:
        json.dump(params, f, indent=2)

    print(f"\nGenerated workspace at: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="INCRCA-03 workspace generator")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", default="./workspace_generated")
    args = parser.parse_args()
    generate(args.seed, args.output_dir)


if __name__ == "__main__":
    main()
