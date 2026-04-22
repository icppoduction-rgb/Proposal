from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

from cybersec_platform.contracts.api import FeatureSchemaDefinition
from cybersec_platform.ml.normalization import ContractValidationError, ensure_columns

CORE_EVENT_COLUMNS = ["entity_id", "event_ts", "source_type", "label", "attack_stage", "mitre_tactic"]


def compute_binary_metrics(y_true: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    predictions = (probabilities >= 0.5).astype(int)
    matrix = confusion_matrix(y_true, predictions, labels=[0, 1])
    tn, fp, fn, tp = matrix.ravel()
    fpr = float(fp / max(fp + tn, 1))
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "fpr": fpr,
        "auc": float(roc_auc_score(y_true, probabilities)) if len(np.unique(y_true)) > 1 else 0.5,
    }


def prepare_training_frame(
    frame: pd.DataFrame,
    feature_schema: FeatureSchemaDefinition,
    expanded_feature_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, np.ndarray, pd.DataFrame, list[str]]:
    ensure_columns(frame, CORE_EVENT_COLUMNS + feature_schema.required_columns)
    if frame["source_type"].dropna().nunique() > 1:
        raise ContractValidationError("Normalized dataset must contain a single source_type for a training run")
    source_type = frame["source_type"].dropna().iloc[0]
    if source_type != feature_schema.source_type.value:
        raise ContractValidationError(
            f"Feature schema source_type={feature_schema.source_type.value} does not match dataset source_type={source_type}"
        )

    feature_frame = frame[feature_schema.required_columns].copy()
    categorical_columns = [column for column in feature_frame.columns if feature_frame[column].dtype == "object"]
    if categorical_columns:
        feature_frame = pd.get_dummies(feature_frame, columns=categorical_columns, dummy_na=True)
    feature_frame = feature_frame.fillna(0.0)

    if expanded_feature_columns is not None:
        for column in expanded_feature_columns:
            if column not in feature_frame.columns:
                feature_frame[column] = 0.0
        feature_frame = feature_frame[expanded_feature_columns]
    else:
        expanded_feature_columns = list(feature_frame.columns)

    labels = pd.to_numeric(frame["label"], errors="coerce").fillna(0).astype(int).to_numpy()
    metadata = frame[CORE_EVENT_COLUMNS].copy()
    metadata["event_ts"] = pd.to_datetime(metadata["event_ts"], errors="coerce", utc=True)
    sort_order = metadata.sort_values(["entity_id", "event_ts"]).index.to_numpy()
    metadata = metadata.loc[sort_order].reset_index(drop=True)

    reordered = feature_frame.iloc[sort_order].reset_index(drop=True)
    labels = labels[sort_order]
    return reordered, labels, metadata, list(expanded_feature_columns)


def build_sequence_windows(
    feature_frame: pd.DataFrame,
    labels: np.ndarray,
    metadata: pd.DataFrame,
    sequence_length: int,
    sequence_stride: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    windows: list[np.ndarray] = []
    window_labels: list[int] = []
    representative_indices: list[int] = []

    for _, group in metadata.groupby("entity_id", sort=False):
        group_indices = group.index.to_list()
        if not group_indices:
            continue
        if len(group_indices) < sequence_length:
            padded_indices = group_indices + [group_indices[-1]] * (sequence_length - len(group_indices))
            windows.append(feature_frame.iloc[padded_indices].to_numpy(dtype=np.float32))
            window_labels.append(int(labels[group_indices].max()))
            representative_indices.append(group_indices[-1])
            continue
        for start in range(0, len(group_indices) - sequence_length + 1, sequence_stride):
            sample_indices = group_indices[start : start + sequence_length]
            windows.append(feature_frame.iloc[sample_indices].to_numpy(dtype=np.float32))
            window_labels.append(int(labels[sample_indices].max()))
            representative_indices.append(sample_indices[-1])

    if not windows:
        raise ContractValidationError("Unable to construct sequence windows from the normalized dataset")

    return np.asarray(windows, dtype=np.float32), np.asarray(window_labels, dtype=np.float32), np.asarray(representative_indices, dtype=np.int64)


def align_inference_features(
    frame: pd.DataFrame,
    required_feature_columns: list[str],
    expanded_feature_columns: list[str],
) -> pd.DataFrame:
    missing_required = [column for column in required_feature_columns if column not in frame.columns]
    if missing_required:
        raise ContractValidationError(f"Inference payload is missing required schema fields: {missing_required}")
    feature_frame = frame[required_feature_columns].copy()
    categorical_columns = [column for column in feature_frame.columns if feature_frame[column].dtype == "object"]
    if categorical_columns:
        feature_frame = pd.get_dummies(feature_frame, columns=categorical_columns, dummy_na=True)
    feature_frame = feature_frame.fillna(0.0)
    for column in expanded_feature_columns:
        if column not in feature_frame.columns:
            feature_frame[column] = 0.0
    return feature_frame[expanded_feature_columns]
