"""Feature artifact quality checks for Stage Three."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow as pa

from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.feature_catalog.validator import FORBIDDEN_X_COLUMNS
from scripts.stage_three.quality.common import (
    QualityCheckRecord,
    duckdb_dict,
    duckdb_scalar,
    fail_check,
    parquet_paths_from_parts,
    parquet_row_count,
    parquet_schema,
    pass_check,
    quoted_identifier,
    warn_check,
)


FEATURE_REQUIRED_BASE_COLUMNS = ("sample_uid",)
KNOWN_NON_FEATURE_COLUMNS = {
    "sample_uid",
    "event_uid",
    "dataset_id",
    "dataset_name",
    "dataset_role",
    "branch",
    "feature_group",
    "source_file",
    "source_path",
    "source_normalized_path",
    "source_file_path",
    "source_file_id",
    "file_id",
    "parser_run_id",
    "normalized_artifact_id",
    "parser_name",
    "parser_version",
    "scenario_name",
    "raw_fields_json",
    "metadata_json",
    "event_timestamp",
    "timestamp",
    "timestamp_type",
    "event_order",
    "label_binary",
    "label_family",
    "label_subtype",
    "label_source",
    "label_status",
    "label_confidence",
    "label_mapping_rule_id",
    "role",
    "source_event_uid_refs",
    "feature_schema_name",
    "feature_schema_version",
    "created_at",
}
DEFAULT_MISSING_RATIO_THRESHOLD = 0.95


def run_feature_quality_checks(
    feature_artifacts: list[Any],
    *,
    storage_root: str | Path,
    feature_catalog: dict[str, Any] | None = None,
    missing_ratio_threshold: float = DEFAULT_MISSING_RATIO_THRESHOLD,
) -> list[QualityCheckRecord]:
    """Run quality checks for feature artifacts using metadata, projection, and DuckDB."""
    catalog = feature_catalog or load_feature_catalog()
    records: list[QualityCheckRecord] = []
    for artifact in feature_artifacts:
        records.extend(
            _check_feature_artifact(
                artifact,
                storage_root=storage_root,
                feature_catalog=catalog,
                missing_ratio_threshold=missing_ratio_threshold,
            )
        )
    return records


def _check_feature_artifact(
    artifact: Any,
    *,
    storage_root: str | Path,
    feature_catalog: dict[str, Any],
    missing_ratio_threshold: float,
) -> list[QualityCheckRecord]:
    artifact_id = int(artifact.id)
    paths = parquet_paths_from_parts(
        getattr(artifact, "metadata_json", None),
        getattr(artifact, "feature_path"),
        storage_root=storage_root,
    )
    group_name = getattr(artifact, "feature_group")
    group_config = _catalog_group(feature_catalog, group_name)
    group_features = _catalog_features(feature_catalog, group_name)
    expected_feature_names = [feature["name"] for feature in group_features]
    records: list[QualityCheckRecord] = []
    if not paths:
        return [
            fail_check(
                check_group="feature_quality",
                check_name="feature_artifact_exists",
                artifact_type="feature",
                artifact_id=artifact_id,
                message="feature artifact path does not resolve to Parquet files",
                details={"feature_path": getattr(artifact, "feature_path", None)},
            )
        ]

    try:
        row_count = parquet_row_count(paths)
        schema = parquet_schema(paths)
    except Exception as exc:
        return [
            fail_check(
                check_group="feature_quality",
                check_name="feature_artifact_readable",
                artifact_type="feature",
                artifact_id=artifact_id,
                message="feature artifact is not readable as Parquet",
                details={"error": str(exc), "paths": [path.as_posix() for path in paths]},
            )
        ]

    columns = list(schema.names)
    records.append(_check_not_empty(artifact_id, row_count, paths))
    records.append(_check_required_columns(artifact_id, columns, expected_feature_names))
    records.append(_check_sample_uid_unique(artifact_id, paths, columns, row_count))
    records.append(_check_dtypes(artifact_id, schema, group_features))
    records.append(_check_missing_ratios(artifact_id, paths, columns, group_features, row_count, missing_ratio_threshold))
    label_record, label_distribution = _check_label_coverage(artifact_id, paths, columns, row_count)
    records.append(label_record)
    records.append(
        _check_timestamp_coverage(
            artifact_id,
            paths,
            columns,
            row_count,
            timestamp_required=_timestamp_required(group_config),
            feature_group=group_name,
        )
    )
    records.append(_check_schema_drift(artifact_id, columns, expected_feature_names))
    records.append(_check_class_distribution(artifact_id, columns, label_distribution))
    records.append(_check_forbidden_feature_fields(artifact_id, expected_feature_names))
    return records


def _check_not_empty(artifact_id: int, row_count: int, paths: list[Path]) -> QualityCheckRecord:
    if row_count <= 0:
        return fail_check(
            check_group="feature_quality",
            check_name="feature_artifact_not_empty",
            artifact_type="feature",
            artifact_id=artifact_id,
            message="feature artifact has zero rows",
            rows_total=row_count,
            details={"paths": [path.as_posix() for path in paths]},
        )
    return pass_check(
        check_group="feature_quality",
        check_name="feature_artifact_not_empty",
        artifact_type="feature",
        artifact_id=artifact_id,
        message="feature artifact has rows",
        rows_total=row_count,
        details={"paths": [path.as_posix() for path in paths]},
    )


def _check_required_columns(
    artifact_id: int,
    columns: list[str],
    expected_feature_names: list[str],
) -> QualityCheckRecord:
    required = [*FEATURE_REQUIRED_BASE_COLUMNS, *expected_feature_names]
    missing = [column for column in required if column not in columns]
    if missing:
        return fail_check(
            check_group="feature_quality",
            check_name="required_columns_present",
            artifact_type="feature",
            artifact_id=artifact_id,
            message="feature artifact is missing required columns",
            schema_mismatch_count=len(missing),
            details={"missing_columns": missing, "required_columns": required},
        )
    return pass_check(
        check_group="feature_quality",
        check_name="required_columns_present",
        artifact_type="feature",
        artifact_id=artifact_id,
        message="required feature columns are present",
        details={"required_columns": required},
    )


def _check_sample_uid_unique(
    artifact_id: int,
    paths: list[Path],
    columns: list[str],
    row_count: int,
) -> QualityCheckRecord:
    if "sample_uid" not in columns:
        return fail_check(
            check_group="feature_quality",
            check_name="sample_uid_unique",
            artifact_type="feature",
            artifact_id=artifact_id,
            message="sample_uid cannot be checked because the column is missing",
            rows_total=row_count,
        )
    unique_count = int(duckdb_scalar(paths, 'COUNT(DISTINCT "sample_uid")'))
    duplicates = max(row_count - unique_count, 0)
    if duplicates:
        return fail_check(
            check_group="feature_quality",
            check_name="sample_uid_unique",
            artifact_type="feature",
            artifact_id=artifact_id,
            message="sample_uid contains duplicate values",
            rows_total=row_count,
            rows_failed=duplicates,
            duplicate_rows_count=duplicates,
            details={"unique_sample_uid_count": unique_count},
        )
    return pass_check(
        check_group="feature_quality",
        check_name="sample_uid_unique",
        artifact_type="feature",
        artifact_id=artifact_id,
        message="sample_uid is unique",
        rows_total=row_count,
        details={"unique_sample_uid_count": unique_count},
    )


def _check_dtypes(
    artifact_id: int,
    schema: pa.Schema,
    group_features: list[dict[str, Any]],
) -> QualityCheckRecord:
    mismatches: list[dict[str, str]] = []
    field_by_name = {field.name: field for field in schema}
    for feature in group_features:
        name = feature["name"]
        if name not in field_by_name:
            continue
        actual = field_by_name[name].type
        expected = str(feature.get("dtype", ""))
        if not _arrow_type_matches(expected, actual):
            mismatches.append(
                {
                    "column": name,
                    "expected_catalog_dtype": expected,
                    "actual_arrow_dtype": str(actual),
                }
            )
    if mismatches:
        return fail_check(
            check_group="feature_quality",
            check_name="dtypes_match_feature_catalog",
            artifact_type="feature",
            artifact_id=artifact_id,
            message="feature artifact dtypes do not match the feature catalog",
            blocking=False,
            schema_mismatch_count=len(mismatches),
            details={"mismatches": mismatches},
        )
    return pass_check(
        check_group="feature_quality",
        check_name="dtypes_match_feature_catalog",
        artifact_type="feature",
        artifact_id=artifact_id,
        message="feature dtypes match the feature catalog",
    )


def _check_missing_ratios(
    artifact_id: int,
    paths: list[Path],
    columns: list[str],
    group_features: list[dict[str, Any]],
    row_count: int,
    threshold: float,
) -> QualityCheckRecord:
    if row_count <= 0:
        return fail_check(
            check_group="feature_quality",
            check_name="missing_ratio_below_threshold_or_documented",
            artifact_type="feature",
            artifact_id=artifact_id,
            message="missing ratio cannot be checked on an empty feature artifact",
            rows_total=row_count,
        )
    violations: list[dict[str, Any]] = []
    documented: list[dict[str, Any]] = []
    total_missing = 0
    for feature in group_features:
        name = feature["name"]
        if name not in columns:
            continue
        missing = int(duckdb_scalar(paths, f"SUM(CASE WHEN {quoted_identifier(name)} IS NULL THEN 1 ELSE 0 END)"))
        total_missing += missing
        ratio = missing / row_count
        if ratio <= threshold:
            continue
        item = {"column": name, "missing_count": missing, "missing_ratio": ratio}
        if bool(feature.get("nullable")) or str((feature.get("preprocessing") or {}).get("missing", "none")) != "none":
            documented.append(item)
        else:
            violations.append(item)
    if violations:
        return fail_check(
            check_group="feature_quality",
            check_name="missing_ratio_below_threshold_or_documented",
            artifact_type="feature",
            artifact_id=artifact_id,
            message="undocumented missing ratio exceeds threshold",
            blocking=False,
            rows_total=row_count,
            missing_values_count=total_missing,
            details={"threshold": threshold, "violations": violations, "documented_high_missing": documented},
        )
    if documented:
        return warn_check(
            check_group="feature_quality",
            check_name="missing_ratio_below_threshold_or_documented",
            artifact_type="feature",
            artifact_id=artifact_id,
            message="high missing ratios are documented by catalog nullability/preprocessing",
            rows_total=row_count,
            missing_values_count=total_missing,
            details={"threshold": threshold, "documented_high_missing": documented},
        )
    return pass_check(
        check_group="feature_quality",
        check_name="missing_ratio_below_threshold_or_documented",
        artifact_type="feature",
        artifact_id=artifact_id,
        message="feature missing ratios are below threshold",
        rows_total=row_count,
        details={"threshold": threshold, "missing_values_count": total_missing},
    )


def _check_label_coverage(
    artifact_id: int,
    paths: list[Path],
    columns: list[str],
    row_count: int,
) -> tuple[QualityCheckRecord, dict[str, Any]]:
    label_column = _first_present(columns, ("label_binary", "label_status", "label_family"))
    if label_column is None:
        distribution = {"missing_label_columns": True}
        return (
            warn_check(
                check_group="feature_quality",
                check_name="label_coverage_calculated",
                artifact_type="feature",
                artifact_id=artifact_id,
                message="feature artifact has no label columns; label coverage is unavailable",
                rows_total=row_count,
                label_distribution=distribution,
            ),
            distribution,
        )
    distribution = duckdb_dict(
        paths,
        f"SELECT CAST({quoted_identifier(label_column)} AS VARCHAR), COUNT(*) FROM {{relation}} GROUP BY 1 ORDER BY 1",
    )
    null_count = int(duckdb_scalar(paths, f"SUM(CASE WHEN {quoted_identifier(label_column)} IS NULL THEN 1 ELSE 0 END)"))
    coverage = {
        "label_column": label_column,
        "distribution": distribution,
        "labeled_rows": row_count - null_count,
        "unlabeled_rows": null_count,
        "coverage_ratio": 0.0 if row_count == 0 else (row_count - null_count) / row_count,
    }
    return (
        pass_check(
            check_group="feature_quality",
            check_name="label_coverage_calculated",
            artifact_type="feature",
            artifact_id=artifact_id,
            message="label coverage was calculated",
            rows_total=row_count,
            rows_valid=row_count - null_count,
            details=coverage,
        ),
        coverage,
    )


def _check_timestamp_coverage(
    artifact_id: int,
    paths: list[Path],
    columns: list[str],
    row_count: int,
    *,
    timestamp_required: bool,
    feature_group: str,
) -> QualityCheckRecord:
    timestamp_column = _first_present(columns, ("event_timestamp", "timestamp"))
    if timestamp_column is None:
        if not timestamp_required:
            coverage = {"missing_timestamp_columns": True, "timestamp_required": False}
            return pass_check(
                check_group="feature_quality",
                check_name="timestamp_coverage_calculated",
                artifact_type="feature",
                artifact_id=artifact_id,
                message="timestamp coverage is not required for this feature group",
                rows_total=row_count,
                details={"feature_group": feature_group, **coverage},
            )
        coverage = {"missing_timestamp_columns": True}
        return warn_check(
            check_group="feature_quality",
            check_name="timestamp_coverage_calculated",
            artifact_type="feature",
            artifact_id=artifact_id,
            message="timestamp coverage is unavailable because no timestamp column is present",
            rows_total=row_count,
            timestamp_coverage=coverage,
            details={"feature_group": feature_group, "timestamp_required": True},
        )
    non_null = int(duckdb_scalar(paths, f"COUNT({quoted_identifier(timestamp_column)})"))
    coverage = {
        "timestamp_column": timestamp_column,
        "rows_with_timestamp": non_null,
        "rows_without_timestamp": row_count - non_null,
        "coverage_ratio": 0.0 if row_count == 0 else non_null / row_count,
    }
    return pass_check(
        check_group="feature_quality",
        check_name="timestamp_coverage_calculated",
        artifact_type="feature",
        artifact_id=artifact_id,
        message="timestamp coverage was calculated",
        rows_total=row_count,
        rows_valid=non_null,
        details=coverage,
    )


def _check_schema_drift(
    artifact_id: int,
    columns: list[str],
    expected_feature_names: list[str],
) -> QualityCheckRecord:
    expected = set(expected_feature_names)
    actual_feature_like = {
        column for column in columns if column not in KNOWN_NON_FEATURE_COLUMNS and not column.startswith("label_")
    }
    missing = sorted(expected.difference(actual_feature_like))
    extra = sorted(actual_feature_like.difference(expected))
    if missing:
        return fail_check(
            check_group="feature_quality",
            check_name="schema_drift_detected_documented",
            artifact_type="feature",
            artifact_id=artifact_id,
            message="feature schema drift removes catalog columns",
            schema_mismatch_count=len(missing) + len(extra),
            details={"missing_catalog_features": missing, "extra_feature_like_columns": extra},
        )
    if extra:
        return warn_check(
            check_group="feature_quality",
            check_name="schema_drift_detected_documented",
            artifact_type="feature",
            artifact_id=artifact_id,
            message="feature artifact has extra feature-like columns not listed in the catalog",
            schema_mismatch_count=len(extra),
            details={"extra_feature_like_columns": extra},
        )
    return pass_check(
        check_group="feature_quality",
        check_name="schema_drift_detected_documented",
        artifact_type="feature",
        artifact_id=artifact_id,
        message="no feature schema drift detected",
    )


def _check_class_distribution(
    artifact_id: int,
    columns: list[str],
    label_distribution: dict[str, Any],
) -> QualityCheckRecord:
    if not any(column.startswith("label_") for column in columns):
        return warn_check(
            check_group="feature_quality",
            check_name="class_distribution_calculated",
            artifact_type="feature",
            artifact_id=artifact_id,
            message="class distribution is unavailable because no label columns are present",
            label_distribution=label_distribution,
        )
    return QualityCheckRecord(
        check_group="feature_quality",
        check_name="class_distribution_calculated",
        artifact_type="feature",
        artifact_id=artifact_id,
        status="PASS",
        severity="INFO",
        message="class distribution was calculated",
        label_distribution=label_distribution,
        details=label_distribution,
    )


def _check_forbidden_feature_fields(
    artifact_id: int,
    expected_feature_names: list[str],
) -> QualityCheckRecord:
    forbidden = sorted(
        name for name in expected_feature_names if name in FORBIDDEN_X_COLUMNS or name.startswith("label_")
    )
    if forbidden:
        return fail_check(
            check_group="feature_quality",
            check_name="feature_columns_do_not_contain_forbidden_fields",
            artifact_type="feature",
            artifact_id=artifact_id,
            message="feature catalog exposes forbidden fields as feature columns",
            leakage_issue_count=len(forbidden),
            details={"forbidden_feature_columns": forbidden},
        )
    return pass_check(
        check_group="feature_quality",
        check_name="feature_columns_do_not_contain_forbidden_fields",
        artifact_type="feature",
        artifact_id=artifact_id,
        message="feature catalog columns do not include forbidden X fields",
    )


def _catalog_features(catalog: dict[str, Any], feature_group: str) -> list[dict[str, Any]]:
    group = _catalog_group(catalog, feature_group)
    features = group.get("features", []) if isinstance(group, dict) else []
    if not isinstance(features, list):
        return []
    return [
        {"name": str(feature["name"]), **feature}
        for feature in features
        if isinstance(feature, dict) and isinstance(feature.get("name"), str)
    ]


def _catalog_group(catalog: dict[str, Any], feature_group: str) -> dict[str, Any]:
    groups = catalog.get("feature_groups", {})
    group = groups.get(feature_group, {}) if isinstance(groups, dict) else {}
    return group if isinstance(group, dict) else {}


def _timestamp_required(group_config: dict[str, Any]) -> bool:
    mappings = group_config.get("extractor_mappings")
    if not isinstance(mappings, list):
        return True
    for mapping in mappings:
        if not isinstance(mapping, dict):
            continue
        source_fields = mapping.get("source_fields")
        if not isinstance(source_fields, list):
            continue
        if any(str(field) in {"event_timestamp", "timestamp"} for field in source_fields):
            return True
    return False


def _arrow_type_matches(expected: str, actual: pa.DataType) -> bool:
    expected = expected.strip()
    if expected == "integer":
        return pa.types.is_integer(actual)
    if expected in {"numeric", "duration"}:
        return pa.types.is_integer(actual) or pa.types.is_floating(actual) or pa.types.is_decimal(actual)
    if expected == "boolean":
        return pa.types.is_boolean(actual)
    if expected == "binary":
        return pa.types.is_boolean(actual) or pa.types.is_integer(actual)
    if expected in {"categorical", "text_token", "token_sequence"}:
        return pa.types.is_string(actual) or pa.types.is_dictionary(actual) or pa.types.is_large_string(actual)
    if expected == "datetime":
        return pa.types.is_timestamp(actual) or pa.types.is_date(actual)
    if expected == "numeric_vector":
        return pa.types.is_list(actual) or pa.types.is_large_list(actual) or pa.types.is_fixed_size_list(actual)
    return False


def _first_present(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None
