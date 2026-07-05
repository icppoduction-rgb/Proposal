"""Build Stage Three report paths from config.py storage settings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config import REPORTS_EN_STAGE_THREE, REPORTS_RU_STAGE_THREE


@dataclass(frozen=True)
class StageThreeReportPaths:
    """Resolved RU and EN report paths for one Stage Three report."""

    ru: Path
    en: Path


def ensure_stage_three_report_dirs() -> None:
    """Create Stage Three report directories configured through PATH_DATA_STORAGE."""
    for report_dir in _stage_three_report_dirs():
        report_dir.mkdir(parents=True, exist_ok=True)


def build_stage_three_task_report_paths(filename: str, *, create_dirs: bool = False) -> StageThreeReportPaths:
    """Return RU and EN paths for a Stage Three report filename."""
    if not filename.strip():
        raise ValueError("filename must not be empty")
    if Path(filename).name != filename:
        raise ValueError("filename must be a file name, not a path")
    if create_dirs:
        ensure_stage_three_report_dirs()
    return StageThreeReportPaths(
        ru=Path(_required_report_root(REPORTS_RU_STAGE_THREE, "REPORTS_RU_STAGE_THREE")) / filename,
        en=Path(_required_report_root(REPORTS_EN_STAGE_THREE, "REPORTS_EN_STAGE_THREE")) / filename,
    )


def _stage_three_report_dirs() -> tuple[Path, Path]:
    return (
        Path(_required_report_root(REPORTS_RU_STAGE_THREE, "REPORTS_RU_STAGE_THREE")),
        Path(_required_report_root(REPORTS_EN_STAGE_THREE, "REPORTS_EN_STAGE_THREE")),
    )


def _required_report_root(value: str, name: str) -> str:
    if not value.strip():
        raise RuntimeError(f"{name} is empty; configure PATH_DATA_STORAGE before resolving Stage Three reports")
    return value

