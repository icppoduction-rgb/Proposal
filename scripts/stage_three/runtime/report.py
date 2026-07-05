"""Reports for Stage Three feature extraction runtime backend selection."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths
from scripts.stage_three.runtime.backend import BackendSelectionResult
from scripts.stage_three.runtime.memory_guard import MemorySnapshot
from scripts.stage_three.runtime.resources import StageThreeRuntimeSettings


TASK06_REPORT_FILENAME = "Task06-feature-extraction-runtime-backend.md"
PREVIOUS_REPORT_PATH = "Task05-feature-catalog-contract-validator.md"


@dataclass(frozen=True)
class RuntimeBackendReport:
    """Serializable report payload for Task06."""

    status: str
    backend_selection: BackendSelectionResult
    runtime_settings: StageThreeRuntimeSettings
    memory_snapshot: MemorySnapshot
    report_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def save_runtime_backend_reports(report: RuntimeBackendReport) -> RuntimeBackendReport:
    """Write RU and EN Task06 runtime backend reports."""
    paths = build_stage_three_task_report_paths(TASK06_REPORT_FILENAME, create_dirs=True)
    report_paths = {"ru": str(paths.ru), "en": str(paths.en)}
    enriched = RuntimeBackendReport(
        status=report.status,
        backend_selection=report.backend_selection,
        runtime_settings=report.runtime_settings,
        memory_snapshot=report.memory_snapshot,
        report_paths=report_paths,
    )
    payload = enriched.to_dict()
    paths.ru.write_text(_render_ru(payload), encoding="utf-8")
    paths.en.write_text(_render_en(payload), encoding="utf-8")
    return enriched


def _render_ru(payload: dict[str, Any]) -> str:
    selection = payload["backend_selection"]
    settings = payload["runtime_settings"]
    memory = payload["memory_snapshot"]
    profile = settings["resource_profile"]
    gpu = selection["gpu_availability"]
    return (
        "# Task 06 — feature-extraction-runtime-backend\n\n"
        f"- Previous report path: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Validation result: `{payload['status']}`\n"
        f"- Backend selected: `{selection['selected_backend']}`\n"
        f"- Requested backend: `{selection['requested_backend']}`\n"
        f"- GPU availability result: `{gpu['available']}` — {gpu['reason']}\n"
        f"- Fallback reason: `{selection.get('fallback_reason') or ''}`\n\n"
        "## CPU/GPU probe result\n\n"
        f"```json\n{_json(selection.get('probe_result'))}\n```\n\n"
        "## RAM limits and peak memory\n\n"
        f"- Profile: `{profile['name']}`\n"
        f"- Reserved RAM GB: `{profile['reserved_ram_gb']}`\n"
        f"- Soft RAM limit GB: `{profile['soft_ram_limit_gb']}`\n"
        f"- Hard RAM limit GB: `{profile['hard_ram_limit_gb']}`\n"
        f"- GPU soft memory limit GB: `{profile['gpu_memory_soft_limit_gb']}`\n"
        f"- GPU hard memory limit GB: `{profile['gpu_memory_hard_limit_gb']}`\n"
        f"- Available RAM GB: `{memory.get('available_ram_gb')}`\n"
        f"- Peak RSS GB: `{memory.get('peak_rss_gb')}`\n"
        f"- Memory probe: `{memory.get('source')}`\n\n"
        "## Machine-readable details\n\n"
        f"```json\n{_json(payload)}\n```\n"
    )


def _render_en(payload: dict[str, Any]) -> str:
    selection = payload["backend_selection"]
    settings = payload["runtime_settings"]
    memory = payload["memory_snapshot"]
    profile = settings["resource_profile"]
    gpu = selection["gpu_availability"]
    return (
        "# Task 06 — feature-extraction-runtime-backend\n\n"
        f"- Previous report path: `{PREVIOUS_REPORT_PATH}`\n"
        f"- Validation result: `{payload['status']}`\n"
        f"- Backend selected: `{selection['selected_backend']}`\n"
        f"- Requested backend: `{selection['requested_backend']}`\n"
        f"- GPU availability result: `{gpu['available']}` — {gpu['reason']}\n"
        f"- Fallback reason: `{selection.get('fallback_reason') or ''}`\n\n"
        "## CPU/GPU Probe Result\n\n"
        f"```json\n{_json(selection.get('probe_result'))}\n```\n\n"
        "## RAM Limits And Peak Memory\n\n"
        f"- Profile: `{profile['name']}`\n"
        f"- Reserved RAM GB: `{profile['reserved_ram_gb']}`\n"
        f"- Soft RAM limit GB: `{profile['soft_ram_limit_gb']}`\n"
        f"- Hard RAM limit GB: `{profile['hard_ram_limit_gb']}`\n"
        f"- GPU soft memory limit GB: `{profile['gpu_memory_soft_limit_gb']}`\n"
        f"- GPU hard memory limit GB: `{profile['gpu_memory_hard_limit_gb']}`\n"
        f"- Available RAM GB: `{memory.get('available_ram_gb')}`\n"
        f"- Peak RSS GB: `{memory.get('peak_rss_gb')}`\n"
        f"- Memory probe: `{memory.get('source')}`\n\n"
        "## Machine-readable Details\n\n"
        f"```json\n{_json(payload)}\n```\n"
    )


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default)


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    return str(value)
