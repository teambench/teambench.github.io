"""
Test suite for the processing pipeline memory behavior.
Tests 1-6: functional correctness (always pass)
Test 7: cache size bounded after many unique-key calls (requires lru_cache fix)
Test 8: no file handle leak after read_csv (requires context manager fix)

Run: pytest test/test_memory.py -v
"""

import sys
import os
import csv
import gc
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

from processor.models import Record, PipelineConfig
from processor.pipeline import process_record, process_batch
from processor.cache import transform_record, get_cache_info, clear_cache
from processor.reader import read_csv, read_csv_string


# ---------------------------------------------------------------------------
# Tests 1-6: Functional (always pass, regardless of memory fixes)
# ---------------------------------------------------------------------------

def test_01_pipeline_processes_record():
    """Basic: pipeline processes a single record without error."""
    clear_cache()
    record = Record(id="rec_001", source="test", payload={"Name": "Alice", "Score": "42"})
    config = PipelineConfig()
    result = process_record(record, config)
    assert result.id == "rec_001"
    assert result.checksum is not None
    assert len(result.checksum) > 0


def test_02_pipeline_batch():
    """Batch of 10 records all processed."""
    clear_cache()
    records = [
        Record(id=f"rec_{i:03d}", source="batch_test", payload={"value": str(i)})
        for i in range(10)
    ]
    config = PipelineConfig(batch_size=10)
    results = process_batch(records, config)
    assert len(results) == 10
    ids = {r.id for r in results}
    assert ids == {f"rec_{i:03d}" for i in range(10)}


def test_03_cache_returns_consistent():
    """Same (key, config) inputs return the same transformed output."""
    clear_cache()
    # Call with a fixed key (not unique timestamp) to test consistency
    result_a = transform_record("fixed_key_abc", "conf_001")
    result_b = transform_record("fixed_key_abc", "conf_001")
    assert result_a == result_b
    assert result_a["checksum"] == result_b["checksum"]


def test_04_reader_parses_csv():
    """CSV reader correctly parses a simple file."""
    content = "name,score,active\nAlice,95,true\nBob,87,false\n"
    rows = read_csv_string(content)
    assert len(rows) == 2
    assert rows[0]["name"] == "Alice"
    assert rows[1]["score"] == "87"


def test_05_reader_handles_empty():
    """CSV reader returns empty list for header-only file."""
    content = "name,score\n"
    rows = read_csv_string(content)
    assert rows == []


def test_06_pipeline_config_variations():
    """Pipeline handles different config combinations."""
    clear_cache()
    record = Record(
        id="rec_cfg",
        source="config_test",
        payload={"Name": "Test", "Value": None, "Score": "10"},
    )

    # With drop_nulls=True, None values should be dropped
    config_drop = PipelineConfig(normalize=True, drop_nulls=True)
    result_drop = process_record(record, config_drop)
    assert "value" not in result_drop.transformed or result_drop.transformed.get("value") is not None

    # With normalize=False, keys stay as-is
    config_no_norm = PipelineConfig(normalize=False, drop_nulls=False)
    result_no_norm = process_record(record, config_no_norm)
    assert result_no_norm.id == "rec_cfg"


# ---------------------------------------------------------------------------
# Test 7: Memory stability — cache must be bounded (requires lru_cache fix)
# ---------------------------------------------------------------------------

def test_07_memory_stability():
    """
    After calling transform_record with 5000 unique keys, the cache size
    must be bounded (maxsize must not be None, and currsize <= maxsize).

    With lru_cache(maxsize=None): currsize will grow to 5000+ — FAIL.
    With lru_cache(maxsize=1000): currsize will be capped at 1000 — PASS.
    """
    clear_cache()

    n_calls = 5000
    for i in range(n_calls):
        # Unique key each time (simulates production behavior)
        transform_record(f"unique_key_{i}", "conf_test")

    info = get_cache_info()

    assert info["maxsize"] is not None, (
        "lru_cache maxsize is None — cache is unbounded and will grow forever. "
        "Fix: change @lru_cache(maxsize=None) to @lru_cache(maxsize=1000) in cache.py"
    )

    assert info["currsize"] <= info["maxsize"], (
        f"Cache size {info['currsize']} exceeds maxsize {info['maxsize']}. "
        "This should not happen with a bounded LRU cache."
    )

    assert info["currsize"] <= 1500, (
        f"Cache size {info['currsize']} after {n_calls} unique calls suggests unbounded growth. "
        "Fix: change @lru_cache(maxsize=None) to @lru_cache(maxsize=1000) in cache.py"
    )

    clear_cache()


# ---------------------------------------------------------------------------
# Test 8: No file handle leak (requires context manager fix in reader.py)
# ---------------------------------------------------------------------------

def test_08_no_file_handle_leak():
    """
    After calling read_csv() many times, open file descriptors must not grow.

    With the bug (no context manager): each call leaks a file handle.
    With the fix (with open(...)): handles are closed immediately after use.

    We check this by inspecting /proc/self/fd (Linux) or using psutil.
    """
    import gc

    # Create a real temp CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        writer = csv.writer(tmp)
        writer.writerow(["id", "value"])
        for i in range(5):
            writer.writerow([f"row_{i}", str(i * 10)])
        tmp_path = tmp.name

    try:
        # Count open fds before
        gc.collect()
        fd_before = _count_open_fds()

        # Call read_csv many times
        n_reads = 50
        for _ in range(n_reads):
            rows = read_csv(tmp_path)
            assert len(rows) == 5

        # Force GC to close any handles that CPython would auto-close
        gc.collect()

        fd_after = _count_open_fds()

        # With the bug, fd_after - fd_before will be ~50 (one per call, not GC'd yet)
        # With the fix, fd_after - fd_before should be 0 or very small (GC noise)
        leaked = fd_after - fd_before
        assert leaked <= 5, (
            f"File descriptor leak detected: {leaked} handles still open after {n_reads} read_csv() calls. "
            "Fix: use 'with open(path) as f:' in reader.py instead of bare open()"
        )
    finally:
        os.unlink(tmp_path)


def _count_open_fds() -> int:
    """Count open file descriptors for the current process."""
    # Try /proc/self/fd first (Linux)
    proc_fd = "/proc/self/fd"
    if os.path.isdir(proc_fd):
        try:
            return len(os.listdir(proc_fd))
        except PermissionError:
            pass

    # Fall back to psutil
    try:
        import psutil
        proc = psutil.Process(os.getpid())
        return proc.num_fds()
    except Exception:
        pass

    # Last resort: iterate /proc/self/fd with os.scandir
    try:
        return sum(1 for _ in os.scandir(proc_fd))
    except Exception:
        return 0
