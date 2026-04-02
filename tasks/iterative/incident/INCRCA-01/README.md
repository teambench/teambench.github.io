# INCRCA-01: Cascading Timeout Misattribution

## Description

The checkout service has a 12% error rate. SLO requires < 0.1%. Agents must
trace the failure through a 3-service chain, identify the actual root cause
(AuthService connection pool exhaustion), and fix it. A second issue
(missing DB index) is revealed after the first fix and must be addressed in
round 2.

## What Makes This Hard

- The symptoms appear in CheckoutService and UserService logs ("downstream timeout")
- The AuthService logs contain the real signal, but agents may stop at UserService
- Fixing only the pool brings error rate from 12% → 4%, still failing SLO
- The DB index fix is only evident from slow-query warnings buried in auth_service.log
- Single-pass agents often miss the secondary fix

## Task Structure

```
workspace/
  services/
    auth_service.py     # BUG: max_connections=5 (fix to 50)
    user_service.py     # correct
    checkout_service.py # correct, cascades failures
  db/
    schema.sql          # BUG: missing index on users.email
  logs/
    auth_service.log    # shows pool exhaustion + slow query warnings
    user_service.log    # shows "downstream timeout" (symptom, not cause)
  test/integration/
    slo_test.py         # measures error rate under concurrent load
```

## Running the Test

```bash
cd workspace
python test/integration/slo_test.py
```

Output:
```
Running SLO test with 500 requests (60 concurrent workers)...
Completed: 500 requests (60 errors)
ERROR_RATE=12.00
RESULT=FAIL (threshold: 0.1%)
```

## Scoring

| Score | Condition |
|-------|-----------|
| 1.0   | ERROR_RATE < 0.1 (both fixes applied) |
| 0.5   | ERROR_RATE < 5.0 (pool fixed, index missing) |
| 0.0   | ERROR_RATE >= 5.0 (root cause not found) |

Run grader:
```bash
bash grader.sh
```

## Expected Scores by Agent Type

| Agent Type | Expected Score | Rationale |
|------------|---------------|-----------|
| Oracle (spec-aware) | 0.50 | Fixes pool only; misses index in single pass |
| Single-pass | 0.60 | May partially fix but miss secondary issue |
| Multi-turn (2 rounds) | 1.00 | Round 1 fixes pool; Verifier feedback triggers index fix |

## Stopping Condition

`ERROR_RATE < 0.1` printed by `slo_test.py`.

## Multi-Turn Attestation Hint

After round 1, the Verifier should produce an `attestation.json` noting:
- error rate achieved (e.g., 4.0%)
- pool fix confirmed
- remaining issue: missing index on users.email (visible in auth_service.log slow query warnings)

## Generating Variants

```bash
python generator.py --seed 42 --output-dir ./workspace_seed42
```

## Real-World Provenance

This task is based on two real incidents:

- **2019 GitHub Actions cascading timeout incident** — surface symptoms (job timeouts, queue backup) masked resource exhaustion one hop upstream:
  https://github.blog/2019-10-11-why-arent-my-actions-working/
- **Shopify 2020 database connection pool exhaustion postmortem** — a high-concurrency checkout spike exhausted PostgreSQL connection pools, causing cascading timeouts in upstream services. Fixing the pool revealed a latent slow-query problem that had been masked by the exhaustion.

The two-fix structure (pool fix → 12% to 4% error rate, then index fix → under 0.1%) mirrors the Shopify postmortem pattern where the primary bottleneck concealed a secondary performance issue visible only in slow-query logs.

See [`../PROVENANCE.md`](../PROVENANCE.md) for full details.
