"""Feature extraction runners for Stage Three MVP tasks."""

from __future__ import annotations

from collections import defaultdict
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
from scripts.stage_three.extraction.dns_extractors import (
    DNS_MVP_FEATURE_GROUPS,
    dns_feature_columns,
    extract_dns_features_from_table,
    missing_ratios,
    required_dns_columns,
    select_existing_required_columns,
)
from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.feature_catalog.validator import FORBIDDEN_X_COLUMNS
from scripts.stage_three.runtime.backend import CpuFeatureExtractionBackend
from scripts.stage_three.runtime.memory_guard import MemoryGuard
from scripts.stage_three.runtime.resources import resolve_stage_three_runtime_settings


def fetch_dns_normalized_artifacts(session: Session, *, branch: str, role: str) -> list[NormalizedArtifactInput]:
    """Fetch DNS normalized artifacts from the PostgreSQL catalog."""
    if branch != "dns":
        raise ValueError("DNS MVP extraction only supports --branch dns")
    statement = (
        select(NormalizedArtifact)
        .where(
            NormalizedArtifact.branch == branch,
            NormalizedArtifact.role == role,
            NormalizedArtifact.status.in_(("SUCCESS", "PARTIAL_SUCCESS")),
        )
        .order_by(NormalizedArtifact.id.asc())
    )
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
) -> FeatureExtractionResult:
    """Extract DNS MVP features from normalized Parquet artifacts."""
    if branch != "dns":
        raise ValueError("DNS MVP extraction only supports branch='dns'")
    if feature_group not in DNS_MVP_FEATURE_GROUPS:
        allowed = ", ".join(DNS_MVP_FEATURE_GROUPS)
        raise ValueError(f"unsupported DNS MVP feature_group={feature_group!r}; allowed: {allowed}")
    _validate_catalog_feature_group(feature_group)
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
            role=role,
            feature_group=feature_group,
            artifact_id=artifact.artifact_id,
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
    )


def _validate_catalog_feature_group(feature_group: str) -> None:
    catalog = load_feature_catalog()
    group = catalog.get("feature_groups", {}).get(feature_group)
    if not isinstance(group, dict):
        raise ValueError(f"feature_group is not defined in feature catalog: {feature_group}")
    catalog_features = {
        str(feature["name"])
        for feature in group.get("features", [])
        if isinstance(feature, dict) and bool(feature.get("allow_in_X"))
    }
    expected = set(dns_feature_columns(feature_group))
    missing = sorted(expected.difference(catalog_features))
    if missing:
        raise ValueError(f"feature catalog is missing DNS MVP feature columns: {', '.join(missing)}")
    forbidden = sorted(expected.intersection(FORBIDDEN_X_COLUMNS))
    if forbidden:
        raise ValueError(f"DNS MVP feature columns include forbidden X columns: {', '.join(forbidden)}")


def _resolve_input_path(artifact_path: str, *, storage_root: str | Path | None) -> Path:
    path = Path(artifact_path).expanduser()
    if path.is_absolute():
        return path
    root = Path(storage_root or PATH_DATA_STORAGE).expanduser()
    return root / path


def _artifact_output_dir(
    *,
    output_root: str | Path | None,
    role: str,
    feature_group: str,
    artifact_id: int,
) -> Path:
    root = Path(output_root or FEATURES_PATH).expanduser()
    if not str(root).strip():
        raise ValueError("FEATURES_PATH/PATH_DATA_STORAGE must be configured for feature extraction output")
    return root / "dns" / feature_group / role / f"artifact-{artifact_id}"


def _missing_ratios_for_parts(parts: list[str], feature_columns: tuple[str, ...]) -> dict[str, float]:
    missing_counts: dict[str, int] = defaultdict(int)
    total_rows = 0
    for part in parts:
        table = pq.read_table(part, columns=[column for column in feature_columns])
        total_rows += table.num_rows
        ratios = missing_ratios(table, feature_columns)
        for column, ratio in ratios.items():
            missing_counts[column] += int(ratio * table.num_rows)
    return {
        column: (missing_counts[column] / total_rows if total_rows else 0.0)
        for column in feature_columns
    }
