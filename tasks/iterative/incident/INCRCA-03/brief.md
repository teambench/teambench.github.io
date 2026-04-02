# INCRCA-03: Memory Leak — Executor Brief

## Your Mission

The data processing service OOMs after ~2 hours in production. RSS grows ~50MB/hour.
Fix the memory leak(s) so that all 8 tests in `test/test_memory.py` pass.

## Files Available

```
processor/
  pipeline.py    — main processing pipeline
  cache.py       — caching utilities
  reader.py      — CSV file reader
  models.py      — data models
test/
  test_memory.py — 8 tests including memory stability test
requirements.txt
```

## How to Run Tests

```bash
pip install -r requirements.txt
pytest test/test_memory.py -v
```

## Stopping Condition

All 8 tests must pass (`8 passed` in pytest output).

## Hints

- The heap profiler pointed at pandas DataFrames — investigate whether that's the real cause
- Look at caching patterns — unbounded caches are a common memory leak source
- Check resource cleanup in file I/O code

## Real-World Provenance

This task is inspired by two real GitHub issues:

- **pandas-dev/pandas#36665** — unbounded internal cache growth in long-running DataFrame processing pipelines:
  https://github.com/pandas-dev/pandas/issues/36665
- **CPython bpo-43498** — `functools.lru_cache` retains references to arguments and return values (including large objects) indefinitely unless bounded with `maxsize` or explicitly cleared:
  https://bugs.python.org/issue43498

The misleading hint ("heap profiler pointed at DataFrames") mirrors the pandas issue's diagnostic misdirection: DataFrames appear as the top heap consumers, but the root cause is the unbounded cache holding references to them, not the DataFrames themselves. The missing file-handle cleanup in `reader.py` is a secondary leak matching resource-management bugs documented across both issues.

See [`../PROVENANCE.md`](../PROVENANCE.md) for full details.
