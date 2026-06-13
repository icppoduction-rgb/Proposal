"""Shared quality check result contracts for Stage Two."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QualityCheckResult:
    """One data quality or leakage check result."""

    check_name: str
    status: str
    severity: str
    rows_total: int | None = None
    rows_failed: int | None = None
    details: dict[str, Any] | None = None


@dataclass(frozen=True)
class QualityReportResult:
    """Aggregate quality report with saved report paths."""

    check_group: str
    status: str
    severity: str
    report_paths: dict[str, str]
    checks: list[QualityCheckResult]
