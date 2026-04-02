"""
CSV file reader for the processing pipeline.

BUG: Opens files without a context manager — file handles are never closed.
Each call to read_csv() leaks one OS file descriptor and a ~5KB buffer.
Over 2 hours (~1000 files processed), this accumulates to ~5MB leaked memory
and may exhaust the OS file descriptor limit.

Fix: Wrap open() in a with statement:
    with open(path) as f:
        reader = csv.DictReader(f)
        return list(reader)
"""

import csv
import io
import os
from typing import List, Dict


def read_csv(path: str) -> List[Dict[str, str]]:
    """
    Read a CSV file and return a list of row dicts.

    BUG: File handle `f` is never closed. The garbage collector may
    eventually close it, but under CPython this is non-deterministic
    and under PyPy/other runtimes the handle leaks indefinitely.

    Args:
        path: Path to the CSV file.

    Returns:
        List of dicts, one per row (header row used as keys).
    """
    # BUG: no context manager — f is never explicitly closed
    f = open(path)                     # noqa: WPS515 (intentional bug)
    reader = csv.DictReader(f)
    rows = list(reader)
    # Missing: f.close() or 'with open(path) as f:'
    return rows


def read_csv_string(content: str) -> List[Dict[str, str]]:
    """
    Parse CSV from a string. Used for in-memory data (no file handle issue here).
    """
    f = io.StringIO(content)
    reader = csv.DictReader(f)
    return list(reader)


def write_csv(path: str, rows: List[Dict], fieldnames: List[str] = None) -> None:
    """
    Write rows to a CSV file. Correctly uses a context manager.
    """
    if not rows:
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
