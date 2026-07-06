"""Stage Three preprocessing helpers."""

from scripts.stage_three.preprocessing.categorical_encoding import (
    CategoricalEncoderArtifact,
    CategoricalEncodingResult,
    EncoderColumnState,
    fit_categorical_encoder,
    transform_categorical_features,
)
from scripts.stage_three.preprocessing.fit_transform import (
    PreprocessingArtifact,
    PreprocessingTransformResult,
    fit_preprocessing_artifact,
    fit_transform_train_preprocessing,
    transform_with_preprocessing_artifact,
)
from scripts.stage_three.preprocessing.missing_values import (
    ImputerColumnState,
    MissingValueImputerArtifact,
    MissingValueTransformResult,
    PreprocessingFitRoleError,
    fit_missing_value_imputer,
    transform_missing_values,
)
from scripts.stage_three.preprocessing.type_casting import (
    DTypeConversion,
    RejectedColumn,
    SchemaWarning,
    TypeCastingResult,
    cast_x_artifacts_to_typed_table,
    cast_x_batches_to_typed_table,
    cast_x_rows_to_typed_table,
    cast_x_table_to_typed_table,
)

__all__ = [
    "CategoricalEncoderArtifact",
    "CategoricalEncodingResult",
    "DTypeConversion",
    "EncoderColumnState",
    "ImputerColumnState",
    "MissingValueImputerArtifact",
    "MissingValueTransformResult",
    "PreprocessingArtifact",
    "PreprocessingFitRoleError",
    "PreprocessingTransformResult",
    "RejectedColumn",
    "SchemaWarning",
    "TypeCastingResult",
    "cast_x_artifacts_to_typed_table",
    "cast_x_batches_to_typed_table",
    "cast_x_rows_to_typed_table",
    "cast_x_table_to_typed_table",
    "fit_categorical_encoder",
    "fit_missing_value_imputer",
    "fit_preprocessing_artifact",
    "fit_transform_train_preprocessing",
    "transform_categorical_features",
    "transform_missing_values",
    "transform_with_preprocessing_artifact",
]
