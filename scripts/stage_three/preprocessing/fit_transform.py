"""Fit/transform orchestration for Task13 missing values and categorical encoding."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import pyarrow as pa

from scripts.stage_three.feature_catalog.loader import load_feature_catalog
from scripts.stage_three.preprocessing.categorical_encoding import (
    CategoricalEncoderArtifact,
    CategoricalEncodingResult,
    fit_categorical_encoder,
    transform_categorical_features,
)
from scripts.stage_three.preprocessing.missing_values import (
    MissingValueImputerArtifact,
    MissingValueTransformResult,
    fit_missing_value_imputer,
    transform_missing_values,
)


@dataclass(frozen=True)
class PreprocessingArtifact:
    """TRAIN-fitted preprocessing artifact for missing values and categorical encoding."""

    fit_role: str
    imputer: MissingValueImputerArtifact
    encoder: CategoricalEncoderArtifact
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON/report friendly preprocessing artifact metadata."""
        return {
            "fit_role": self.fit_role,
            "imputer": self.imputer.to_dict(),
            "encoder": self.encoder.to_dict(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class PreprocessingTransformResult:
    """Rows after imputation and categorical encoding plus preprocessing metadata."""

    rows: list[dict[str, Any]]
    artifact: PreprocessingArtifact
    split_role: str
    missing_result: MissingValueTransformResult
    encoding_result: CategoricalEncodingResult
    report_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return report-friendly preprocessing result metadata."""
        return {
            "split_role": self.split_role,
            "fit_role": self.artifact.fit_role,
            "row_count": len(self.rows),
            "imputer": self.missing_result.to_dict(),
            "encoder": self.encoding_result.to_dict(),
            "preprocessing_metadata": self.artifact.to_dict(),
            "report_paths": dict(self.report_paths),
        }


def fit_preprocessing_artifact(
    rows: list[dict[str, Any]] | pa.Table,
    *,
    role: str,
    feature_catalog: dict[str, Any] | None = None,
) -> PreprocessingArtifact:
    """Fit Task13 preprocessing metadata on TRAIN rows only."""
    catalog = feature_catalog if feature_catalog is not None else load_feature_catalog()
    imputer = fit_missing_value_imputer(rows, role=role, feature_catalog=catalog)
    imputed_train = transform_missing_values(rows, artifact=imputer)
    encoder = fit_categorical_encoder(imputed_train.rows, role=role, feature_catalog=catalog)
    return PreprocessingArtifact(
        fit_role=imputer.fit_role,
        imputer=imputer,
        encoder=encoder,
        metadata={
            "stage": "stage-three",
            "task": "Task13-missing-values-and-categorical-encoding",
            "artifact_type": "preprocessing_metadata",
        },
    )


def transform_with_preprocessing_artifact(
    rows: list[dict[str, Any]] | pa.Table,
    *,
    artifact: PreprocessingArtifact,
    role: str,
) -> PreprocessingTransformResult:
    """Transform one split using TRAIN-fitted preprocessing metadata."""
    missing_result = transform_missing_values(rows, artifact=artifact.imputer)
    encoding_result = transform_categorical_features(missing_result.rows, artifact=artifact.encoder)
    return PreprocessingTransformResult(
        rows=encoding_result.rows,
        artifact=artifact,
        split_role=role.strip().upper(),
        missing_result=missing_result,
        encoding_result=encoding_result,
    )


def fit_transform_train_preprocessing(
    rows: list[dict[str, Any]] | pa.Table,
    *,
    feature_catalog: dict[str, Any] | None = None,
) -> PreprocessingTransformResult:
    """Fit preprocessing on TRAIN and transform the same TRAIN rows."""
    artifact = fit_preprocessing_artifact(rows, role="TRAIN", feature_catalog=feature_catalog)
    return transform_with_preprocessing_artifact(rows, artifact=artifact, role="TRAIN")


def preprocessing_artifact_dict(artifact: PreprocessingArtifact) -> dict[str, Any]:
    """Return a dict for artifact registration or report embedding."""
    return asdict(artifact)
