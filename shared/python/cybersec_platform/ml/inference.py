from __future__ import annotations

from typing import Any

import joblib
import numpy as np
import pandas as pd

from cybersec_platform.contracts.api import InferenceRequest
from cybersec_platform.ml.features import align_inference_features, build_sequence_windows

try:
    from cybersec_platform.ml.nn_models import predict_event_cnn, predict_sequence_lstm
except ModuleNotFoundError:  # pragma: no cover - depends on optional local runtime extras.
    predict_event_cnn = None
    predict_sequence_lstm = None


def _map_sequence_probabilities(representative_indices: np.ndarray, probabilities: np.ndarray, size: int) -> np.ndarray:
    event_probabilities = np.full(size, 0.5, dtype=np.float32)
    for index, probability in zip(representative_indices, probabilities, strict=True):
        event_probabilities[int(index)] = float(probability)
    last_probability = 0.5
    for idx in range(size):
        if event_probabilities[idx] != 0.5:
            last_probability = event_probabilities[idx]
        else:
            event_probabilities[idx] = last_probability
    return event_probabilities


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(values, -30.0, 30.0)))


def _predict_linear_fallback(payload: dict[str, Any], features: np.ndarray) -> np.ndarray:
    dense_features = features.mean(axis=1) if payload.get("aggregate_sequences") else features
    weights = np.asarray(payload["weights"], dtype=np.float32)
    bias = float(payload["bias"])
    return _sigmoid(dense_features @ weights + bias).astype(np.float32)


class InferenceEngine:
    def predict(self, request: InferenceRequest, model_bundle: dict[str, Any]) -> list[dict[str, Any]]:
        frame = pd.DataFrame(
            [
                {
                    "entity_id": record.entity_id,
                    "event_ts": record.event_ts,
                    "source_type": record.source_type.value,
                    "label": 0,
                    "attack_stage": None,
                    "mitre_tactic": None,
                    **record.features,
                }
                for record in request.records
            ]
        ).fillna(0.0)
        required_feature_columns = model_bundle["required_feature_columns"]
        feature_columns = model_bundle["feature_columns"]
        aligned_frame = align_inference_features(frame, required_feature_columns, feature_columns)

        rf_prob = model_bundle["models"]["random_forest"].predict_proba(aligned_frame)[:, 1]
        xgb_prob = model_bundle["models"]["xgboost"].predict_proba(aligned_frame)[:, 1]
        cnn_payload = model_bundle["models"]["cnn"]
        if cnn_payload.get("kind") == "linear_fallback":
            cnn_prob = _predict_linear_fallback(cnn_payload, aligned_frame.to_numpy(dtype=np.float32))
        else:
            cnn_prob = predict_event_cnn(cnn_payload, aligned_frame.to_numpy(dtype=np.float32))

        metadata = frame[["entity_id", "event_ts", "source_type", "label", "attack_stage", "mitre_tactic"]].copy()
        metadata["event_ts"] = pd.to_datetime(metadata["event_ts"], utc=True)
        sequence_length = int(model_bundle.get("sequence_length", 50))
        sequence_stride = int(model_bundle.get("sequence_stride", 10))
        sequences, _, representative_indices = build_sequence_windows(
            aligned_frame,
            np.zeros(len(aligned_frame), dtype=np.int64),
            metadata,
            sequence_length,
            sequence_stride,
        )
        lstm_payload = model_bundle["models"]["lstm"]
        if lstm_payload.get("kind") == "linear_fallback":
            lstm_window_prob = _predict_linear_fallback(lstm_payload, sequences)
        else:
            lstm_window_prob = predict_sequence_lstm(lstm_payload, sequences)
        lstm_prob = _map_sequence_probabilities(representative_indices, lstm_window_prob, len(aligned_frame))
        fusion_prob = np.vstack([rf_prob, xgb_prob, cnn_prob, lstm_prob]).mean(axis=0)

        return [
            {
                "entity_id": record.entity_id,
                "score": float(score),
                "predicted_label": int(score >= 0.5),
                "top_features": model_bundle.get("required_feature_columns", [])[:5],
            }
            for record, score in zip(request.records, fusion_prob, strict=True)
        ]


def save_model_bundle(path: str, payload: dict[str, Any]) -> None:
    joblib.dump(payload, path)


def load_model_bundle(path: str) -> dict[str, Any]:
    return joblib.load(path)
