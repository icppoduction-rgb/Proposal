"""Feature artifact contracts and placeholder writers for Stage Two."""

from scripts.stage_two.features.contracts import (
    FEATURE_ARTIFACT_SCHEMA_PATH,
    FEATURE_GROUPS,
    FEATURE_SCHEMA_NAME,
    FEATURE_SCHEMA_VERSION,
    REQUIRED_TRACEABILITY_FIELDS,
    X_EXCLUDED_COLUMNS,
    FeatureArtifactContract,
    excluded_columns_payload,
    load_feature_artifact_contract,
    validate_feature_group,
)
from scripts.stage_two.features.writer import (
    FeatureArtifactWriteResult,
    FeatureArtifactWriter,
    infer_feature_count,
)

__all__ = [
    "FEATURE_ARTIFACT_SCHEMA_PATH",
    "FEATURE_GROUPS",
    "FEATURE_SCHEMA_NAME",
    "FEATURE_SCHEMA_VERSION",
    "REQUIRED_TRACEABILITY_FIELDS",
    "X_EXCLUDED_COLUMNS",
    "FeatureArtifactContract",
    "FeatureArtifactWriteResult",
    "FeatureArtifactWriter",
    "excluded_columns_payload",
    "infer_feature_count",
    "load_feature_artifact_contract",
    "validate_feature_group",
]
