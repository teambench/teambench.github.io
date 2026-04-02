#!/usr/bin/env python3
"""
SLO Integration Test for CheckoutService.

Simulates realistic concurrent load and measures error rate.
The error rate is determined by reading the service configuration:
  - max_connections=5 and no email index  -> ~12% error rate  (FAIL)
  - max_connections=50 and no email index -> ~4% error rate   (FAIL)
  - max_connections=50 with email index   -> ~0.02% error rate (PASS)

Prints ERROR_RATE=X.XX and RESULT=PASS/FAIL.

Usage:
    python test/integration/slo_test.py

Exit codes:
    0 — error rate < threshold (SLO met)
    1 — error rate >= threshold (SLO violated)
"""

import sys
import os
import time
import random

# Ensure workspace root is on the path
_HERE = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE = os.path.abspath(os.path.join(_HERE, '..', '..'))
if _WORKSPACE not in sys.path:
    sys.path.insert(0, _WORKSPACE)

# Force re-import so changes to service files are picked up
for mod in list(sys.modules.keys()):
    if mod.startswith('services'):
        del sys.modules[mod]

import services.auth_service as _auth_mod
_auth_mod.reset_pool()

SLO_THRESHOLD = 0.1   # percent
NUM_REQUESTS = 500


def _check_max_connections():
    """Read max_connections from auth_service module."""
    import services.auth_service as a
    return a.max_connections


def _check_email_index():
    """Check if schema.sql defines an index on users.email."""
    schema_path = os.path.join(_WORKSPACE, 'db', 'schema.sql')
    try:
        with open(schema_path) as f:
            content = f.read()
        # Look for any CREATE INDEX referencing email column
        import re
        # Must be an uncommented index line
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith('--'):
                continue
            if 'INDEX' in stripped.upper() and 'email' in stripped.lower():
                return True
        return False
    except FileNotFoundError:
        return False


def _compute_error_rate(max_conn: int, has_index: bool) -> float:
    """
    Compute realistic error rate based on service configuration.

    Model:
      - With max_connections=5 (broken): pool exhausts under load, ~12% error rate
      - With max_connections>=50 (fixed) but no index: slow queries still cause ~4% timeouts
      - With max_connections>=50 AND index: fast queries, ~0.02% error rate (noise floor)

    Small random jitter is added to make each run realistic.
    """
    rng = random.Random(int(time.time() * 1000) % 2**31)

    if max_conn < 20:
        # Broken pool: 12% ± 2%
        base = 12.0
        jitter = rng.uniform(-2.0, 2.0)
    elif not has_index:
        # Fixed pool but slow queries: 4% ± 1%
        base = 4.0
        jitter = rng.uniform(-1.0, 1.0)
    else:
        # Both fixed: near-zero, 0.02% ± 0.01%
        base = 0.02
        jitter = rng.uniform(-0.01, 0.01)

    return max(0.0, base + jitter)


def run_slo_test(num_requests: int = NUM_REQUESTS):
    max_conn = _check_max_connections()
    has_index = _check_email_index()

    print(f"Running SLO test with {num_requests} requests...")
    print(f"  auth_service max_connections : {max_conn}")
    print(f"  db/schema.sql email index    : {'yes' if has_index else 'no'}")

    # Simulate a brief warm-up period
    time.sleep(0.05)

    error_rate = _compute_error_rate(max_conn, has_index)
    errors = int(round(num_requests * error_rate / 100))
    # Clamp to valid range
    errors = max(0, min(errors, num_requests))
    error_rate_actual = errors / num_requests * 100

    print(f"Completed: {num_requests} requests ({errors} errors)")
    print(f"ERROR_RATE={error_rate_actual:.2f}")

    if error_rate_actual < SLO_THRESHOLD:
        print(f"RESULT=PASS (threshold: {SLO_THRESHOLD}%)")
        return True
    else:
        print(f"RESULT=FAIL (threshold: {SLO_THRESHOLD}%)")
        return False


if __name__ == "__main__":
    passed = run_slo_test()
    sys.exit(0 if passed else 1)
