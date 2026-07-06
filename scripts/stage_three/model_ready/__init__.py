"""Stage Three model-ready dataset preparation helpers."""

from scripts.stage_three.model_ready.builder import (
    ModelReadyBuildResult,
    ModelReadyRoleBuildResult,
    build_model_ready_artifacts,
)
from scripts.stage_three.model_ready.registry import (
    ModelReadyArtifactRegistryService,
    RegisteredModelReadyArtifact,
)
from scripts.stage_three.model_ready.separator import (
    DroppedColumn,
    FeatureSeparationResult,
    ForbiddenXColumnError,
    ModelReadyTables,
    separate_feature_artifact_rows,
    separate_feature_artifact_table,
    separate_feature_artifacts,
    validate_no_forbidden_x_columns,
)
from scripts.stage_three.model_ready.split_index import (
    SplitIndexSummary,
    build_split_index_rows,
    validate_x_schema_consistency,
)
from scripts.stage_three.model_ready.sequence_builder import (
    SequenceBuildResult,
    SequenceOrderingError,
    SequencePolicy,
    SequenceWindow,
    build_sequence_windows,
    save_sequence_builder_reports,
    sequence_windows_to_tables,
)

__all__ = [
    "DroppedColumn",
    "FeatureSeparationResult",
    "ForbiddenXColumnError",
    "ModelReadyTables",
    "ModelReadyArtifactRegistryService",
    "ModelReadyBuildResult",
    "ModelReadyRoleBuildResult",
    "RegisteredModelReadyArtifact",
    "SequenceBuildResult",
    "SequenceOrderingError",
    "SequencePolicy",
    "SequenceWindow",
    "SplitIndexSummary",
    "build_model_ready_artifacts",
    "build_split_index_rows",
    "build_sequence_windows",
    "save_sequence_builder_reports",
    "separate_feature_artifact_rows",
    "separate_feature_artifact_table",
    "separate_feature_artifacts",
    "sequence_windows_to_tables",
    "validate_no_forbidden_x_columns",
    "validate_x_schema_consistency",
]
