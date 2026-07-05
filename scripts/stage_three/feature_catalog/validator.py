"""Validate the Stage Three feature catalog contract."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any


PASS = "PASS"
FAIL = "FAIL"

ALLOWED_BRANCHES = frozenset({"dns", "host", "network", "hybrid", "sequence"})
ALLOWED_LEVELS = frozenset({"event", "window", "flow", "trace", "sequence", "hybrid"})
ALLOWED_DTYPES = frozenset(
    {
        "numeric",
        "integer",
        "numeric_vector",
        "categorical",
        "boolean",
        "binary",
        "datetime",
        "duration",
        "text_token",
        "token_sequence",
    }
)

FORBIDDEN_X_COLUMNS = frozenset(
    {
        "dataset_name",
        "dataset_role",
        "source_file",
        "source_path",
        "source_file_path",
        "scenario_name",
        "parser_name",
        "parser_version",
        "raw_fields_json",
        "metadata_json",
        "event_uid",
        "source_file_id",
        "file_id",
        "parser_run_id",
        "normalized_artifact_id",
        "dataset_id",
        "label_binary",
        "label_family",
        "label_subtype",
        "label_source",
        "label_status",
        "label_confidence",
        "label_mapping_rule_id",
    }
)

MISSING_BY_DTYPE = {
    "numeric": frozenset({"none", "zero", "mean", "median", "constant"}),
    "integer": frozenset({"none", "zero", "median", "constant"}),
    "numeric_vector": frozenset({"none", "zero", "constant"}),
    "duration": frozenset({"none", "zero", "mean", "median", "constant"}),
    "categorical": frozenset({"none", "unknown", "most_frequent", "constant"}),
    "boolean": frozenset({"none", "false", "most_frequent"}),
    "binary": frozenset({"none", "zero", "most_frequent"}),
    "datetime": frozenset({"none", "drop", "constant"}),
    "text_token": frozenset({"none", "empty", "unknown"}),
    "token_sequence": frozenset({"none", "empty", "unknown"}),
}
SCALING_BY_DTYPE = {
    "numeric": frozenset({"none", "standard", "minmax", "robust"}),
    "integer": frozenset({"none", "standard", "minmax", "robust"}),
    "numeric_vector": frozenset({"none", "standard", "minmax", "l2"}),
    "duration": frozenset({"none", "standard", "minmax", "robust"}),
    "categorical": frozenset({"none"}),
    "boolean": frozenset({"none"}),
    "binary": frozenset({"none"}),
    "datetime": frozenset({"none"}),
    "text_token": frozenset({"none"}),
    "token_sequence": frozenset({"none"}),
}
ENCODING_BY_DTYPE = {
    "numeric": frozenset({"none"}),
    "integer": frozenset({"none"}),
    "numeric_vector": frozenset({"none"}),
    "duration": frozenset({"none"}),
    "categorical": frozenset({"none", "one_hot", "ordinal", "hashing", "target_safe"}),
    "boolean": frozenset({"none", "boolean"}),
    "binary": frozenset({"none", "binary"}),
    "datetime": frozenset({"none", "timestamp_parts", "cyclical"}),
    "text_token": frozenset({"none", "hashing", "token_id", "vocabulary"}),
    "token_sequence": frozenset({"none", "token_id", "vocabulary"}),
}


@dataclass(frozen=True)
class FeatureCatalogIssue:
    """One validation issue in the feature catalog."""

    path: str
    message: str


@dataclass(frozen=True)
class FeatureCatalogValidationResult:
    """Feature catalog validation result used by CLI, reports, and tests."""

    status: str
    catalog_version: str
    feature_group_count: int
    feature_count: int
    enabled_feature_groups: list[str]
    planned_feature_groups: list[str]
    forbidden_X_columns: list[str]
    issues: list[FeatureCatalogIssue] = field(default_factory=list)
    normalized_snapshot_path: str | None = None
    report_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON/Markdown friendly payload."""
        return asdict(self)


