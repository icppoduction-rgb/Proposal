"""Benchmark helpers for Stage Two normalization throughput reports."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
import json
from pathlib import Path
import re
import time
import tracemalloc
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import PATH_REPORT
from scripts.db.models import DatasetFile, NormalizedArtifact, ParserRun
from scripts.db.models.constants import ACTIVE_CATALOG_SOURCE_GROUP
from scripts.db.repositories import DatasetFileRepository
from scripts.stage_two.normalization.runner import (
    NormalizeFormatRequest,
    NormalizeFormatResult,
    NormalizeFormatRunner,
)


BYTES_PER_GB = 1024**3
BENCHMARK_TARGET_GB = 17.0
BENCHMARK_TARGET_HOURS = 3.0
REQUIRED_GB_PER_HOUR = round(BENCHMARK_TARGET_GB / BENCHMARK_TARGET_HOURS, 2)


@dataclass(frozen=True)
class BenchmarkNormalizationRequest:
    """CLI request for scoped Stage Two normalization benchmarking."""

    branch: str
    role: str
    source_format: str
    limit: int | None = None
    sample_ratio: float | None = None
    dry_run: bool = False
    resume: bool = False


@dataclass(frozen=True)
class BenchmarkInputFile:
    """Input file selected for a benchmark run."""

    file_id: int
    file_path: str
    size_bytes: int


@dataclass(frozen=True)
class BenchmarkRuntimeSample:
    """Host-side runtime counters captured around the normalization command."""

    elapsed_seconds: float
    process_cpu_seconds: float | None = None
    peak_python_memory_bytes: int | None = None


@dataclass(frozen=True)
class BenchmarkArtifactSample:
    """Catalog counters collected from parser runs and normalized artifacts."""

    rows_read: int = 0
    events_emitted: int = 0
    parquet_output_size: int = 0
    parser_time_seconds: float = 0.0
    write_time_seconds: float = 0.0
    parser_time_file_count: int = 0
    write_time_artifact_count: int = 0


@dataclass(frozen=True)
class BenchmarkMetrics:
    """Normalized benchmark metrics suitable for JSON and markdown reports."""

    input_bytes: int
    processed_bytes: int
    processed_gb: float
    elapsed_seconds: float
    gb_per_hour: float
    files_per_second: float | None
    rows_per_second: float | None
    events_per_second: float | None
    successful_files: int
    partial_files: int
    failed_files: int
    skipped_files: int
    unsupported_files: int
    parquet_output_size: int
    average_parser_time_per_file: float | None
    average_write_time_per_artifact: float | None
    process_cpu_seconds: float | None
    peak_python_memory_bytes: int | None
    estimated_time_for_17gb: float | None
    estimated_time_for_17gb_seconds: float | None
    meets_3_hour_target: bool
    required_gb_per_hour: float
    current_gb_per_hour: float
    rows_read: int
    events_emitted: int


@dataclass(frozen=True)
class BenchmarkReportPaths:
    """Paths written by benchmark report generation."""

    ru_markdown: str
    en_markdown: str
    ru_json: str
    en_json: str


@dataclass(frozen=True)
class BenchmarkNormalizationResult:
    """Benchmark command result returned to the CLI."""

    status: str
    request: BenchmarkNormalizationRequest
    normalize_request: NormalizeFormatRequest
    selected_files: tuple[BenchmarkInputFile, ...]
    metrics: BenchmarkMetrics
    report_paths: BenchmarkReportPaths
    normalize_result: NormalizeFormatResult | None = None
    resume_forced: bool = False


def select_benchmark_files(
    session: Session,
    request: BenchmarkNormalizationRequest,
) -> tuple[BenchmarkInputFile, ...]:
    """Select READY_FOR_PARSING files, applying limit and deterministic sample ratio."""
    files = DatasetFileRepository(session).get_files_ready_for_parsing(
        branch=request.branch,
        role=request.role,
        source_format=request.source_format,
        limit=request.limit,
        source_group=ACTIVE_CATALOG_SOURCE_GROUP,
    )
    sampled = _apply_sample_ratio(files, request.sample_ratio)
    return tuple(
        BenchmarkInputFile(
            file_id=int(file.id),
            file_path=str(file.file_path),
            size_bytes=int(file.file_size_bytes or 0),
        )
        for file in sampled
    )


def benchmark_normalization(
    session: Session,
    *,
    benchmark_request: BenchmarkNormalizationRequest,
    normalize_request: NormalizeFormatRequest,
    progress_callback: Any | None = None,
) -> BenchmarkNormalizationResult:
    """Run or dry-run a scoped normalization benchmark and persist reports."""
    selected_files = select_benchmark_files(session, benchmark_request)
    selected_ids = tuple(file.file_id for file in selected_files)
    effective_normalize_request = replace(
        normalize_request,
        file_ids=selected_ids,
        limit=None,
        resume=normalize_request.resume or not benchmark_request.dry_run,
    )
    resume_forced = effective_normalize_request.resume and not benchmark_request.resume
    started_after_parser_run_id = _max_parser_run_id(session)
    started_after_artifact_id = _max_artifact_id(session)

    normalize_result: NormalizeFormatResult | None = None
    runtime_sample: BenchmarkRuntimeSample
    if benchmark_request.dry_run:
        runtime_sample = BenchmarkRuntimeSample(elapsed_seconds=0.0)
    else:
        started_at = time.perf_counter()
        cpu_started_at = time.process_time()
        started_tracing_here = not tracemalloc.is_tracing()
        if started_tracing_here:
            tracemalloc.start()
        try:
            normalize_result = NormalizeFormatRunner(
                session,
                progress_callback=progress_callback,
            ).normalize_format(effective_normalize_request)
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            _ = current_memory
        finally:
            if started_tracing_here:
                tracemalloc.stop()
        runtime_sample = BenchmarkRuntimeSample(
            elapsed_seconds=time.perf_counter() - started_at,
            process_cpu_seconds=time.process_time() - cpu_started_at,
            peak_python_memory_bytes=int(peak_memory),
        )

    artifact_sample = collect_benchmark_artifact_sample(
        session,
        file_ids=selected_ids,
        started_after_parser_run_id=started_after_parser_run_id,
        started_after_artifact_id=started_after_artifact_id,
    )
    metrics = calculate_benchmark_metrics(
        selected_files=selected_files,
        normalize_result=normalize_result,
        runtime_sample=runtime_sample,
        artifact_sample=artifact_sample,
    )
    status = "DRY_RUN" if benchmark_request.dry_run else (normalize_result.status if normalize_result else "SUCCESS")
    result = BenchmarkNormalizationResult(
        status=status,
        request=benchmark_request,
        normalize_request=effective_normalize_request,
        selected_files=selected_files,
        metrics=metrics,
        report_paths=BenchmarkReportPaths("", "", "", ""),
        normalize_result=normalize_result,
        resume_forced=resume_forced,
    )
    report_paths = save_benchmark_reports(result)
    return replace(result, report_paths=report_paths)


def calculate_benchmark_metrics(
    *,
    selected_files: Sequence[BenchmarkInputFile],
    normalize_result: NormalizeFormatResult | None,
    runtime_sample: BenchmarkRuntimeSample,
    artifact_sample: BenchmarkArtifactSample,
) -> BenchmarkMetrics:
    """Calculate throughput and target-fit metrics for a benchmark sample."""
    input_bytes = sum(file.size_bytes for file in selected_files)
    processed_file_ids = _processed_file_ids(normalize_result)
    size_by_id = {file.file_id: file.size_bytes for file in selected_files}
    processed_bytes = sum(size_by_id.get(file_id, 0) for file_id in processed_file_ids)
    processed_gb = processed_bytes / BYTES_PER_GB
    elapsed_seconds = max(runtime_sample.elapsed_seconds, 0.0)
    elapsed_hours = elapsed_seconds / 3600 if elapsed_seconds > 0 else 0.0
    gb_per_hour = processed_gb / elapsed_hours if elapsed_hours > 0 else 0.0
    processed_files = len(processed_file_ids)
    estimated_hours = BENCHMARK_TARGET_GB / gb_per_hour if gb_per_hour > 0 else None
    estimated_seconds = estimated_hours * 3600 if estimated_hours is not None else None

    return BenchmarkMetrics(
        input_bytes=input_bytes,
        processed_bytes=processed_bytes,
        processed_gb=round(processed_gb, 6),
        elapsed_seconds=round(elapsed_seconds, 6),
        gb_per_hour=round(gb_per_hour, 6),
        files_per_second=_rate(processed_files, elapsed_seconds),
        rows_per_second=_rate(artifact_sample.rows_read, elapsed_seconds),
        events_per_second=_rate(artifact_sample.events_emitted, elapsed_seconds),
        successful_files=_result_count(normalize_result, "parsed"),
        partial_files=_result_count(normalize_result, "partially_parsed"),
        failed_files=_result_count(normalize_result, "failed"),
        skipped_files=_result_count(normalize_result, "skipped"),
        unsupported_files=_result_count(normalize_result, "unsupported"),
        parquet_output_size=artifact_sample.parquet_output_size,
        average_parser_time_per_file=_average(
            artifact_sample.parser_time_seconds,
            artifact_sample.parser_time_file_count,
        ),
        average_write_time_per_artifact=_average(
            artifact_sample.write_time_seconds,
            artifact_sample.write_time_artifact_count,
        ),
        process_cpu_seconds=(
            round(runtime_sample.process_cpu_seconds, 6)
            if runtime_sample.process_cpu_seconds is not None
            else None
        ),
        peak_python_memory_bytes=runtime_sample.peak_python_memory_bytes,
        estimated_time_for_17gb=(round(estimated_hours, 6) if estimated_hours is not None else None),
        estimated_time_for_17gb_seconds=(
            round(estimated_seconds, 6) if estimated_seconds is not None else None
        ),
        meets_3_hour_target=bool(estimated_hours is not None and estimated_hours <= BENCHMARK_TARGET_HOURS),
        required_gb_per_hour=REQUIRED_GB_PER_HOUR,
        current_gb_per_hour=round(gb_per_hour, 6),
        rows_read=artifact_sample.rows_read,
        events_emitted=artifact_sample.events_emitted,
    )


def collect_benchmark_artifact_sample(
    session: Session,
    *,
    file_ids: tuple[int, ...],
    started_after_parser_run_id: int,
    started_after_artifact_id: int,
) -> BenchmarkArtifactSample:
    """Collect counters generated by the benchmark run from catalog tables."""
    if not file_ids:
        return BenchmarkArtifactSample()
    parser_runs = list(
        session.execute(
            select(ParserRun)
            .where(ParserRun.id > started_after_parser_run_id, ParserRun.file_id.in_(file_ids))
            .order_by(ParserRun.id.asc())
        ).scalars()
    )
    artifacts = list(
        session.execute(
            select(NormalizedArtifact)
            .where(
                NormalizedArtifact.id > started_after_artifact_id,
                NormalizedArtifact.file_id.in_(file_ids),
            )
            .order_by(NormalizedArtifact.id.asc())
        ).scalars()
    )
    rows_read = sum(int(run.rows_read or 0) for run in parser_runs)
    events_emitted = sum(int(run.events_emitted or 0) for run in parser_runs)
    parser_time_seconds = 0.0
    parser_time_file_count = 0
    write_time_seconds = 0.0
    for run in parser_runs:
        performance = _mapping(run.metadata_json).get("performance")
        if not isinstance(performance, dict):
            continue
        parser_time_seconds += _float_value(performance.get("parse_seconds"))
        write_time_seconds += _float_value(performance.get("parquet_write_seconds"))
        parser_time_file_count += 1

    parquet_output_size = sum(int(artifact.file_size_bytes or 0) for artifact in artifacts)
    artifact_write_time_seconds = 0.0
    artifact_write_count = 0
    for artifact in artifacts:
        counters = _mapping(artifact.metadata_json).get("output_counters")
        if not isinstance(counters, dict):
            continue
        artifact_write_time_seconds += _float_value(counters.get("write_duration_seconds"))
        artifact_write_count += 1
    if artifact_write_count:
        write_time_seconds = artifact_write_time_seconds

    return BenchmarkArtifactSample(
        rows_read=rows_read,
        events_emitted=events_emitted,
        parquet_output_size=parquet_output_size,
        parser_time_seconds=parser_time_seconds,
        write_time_seconds=write_time_seconds,
        parser_time_file_count=parser_time_file_count,
        write_time_artifact_count=artifact_write_count or len(artifacts),
    )


def save_benchmark_reports(
    result: BenchmarkNormalizationResult,
    *,
    report_root: str | Path | None = None,
) -> BenchmarkReportPaths:
    """Write localized markdown and JSON benchmark reports."""
    root = Path(report_root or PATH_REPORT)
    base_name = _benchmark_report_base_name(
        result.request.branch,
        result.request.role,
        result.request.source_format,
    )
    ru_dir = root / "ru" / "stage-two" / "performance"
    en_dir = root / "en" / "stage-two" / "performance"
    ru_dir.mkdir(parents=True, exist_ok=True)
    en_dir.mkdir(parents=True, exist_ok=True)

    ru_markdown = ru_dir / f"{base_name}.md"
    en_markdown = en_dir / f"{base_name}.md"
    ru_json = ru_dir / f"{base_name}.json"
    en_json = en_dir / f"{base_name}.json"
    payload = _benchmark_json_payload(result)
    ru_markdown.write_text(_benchmark_markdown(result, language="ru"), encoding="utf-8")
    en_markdown.write_text(_benchmark_markdown(result, language="en"), encoding="utf-8")
    json_payload = json.dumps(payload, indent=2, sort_keys=True, default=str)
    ru_json.write_text(json_payload + "\n", encoding="utf-8")
    en_json.write_text(json_payload + "\n", encoding="utf-8")
    return BenchmarkReportPaths(
        ru_markdown=str(ru_markdown),
        en_markdown=str(en_markdown),
        ru_json=str(ru_json),
        en_json=str(en_json),
    )


def _processed_file_ids(result: NormalizeFormatResult | None) -> set[int]:
    if result is None:
        return set()
    return {
        int(file.file_id)
        for file in result.files
        if file.file_id is not None and file.status in {"PARSED", "PARTIALLY_PARSED"}
    }


def _result_count(result: NormalizeFormatResult | None, field_name: str) -> int:
    return int(getattr(result, field_name, 0) or 0) if result is not None else 0


def _rate(value: int | float, seconds: float) -> float | None:
    if seconds <= 0:
        return None
    return round(float(value) / seconds, 6)


def _average(total: float, count: int) -> float | None:
    if count <= 0:
        return None
    return round(total / count, 6)


def _apply_sample_ratio(
    files: Sequence[DatasetFile],
    sample_ratio: float | None,
) -> Sequence[DatasetFile]:
    if sample_ratio is None or sample_ratio >= 1:
        return files
    if sample_ratio <= 0:
        raise ValueError("benchmark-normalization sample-ratio must be greater than 0")
    sample_size = max(1, int(len(files) * sample_ratio)) if files else 0
    return files[:sample_size]


def _max_parser_run_id(session: Session) -> int:
    value = session.execute(select(ParserRun.id).order_by(ParserRun.id.desc()).limit(1)).scalar_one_or_none()
    return int(value or 0)


def _max_artifact_id(session: Session) -> int:
    value = (
        session.execute(select(NormalizedArtifact.id).order_by(NormalizedArtifact.id.desc()).limit(1))
        .scalar_one_or_none()
    )
    return int(value or 0)


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _float_value(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _benchmark_report_base_name(branch: str, role: str, source_format: str) -> str:
    safe_format = re.sub(r"[^A-Za-z0-9_.-]+", "_", source_format.strip())
    safe_role = re.sub(r"[^A-Za-z0-9_.-]+", "_", role.strip())
    safe_branch = re.sub(r"[^A-Za-z0-9_.-]+", "_", branch.strip())
    return f"benchmark_{safe_branch}_{safe_role}_{safe_format}"


def _benchmark_json_payload(result: BenchmarkNormalizationResult) -> dict[str, Any]:
    payload = {
        "status": result.status,
        "request": asdict(result.request),
        "normalize_request": asdict(result.normalize_request),
        "selected_files": [asdict(file) for file in result.selected_files],
        "metrics": asdict(result.metrics),
        "report_paths": asdict(result.report_paths),
        "resume_forced": result.resume_forced,
        "gpu_metrics": None,
    }
    if result.normalize_result is not None:
        payload["normalize_result"] = asdict(result.normalize_result)
    return payload


def _benchmark_markdown(result: BenchmarkNormalizationResult, *, language: str) -> str:
    metrics = result.metrics
    title = (
        "Stage Two normalization benchmark"
        if language == "en"
        else "Benchmark Stage Two normalization"
    )
    labels = _labels(language)
    return "\n".join(
        [
            f"# {title}",
            "",
            f"- {labels['status']}: `{result.status}`",
            f"- branch/role/format: `{result.request.branch}/{result.request.role}/{result.request.source_format}`",
            f"- dry_run: `{result.request.dry_run}`",
            f"- resume: `{result.normalize_request.resume}`",
            f"- resume_forced: `{result.resume_forced}`",
            f"- selected_files: `{len(result.selected_files)}`",
            "",
            f"## {labels['throughput']}",
            "",
            "| metric | value |",
            "| --- | ---: |",
            f"| input_bytes | {metrics.input_bytes} |",
            f"| processed_bytes | {metrics.processed_bytes} |",
            f"| processed_gb | {metrics.processed_gb} |",
            f"| elapsed_seconds | {metrics.elapsed_seconds} |",
            f"| gb_per_hour | {metrics.gb_per_hour} |",
            f"| current_gb_per_hour | {metrics.current_gb_per_hour} |",
            f"| required_gb_per_hour | {metrics.required_gb_per_hour} |",
            f"| estimated_time_for_17gb_hours | {_nullable(metrics.estimated_time_for_17gb)} |",
            f"| estimated_time_for_17gb_seconds | {_nullable(metrics.estimated_time_for_17gb_seconds)} |",
            f"| meets_3_hour_target | {str(metrics.meets_3_hour_target).lower()} |",
            f"| files_per_second | {_nullable(metrics.files_per_second)} |",
            f"| rows_per_second | {_nullable(metrics.rows_per_second)} |",
            f"| events_per_second | {_nullable(metrics.events_per_second)} |",
            "",
            f"## {labels['files']}",
            "",
            "| metric | value |",
            "| --- | ---: |",
            f"| successful_files | {metrics.successful_files} |",
            f"| partial_files | {metrics.partial_files} |",
            f"| failed_files | {metrics.failed_files} |",
            f"| skipped_files | {metrics.skipped_files} |",
            f"| unsupported_files | {metrics.unsupported_files} |",
            "",
            f"## {labels['runtime']}",
            "",
            "| metric | value |",
            "| --- | ---: |",
            f"| parquet_output_size | {metrics.parquet_output_size} |",
            f"| rows_read | {metrics.rows_read} |",
            f"| events_emitted | {metrics.events_emitted} |",
            f"| average_parser_time_per_file | {_nullable(metrics.average_parser_time_per_file)} |",
            f"| average_write_time_per_artifact | {_nullable(metrics.average_write_time_per_artifact)} |",
            f"| process_cpu_seconds | {_nullable(metrics.process_cpu_seconds)} |",
            f"| peak_python_memory_bytes | {_nullable(metrics.peak_python_memory_bytes)} |",
            f"| gpu_metrics | null |",
            "",
            f"## {labels['settings']}",
            "",
            "```json",
            json.dumps(asdict(result.normalize_request), indent=2, sort_keys=True, default=str),
            "```",
            "",
        ]
    )


def _labels(language: str) -> dict[str, str]:
    if language == "ru":
        return {
            "status": "статус",
            "throughput": "Скорость",
            "files": "Файлы",
            "runtime": "Runtime metrics",
            "settings": "Resolved runtime settings",
        }
    return {
        "status": "status",
        "throughput": "Throughput",
        "files": "Files",
        "runtime": "Runtime metrics",
        "settings": "Resolved runtime settings",
    }


def _nullable(value: object) -> object:
    return "null" if value is None else value
