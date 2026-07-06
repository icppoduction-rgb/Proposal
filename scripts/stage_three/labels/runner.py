"""Streaming label alignment summaries for Stage Three feature artifacts."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from config import PATH_DATA_STORAGE
from scripts.db.models import FeatureArtifact
from scripts.db.repositories import ArtifactRepository
from scripts.stage_three.labels.label_policy import (
    LABEL_COLUMNS,
    LabelAlignmentOutput,
    align_event_samples,
)


SUPPORTED_STREAMING_POLICIES = frozenset({"explicit_only", "weak_allowed_with_confidence"})
SAMPLE_ROW_LIMIT = 100


def run_label_alignment(
    repository: ArtifactRepository,
    *,
    branch: str,
    role: str,
    policy: str,
    storage_root: str | Path | None = None,
) -> LabelAlignmentOutput:
    """Validate and summarize label alignment over successful feature artifacts."""
    if policy not in SUPPORTED_STREAMING_POLICIES:
        allowed = ", ".join(sorted(SUPPORTED_STREAMING_POLICIES))
        raise ValueError(
            f"streaming align-labels supports event-level policies only: {allowed}; "
            f"got {policy!r}"
        )
    feature_artifacts = repository.list_successful_feature_artifacts(branch=branch, role=role)
    if not feature_artifacts:
        raise ValueError(f"no successful feature_artifacts found for branch={branch}, role={role}")

    root = Path(storage_root or PATH_DATA_STORAGE).expanduser()
    counters = _empty_counters()
    sample_rows: list[dict[str, Any]] = []
    feature_groups: Counter[str] = Counter()
    artifact_ids: list[int] = []
    warnings: list[str] = []

    for artifact in feature_artifacts:
        artifact_ids.append(int(artifact.id))
        feature_groups[str(artifact.feature_group)] += 1
        part_paths = _feature_part_paths(artifact, storage_root=root)
        if not part_paths:
            warnings.append(f"feature_artifact {artifact.id} has no registered Parquet parts")
            continue
        for path in part_paths:
            _consume_part(path, policy=policy, counters=counters, sample_rows=sample_rows, warnings=warnings)

    sample_output = align_event_samples(sample_rows, policy=policy) if sample_rows else _empty_output(policy)
    summary = {
        "branch": branch,
        "role": role,
        "feature_artifact_count": len(feature_artifacts),
        "feature_artifact_ids": artifact_ids,
        "feature_groups": dict(sorted(feature_groups.items())),
        "sample_count": counters["sample_count"],
        "labeled_count": counters["labeled_count"],
        "label_coverage": counters["labeled_count"] / counters["sample_count"]
        if counters["sample_count"]
        else 0.0,
        "unlabeled_count": counters["unlabeled_count"],
        "conflicting_count": 0,
        "label_source_distribution": dict(sorted(counters["label_source_distribution"].items())),
        "label_status_distribution": dict(sorted(counters["label_status_distribution"].items())),
        "label_binary_distribution": dict(sorted(counters["label_binary_distribution"].items())),
        "sampled_rows_in_report": len(sample_rows),
        "warnings": warnings,
    }
    return LabelAlignmentOutput(
        policy=policy,
        sample_level="event",
        x_rows=sample_output.x_rows,
        y_rows=sample_output.y_rows,
        metadata_rows=sample_output.metadata_rows,
        decisions=sample_output.decisions,
        summary=summary,
    )


def _empty_counters() -> dict[str, Any]:
    return {
        "sample_count": 0,
        "labeled_count": 0,
        "unlabeled_count": 0,
        "label_source_distribution": Counter(),
        "label_status_distribution": Counter(),
        "label_binary_distribution": Counter(),
    }


def _consume_part(
    path: Path,
    *,
    policy: str,
    counters: dict[str, Any],
    sample_rows: list[dict[str, Any]],
    warnings: list[str],
) -> None:
    if not path.exists():
        warnings.append(f"feature part is missing: {path}")
        return
    parquet_file = pq.ParquetFile(path)
    schema_columns = set(parquet_file.schema_arrow.names)
    required = set(LABEL_COLUMNS)
    missing = sorted(required.difference(schema_columns))
    if missing:
        warnings.append(f"{path} missing label columns: {missing}")
    columns = [column for column in ("sample_uid", *LABEL_COLUMNS) if column in schema_columns]
    if not columns:
        warnings.append(f"{path} has no label/sample columns")
        return
    for batch in parquet_file.iter_batches(batch_size=250_000, columns=columns):
        rows = batch.to_pylist()
        counters["sample_count"] += len(rows)
        for row in rows:
            status = _clean_text(row.get("label_status")) or "unlabeled"
            source = _clean_text(row.get("label_source")) or "none"
            label_binary = _normalize_binary(row.get("label_binary"))
            labeled = _is_labeled(row, policy=policy)
            counters["labeled_count"] += 1 if labeled else 0
            counters["unlabeled_count"] += 0 if labeled else 1
            counters["label_status_distribution"][status] += 1
            counters["label_source_distribution"][source] += 1
            counters["label_binary_distribution"][
                "unlabeled" if label_binary is None or not labeled else str(label_binary)
            ] += 1
            if len(sample_rows) < SAMPLE_ROW_LIMIT:
                sample_rows.append(row)


def _is_labeled(row: dict[str, Any], *, policy: str) -> bool:
    label_binary = _normalize_binary(row.get("label_binary"))
    has_label = label_binary is not None or row.get("label_family") is not None or row.get("label_subtype") is not None
    if not has_label:
        return False
    status = (_clean_text(row.get("label_status")) or "").lower()
    source = (_clean_text(row.get("label_source")) or "").lower()
    if status in {"explicit", "explicit_label", "verified", "ground_truth", "manual"}:
        return True
    if policy == "weak_allowed_with_confidence":
        confidence = _normalize_float(row.get("label_confidence"))
        return ("weak" in status or source == "weak") and confidence is not None and confidence >= 0.0
    return False


def _feature_part_paths(artifact: FeatureArtifact, *, storage_root: Path) -> list[Path]:
    metadata = artifact.metadata_json or {}
    parts = metadata.get("parts")
    paths: list[Path] = []
    if isinstance(parts, list):
        for part in parts:
            if isinstance(part, dict) and part.get("path"):
                paths.append(_resolve_path(str(part["path"]), storage_root=storage_root))
    if paths:
        return paths
    artifact_path = _resolve_path(artifact.feature_path, storage_root=storage_root)
    if artifact_path.is_dir():
        return sorted(artifact_path.glob("*.parquet"))
    return [artifact_path]


def _resolve_path(path_text: str, *, storage_root: Path) -> Path:
    path = Path(path_text).expanduser()
    return path if path.is_absolute() else storage_root / path


def _empty_output(policy: str) -> LabelAlignmentOutput:
    return LabelAlignmentOutput(
        policy=policy,
        sample_level="event",
        x_rows=[],
        y_rows=[],
        metadata_rows=[],
        decisions=[],
        summary={},
    )


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_binary(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int) and value in {0, 1}:
        return value
    text = str(value).strip().lower()
    if text in {"0", "false", "benign", "normal"}:
        return 0
    if text in {"1", "true", "attack", "malicious", "malware"}:
        return 1
    return None


def _normalize_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