def validate_feature_catalog(catalog: dict[str, Any]) -> FeatureCatalogValidationResult:
    """Validate the catalog contract without touching storage or the database."""
    issues: list[FeatureCatalogIssue] = []
    version = _required_text(catalog.get("version"), "version", issues)
    _required_text(catalog.get("project"), "project", issues)
    _required_text(catalog.get("stage"), "stage", issues)

    forbidden_columns = _forbidden_columns(catalog, issues)
    groups = catalog.get("feature_groups")
    if not isinstance(groups, dict) or not groups:
        issues.append(FeatureCatalogIssue("feature_groups", "feature_groups must be a non-empty mapping"))
        groups = {}

    feature_names: list[str] = []
    enabled_groups: list[str] = []
    planned_groups: list[str] = []

    for group_name, group in groups.items():
        group_path = f"feature_groups.{group_name}"
        if not isinstance(group, dict):
            issues.append(FeatureCatalogIssue(group_path, "feature group must be a mapping"))
            continue
        if bool(group.get("enabled", False)):
            enabled_groups.append(str(group_name))
        if bool(group.get("planned", False)):
            planned_groups.append(str(group_name))
        _validate_group(group_name=str(group_name), group=group, path=group_path, issues=issues)
        features = group.get("features", [])
        if isinstance(features, list):
            for index, feature in enumerate(features):
                feature_path = f"{group_path}.features[{index}]"
                if isinstance(feature, dict):
                    name = _validate_feature(feature, feature_path, forbidden_columns, issues)
                    if name:
                        feature_names.append(name)
                else:
                    issues.append(FeatureCatalogIssue(feature_path, "feature must be a mapping"))

    _validate_unique_feature_names(feature_names, issues)
    return FeatureCatalogValidationResult(
        status=FAIL if issues else PASS,
        catalog_version=version,
        feature_group_count=len(groups),
        feature_count=len(feature_names),
        enabled_feature_groups=sorted(enabled_groups),
        planned_feature_groups=sorted(planned_groups),
        forbidden_X_columns=sorted(forbidden_columns),
        issues=issues,
    )


def _validate_group(
    *,
    group_name: str,
    group: dict[str, Any],
    path: str,
    issues: list[FeatureCatalogIssue],
) -> None:
    branch = group.get("branch")
    if not isinstance(branch, str) or not branch.strip():
        issues.append(FeatureCatalogIssue(f"{path}.branch", "branch must exist"))
    elif branch.strip().lower() not in ALLOWED_BRANCHES:
        issues.append(FeatureCatalogIssue(f"{path}.branch", f"unsupported branch: {branch}"))
    level = group.get("level")
    if not isinstance(level, str) or not level.strip():
        issues.append(FeatureCatalogIssue(f"{path}.level", "level must exist"))
    elif level.strip().lower() not in ALLOWED_LEVELS:
        issues.append(FeatureCatalogIssue(f"{path}.level", f"unsupported level: {level}"))
    if "planned" not in group:
        issues.append(FeatureCatalogIssue(f"{path}.planned", "planned must be explicit"))
    mappings = group.get("extractor_mappings", [])
    if group.get("planned") is not False and not mappings:
        issues.append(
            FeatureCatalogIssue(
                f"{path}.extractor_mappings",
                "feature group must have at least one extractor mapping or planned=false",
            )
        )
    features = group.get("features")
    if not isinstance(features, list) or not features:
        issues.append(FeatureCatalogIssue(f"{path}.features", f"{group_name} must define at least one feature"))


