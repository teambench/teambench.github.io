# INCRCA-02: Silent Data Corruption — Full Specification

## Overview

Approximately 3% of orders have incorrect totals — off by $0.01 to $0.05. The monitoring
team suspects floating-point rounding. You must identify all root causes and fix them so
that all 10 tests in `test/test_orders.py` pass.

---

## Symptom Details

- Customer support tickets report order totals differing from what customers saw at checkout
- Discrepancy ranges: $0.01 to $0.05, occasionally more under high load
- Monitoring dashboard flags ~3% of orders as having incorrect totals
- Initial hypothesis from the monitoring team: floating-point rounding in price calculation

---

## Root Cause Analysis

### Issue 1 — Floating-Point Rounding (PARTIAL, ~0.1% of orders)
**Location:** `orders/calculator.py`
**Bug:** Prices are stored and computed using Python `float`, which cannot represent many
decimal values exactly. For example, `0.1 + 0.2 != 0.3` in float arithmetic.
**Impact:** Affects ~0.1% of orders (edge cases with certain price combinations).
**Fix:** Use `decimal.Decimal` for all price arithmetic. Parse incoming prices with
`Decimal(str(price))` or `Decimal(price)` if already a string.

### Issue 2 — Race Condition in Discount Application (ACTUAL ROOT CAUSE, ~3% of orders)
**Location:** `orders/discounts.py`
**Bug:** The `apply_discount` function reads the current price, computes the discounted
price, then writes it back — without any database-level lock. Under concurrent load,
two requests for the same order can both read the original price and both apply the
discount, resulting in a double-discount (price reduced twice).

```python
# BROKEN: read-modify-write without lock
order = session.query(Order).filter_by(id=order_id).first()  # both threads read same price
discounted = order.total * (1 - discount_rate)
order.total = discounted  # both threads write discounted price
session.commit()
```

**Impact:** When two discount requests race, the final total is `original * (1-rate)^2`
instead of `original * (1-rate)`. This causes the $0.01-$0.05 discrepancy at typical
discount rates.

**Fix:** Use `SELECT FOR UPDATE` to acquire a row-level lock before reading:

```python
# FIXED: lock the row first
order = session.query(Order).filter_by(id=order_id).with_for_update().first()
discounted = order.total * (1 - discount_rate)
order.total = discounted
session.commit()
```

---

## Fix Sequence

### Round 1 Fix (addresses floating-point issue — fixes tests 1-8)
- In `orders/calculator.py`: replace `float` arithmetic with `decimal.Decimal`
- Tests 1-8 will pass. Tests 9-10 (concurrency) will still fail.

### Round 2 Fix (addresses race condition — fixes tests 9-10)
- In `orders/discounts.py`: add `.with_for_update()` to the SQLAlchemy query
- All 10 tests pass.

---

## Files

| File | Description |
|------|-------------|
| `orders/calculator.py` | Price calculation — uses `float` (bug) |
| `orders/discounts.py` | Discount application — race condition (bug) |
| `orders/models.py` | SQLAlchemy Order model |
| `orders/db.py` | Database setup (SQLite in-memory for tests) |
| `test/test_orders.py` | 10 tests; run with `pytest test/test_orders.py` |
| `requirements.txt` | Dependencies |

---

## Test Breakdown

| Test | Description | Passes after |
|------|-------------|--------------|
| test_01_basic_total | Simple order total correct | Decimal fix |
| test_02_multi_item_total | Multi-item total correct | Decimal fix |
| test_03_zero_quantity | Zero quantity item ignored | Decimal fix |
| test_04_rounding_edge_case | 0.1+0.2 type edge case | Decimal fix |
| test_05_discount_basic | Basic discount applied correctly | Decimal fix |
| test_06_discount_zero | Zero discount leaves total unchanged | Decimal fix |
| test_07_discount_hundred_pct | 100% discount gives zero | Decimal fix |
| test_08_multiple_items_with_discount | Multi-item order with discount | Decimal fix |
| test_09_concurrent_discount_no_double | Concurrent discounts don't double-apply | SELECT FOR UPDATE fix |
| test_10_concurrent_discount_idempotent | Concurrent same discount idempotent | SELECT FOR UPDATE fix |

---

## Scoring

Score = (passing tests) / 10

A score of 1.0 requires all 10 tests to pass.

---

## Multi-Turn Behavior

- **Round 1:** Agents fix floating-point. Tests 1-8 pass (score = 0.8). Verifier reports
  tests 9-10 still fail — notes the concurrency failure pattern in its attestation.
- **Round 2:** Executor adds `with_for_update()`. All 10 tests pass (score = 1.0).
