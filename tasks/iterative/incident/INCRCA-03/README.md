# INCRCA-03: Memory Leak — Wrong Red Herring

## Description

The data processing service OOMs after ~2 hours. RSS grows ~50MB/hour.
A heap profile points to pandas DataFrames (red herring — they are collected correctly).
The actual root causes are an unbounded `lru_cache(maxsize=None)` called with unique
keys (growing forever) and a file handle leak in the CSV reader. Agents that fix
DataFrames alone still fail tests 7-8. The verifier's attestation after round 1
must point to the cache and file handle issues.

## What Makes This Hard

- Heap profiler evidence is misleading — DataFrames look suspicious but are fine
- `lru_cache(maxsize=None)` is a common Python idiom that looks harmless
- The cache key includes a timestamp, so every call is a cache miss — but the entries never evict
- File handle leaks are invisible to most profilers
- Round 1 agents almost always chase the red herring

## Task Structure

```
workspace/
  processor/
    pipeline.py  # uses transform_record with unique keys (feeds the leak)
    cache.py     # BUG: lru_cache(maxsize=None) — fix to lru_cache(maxsize=1000)
    reader.py    # BUG: open() without context manager — fix to with open(...)
    models.py    # data models
  test/
    test_memory.py  # 8 tests including memory stability and fd leak tests
  requirements.txt
```

## Running the Tests

```bash
cd workspace
pip install -r requirements.txt
pytest test/test_memory.py -v
```

Expected baseline output (unfixed):
```
PASSED  test_01 through test_06  (6 functional tests)
FAILED  test_07_memory_stability
FAILED  test_08_no_file_handle_leak
```

## Scoring

Score = passing_tests / 8

| Score | State |
|-------|-------|
| 1.0 | All 8 pass (both fixes applied) |
| 0.75 | Tests 1-6 pass (red herring fix or no fix) |
| 0.75 | Tests 1-6 pass (one of two real fixes) |

Run grader:
```bash
bash grader.sh
```

## Expected Scores by Agent Type

| Agent Type | Expected Score | Rationale |
|------------|---------------|-----------|
| Oracle (spec-aware) | 0.45 | Fixes DataFrames (red herring); tests 7-8 still fail |
| Single-pass | 0.55 | May fix one of two real issues |
| Multi-turn (2 rounds) | 1.00 | Round 2 fixes cache + file handles after verifier feedback |

## Stopping Condition

`8 passed` in pytest output.

## Multi-Turn Attestation Hint

After round 1, the Verifier should note:
- Tests 1-6 pass (6/8)
- Test 7 fails: `cache.currsize` grows to 5000 — `lru_cache(maxsize=None)` is unbounded
- Test 8 fails: file descriptor count grows — `open()` in `reader.py` not closed

## Generating Variants

```bash
python generator.py --seed 42 --output-dir ./workspace_seed42
```
