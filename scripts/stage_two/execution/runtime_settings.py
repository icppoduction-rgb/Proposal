"""Resolved execution settings for bounded Stage Two worker pools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutionRuntimeSettings:
    """Worker pool and queue bounds derived from normalization options."""

    max_workers: int
    max_pending_futures: int

    @classmethod
    def from_options(
        cls,
        options: Any,
        *,
        selected_units: int | None = None,
        pending_multiplier: int = 4,
    ) -> "ExecutionRuntimeSettings":
        """Build bounded runtime settings from already validated normalization options."""
        if pending_multiplier <= 0:
            raise ValueError("pending_multiplier must be a positive integer")
        max_workers = max(options.workers, 1)
        if selected_units is not None and selected_units > 0:
            max_workers = min(max_workers, selected_units)
        max_pending = max(max_workers * pending_multiplier, max_workers, 1)
        return cls(max_workers=max_workers, max_pending_futures=max_pending)
