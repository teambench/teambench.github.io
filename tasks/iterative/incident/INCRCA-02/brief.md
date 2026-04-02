# INCRCA-02: Silent Data Corruption — Executor Brief

## Your Mission

Approximately 3% of orders have incorrect totals. Fix the root cause(s) so that
all 10 tests in `test/test_orders.py` pass.

## Files Available

```
orders/
  calculator.py     — price calculation logic
  discounts.py      — discount application logic
  models.py         — SQLAlchemy Order model
  db.py             — database session setup
test/
  test_orders.py    — 10 tests (run these to check progress)
requirements.txt
```

## How to Run Tests

```bash
pip install -r requirements.txt
pytest test/test_orders.py -v
```

## Stopping Condition

All 10 tests must pass (`10 passed` in pytest output).

## Hints

- The monitoring team suspects floating-point rounding — investigate `calculator.py`
- Look carefully at concurrency in `discounts.py` — there may be more than one issue
- Check the test names for clues about what each test validates

## Real-World Provenance

This task is inspired by two overlapping real-world bug classes:

- **Lost Update concurrency anomaly** — the canonical formulation is from Berenson et al. (1995), "A Critique of ANSI SQL Isolation Levels", *SIGMOD 1995*, Section 3.1. Two concurrent transactions both read the pre-discount price, compute a discounted value independently, and one write silently overwrites the other. This is the root cause of the ~3% incorrect-total rate in this task.
- **MySQL/InnoDB READ COMMITTED isolation gap** — HN thread "Lost Updates in MySQL" documents real e-commerce incidents where discount application races at `READ COMMITTED` isolation level cause one discount to be silently dropped under concurrent load.
- **Floating-point rounding in financial calculations** — using Python `float` for monetary arithmetic accumulates IEEE 754 rounding errors across aggregations; the standard fix is `decimal.Decimal` with explicit quantization.

See [`../PROVENANCE.md`](../PROVENANCE.md) for full details.
