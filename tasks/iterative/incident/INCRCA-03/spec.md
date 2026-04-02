# INCRCA-03: Memory Leak — Wrong Red Herring

## Overview

The data processing service OOMs (Out of Memory) after approximately 2 hours in production.
RSS grows ~50MB per hour. You must identify and fix the memory leak(s) so that all 8 tests
in `test/test_memory.py` pass, including the memory stability test.

---

## Symptom Details

- Production service RSS grows ~50MB per hour
- OOM kill occurs after ~2 hours (RSS reaches container limit of ~100MB)
- Heap profile shows large pandas DataFrames in memory
- Initial hypothesis: DataFrames are not being released

---

## Root Cause Analysis

### Red Herring — pandas DataFrames
**Location:** `processor/pipeline.py`
**Observation:** Heap profiler shows large DataFrames in memory.
**Reality:** The DataFrames ARE large but they ARE being garbage collected properly.
The issue is that they briefly coexist in memory during batch processing, which looks
like a leak but is not. Fixing DataFrame handling (e.g., explicit `del df` or chunking)
will NOT fix the memory growth trend.

### Root Cause 1 — Unbounded LRU Cache (MAIN LEAK, ~45MB/hour)
**Location:** `processor/cache.py` and `processor/pipeline.py`
**Bug:** A function decorated with `@lru_cache(maxsize=None)` is called with unique
string keys derived from record IDs and timestamps. Because `maxsize=None` means the
cache has no eviction policy, it grows without bound — one entry per unique input ever seen.

```python
# BROKEN: unbounded cache, called with unique keys
@lru_cache(maxsize=None)
def transform_record(record_key: str, config_hash: str) -> dict:
    ...
```

After 2 hours of processing (assuming ~100 records/sec), the cache holds ~720,000 entries,
consuming ~45MB of memory.

**Fix:** Bound the cache:
```python
@lru_cache(maxsize=1000)
def transform_record(record_key: str, config_hash: str) -> dict:
    ...
```

### Root Cause 2 — File Handle Leak (SECONDARY LEAK, ~5MB/hour)
**Location:** `processor/reader.py`
**Bug:** CSV files are opened with `open()` but the file handle is never closed because
there is no `try/finally` or context manager:

```python
# BROKEN: file handle never closed
def read_csv(path: str):
    f = open(path)
    reader = csv.DictReader(f)
    return list(reader)
    # f is never closed — handle leaks
```

Each unprocessed file handle holds an OS file descriptor and a small buffer (~5KB).
Over 2 hours, ~1000 files processed = ~5MB leaked.

**Fix:** Use a context manager:
```python
def read_csv(path: str):
    with open(path) as f:
        reader = csv.DictReader(f)
        return list(reader)
```

---

## Fix Sequence

### Round 1 Fix (red herring — fixes tests 1-6 only, memory tests still fail)
Agents that "fix" the DataFrame issue (e.g., add `del df`, use chunked processing)
will not address the actual memory leaks. Tests 1-6 pass regardless. Tests 7-8 still fail.

### Round 2 Fix (addresses actual leaks — fixes tests 7-8)
- In `processor/cache.py`: change `lru_cache(maxsize=None)` to `lru_cache(maxsize=1000)`
- In `processor/reader.py`: wrap file open in a `with` statement
- All 8 tests pass.

---

## Files

| File | Description |
|------|-------------|
| `processor/pipeline.py` | Main processing pipeline — uses the cache |
| `processor/cache.py` | Cache utilities — `lru_cache(maxsize=None)` bug |
| `processor/reader.py` | CSV reader — file handle leak bug |
| `processor/models.py` | Data models |
| `test/test_memory.py` | 8 tests; run with `pytest test/test_memory.py` |
| `requirements.txt` | Dependencies |

---

## Test Breakdown

| Test | Description | Passes after |
|------|-------------|--------------|
| test_01_pipeline_processes_record | Basic record processing | Always |
| test_02_pipeline_batch | Batch of 10 records processed | Always |
| test_03_cache_returns_consistent | Cache returns same result | Always |
| test_04_reader_parses_csv | CSV reader parses correctly | Always |
| test_05_reader_handles_empty | Empty CSV handled | Always |
| test_06_pipeline_config_variations | Multiple config values | Always |
| test_07_memory_stability | Cache size bounded after 5000 calls with unique keys | lru_cache fix |
| test_08_no_file_handle_leak | File handles closed after read_csv | context manager fix |

---

## Scoring

Score = (passing tests) / 8

A score of 1.0 requires all 8 tests to pass.

---

## Multi-Turn Behavior

- **Round 1:** Agents fix DataFrames (red herring). Tests 1-6 pass (score = 0.75).
  Verifier reports tests 7-8 fail, notes cache and file handle patterns in attestation.
- **Round 2:** Executor fixes `lru_cache` and file handles. All 8 tests pass (score = 1.0).
