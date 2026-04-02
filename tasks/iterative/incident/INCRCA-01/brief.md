# INCRCA-01: Cascading Timeout — Executor Brief

## Your Mission

The checkout service has a **12% error rate**. SLO requires **< 0.1%**. Find the root cause and fix it.

## Files Available

```
services/
  auth_service.py       — AuthService implementation
  user_service.py       — UserService implementation
  checkout_service.py   — CheckoutService implementation
db/
  schema.sql            — Database schema
logs/
  auth_service.log      — Auth service runtime logs
  user_service.log      — User service runtime logs
test/integration/
  slo_test.py           — Run this to measure error rate
```

## How to Measure

```bash
python test/integration/slo_test.py
```

Output format:
```
Running SLO test with 500 requests...
Completed: 500 requests
ERROR_RATE=12.00
RESULT=FAIL (threshold: 0.1%)
```

## Stopping Condition

`ERROR_RATE` must be below `0.1` for the task to be considered complete.

## Hints

- Start by reading the logs — they point to where the problem is
- Check configuration values in the service files
- The database schema may also need attention
