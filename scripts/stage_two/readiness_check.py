"""Final readiness checks for Stage Two normalization."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from config import (
    ALEMBIC_INI_PATH,
    PATH_DATA_STORAGE,
    REPORTS_EN_STAGE_TWO,
    REPORTS_RU_STAGE_TWO,
    STAGE_TWO_READINESS_DB_YIELD_PER,
    STAGE_TWO_READINESS_HASH_CHUNK_BYTES,
)
from scripts.db import session_scope
from scripts.db.models import (
    DataQualityReport,
    Dataset,
    DatasetFile,
    FeatureArtifact,
    ModelReadyArtifact,
    NormalizedArtifact,
    ParserRegistry,
    SchemaVersion,
)
from scripts.db.repositories import ParserRepository
from scripts.stage_two.storage.bootstrap import StorageBootstrapper
from scripts.stage_two.traceability import TraceabilityError, TraceabilityService

try:
    from rich.console import Console
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
except ModuleNotFoundError:
    BarColumn = None  # type: ignore[assignment]
    Console = None  # type: ignore[assignment]
    Progress = None  # type: ignore[assignment]
    SpinnerColumn = None  # type: ignore[assignment]
    TextColumn = None  # type: ignore[assignment]
    TimeElapsedColumn = None  # type: ignore[assignment]

ProgressCallback = Callable[[str, dict[str, Any]], None]


@dataclass(frozen=True)
class StageTwoReadinessResult:
    """Serializable Stage Two readiness result."""

    status: str
    checks: dict[str, Any]
    report_paths: dict[str, str]


def run_stage_two_readiness_check(
    progress_callback: ProgressCallback | None = None,
) -> StageTwoReadinessResult:
    """Run final Stage Two readiness checks and save RU/EN reports."""
    storage_root = _configured_storage_root()
    checks: dict[str, Any] = {}
    _run_named_check(checks, "migrations", _migration_check, progress_callback)
    _run_named_check(checks, "storage_paths", lambda: _storage_path_check(storage_root), progress_callback)
    with session_scope() as session:
        _run_named_check(checks, "catalog_counts", lambda: _catalog_counts(session), progress_callback)
        _run_named_check(checks, "schema_versions", lambda: _schema_version_check(session), progress_callback)
        _run_named_check(checks, "parser_coverage", lambda: _parser_coverage(session), progress_callback)
        _run_named_check(
            checks,
            "normalized_artifacts",
            lambda: _normalized_artifact_check(session),
            progress_callback,
        )
        _run_named_check(
            checks,
            "artifact_registration",
            lambda: _artifact_registration_check(session),
            progress_callback,
        )
        _run_named_check(
            checks,
            "quality_leakage_reports",
            lambda: _quality_leakage_check(session),
            progress_callback,
        )
        _run_named_check(checks, "traceability", lambda: _traceability_check(session), progress_callback)
        _run_named_check(
            checks,
            "raw_files",
            lambda: _raw_file_hash_check(session, progress_callback=progress_callback),
            progress_callback,
        )

    status = "SUCCESS" if _all_checks_success(checks) else "FAILED"
    result = StageTwoReadinessResult(status=status, checks=checks, report_paths={})
    _emit(progress_callback, "report_started", status=status)
    report_paths = _save_reports(storage_root, result)
    _emit(progress_callback, "report_finished", status=status, report_paths=report_paths)
    return StageTwoReadinessResult(status=status, checks=checks, report_paths=report_paths)


def _run_named_check(
    checks: dict[str, Any],
    name: str,
    callback: Callable[[], dict[str, Any]],
    progress_callback: ProgressCallback | None,
) -> None:
    _emit(progress_callback, "check_started", check_name=name)
    result = callback()
    checks[name] = result
    _emit(progress_callback, "check_finished", check_name=name, status=result.get("status"))


def _configured_storage_root() -> Path:
    if not PATH_DATA_STORAGE.strip():
        raise ValueError("PATH_DATA_STORAGE must be configured for readiness checks.")
    return Path(PATH_DATA_STORAGE).expanduser()


def _migration_check() -> dict[str, Any]:
    config = Config(ALEMBIC_INI_PATH)
    script = ScriptDirectory.from_config(config)
    expected_heads = sorted(script.get_heads())
    with session_scope() as session:
        applied = sorted(row[0] for row in session.execute(text("SELECT version_num FROM alembic_version")).all())
    return {
        "status": "SUCCESS" if applied == expected_heads else "FAILED",
        "expected_heads": expected_heads,
        "applied_versions": applied,
    }


def _storage_path_check(storage_root: Path) -> dict[str, Any]:
    missing = [
        relative_path.as_posix()
        for relative_path in StorageBootstrapper.required_relative_paths()
        if not (storage_root / relative_path).exists()
    ]
    return {
        "status": "SUCCESS" if not missing else "FAILED",
        "storage_root": str(storage_root),
        "missing_paths": missing,
        "required_path_count": len(StorageBootstrapper.required_relative_paths()),
    }


def _catalog_counts(session: Session) -> dict[str, Any]:
    tables = {
        "datasets": Dataset,
        "dataset_files": DatasetFile,
        "parser_registry": ParserRegistry,
        "normalized_artifacts": NormalizedArtifact,
        "feature_artifacts": FeatureArtifact,
        "model_ready_artifacts": ModelReadyArtifact,
        "data_quality_reports": DataQualityReport,
        "schema_versions": SchemaVersion,
    }
    counts = {
        name: session.execute(select(func.count()).select_from(model)).scalar_one()
        for name, model in tables.items()
    }
    required_non_empty = (
        "datasets",
        "dataset_files",
        "parser_registry",
        "normalized_artifacts",
        "feature_artifacts",
        "model_ready_artifacts",
        "data_quality_reports",
        "schema_versions",
    )
    missing = [name for name in required_non_empty if counts[name] == 0]
    return {"status": "SUCCESS" if not missing else "FAILED", "counts": counts, "empty_required_tables": missing}


def _schema_version_check(session: Session) -> dict[str, Any]:
    schema = session.execute(
        select(SchemaVersion).where(
            SchemaVersion.schema_name == "normalized_event",
            SchemaVersion.schema_version == "v1",
            SchemaVersion.layer == "normalized",
            SchemaVersion.branch.is_(None),
            SchemaVersion.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if schema is None:
        return {"status": "FAILED", "error": "Active normalized_event v1 schema was not found."}
    return {
        "status": "SUCCESS",
        "schema_version_id": schema.id,
        "schema_name": schema.schema_name,
        "schema_version": schema.schema_version,
        "layer": schema.layer,
        "schema_path": schema.schema_path,
    }


def _parser_coverage(session: Session) -> dict[str, Any]:
    repository = ParserRepository(session)
    combinations = session.execute(
        select(
            DatasetFile.branch,
            DatasetFile.role,
            DatasetFile.source_format,
        )
        .distinct()
        .order_by(DatasetFile.branch, DatasetFile.role, DatasetFile.source_format)
    ).all()
    uncovered = []
    covered = []
    for branch, role, source_format in combinations:
        parser = repository.resolve_parser(branch=branch, role=role, source_format=source_format)
        row = {"branch": branch, "role": role, "source_format": source_format}
        if parser is None:
            uncovered.append(row)
        else:
            covered.append({**row, "parser_name": parser.parser_name, "parser_version": parser.parser_version})
    return {
        "status": "SUCCESS" if not uncovered else "FAILED",
        "covered": covered,
        "uncovered": uncovered,
    }


def _normalized_artifact_check(session: Session) -> dict[str, Any]:
    counts = {
        status: count
        for status, count in session.execute(
            select(NormalizedArtifact.status, func.count()).group_by(NormalizedArtifact.status)
        ).all()
    }
    failed = sum(count for status, count in counts.items() if status in {"FAILED", "BLOCKED"})
    total = sum(counts.values())
    return {"status": "SUCCESS" if total > 0 and failed == 0 else "FAILED", "total": total, "by_status": counts}


def _artifact_registration_check(session: Session) -> dict[str, Any]:
    feature_without_normalized = session.execute(
        select(func.count()).select_from(FeatureArtifact).where(FeatureArtifact.normalized_artifact_id.is_(None))
    ).scalar_one()
    model_ready_without_feature = session.execute(
        select(func.count()).select_from(ModelReadyArtifact).where(ModelReadyArtifact.feature_artifact_id.is_(None))
    ).scalar_one()
    counts = _catalog_counts(session)["counts"]
    failed = feature_without_normalized + model_ready_without_feature
    return {
        "status": "SUCCESS" if failed == 0 and counts["feature_artifacts"] > 0 and counts["model_ready_artifacts"] > 0 else "FAILED",
        "feature_without_normalized": feature_without_normalized,
        "model_ready_without_feature": model_ready_without_feature,
        "counts": {
            "normalized_artifacts": counts["normalized_artifacts"],
            "feature_artifacts": counts["feature_artifacts"],
            "model_ready_artifacts": counts["model_ready_artifacts"],
        },
    }


def _quality_leakage_check(session: Session) -> dict[str, Any]:
    report_counts = {
        group: count
        for group, count in session.execute(
            select(DataQualityReport.check_group, func.count()).group_by(DataQualityReport.check_group)
        ).all()
    }
    critical_leakage = session.execute(
        select(func.count())
        .select_from(DataQualityReport)
        .where(
            DataQualityReport.check_group == "leakage",
            DataQualityReport.severity == "CRITICAL",
            DataQualityReport.status.in_(("FAILED", "BLOCKED")),
        )
    ).scalar_one()
    return {
        "status": "SUCCESS" if report_counts and critical_leakage == 0 else "FAILED",
        "report_counts": report_counts,
        "critical_leakage_issues": critical_leakage,
    }


def _traceability_check(session: Session) -> dict[str, Any]:
    artifact = session.execute(
        select(ModelReadyArtifact)
        .where(ModelReadyArtifact.feature_artifact_id.is_not(None))
        .order_by(ModelReadyArtifact.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if artifact is None:
        return {"status": "FAILED", "error": "No model-ready artifact with feature_artifact_id was found."}
    try:
        chain = TraceabilityService(session).get_by_model_ready_id(artifact.id)
    except TraceabilityError as exc:
        return {"status": "FAILED", "model_ready_artifact_id": artifact.id, "error": str(exc)}
    return {
        "status": "SUCCESS",
        "model_ready_artifact_id": artifact.id,
        "feature_artifact_id": chain.feature_artifact["id"],
        "normalized_artifact_id": chain.normalized_artifact["id"],
        "parser_run_id": chain.parser_run["id"],
        "dataset_file_id": chain.dataset_file["id"],
        "dataset_id": chain.dataset["id"],
    }


def _raw_file_hash_check(
    session: Session,
    *,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    catalog_files = session.execute(select(func.count()).select_from(DatasetFile)).scalar_one()
    file_rows = session.execute(
        select(
            DatasetFile.id,
            DatasetFile.file_path,
            DatasetFile.file_hash_sha256,
        )
        .order_by(DatasetFile.id)
        .execution_options(
            stream_results=True,
            yield_per=STAGE_TWO_READINESS_DB_YIELD_PER,
        )
    )
    missing = []
    mismatched = []
    checked = 0
    seen = 0
    _emit(
        progress_callback,
        "raw_hash_started",
        total=catalog_files,
        db_yield_per=STAGE_TWO_READINESS_DB_YIELD_PER,
        hash_chunk_bytes=STAGE_TWO_READINESS_HASH_CHUNK_BYTES,
    )
    for file_id, file_path, file_hash_sha256 in file_rows:
        seen += 1
        path = Path(file_path)
        if not path.exists():
            missing.append({"id": file_id, "file_path": file_path})
        elif file_hash_sha256:
            checked += 1
            actual_hash = _sha256(path, chunk_size=STAGE_TWO_READINESS_HASH_CHUNK_BYTES)
            if actual_hash != file_hash_sha256:
                mismatched.append({"id": file_id, "file_path": file_path})
        if seen == catalog_files or seen % 100 == 0:
            _emit(progress_callback, "raw_hash_progress", current=seen, total=catalog_files)
    _emit(progress_callback, "raw_hash_finished", current=seen, total=catalog_files)
    return {
        "status": "SUCCESS" if not missing and not mismatched else "FAILED",
        "catalog_files": catalog_files,
        "hash_checked": checked,
        "missing_files": missing,
        "hash_mismatches": mismatched,
    }


def _all_checks_success(checks: dict[str, Any]) -> bool:
    return all(check.get("status") == "SUCCESS" for check in checks.values())


def _save_reports(storage_root: Path, result: StageTwoReadinessResult) -> dict[str, str]:
    paths = {
        "en": f"{REPORTS_EN_STAGE_TWO}/stage_two_readiness_report.md",
        "ru": f"{REPORTS_RU_STAGE_TWO}/stage_two_readiness_report.md",
        "json": f"{REPORTS_EN_STAGE_TWO}/stage_two_readiness_report.json",
    }
    payload = {**asdict(result), "report_paths": paths}
    for language in ("en", "ru"):
        relative_path = paths[language]
        path = storage_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_render_markdown(language, payload), encoding="utf-8")
    json_path = storage_root / paths["json"]
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return paths


def _render_markdown(language: str, payload: dict[str, Any]) -> str:
    title = "Stage Two readiness report" if language == "en" else "Отчет готовности Stage Two"
    status_label = "Status" if language == "en" else "Статус"
    return (
        f"# {title}\n\n"
        f"- {status_label}: `{payload['status']}`\n"
        f"- Report paths: `{payload['report_paths']}`\n\n"
        "## Checks\n\n"
        "```json\n"
        f"{json.dumps(payload['checks'], indent=2, sort_keys=True, default=str)}\n"
        "```\n"
    )


def _sha256(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _emit(progress_callback: ProgressCallback | None, event: str, **payload: Any) -> None:
    if progress_callback is not None:
        progress_callback(event, payload)


def _readiness_progress_callback(progress: Any) -> ProgressCallback:
    main_task_id = progress.add_task("readiness: starting", total=11)
    raw_hash_task_id: int | None = None
    completed = 0

    def callback(event: str, payload: dict[str, Any]) -> None:
        nonlocal completed, raw_hash_task_id
        if event == "check_started":
            description = f"readiness: {payload.get('check_name') or 'check'}"
            progress.update(main_task_id, description=description, completed=completed)
            return
        if event == "check_finished":
            completed = min(completed + 1, 11)
            description = (
                f"readiness: {payload.get('check_name') or 'check'} "
                f"{payload.get('status') or ''}"
            ).strip()
            progress.update(main_task_id, description=description, completed=completed)
            return
        if event == "report_started":
            progress.update(main_task_id, description="readiness: saving reports", completed=completed)
            return
        if event == "report_finished":
            completed = min(completed + 1, 11)
            progress.update(main_task_id, description="readiness: reports saved", completed=completed)
            return
        if event == "raw_hash_started":
            total = max(int(payload.get("total") or 1), 1)
            db_yield_per = int(payload.get("db_yield_per") or 0)
            chunk_bytes = int(payload.get("hash_chunk_bytes") or 0)
            description = (
                f"readiness: hashing raw files "
                f"(db_batch={db_yield_per}, chunk={chunk_bytes // 1024} KiB)"
            )
            raw_hash_task_id = progress.add_task(description, total=total)
            return
        if event == "raw_hash_progress" and raw_hash_task_id is not None:
            total = max(int(payload.get("total") or 1), 1)
            current = min(int(payload.get("current") or 0), total)
            progress.update(raw_hash_task_id, completed=current, total=total)
            return
        if event == "raw_hash_finished" and raw_hash_task_id is not None:
            total = max(int(payload.get("total") or 1), 1)
            progress.update(raw_hash_task_id, completed=total, total=total)

    return callback


if __name__ == "__main__":
    if Progress is None or Console is None:
        result = run_stage_two_readiness_check()
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=Console(stderr=True),
        ) as readiness_progress:
            result = run_stage_two_readiness_check(
                progress_callback=_readiness_progress_callback(readiness_progress),
            )
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
