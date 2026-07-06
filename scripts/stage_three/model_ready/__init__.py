"""Stage Three model-ready dataset preparation helpers."""

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
    "SequenceBuildResult",
    "SequenceOrderingError",
    "SequencePolicy",
    "SequenceWindow",
    "build_sequence_windows",
    "save_sequence_builder_reports",
    "separate_feature_artifact_rows",
    "separate_feature_artifact_table",
    "separate_feature_artifacts",
    "sequence_windows_to_tables",
    "validate_no_forbidden_x_columns",
]
