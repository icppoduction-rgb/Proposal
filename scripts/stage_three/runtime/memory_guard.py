"""Memory guard utilities for bounded Stage Three batch processing."""

from __future__ import annotations

import os
from dataclasses import dataclass
from time import perf_counter
from typing import Any


GB = 1024**3


class MemoryGuardError(RuntimeError):
    """Raised when Stage Three must stop before violating RAM safety limits."""


@dataclass(frozen=True)
class MemorySnapshot:
    """Process/system memory snapshot."""

    available_ram_gb: float | None
    rss_gb: float | None
    peak_rss_gb: float | None
    source: str


@dataclass(frozen=True)
class MemoryGuardDecision:
    """Decision made before processing a batch."""

    action: str
    batch_rows: int
    reason: str
    snapshot: MemorySnapshot


@dataclass(frozen=True)
class BatchRuntimeMetric:
    """Runtime metric for one processed batch."""

    backend: str
    batch_index: int
    batch_rows: int
    elapsed_seconds: float
    rss_gb: float | None
    peak_rss_gb: float | None


class MemoryGuard:
    """Check free RAM before every batch and track process RSS peaks."""

    def __init__(
        self,
        *,
        reserved_ram_gb: int,
        soft_ram_limit_gb: int,
        hard_ram_limit_gb: int,
        min_batch_rows: int = 1_000,
        reduction_factor: float = 0.5,
        psutil_module: Any | None = None,
    ) -> None:
        if reserved_ram_gb < 1:
            raise ValueError("reserved_ram_gb must be positive")
        if soft_ram_limit_gb > hard_ram_limit_gb:
            raise ValueError("soft_ram_limit_gb must be less than or equal to hard_ram_limit_gb")
        if min_batch_rows < 1:
            raise ValueError("min_batch_rows must be positive")
        if not 0 < reduction_factor < 1:
            raise ValueError("reduction_factor must be in (0, 1)")
        self.reserved_ram_gb = reserved_ram_gb
        self.soft_ram_limit_gb = soft_ram_limit_gb
        self.hard_ram_limit_gb = hard_ram_limit_gb
        self.min_batch_rows = min_batch_rows
        self.reduction_factor = reduction_factor
        self._psutil = self._resolve_psutil(psutil_module)
        self._peak_rss_gb: float | None = None
        self._batch_starts: dict[int, float] = {}

    @property
    def peak_rss_gb(self) -> float | None:
        return self._peak_rss_gb

    def snapshot(self) -> MemorySnapshot:
        """Return a live memory snapshot, or static fallback when psutil is missing."""
        if self._psutil is None:
            return MemorySnapshot(
                available_ram_gb=None,
                rss_gb=None,
                peak_rss_gb=self._peak_rss_gb,
                source="static-fallback",
            )
        virtual_memory = self._psutil.virtual_memory()
        process = self._psutil.Process(os.getpid())
        rss_gb = float(process.memory_info().rss / GB)
        if self._peak_rss_gb is None or rss_gb > self._peak_rss_gb:
            self._peak_rss_gb = rss_gb
        return MemorySnapshot(
            available_ram_gb=float(virtual_memory.available / GB),
            rss_gb=rss_gb,
            peak_rss_gb=self._peak_rss_gb,
            source="psutil",
        )

    def check_before_batch(self, requested_batch_rows: int) -> MemoryGuardDecision:
        """Return a safe batch decision; raise only for invalid input."""
        if requested_batch_rows < 1:
            raise ValueError("requested_batch_rows must be positive")
        snapshot = self.snapshot()
        if snapshot.available_ram_gb is None:
            return MemoryGuardDecision(
                action="proceed",
                batch_rows=requested_batch_rows,
                reason="live available RAM is unavailable; proceeding with configured batch size",
                snapshot=snapshot,
            )
        if snapshot.available_ram_gb >= self.reserved_ram_gb:
            return MemoryGuardDecision(
                action="proceed",
                batch_rows=requested_batch_rows,
                reason="available RAM is above reserved floor",
                snapshot=snapshot,
            )
        reduced = max(self.min_batch_rows, int(requested_batch_rows * self.reduction_factor))
        if requested_batch_rows > self.min_batch_rows and reduced < requested_batch_rows:
            return MemoryGuardDecision(
                action="reduce",
                batch_rows=reduced,
                reason=(
                    "available RAM is below reserved floor; reduce batch size before "
                    "continuing"
                ),
                snapshot=snapshot,
            )
        return MemoryGuardDecision(
            action="fail",
            batch_rows=requested_batch_rows,
            reason="available RAM is below reserved floor and batch size cannot be reduced",
            snapshot=snapshot,
        )

    def ensure_batch_allowed(self, requested_batch_rows: int) -> MemoryGuardDecision:
        """Return a decision or fail safely when RAM is below the floor."""
        decision = self.check_before_batch(requested_batch_rows)
        if decision.action == "fail":
            available = decision.snapshot.available_ram_gb
            available_text = "unknown" if available is None else f"{available:.2f} GB"
            raise MemoryGuardError(
                "Stage Three memory guard stopped before processing a batch: "
                f"{available_text} available, {self.reserved_ram_gb} GB reserved floor"
            )
        return decision

    def start_batch_timer(self, batch_index: int) -> None:
        self._batch_starts[batch_index] = perf_counter()

    def finish_batch_metric(
        self,
        *,
        backend: str,
        batch_index: int,
        batch_rows: int,
    ) -> BatchRuntimeMetric:
        """Return elapsed/RSS metric for a completed batch."""
        started_at = self._batch_starts.pop(batch_index, perf_counter())
        snapshot = self.snapshot()
        return BatchRuntimeMetric(
            backend=backend,
            batch_index=batch_index,
            batch_rows=batch_rows,
            elapsed_seconds=perf_counter() - started_at,
            rss_gb=snapshot.rss_gb,
            peak_rss_gb=snapshot.peak_rss_gb,
        )

    @staticmethod
    def _resolve_psutil(psutil_module: Any | None) -> Any | None:
        if psutil_module is False:
            return None
        if psutil_module is not None:
            return psutil_module
        try:
            import psutil
        except ImportError:
            return None
        return psutil
