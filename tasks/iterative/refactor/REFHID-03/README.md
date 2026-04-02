# REFHID-03: ORM Migration with Unsupported Patterns

## Description

Migrate `db/queries.py` from SQLAlchemy Core to the Prisma Python client. Two query patterns have no direct Prisma equivalent:

1. **SELECT FOR UPDATE** (pessimistic locking) — must use `query_raw`
2. **LATERAL JOIN** — must be rewritten as two queries + Python join

The Planner's `spec.md` documents both workarounds. The Executor's `brief.md` does not. The Verifier's concurrency tests catch the missing `FOR UPDATE` lock after round 1.

## Multi-Turn Dynamics

| Round | What happens |
|-------|-------------|
| Round 1 | Executor migrates most queries using standard Prisma APIs. Unit tests pass for simple queries. `lock_and_get_order` silently uses `find_unique` (no lock). Concurrency tests fail. |
| Round 2 | Verifier's attestation flags the 2 concurrency tests. Executor adds `query_raw` with `FOR UPDATE`. All 10 pass. |

The concurrency tests fail because:
- `test_lock_and_get_order_uses_query_raw` — asserts `query_raw` was called, not `find_unique`
- `test_lock_and_get_order_sql_contains_for_update` — asserts SQL contains `FOR UPDATE`

## Expected Scores

| Agent type | Expected score |
|-----------|---------------|
| Oracle (reads spec.md) | 0.45 round 1 → 1.0 round 2 |
| Single-pass (brief.md only) | ~0.60 |
| Multi-turn | 1.0 |

## Stopping Condition

Stop when score = 1.0 (all 10 tests pass), or after 3 rounds.

## Running Tests

```bash
cd workspace
pip install -r requirements.txt
python -m pytest test/ -v
```

No real database required — all tests use AsyncMock.

## Grading

```bash
bash grader.sh
# outputs: 0.0000 to 1.0000
```

Score = passing_tests / 10

## Generating Variants

```bash
python generator.py --seed 123 --output-dir ./generated/seed-123/
```

Parameterizes: table names, field names (total, stock), LATERAL limit.
