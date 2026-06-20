"""Performance counters for Stage Two normalization runs."""

from __future__ import annotations

import time
import tracemalloc
from dataclasses import asdict, dataclass


@dataclass
class NormalizationPerformance:
    """Mutable timing and throughput counters for one normalized file."""

    input_size_bytes: int | None = None
    rows_read: int = 0
    events_emitted: int = 0
    output_parts_count: int = 0
    parse_seconds: float = 0.0
    parquet_write_seconds: float = 0.0
    catalog_seconds: float = 0.0
    total_seconds: float = 0.0
    peak_memory_bytes: int | None = None

    def payload(self) -> dict[str, object]:
        """Return a JSON-safe performance payload with derived rates."""
        input_mb = (self.input_size_bytes or 0) / (1024 * 1024)
        total = self.total_seconds if self.total_seconds > 0 else 0.0
        parse = self.parse_seconds if self.parse_seconds > 0 else total
        payload = asdict(self)
        payload.update(
            {
                "input_size_mb": round(input_mb, 3),
                "rows_per_sec": _rate(self.rows_read, parse),
                "packets_per_sec": _rate(self.rows_read, parse),
                "events_per_sec": _rate(self.events_emitted, parse),
                "mb_per_sec": _rate(input_mb, total),
                "peak_memory_mb": (
                    round(self.peak_memory_bytes / (1024 * 1024), 3)
                    if self.peak_memory_bytes is not None
                    else None
                ),
            }
        )
        return payload


class PerfTimer:
    """Simple context timer that accumulates elapsed seconds on an object attribute."""

    def __init__(self, performance: NormalizationPerformance, field_name: str) -> None:
        self.performance = performance
        self.field_name = field_name
        self.started_at = 0.0

    def __enter__(self) -> "PerfTimer":
        self.started_at = time.perf_counter()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        elapsed = time.perf_counter() - self.started_at
        current = getattr(self.performance, self.field_name)
        setattr(self.performance, self.field_name, current + elapsed)


class MemoryTracker:
    """Track peak Python memory allocations for one normalization run."""

    def __enter__(self) -> "MemoryTracker":
        self._started_here = not tracemalloc.is_tracing()
        if self._started_here:
            tracemalloc.start()
        self._start_current, self._start_peak = tracemalloc.get_traced_memory()
        self.peak_bytes: int | None = None
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        _current, peak = tracemalloc.get_traced_memory()
        self.peak_bytes = max(0, peak - self._start_current)
        if self._started_here:
            tracemalloc.stop()


def _rate(value: float, seconds: float) -> float | None:
    if seconds <= 0:
        return None
    return round(value / seconds, 3)
