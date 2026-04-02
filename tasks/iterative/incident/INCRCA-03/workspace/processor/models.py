"""
Data models for the processing pipeline.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Record:
    """A single data record to be processed."""
    id: str
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class ProcessedRecord:
    """A record after transformation."""
    id: str
    source: str
    transformed: Dict[str, Any] = field(default_factory=dict)
    checksum: Optional[str] = None


@dataclass
class PipelineConfig:
    """Configuration for a pipeline run."""
    batch_size: int = 100
    normalize: bool = True
    drop_nulls: bool = True
    output_format: str = "json"

    def hash(self) -> str:
        """Stable hash of this config for cache keys."""
        import hashlib
        s = f"{self.batch_size}:{self.normalize}:{self.drop_nulls}:{self.output_format}"
        return hashlib.md5(s.encode()).hexdigest()[:8]
