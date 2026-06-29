"""Progress callback adapter for Stage Two execution."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from scripts.stage_two.execution.work_unit import WorkUnitResult


ProgressCallback = Callable[[str, dict[str, Any]], None]


class ProgressReporter:
    """Small adapter that keeps executor progress events consistent with CLI progress."""

    def __init__(self, callback: ProgressCallback | None = None) -> None:
        self.callback = callback

    def emit_batch_started(self, *, branch: str, role: str, source_format: str, total: int) -> None:
        self._emit(
            "batch_started",
            branch=branch,
            role=role,
            source_format=source_format,
            total=total,
        )

    def emit_file_processed(self, result: WorkUnitResult, *, current: int, total: int) -> None:
        self._emit(
            "file_processed",
            current=current,
            total=total,
            file_id=result.work_unit.dataset_file_id,
            file_path=result.work_unit.source_path,
            status=result.status,
            artifact_id=result.artifact_id,
            error=result.error,
        )

    def _emit(self, event: str, **payload: Any) -> None:
        if self.callback is not None:
            self.callback(event, payload)
