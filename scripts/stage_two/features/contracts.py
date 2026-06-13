"""Feature artifact schema contract helpers for Stage Two."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FEATURE_ARTIFACT_SCHEMA_PATH = Path("schemas/features/feature_artifact_v1.json")
FEATURE_SCHEMA_NAME = "feature_artifact"
FEATURE_SCHEMA_VERSION = "v1"
FEATURE_GROUPS: tuple[str, ...] = (
    "dns_features",
    "host_syscall_features",
    "host_eventlog_features",
    "host_metrics_features",
    "network_flow_features",
    "hybrid_features",
    "sequence_features",
)
X_EXCLUDED_COLUMNS: tuple[str, ...] = (
    "label_binary",
    "label_family",
    "label_subtype",
    "label_source",
    "label_status",
    "label_confidence",
    "label_mapping_rule_id",
    "dataset_id",
    "dataset_name",
    "dataset_role",
    "role",
    "branch",
    "source_file_path",
    "source_file_hash",
    "source_normalized_path",
    "source_event_uid_refs",
    "parser_run_id",
    "normalized_artifact_id",
    "feature_group",
    "feature_schema_name",
    "feature_schema_version",
    "event_uid",
    "sample_uid",
    "entity_type",
    "entity_id",
    "window_start",
    "window_end",
    "window_size_seconds",
    "window_step_seconds",
    "scenario_name",
    "raw_fields_json",
    "metadata_json",
    "created_at",
)
REQUIRED_TRACEABILITY_FIELDS: tuple[str, ...] = (
    "sample_uid",
    "dataset_id",
    "normalized_artifact_id",
    "role",
    "branch",
    "feature_group",
    "feature_schema_name",
    "feature_schema_version",
    "source_event_uid_refs",
    "source_normalized_path",
    "created_at",
)


@dataclass(frozen=True)
class FeatureArtifactContract:
    """Loaded feature artifact contract metadata."""

    schema_name: str
    schema_version: str
    feature_groups: tuple[str, ...]
    required_traceability_fields: tuple[str, ...]
    x_excluded_columns: tuple[str, ...]


def load_feature_artifact_contract(path: str | Path = FEATURE_ARTIFACT_SCHEMA_PATH) -> FeatureArtifactContract:
    """Load the feature artifact JSON contract."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return FeatureArtifactContract(
        schema_name=payload["schema_name"],
        schema_version=payload["schema_version"],
        feature_groups=tuple(group["name"] for group in payload["feature_groups"]),
        required_traceability_fields=tuple(payload["required_traceability_fields"]),
        x_excluded_columns=tuple(payload["x_excluded_columns"]),
    )


def validate_feature_group(feature_group: str) -> None:
    """Raise ValueError when a feature group is not part of the Stage Two contract."""
    if feature_group not in FEATURE_GROUPS:
        allowed = ", ".join(FEATURE_GROUPS)
        raise ValueError(f"unsupported feature_group={feature_group!r}; allowed values: {allowed}")


def excluded_columns_payload(extra_columns: list[str] | tuple[str, ...] | None = None) -> dict[str, Any]:
    """Return a catalog-ready excluded columns payload for X contracts."""
    columns = list(X_EXCLUDED_COLUMNS)
    for column in extra_columns or ():
        if column not in columns:
            columns.append(column)
    return {"x_excluded_columns": columns}