def _validate_feature(
    feature: dict[str, Any],
    path: str,
    forbidden_columns: set[str],
    issues: list[FeatureCatalogIssue],
) -> str | None:
    name = feature.get("name")
    if not isinstance(name, str) or not name.strip():
        issues.append(FeatureCatalogIssue(f"{path}.name", "feature name must exist"))
        return None
    feature_name = name.strip()
    dtype = feature.get("dtype")
    if not isinstance(dtype, str) or not dtype.strip():
        issues.append(FeatureCatalogIssue(f"{path}.dtype", "dtype must exist"))
    elif dtype.strip() not in ALLOWED_DTYPES:
        issues.append(FeatureCatalogIssue(f"{path}.dtype", f"unsupported dtype: {dtype}"))
    preprocessing = feature.get("preprocessing")
    if not isinstance(preprocessing, dict):
        issues.append(FeatureCatalogIssue(f"{path}.preprocessing", "preprocessing strategy must exist"))
        preprocessing = {}
    if "allow_in_X" not in feature or not isinstance(feature.get("allow_in_X"), bool):
        issues.append(FeatureCatalogIssue(f"{path}.allow_in_X", "allow_in_X must be explicit boolean"))
    elif feature["allow_in_X"] and _is_forbidden_x_column(feature_name, forbidden_columns):
        issues.append(FeatureCatalogIssue(f"{path}.allow_in_X", "forbidden X column cannot allow_in_X=true"))
    if isinstance(dtype, str) and dtype.strip() in ALLOWED_DTYPES:
        _validate_preprocessing_compatibility(dtype.strip(), preprocessing, path, issues)
    return feature_name


def _validate_preprocessing_compatibility(
    dtype: str,
    preprocessing: dict[str, Any],
    path: str,
    issues: list[FeatureCatalogIssue],
) -> None:
    for key in ("missing", "scaling", "encoding"):
        if key not in preprocessing or not isinstance(preprocessing.get(key), str) or not preprocessing[key].strip():
            issues.append(FeatureCatalogIssue(f"{path}.preprocessing.{key}", f"{key} strategy must exist"))
    missing = str(preprocessing.get("missing", "")).strip()
    scaling = str(preprocessing.get("scaling", "")).strip()
    encoding = str(preprocessing.get("encoding", "")).strip()
    if missing and missing not in MISSING_BY_DTYPE[dtype]:
        issues.append(FeatureCatalogIssue(f"{path}.preprocessing.missing", f"{missing} is incompatible with {dtype}"))
    if scaling and scaling not in SCALING_BY_DTYPE[dtype]:
        issues.append(FeatureCatalogIssue(f"{path}.preprocessing.scaling", f"{scaling} is incompatible with {dtype}"))
    if encoding and encoding not in ENCODING_BY_DTYPE[dtype]:
        issues.append(FeatureCatalogIssue(f"{path}.preprocessing.encoding", f"{encoding} is incompatible with {dtype}"))


def _validate_unique_feature_names(feature_names: list[str], issues: list[FeatureCatalogIssue]) -> None:
    counts = Counter(feature_names)
    duplicates = sorted(name for name, count in counts.items() if count > 1)
    if duplicates:
        issues.append(
            FeatureCatalogIssue(
                "feature_groups.*.features.name",
                f"feature names must be unique: {', '.join(duplicates)}",
            )
        )


def _forbidden_columns(catalog: dict[str, Any], issues: list[FeatureCatalogIssue]) -> set[str]:
    raw_values = catalog.get("forbidden_X_columns")
    if not isinstance(raw_values, list) or not raw_values:
        issues.append(FeatureCatalogIssue("forbidden_X_columns", "forbidden_X_columns must be a non-empty list"))
        return set(FORBIDDEN_X_COLUMNS)
    normalized = {str(value).strip() for value in raw_values if str(value).strip()}
    required = set(FORBIDDEN_X_COLUMNS)
    required.add("label_*")
    missing = sorted(required.difference(normalized))
    if missing:
        issues.append(
            FeatureCatalogIssue(
                "forbidden_X_columns",
                f"missing required forbidden X columns: {', '.join(missing)}",
            )
        )
    return normalized


def _is_forbidden_x_column(name: str, forbidden_columns: set[str]) -> bool:
    normalized = name.strip()
    return normalized in forbidden_columns or ("label_*" in forbidden_columns and normalized.startswith("label_"))


def _required_text(value: Any, path: str, issues: list[FeatureCatalogIssue]) -> str:
    if not isinstance(value, str) or not value.strip():
        issues.append(FeatureCatalogIssue(path, f"{path} must exist"))
        return ""
    return value.strip()
