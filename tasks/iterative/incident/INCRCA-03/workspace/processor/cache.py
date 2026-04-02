"""
Caching utilities for the processing pipeline.

BUG: Uses @lru_cache(maxsize=None) on a function that is called with unique
string keys (record IDs + timestamps). Because maxsize=None disables eviction,
the cache grows without bound — one entry per unique input ever seen.

After 2 hours of processing at ~100 records/sec, the cache holds ~720,000 entries
consuming approximately 45MB of memory.

Fix: Change lru_cache(maxsize=None) to lru_cache(maxsize=1000).
"""

import hashlib
from functools import lru_cache


# BUG: maxsize=None means no eviction — cache grows forever
# Fix: change to @lru_cache(maxsize=1000)
@lru_cache(maxsize=None)
def transform_record(record_key: str, config_hash: str) -> dict:
    """
    Compute a transformation for a record identified by record_key,
    under a given pipeline config hash.

    This function is called with record_key = f"{record.id}:{timestamp}"
    which makes every call unique, causing the cache to never evict entries.

    Args:
        record_key:  Unique string identifying this record (id + timestamp)
        config_hash: Hash of the pipeline configuration

    Returns:
        Dict of transformed fields
    """
    # Simulate some computation
    checksum = hashlib.sha256(f"{record_key}:{config_hash}".encode()).hexdigest()[:16]
    return {
        "checksum": checksum,
        "normalized_key": record_key.lower().replace(" ", "_"),
        "config": config_hash,
    }


def get_cache_info():
    """Return cache statistics for monitoring."""
    info = transform_record.cache_info()
    return {
        "hits": info.hits,
        "misses": info.misses,
        "maxsize": info.maxsize,
        "currsize": info.currsize,
    }


def clear_cache():
    """Clear the transform cache (for testing)."""
    transform_record.cache_clear()
