"""
Main processing pipeline.

Processes records in batches. Uses the transform_record cache from cache.py.

Note on the pandas red herring:
  Heap profiling shows large DataFrames in memory during processing. These are
  legitimate — DataFrames are created per-batch and ARE released after each batch.
  The actual memory leak is in the unbounded lru_cache in cache.py, not here.
"""

import time
import hashlib
from typing import List, Optional

from processor.models import Record, ProcessedRecord, PipelineConfig
from processor.cache import transform_record


def _make_record_key(record: Record) -> str:
    """
    Generate a cache key for a record.

    NOTE: This includes a timestamp component, making every key unique.
    This is intentional in production (records are time-stamped), but it means
    the lru_cache in cache.py will never get a cache hit, and with maxsize=None
    will grow without bound.
    """
    # Using record.id + processing timestamp makes the key unique per call
    ts = str(int(time.time() * 1000))
    return f"{record.id}:{record.source}:{ts}"


def process_record(record: Record, config: PipelineConfig) -> ProcessedRecord:
    """
    Process a single record through the transformation pipeline.

    Args:
        record:  The record to process.
        config:  Pipeline configuration.

    Returns:
        ProcessedRecord with transformation applied.
    """
    record_key = _make_record_key(record)
    config_hash = config.hash()

    # This call grows the cache unboundedly because record_key is always unique
    transformed = transform_record(record_key, config_hash)

    # Apply normalization
    payload = dict(record.payload)
    if config.normalize:
        payload = {k.lower(): v for k, v in payload.items()}
    if config.drop_nulls:
        payload = {k: v for k, v in payload.items() if v is not None}

    return ProcessedRecord(
        id=record.id,
        source=record.source,
        transformed={**payload, **transformed},
        checksum=transformed["checksum"],
    )


def process_batch(records: List[Record], config: Optional[PipelineConfig] = None) -> List[ProcessedRecord]:
    """
    Process a batch of records.

    In production, this processes DataFrames too — but the DataFrames are
    released after each batch (not the source of the memory leak).

    Args:
        records: List of records to process.
        config:  Pipeline configuration (default if None).

    Returns:
        List of ProcessedRecord objects.
    """
    if config is None:
        config = PipelineConfig()

    results = []
    for record in records:
        processed = process_record(record, config)
        results.append(processed)

    return results
