# INCRCA-01: Cascading Timeout Misattribution — Full Specification

## Overview

The checkout service has a **12% error rate**. Your SLO requires **< 0.1%**. You must identify the root cause, apply the correct fix, and validate by running the integration test suite.

All fixes must be applied to files in `services/` and `db/`. Run `python test/integration/slo_test.py` to measure the error rate.

---

## Architecture

```
CheckoutService → UserService → AuthService → PostgreSQL DB
```

Each hop adds latency. When a downstream service fails, the upstream service propagates the error and may time out.

---

## SLO

- **Target:** error rate < 0.1% (measured as failed requests / total requests under load)
- **Measured by:** `test/integration/slo_test.py` — simulates 500 concurrent requests and reports error rate
- **Pass condition:** error rate printed as `ERROR_RATE=X.XX` must be < 0.1

---

## Known Symptoms

- CheckoutService times out after 30s on ~12% of requests
- `logs/user_service.log` contains repeated "downstream timeout" warnings
- `logs/auth_service.log` contains "connection pool exhausted" errors

---

## Candidate Root Causes

The on-call team has identified three candidates:

### Candidate A — UserService Thread Pool
**Hypothesis:** UserService thread pool is too small, causing request queuing.
**Evidence:** UserService log shows slow request processing under load.
**Status:** RED HERRING. The thread pool size is adequate. The slowness in UserService is caused entirely by AuthService being slow.

### Candidate B — AuthService Connection Pool (ACTUAL ROOT CAUSE)
**Location:** `services/auth_service.py`, line with `max_connections=5`
**Hypothesis:** AuthService can only hold 5 simultaneous DB connections, causing pool exhaustion at load.
**Evidence:** `logs/auth_service.log` shows `[ERROR] connection pool exhausted` repeatedly.
**Fix:** Change `max_connections=5` to `max_connections=50` in `services/auth_service.py`.

### Candidate C — DB Slow Queries (partial issue, not root cause of 12%)
**Hypothesis:** Slow queries on the `users` table cause timeouts.
**Evidence:** DB slow query log shows queries on `users` table taking 200ms+.
**Status:** Real issue, but secondary. Even after fixing Candidate B, a missing index on `users.email` causes 4% error rate.

---

## Fix Sequence

### Round 1 Fix (addresses 12% → 4%)
Change `max_connections` in `services/auth_service.py`:
```python
# Before
max_connections=5
# After
max_connections=50
```

### Round 2 Fix (addresses 4% → 0.02%)
Add index on `users.email` in `db/schema.sql`:
```sql
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```
The test suite checks for this index by looking at the schema file AND measuring actual query performance.

---

## Error Rate Behavior (by fix state)

| State | Error Rate | SLO Pass |
|-------|-----------|----------|
| Baseline (max_connections=5, no index) | ~12% | No |
| max_connections=50, no index | ~4% | No |
| max_connections=5, index added | ~10% (pool still exhausted) | No |
| Both fixes applied | ~0.02% | Yes |

---

## Files

| File | Description |
|------|-------------|
| `services/auth_service.py` | AuthService — has `max_connections=5` bug |
| `services/user_service.py` | UserService — correct implementation |
| `services/checkout_service.py` | CheckoutService — cascades failures |
| `db/schema.sql` | Database schema — missing index on `users.email` |
| `logs/auth_service.log` | Auth service logs showing pool exhaustion |
| `logs/user_service.log` | User service logs showing downstream timeouts |
| `test/integration/slo_test.py` | Integration test — measures error rate |

---

## Scoring

| Score | Condition |
|-------|-----------|
| 1.0 | Error rate < 0.1% (both fixes applied) |
| 0.5 | Error rate < 5% (AuthService pool fixed, missing index) |
| 0.0 | Error rate ≥ 5% (root cause not fixed) |

---

## Multi-Turn Behavior

- **Round 1:** Verifier sees error rate of ~4% after pool fix. Attestation notes index still missing.
- **Round 2:** Executor must add the index to `db/schema.sql` to achieve < 0.1%.
