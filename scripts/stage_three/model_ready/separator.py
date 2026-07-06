"""Separate feature artifacts into model X, y, metadata, and traceability tables."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.feature_catalog.validator import FORBIDDEN_X_COLUMNS
from scripts.stage_three.labels.label_policy import LABEL_COLUMNS, METADATA_COLUMNS


TRACEABILITY_COLUMNS: tuple[str, ...] = (
    "sample_uid",
    "event_uid",
    "window_id",
    "flow_id",
    "session_id",
    "sequence_id",
    "dataset_id",
    "source_file_id",
    "file_id",
    "parser_run_id",
    "normalized_artifact_id",
    "feature_artifact_id",
    "source_file",
    "source_path",
    "source_file_path",
    "source_normalized_path",
    "source_feature_artifact_path",
)

AUDIT_METADATA_COLUMNS: tuple[str, ...] = tuple(
    dict.fromkeys(
        (
            *METADATA_COLUMNS,
            "sample_uid",
            "dataset_name",
            "dataset_role",
            "role",
            "branch",
            "feature_group",
            "scenario_name",
            "parser_name",
            "parser_version",
            "source_format",
            "timestamp_type",
            "event_timestamp",
            "event_order",
            "label_policy",
            "label_status",
            "label_source",
            "label_confidence",
            "label_mapping_rule_id",
            "raw_fields_json",
            "metadata_json",
        )
    )
)

_ABSOLUTE_PATH_RE = re.compile(
    r"^(?:[A-Za-z]:[\\/]|\\\\[^\\/]+[\\/][^\\/]+[\\/]|/(?:home|users|var|tmp|etc|mnt|opt|data|srv)/)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DroppedColumn:
    """One input column intentionally excluded from model X."""

    name: str
    reason: str


@dataclass(frozen=True)
class ModelReadyTables:
    """Four logical tables created before preprocessing."""

    X: list[dict[str, Any]]
    y: list[dict[str, Any]]
    metadata: list[dict[str, Any]]
    traceability: list[dict[str, Any]]


@dataclass(frozen=True)
class FeatureSeparationPlan:
    """Column-level separation plan that can be applied to streaming batches."""

    x_columns: list[str]
    y_columns: list[str]
    metadata_columns: list[str]
    traceability_columns: list[str]
    dropped_columns: list[DroppedColumn]
    forbidden_x_columns: list[str]
    source_columns: list[str]
    row_count: int = 0


@dataclass(frozen=True)
class FeatureSeparationResult:
    """Result and audit metadata for X/y/metadata/traceability separation."""

    status: str
    tables: ModelReadyTables
    x_columns: list[str]
    y_columns: list[str]
    metadata_columns: list[str]
    traceability_columns: list[str]
    dropped_columns: list[DroppedColumn] = field(default_factory=list)
    forbidden_x_columns: list[str] = field(default_factory=list)
    source_columns: list[str] = field(default_factory=list)
    row_count: int = 0
    report_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a report-friendly payload."""
        payload = asdict(self)
        payload["tables"] = {
            "X": self.tables.X,
            "y": self.tables.y,
            "metadata": self.tables.metadata,
            "traceability": self.tables.traceability,
        }
        return payload


class ForbiddenXColumnError(ValueError):
    """Raised when model X still contains forbidden non-null values."""


def separate_feature_artifacts(
    paths: Iterable[str | Path],
    *,
    feature_catalog: dict[str, Any] | None = None,
) -> FeatureSeparationResult:
    """Read Parquet feature artifacts and split them into four logical tables."""
    artifact_paths = [Path(path) for path in paths]
    if not artifact_paths:
        raise ValueError("at least one feature artifact path is required")
    tables = [pq.read_table(path) for path in artifact_paths]
    return separate_feature_artifact_table(
        pa.concat_tables(tables, promote_options="default"),
        feature_catalog=feature_catalog,
    )


def plan_feature_artifact_separation(
    paths: Iterable[str | Path],
    *,
    feature_catalog: dict[str, Any] | None = None,
) -> FeatureSeparationPlan:
    """Build a separation plan from Parquet metadata without loading rows."""
    artifact_paths = [Path(path) for path in paths]
    if not artifact_paths:
        raise ValueError("at least one feature artifact path is required")

    source_columns: list[str] = []
    seen: set[str] = set()
    row_count = 0
    for path in artifact_paths:
        metadata = pq.read_metadata(path)
        schema = pq.read_schema(path)
        row_count += int(metadata.num_rows)
        for column in schema.names:
            if column not in seen:
                seen.add(column)
                source_columns.append(column)
    return _build_separation_plan(
        source_columns,
        row_count=row_count,
        feature_catalog=feature_catalog,
    )


