# INCRCA-02: Silent Data Corruption

## Description

Approximately 3% of orders have incorrect totals. The monitoring team suspects
floating-point rounding in `calculator.py`, but the actual root cause is a race
condition in `discounts.py` — two concurrent requests can both read the pre-discount
price and apply the discount independently (lost update anomaly). Fixing floats
alone only addresses 0.1% of cases. The concurrency fix is required for tests 9-10.

## What Makes This Hard

- The monitoring hypothesis (float rounding) is directionally correct but incomplete
- Fixing only floats passes 8/10 tests — looks like near-complete success
- The concurrency tests (9-10) require understanding SELECT FOR UPDATE semantics
- Single-pass agents typically fix the obvious float issue and miss the race condition
- The verifier must notice tests 9-10 are failing and report the race condition pattern

## Task Structure

```
workspace/
  orders/
    calculator.py   # BUG: float arithmetic (fix to Decimal)
    discounts.py    # BUG: missing .with_for_update() (race condition)
    models.py       # SQLAlchemy Order model
    db.py           # database session setup
  test/
    test_orders.py  # 10 tests
  requirements.txt
```

## Running the Tests

```bash
cd workspace
pip install -r requirements.txt
pytest test/test_orders.py -v
```

Expected baseline output (unfixed):
```
FAILED test/test_orders.py::test_04_rounding_edge_case
FAILED test/test_orders.py::test_09_concurrent_discount_no_double
FAILED test/test_orders.py::test_10_concurrent_discount_idempotent
```

## Scoring

Score = passing_tests / 10

| Score | State |
|-------|-------|
| 1.0 | All 10 pass (both fixes applied) |
| 0.8 | Tests 1-8 pass (Decimal fix only) |
| 0.0 | Most tests fail (no fixes) |

Run grader:
```bash
bash grader.sh
```

## Expected Scores by Agent Type

| Agent Type | Expected Score | Rationale |
|------------|---------------|-----------|
| Oracle (spec-aware) | 0.40 | Fixes float only; misses race condition |
| Single-pass | 0.55 | May partially fix; concurrency often missed |
| Multi-turn (2 rounds) | 1.00 | Round 2 adds with_for_update after verifier feedback |

## Stopping Condition

`10 passed` in pytest output.

## Multi-Turn Attestation Hint

After round 1, the Verifier should note:
- Tests 1-8 pass (8/10)
- Tests 9-10 fail with double-discount or assertion error
- Root cause: `discounts.py` query missing `.with_for_update()`

## Generating Variants

```bash
python generator.py --seed 42 --output-dir ./workspace_seed42
```
