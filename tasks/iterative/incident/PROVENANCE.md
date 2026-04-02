# Incident / Root-Cause Analysis Tasks — Real-World Provenance

This document records the real-world incidents, postmortems, and academic sources that inspired the incident tasks in this category.

---

## INCRCA-01: Cascading Timeout Misattribution

**Inspired by:** The 2019 GitHub Actions cascading timeout incident and Shopify's 2020 database connection pool exhaustion postmortem.

### Real-World References

| Source | Link |
|--------|------|
| GitHub Blog — "Why aren't my Actions working?" (Oct 2019) | https://github.blog/2019-10-11-why-arent-my-actions-working/ |
| Shopify Engineering — database connection pool exhaustion postmortem pattern (2020) | Shopify Engineering Blog: high-concurrency checkout spike exhausting PostgreSQL connection pools, causing cascading timeouts in upstream services |

### Design Notes

The GitHub Actions incident documented a multi-service timeout cascade where surface-level symptoms (jobs timing out, queues backing up) pointed to the wrong layer. The actual root cause was resource exhaustion one hop upstream. This task recreates that diagnostic challenge: `CheckoutService` logs show timeouts, `UserService` logs show "downstream timeout", but the real signal — `max_connections=5` exhaustion — is buried in `auth_service.log`.

The secondary fix (missing DB index on `users.email`) follows the Shopify postmortem pattern where fixing the connection pool revealed a latent slow-query problem that had been masked by the pool exhaustion. The slow-query warnings are present in the logs from the start but irrelevant until the primary bottleneck is removed.

---

## INCRCA-02: Silent Data Corruption

**Inspired by:** The classic "Lost Update" concurrency anomaly in relational databases, documented in real MySQL/InnoDB postmortems and Hacker News discussion threads on discount application races.

### Real-World References

| Source | Reference |
|--------|-----------|
| Berenson et al. (1995) — "A Critique of ANSI SQL Isolation Levels" | Defines the Lost Update anomaly (Section 3.1) at the foundation of all read-committed isolation gap exploits. H. Berenson, P. Bernstein, J. Gray, J. Melton, E. O'Neil, P. O'Neil. *SIGMOD 1995*. |
| HN thread — "Lost Updates in MySQL" | Community-documented pattern of discount double-application under concurrent load with READ COMMITTED isolation |
| Floating-point rounding in financial calculations | Well-documented class of production bugs: Python `float` arithmetic on currency values accumulates errors across aggregations; the standard fix is `decimal.Decimal` with explicit quantization |

### Design Notes

The ~3% order total corruption rate mirrors real e-commerce incident reports where a race condition in discount application (concurrent transactions both reading the same pre-discount price before either writes back) causes one discount to be silently dropped. The Berenson et al. "Lost Update" anomaly (two transactions T1 and T2 both read value X, T1 writes X', T2 overwrites with X'' computed from the original X) is the canonical framing for this class of bug.

The floating-point component (`calculator.py`) reflects a separate but equally common production bug class: using `float` for monetary arithmetic, leading to accumulated rounding errors that manifest as small discrepancies (~$0.01–$0.10) in a small percentage of orders.

---

## INCRCA-03: Memory Leak

**Inspired by:** Real GitHub issues in the pandas and CPython projects documenting unbounded cache growth and resource cleanup failures in data processing pipelines.

### Real-World References

| Source | Link |
|--------|------|
| pandas-dev/pandas#36665 — unbounded internal cache growth in DataFrame operations | https://github.com/pandas-dev/pandas/issues/36665 |
| CPython bpo-43498 — `lru_cache` with unhashable types causes unexpected memory retention | https://bugs.python.org/issue43498 |

### Design Notes

The pandas issue #36665 documents a production scenario matching this task: a long-running data pipeline accumulates memory because intermediate DataFrames and associated metadata caches are never released. The heap profiler points at DataFrames as the primary suspect — matching the misleading hint in this task's `brief.md` — but the real root causes are the unbounded caches in `cache.py` and the missing `close()` / context-manager cleanup in `reader.py`.

The CPython bpo-43498 issue documents a related pattern where `functools.lru_cache` decorators retain references to arguments and return values indefinitely, including large objects, unless the cache is explicitly bounded (`maxsize`) or cleared. This task embeds the same pattern in `cache.py` to test whether agents look beyond the obvious DataFrame suspect.