def separate_feature_artifact_table(
    table: pa.Table,
    *,
    feature_catalog: dict[str, Any] | None = None,
) -> FeatureSeparationResult:
    """Split a PyArrow feature table into X, y, metadata, and traceability."""
    return separate_feature_artifact_rows(table.to_pylist(), feature_catalog=feature_catalog)


def separate_feature_artifact_rows(
    rows: list[dict[str, Any]],
    *,
    feature_catalog: dict[str, Any] | None = None,
) -> FeatureSeparationResult:
    """Split feature rows into X/y/metadata/traceability using the feature catalog."""
    plan = _build_separation_plan(
        _ordered_source_columns(rows),
        row_count=len(rows),
        feature_catalog=feature_catalog,
    )

    x_rows: list[dict[str, Any]] = []
    y_rows: list[dict[str, Any]] = []
    metadata_rows: list[dict[str, Any]] = []
    traceability_rows: list[dict[str, Any]] = []

    for index, row in enumerate(rows):
        sample_uid = _sample_uid(row, index)
        x_rows.append({column: row.get(column) for column in plan.x_columns})
        y_rows.append(_row_with_sample_uid(row, plan.y_columns, sample_uid))
        metadata_rows.append(_row_with_sample_uid(row, plan.metadata_columns, sample_uid))
        traceability_rows.append(_row_with_sample_uid(row, plan.traceability_columns, sample_uid))

    validate_no_forbidden_x_columns(x_rows, forbidden_x_columns=plan.forbidden_x_columns)
    return FeatureSeparationResult(
        status="SUCCESS",
        tables=ModelReadyTables(
            X=x_rows,
            y=y_rows,
            metadata=metadata_rows,
            traceability=traceability_rows,
        ),
        x_columns=plan.x_columns,
        y_columns=plan.y_columns,
        metadata_columns=plan.metadata_columns,
        traceability_columns=plan.traceability_columns,
        dropped_columns=plan.dropped_columns,
        forbidden_x_columns=plan.forbidden_x_columns,
        source_columns=plan.source_columns,
        row_count=plan.row_count,
    )


def validate_no_forbidden_x_columns(
    x_rows: list[dict[str, Any]],
    *,
    forbidden_x_columns: Iterable[str] | None = None,
) -> None:
    """Fail if X contains forbidden non-null columns or absolute local paths."""
    forbidden = set(forbidden_x_columns or FORBIDDEN_X_COLUMNS)
    forbidden.add("label_*")
    violations: dict[str, int] = {}
    for row in x_rows:
        for column, value in row.items():
            if _is_forbidden_column(column, forbidden) and _is_non_null(value):
                violations[column] = violations.get(column, 0) + 1
            elif _is_non_null(value) and _contains_absolute_path(value):
                key = f"{column}:absolute_path"
                violations[key] = violations.get(key, 0) + 1
    if violations:
        details = ", ".join(f"{name}={count}" for name, count in sorted(violations.items()))
        raise ForbiddenXColumnError(f"forbidden non-null values remain in X: {details}")


def _allowed_x_columns(catalog: dict[str, Any]) -> set[str]:
    columns: set[str] = set()
    groups = catalog.get("feature_groups", {})
    if not isinstance(groups, dict):
        return columns
    for group in groups.values():
        if not isinstance(group, dict):
            continue
        features = group.get("features", [])
        if not isinstance(features, list):
            continue
        for feature in features:
            if not isinstance(feature, dict) or feature.get("allow_in_X") is not True:
                continue
            name = feature.get("name")
            if isinstance(name, str) and name.strip():
                columns.add(name.strip())
            for encoded_name in feature.get("encoded_outputs", []) or []:
                if isinstance(encoded_name, str) and encoded_name.strip():
                    columns.add(encoded_name.strip())
    return columns


def _forbidden_x_columns(catalog: dict[str, Any]) -> set[str]:
    raw_columns = catalog.get("forbidden_X_columns", [])
    columns = {str(column).strip() for column in raw_columns if str(column).strip()} if isinstance(raw_columns, list) else set()
    columns.update(FORBIDDEN_X_COLUMNS)
    columns.add("label_*")
    return columns


