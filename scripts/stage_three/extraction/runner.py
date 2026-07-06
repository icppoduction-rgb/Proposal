"""Feature extraction runners for Stage Three MVP tasks."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import FEATURES_PATH, PATH_DATA_STORAGE
from scripts.db.models import NormalizedArtifact
from scripts.stage_three.extraction.base import (
    FeatureExtractionArtifact,
    FeatureExtractionResult,
    NormalizedArtifactInput,
)
from scripts.stage_three.extraction.registry import FEATURE_ARTIFACT_SCHEMA_VERSION
from scripts.stage_three.extraction.common import unsupported_field_warnings
from scripts.stage_three.extraction.dns_extractors import (
    DNS_MVP_FEATURE_GROUPS,
    dns_feature_columns,
    extract_dns_features_from_table,
    missing_ratios,
    required_dns_columns,
    select_existing_required_columns,
)
from scripts.stage_three.extraction.host_extractors import (
    HOST_FEATURE_GROUPS,
    host_feature_columns,
    host_missing_ratios,
    extract_host_features_from_table,
    required_host_columns,
    select_existing_required_columns as select_existing_host_columns,
)
from scripts.stage_three.extraction.network_extractors import (
    NETWORK_FEATURE_GROUPS,
    network_feature_columns,
    network_missing_ratios,
    extract_network_features_from_table,
    required_network_columns,
    select_existing_required_columns as select_existing_network_columns,
)
from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.feature_catalog.validator import FORBIDDEN_X_COLUMNS
from scripts.stage_three.runtime.backend import CpuFeatureExtractionBackend
from scripts.stage_three.runtime.memory_guard import MemoryGuard
from scripts.stage_three.runtime.resources import resolve_stage_three_runtime_settings


CORE_FEATURE_GROUPS: tuple[str, ...] = (*DNS_MVP_FEATURE_GROUPS, *HOST_FEATURE_GROUPS, *NETWORK_FEATURE_GROUPS)


def fetch_dns_normalized_artifacts(session: Session, *, branch: str, role: str) -> list[NormalizedArtifactInput]:
    """Fetch DNS normalized artifacts from the PostgreSQL catalog."""
    if branch != "dns":
        raise ValueError("DNS MVP extraction only supports --branch dns")
    return fetch_normalized_artifacts(session, branch=branch, role=role)


def fetch_normalized_artifacts(
    session: Session,
    *,
    branch: str,
    role: str,
    source_formats: tuple[str, ...] | None = None,
) -> list[NormalizedArtifactInput]:
    """Fetch normalized artifacts by branch, role, and optional source-format filter."""
    statement = (
        select(NormalizedArtifact)
        .where(
            NormalizedArtifact.branch == branch,
            NormalizedArtifact.role == role,
            NormalizedArtifact.status.in_(("SUCCESS", "PARTIAL_SUCCESS")),
        )
        .order_by(NormalizedArtifact.id.asc())
    )
    if source_formats:
        statement = statement.where(NormalizedArtifact.source_format.in_(source_formats))
    return [
        NormalizedArtifactInput(
            artifact_id=artifact.id,
            dataset_id=artifact.dataset_id,
            role=artifact.role,
            branch=artifact.branch,
            normalized_path=artifact.normalized_path,
            source_format=artifact.source_format,
            row_count=artifact.row_count,
        )
        for artifact in session.scalars(statement).all()
    ]


def run_dns_feature_extraction(
    *,
    artifacts: list[NormalizedArtifactInput],
    branch: str,
    role: str,
    feature_group: str,
    output_root: str | Path | None = None,
    storage_root: str | Path | None = None,
    batch_rows: int | None = None,
    memory_guard: MemoryGuard | None = None,
    backend: CpuFeatureExtractionBackend | None = None,
    run_id: str | int | None = None,
    schema_version: str = FEATURE_ARTIFACT_SCHEMA_VERSION,
) -> FeatureExtractionResult:
    """Extract DNS MVP features from normalized Parquet artifacts."""
    if branch != "dns":
        raise ValueError("DNS MVP extraction only supports branch='dns'")
    if feature_group not in DNS_MVP_FEATURE_GROUPS:
        allowed = ", ".join(DNS_MVP_FEATURE_GROUPS)
        raise ValueError(f"unsupported DNS MVP feature_group={feature_group!r}; allowed: {allowed}")
    _validate_catalog_feature_group(feature_group, expected_columns=dns_feature_columns(feature_group))
    settings = resolve_stage_three_runtime_settings(backend="cpu")
    guard = memory_guard or MemoryGuard(
        reserved_ram_gb=settings.resource_profile.reserved_ram_gb,
        soft_ram_limit_gb=settings.resource_profile.soft_ram_limit_gb,
        hard_ram_limit_gb=settings.resource_profile.hard_ram_limit_gb,
    )
    extractor_backend = backend or CpuFeatureExtractionBackend()
    resolved_batch_rows = batch_rows or settings.resource_profile.batch_rows
    feature_columns = list(dns_feature_columns(feature_group))
    outputs: list[FeatureExtractionArtifact] = []
    merged_missing_counts: dict[str, float] = defaultdict(float)
    started_at = perf_counter()
    for artifact in artifacts:
        input_path = _resolve_input_path(artifact.normalized_path, storage_root=storage_root)
        output_dir = _artifact_output_dir(
            output_root=output_root,
            branch=branch,
            role=role,
            feature_group=feature_group,
            schema_version=schema_version,
        )
        schema = ds.dataset(input_path, format="parquet").schema
        required_columns = select_existing_required_columns(schema, required_dns_columns(feature_group))

        def transform(table: pa.Table) -> pa.Table:
            return extract_dns_features_from_table(
                table,
                feature_group=feature_group,
                normalized_artifact_id=artifact.artifact_id,
                dataset_id=artifact.dataset_id,
                role=role,
                source_normalized_path=str(input_path),
            )

        run_result = extractor_backend.extract_to_parquet_parts(
            input_path=input_path,
            output_dir=output_dir,
            required_columns=required_columns,
            batch_rows=resolved_batch_rows,
            memory_guard=guard,
            transform=transform,
            part_name_prefix=_part_name_prefix(run_id=run_id, artifact_id=artifact.artifact_id),
        )
        artifact_missing = _missing_ratios_for_parts(run_result.output_parts, tuple(feature_columns))
        for column, ratio in artifact_missing.items():
            merged_missing_counts[column] += ratio * run_result.rows_written
        outputs.append(
            FeatureExtractionArtifact(
                normalized_artifact_id=artifact.artifact_id,
                feature_group=feature_group,
                feature_path=str(output_dir),
                parts=run_result.output_parts,
                rows_read=run_result.rows_read,
                rows_written=run_result.rows_written,
                columns_created=feature_columns,
                missing_ratios=artifact_missing,
                runtime_seconds=run_result.elapsed_seconds,
                peak_rss_gb=run_result.peak_rss_gb,
                warnings=_artifact_warnings(
                    schema_names=schema.names,
                    selected_columns=required_columns,
                    feature_group=feature_group,
                ),
                runtime_stats=_run_stats(
                    run_result=run_result,
                    configured_batch_rows=resolved_batch_rows,
                    settings=settings,
                    guard=guard,
                ),
                feature_schema_version=schema_version,
                source_artifact_ids=[artifact.artifact_id],
                column_count=len(feature_columns),
            )
        )
    rows_read = sum(output.rows_read for output in outputs)
    rows_written = sum(output.rows_written for output in outputs)
    missing_summary = {
        column: (merged_missing_counts[column] / rows_written if rows_written else 0.0)
        for column in feature_columns
    }
    peak_rss_values = [output.peak_rss_gb for output in outputs if output.peak_rss_gb is not None]
    return FeatureExtractionResult(
        status="SUCCESS",
        branch=branch,
        role=role,
        feature_group=feature_group,
        input_normalized_artifacts=artifacts,
        output_feature_artifacts=outputs,
        rows_read=rows_read,
        rows_written=rows_written,
        columns_created=feature_columns,
        missing_ratios=missing_summary,
        runtime_seconds=perf_counter() - started_at,
        backend_used=extractor_backend.name,
        peak_rss_gb=max(peak_rss_values) if peak_rss_values else guard.peak_rss_gb,
        warnings=_merge_warnings(outputs, settings_warnings=list(settings.warnings)),
        runtime_stats=_result_stats(
            outputs=outputs,
            settings=settings,
            configured_batch_rows=resolved_batch_rows,
            guard=guard,
        ),
    )


def run_host_network_feature_extraction(
    *,
    artifacts: list[NormalizedArtifactInput],
    branch: str,
    role: str,
    feature_group: str,
    output_root: str | Path | None = None,
    storage_root: str | Path | None = None,
    batch_rows: int | None = None,
    memory_guard: MemoryGuard | None = None,
    backend: CpuFeatureExtractionBackend | None = None,
    run_id: str | int | None = None,
    schema_version: str = FEATURE_ARTIFACT_SCHEMA_VERSION,
) -> FeatureExtractionResult:
    """Extract core Host or Network features from normalized Parquet artifacts."""
    if branch not in {"host", "network"}:
        raise ValueError("core Host/Network extraction supports branch='host' or branch='network'")
    if branch == "host" and feature_group not in HOST_FEATURE_GROUPS:
        allowed = ", ".join(HOST_FEATURE_GROUPS)
        raise ValueError(f"unsupported Host feature_group={feature_group!r}; allowed: {allowed}")
    if branch == "network" and feature_group not in NETWORK_FEATURE_GROUPS:
        allowed = ", ".join(NETWORK_FEATURE_GROUPS)
        raise ValueError(f"unsupported Network feature_group={feature_group!r}; allowed: {allowed}")

    feature_columns = list(_feature_columns(feature_group))
    _validate_catalog_feature_group(feature_group, expected_columns=tuple(feature_columns))
    settings = resolve_stage_three_runtime_settings(backend="cpu")
    guard = memory_guard or MemoryGuard(
        reserved_ram_gb=settings.resource_profile.reserved_ram_gb,
        soft_ram_limit_gb=settings.resource_profile.soft_ram_limit_gb,
        hard_ram_limit_gb=settings.resource_profile.hard_ram_limit_gb,
    )
    extractor_backend = backend or CpuFeatureExtractionBackend()
    resolved_batch_rows = batch_rows or settings.resource_profile.batch_rows
    outputs: list[FeatureExtractionArtifact] = []
    merged_missing_counts: dict[str, float] = defaultdict(float)
    started_at = perf_counter()

    for artifact in artifacts:
        if artifact.branch != branch or artifact.role != role:
            raise ValueError(
                "normalized artifact does not match requested branch/role: "
                f"artifact={artifact.branch}/{artifact.role}, requested={branch}/{role}"
            )
        input_path = _resolve_input_path(artifact.normalized_path, storage_root=storage_root)
        output_dir = _artifact_output_dir(
            output_root=output_root,
            branch=branch,
            role=role,
            feature_group=feature_group,
            schema_version=schema_version,
        )
        schema = ds.dataset(input_path, format="parquet").schema
        required_columns = _select_required_columns(branch, schema, feature_group)

        def transform(table: pa.Table) -> pa.Table:
            if branch == "host":
                return extract_host_features_from_table(
                    table,
                    feature_group=feature_group,
                    normalized_artifact_id=artifact.artifact_id,
                    dataset_id=artifact.dataset_id,
                    role=role,
                    source_normalized_path=str(input_path),
                )
            return extract_network_features_from_table(
                table,
                feature_group=feature_group,
                normalized_artifact_id=artifact.artifact_id,
                dataset_id=artifact.dataset_id,
                role=role,
                source_normalized_path=str(input_path),
            )

        run_result = extractor_backend.extract_to_parquet_parts(
            input_path=input_path,
            output_dir=output_dir,
            required_columns=required_columns,
            batch_rows=resolved_batch_rows,
            memory_guard=guard,
            transform=transform,
            part_name_prefix=_part_name_prefix(run_id=run_id, artifact_id=artifact.artifact_id),
        )
        artifact_missing = _missing_ratios_for_parts(
            run_result.output_parts,
            tuple(feature_columns),
            missing_fn=host_missing_ratios if branch == "host" else network_missing_ratios,
        )
        for column, ratio in artifact_missing.items():
            merged_missing_counts[column] += ratio * run_result.rows_written
        outputs.append(
            FeatureExtractionArtifact(
                normalized_artifact_id=artifact.artifact_id,
                feature_group=feature_group,
                feature_path=str(output_dir),
                parts=run_result.output_parts,
                rows_read=run_result.rows_read,
                rows_written=run_result.rows_written,
                columns_created=feature_columns,
                missing_ratios=artifact_missing,
                runtime_seconds=run_result.elapsed_seconds,
                peak_rss_gb=run_result.peak_rss_gb,
                warnings=_artifact_warnings(
                    schema_names=schema.names,
                    selected_columns=required_columns,
                    feature_group=feature_group,
                ),
                runtime_stats=_run_stats(
                    run_result=run_result,
                    configured_batch_rows=resolved_batch_rows,
                    settings=settings,
                    guard=guard,
                ),
                feature_schema_version=schema_version,
                source_artifact_ids=[artifact.artifact_id],
                column_count=len(feature_columns),
            )
        )

    rows_read = sum(output.rows_read for output in outputs)
    rows_written = sum(output.rows_written for output in outputs)
    missing_summary = {
        column: (merged_missing_counts[column] / rows_written if rows_written else 0.0)
        for column in feature_columns
    }
    peak_rss_values = [output.peak_rss_gb for output in outputs if output.peak_rss_gb is not None]
    return FeatureExtractionResult(
        status="SUCCESS",
        branch=branch,
        role=role,
        feature_group=feature_group,
        input_normalized_artifacts=artifacts,
        output_feature_artifacts=outputs,
        rows_read=rows_read,
        rows_written=rows_written,
        columns_created=feature_columns,
        missing_ratios=missing_summary,
        runtime_seconds=perf_counter() - started_at,
        backend_used=extractor_backend.name,
        peak_rss_gb=max(peak_rss_values) if peak_rss_values else guard.peak_rss_gb,
        warnings=_merge_warnings(outputs, settings_warnings=list(settings.warnings)),
        runtime_stats=_result_stats(
            outputs=outputs,
            settings=settings,
            configured_batch_rows=resolved_batch_rows,
            guard=guard,
        ),
    )


def _validate_catalog_feature_group(feature_group: str, *, expected_columns: tuple[str, ...]) -> None:
    catalog = load_feature_catalog()
    group = catalog.get("feature_groups", {}).get(feature_group)
    if not isinstance(group, dict):
        raise ValueError(f"feature_group is not defined in feature catalog: {feature_group}")
    catalog_features = {
        str(feature["name"])
        for feature in group.get("features", [])
        if isinstance(feature, dict) and bool(feature.get("allow_in_X"))
    }
    expected = set(expected_columns)
    missing = sorted(expected.difference(catalog_features))
    if missing:
        raise ValueError(f"feature catalog is missing feature columns: {', '.join(missing)}")
    forbidden = sorted(expected.intersection(FORBIDDEN_X_COLUMNS))
    if forbidden:
        raise ValueError(f"feature columns include forbidden X columns: {', '.join(forbidden)}")


def _feature_columns(feature_group: str) -> tuple[str, ...]:
    if feature_group in DNS_MVP_FEATURE_GROUPS:
        return dns_feature_columns(feature_group)
    if feature_group in HOST_FEATURE_GROUPS:
        return host_feature_columns(feature_group)
    if feature_group in NETWORK_FEATURE_GROUPS:
        return network_feature_columns(feature_group)
    allowed = ", ".join(CORE_FEATURE_GROUPS)
    raise ValueError(f"unsupported feature_group={feature_group!r}; allowed: {allowed}")


def _select_required_columns(branch: str, schema: pa.Schema, feature_group: str) -> list[str]:
    if branch == "host":
        return select_existing_host_columns(schema, required_host_columns(feature_group))
    if branch == "network":
        return select_existing_network_columns(schema, required_network_columns(feature_group))
    return select_existing_required_columns(schema, required_dns_columns(feature_group))


def _resolve_input_path(artifact_path: str, *, storage_root: str | Path | None) -> Path:
    path = Path(artifact_path).expanduser()
    if path.is_absolute():
        return path
    root = Path(storage_root or PATH_DATA_STORAGE).expanduser()
    return root / path


def _artifact_output_dir(
    *,
    output_root: str | Path | None,
    branch: str,
    role: str,
    feature_group: str,
    schema_version: str,
) -> Path:
    root = Path(output_root or FEATURES_PATH).expanduser()
    if not str(root).strip():
        raise ValueError("FEATURES_PATH/PATH_DATA_STORAGE must be configured for feature extraction output")
    return root / feature_group / branch / role / f"schema={schema_version}"


def _part_name_prefix(*, run_id: str | int | None, artifact_id: int) -> str:
    prefix = (
        str(run_id).strip()
        if run_id is not None and str(run_id).strip()
        else datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    )
    safe_prefix = prefix.replace("\\", "-").replace("/", "-").replace(":", "-")
    return f"part-{safe_prefix}-artifact-{artifact_id}"


def _missing_ratios_for_parts(
    parts: list[str],
    feature_columns: tuple[str, ...],
    *,
    missing_fn=missing_ratios,
) -> dict[str, float]:
    missing_counts: dict[str, int] = defaultdict(int)
    total_rows = 0
    for part in parts:
        table = pq.read_table(part, columns=[column for column in feature_columns])
        total_rows += table.num_rows
        ratios = missing_fn(table, feature_columns)
        for column, ratio in ratios.items():
            missing_counts[column] += int(ratio * table.num_rows)
    return {
        column: (missing_counts[column] / total_rows if total_rows else 0.0)
        for column in feature_columns
    }


def _artifact_warnings(
    *,
    schema_names: list[str],
    selected_columns: list[str],
    feature_group: str,
) -> list[str]:
    table = pa.table({column: pa.array([], type=pa.null()) for column in schema_names})
    return unsupported_field_warnings(
        table=table,
        supported_columns=selected_columns,
        feature_group=feature_group,
    )


def _run_stats(
    *,
    run_result: Any,
    configured_batch_rows: int,
    settings: Any,
    guard: MemoryGuard,
) -> dict[str, Any]:
    effective_workers, throttle_reason = _throttled_worker_count(settings=settings, guard=guard)
    return {
        "configured_batch_rows": configured_batch_rows,
        "batch_count": run_result.batch_count,
        "batch_metrics": [metric.__dict__ for metric in run_result.batch_metrics],
        "configured_workers": settings.resource_profile.default_workers,
        "effective_workers": effective_workers,
        "worker_throttle_reason": throttle_reason,
    }


def _result_stats(
    *,
    outputs: list[FeatureExtractionArtifact],
    settings: Any,
    configured_batch_rows: int,
    guard: MemoryGuard,
) -> dict[str, Any]:
    effective_workers, throttle_reason = _throttled_worker_count(settings=settings, guard=guard)
    return {
        "configured_batch_rows": configured_batch_rows,
        "configured_workers": settings.resource_profile.default_workers,
        "effective_workers": effective_workers,
        "worker_throttle_reason": throttle_reason,
        "artifact_count": len(outputs),
        "batch_count": sum(int(output.runtime_stats.get("batch_count", 0)) for output in outputs),
        "memory_probe": settings.memory_probe,
        "reserved_ram_gb": settings.resource_profile.reserved_ram_gb,
        "soft_ram_limit_gb": settings.resource_profile.soft_ram_limit_gb,
        "hard_ram_limit_gb": settings.resource_profile.hard_ram_limit_gb,
    }


def _throttled_worker_count(*, settings: Any, guard: MemoryGuard) -> tuple[int, str]:
    snapshot = guard.snapshot()
    configured = settings.resource_profile.default_workers
    if snapshot.available_ram_gb is None:
        return 1, "live RAM unavailable; core extractor uses one bounded batch worker"
    if snapshot.available_ram_gb < settings.resource_profile.reserved_ram_gb:
        return 1, "available RAM below reserved floor; workers throttled to one"
    if snapshot.available_ram_gb < settings.resource_profile.soft_ram_limit_gb / 2:
        return max(1, configured // 4), "available RAM below half soft limit"
    if snapshot.available_ram_gb < settings.resource_profile.soft_ram_limit_gb:
        return max(1, configured // 2), "available RAM below soft limit"
    return configured, "available RAM above soft limit"


def _merge_warnings(
    outputs: list[FeatureExtractionArtifact],
    *,
    settings_warnings: list[str],
) -> list[str]:
    warnings: list[str] = []
    for warning in settings_warnings:
        if warning not in warnings:
            warnings.append(warning)
    for output in outputs:
        for warning in output.warnings:
            if warning not in warnings:
                warnings.append(warning)
    return warnings