def _ordered_source_columns(rows: list[dict[str, Any]]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for column in row:
            if column not in seen:
                seen.add(column)
                columns.append(column)
    return columns


def _build_separation_plan(
    source_columns: list[str],
    *,
    row_count: int,
    feature_catalog: dict[str, Any] | None,
) -> FeatureSeparationPlan:
    catalog = feature_catalog if feature_catalog is not None else load_feature_catalog()
    allowed_x_columns = _allowed_x_columns(catalog)
    forbidden_x_columns = _forbidden_x_columns(catalog)
    x_columns = [
        column
        for column in source_columns
        if column in allowed_x_columns and not _is_forbidden_column(column, forbidden_x_columns)
    ]
    raw_y_columns = [column for column in source_columns if _is_label_column(column)]
    raw_metadata_columns = [
        column
        for column in source_columns
        if column in AUDIT_METADATA_COLUMNS and column not in raw_y_columns
    ]
    raw_traceability_columns = [
        column
        for column in source_columns
        if column in TRACEABILITY_COLUMNS and column not in raw_y_columns
    ]
    dropped_columns = _dropped_columns(
        source_columns,
        x_columns=x_columns,
        y_columns=raw_y_columns,
        metadata_columns=raw_metadata_columns,
        traceability_columns=raw_traceability_columns,
        allowed_x_columns=allowed_x_columns,
        forbidden_x_columns=forbidden_x_columns,
    )
    return FeatureSeparationPlan(
        x_columns=x_columns,
        y_columns=["sample_uid", *[column for column in raw_y_columns if column != "sample_uid"]],
        metadata_columns=["sample_uid", *[column for column in raw_metadata_columns if column != "sample_uid"]],
        traceability_columns=["sample_uid", *[column for column in raw_traceability_columns if column != "sample_uid"]],
        dropped_columns=dropped_columns,
        forbidden_x_columns=sorted(forbidden_x_columns),
        source_columns=source_columns,
        row_count=row_count,
    )


def _dropped_columns(
    source_columns: list[str],
    *,
    x_columns: list[str],
    y_columns: list[str],
    metadata_columns: list[str],
    traceability_columns: list[str],
    allowed_x_columns: set[str],
    forbidden_x_columns: set[str],
) -> list[DroppedColumn]:
    x_set = set(x_columns)
    y_set = set(y_columns)
    metadata_set = set(metadata_columns)
    traceability_set = set(traceability_columns)
    dropped: list[DroppedColumn] = []
    for column in source_columns:
        if column in x_set:
            continue
        dropped.append(
            DroppedColumn(
                name=column,
                reason=_drop_reason(
                    column,
                    y_columns=y_set,
                    metadata_columns=metadata_set,
                    traceability_columns=traceability_set,
                    allowed_x_columns=allowed_x_columns,
                    forbidden_x_columns=forbidden_x_columns,
                ),
            )
        )
    return dropped


def _drop_reason(
    column: str,
    *,
    y_columns: set[str],
    metadata_columns: set[str],
    traceability_columns: set[str],
    allowed_x_columns: set[str],
    forbidden_x_columns: set[str],
) -> str:
    if _is_forbidden_column(column, forbidden_x_columns):
        if column in y_columns:
            return "target label stored in y"
        if column in traceability_columns:
            return "forbidden in X; stored in traceability"
        if column in metadata_columns:
            return "forbidden/audit field stored in metadata"
        return "forbidden in X"
    if column in y_columns:
        return "target label stored in y"
    if column in traceability_columns:
        return "traceability field stored outside X"
    if column in metadata_columns:
        return "audit metadata stored outside X"
    if column in allowed_x_columns:
        return "not selected for X by separation policy"
    return "not declared allow_in_X in feature_catalog"


def _row_with_sample_uid(row: dict[str, Any], columns: list[str], sample_uid: str) -> dict[str, Any]:
    output = {"sample_uid": sample_uid}
    for column in columns:
        if column != "sample_uid":
            output[column] = row.get(column)
    return output


def _sample_uid(row: dict[str, Any], index: int) -> str:
    for key in ("sample_uid", "event_uid", "window_id", "flow_id", "sequence_id"):
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return f"sample-{index}"


def _is_label_column(column: str) -> bool:
    return column in LABEL_COLUMNS or column.startswith("label_")


def _is_forbidden_column(column: str, forbidden_columns: set[str]) -> bool:
    return column in forbidden_columns or ("label_*" in forbidden_columns and column.startswith("label_"))


def _is_non_null(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return True


def _contains_absolute_path(value: Any) -> bool:
    if isinstance(value, str):
        return bool(_ABSOLUTE_PATH_RE.search(value.strip()))
    if isinstance(value, list):
        return any(_contains_absolute_path(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_absolute_path(item) for item in value.values())
    return False
