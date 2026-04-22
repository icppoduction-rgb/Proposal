from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, train_test_split
from xgboost import XGBClassifier

from cybersec_platform.contracts.api import DatasetManifest, FeatureSchemaDefinition
from cybersec_platform.ml.features import align_inference_features, build_sequence_windows, compute_binary_metrics, prepare_training_frame
from cybersec_platform.ml.normalization import ContractValidationError

try:
    import shap
except ModuleNotFoundError:  # pragma: no cover - depends on optional local runtime extras.
    shap = None

try:
    import torch
    from cybersec_platform.ml.nn_models import EventCnnBinaryClassifier, SequenceLstmBinaryClassifier, predict_event_cnn, predict_sequence_lstm
except ModuleNotFoundError:  # pragma: no cover - depends on optional local runtime extras.
    torch = None
    EventCnnBinaryClassifier = None
    SequenceLstmBinaryClassifier = None
    predict_event_cnn = None
    predict_sequence_lstm = None


def _json_safe(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return str(value)


def _read_normalized_frame(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["event_ts"] = pd.to_datetime(frame["event_ts"], errors="coerce", utc=True)
    return frame


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(values, -30.0, 30.0)))


def _extract_shap_row_values(shap_values: Any, sample_count: int, feature_count: int) -> np.ndarray:
    values = np.asarray(shap_values, dtype=float)
    if values.ndim == 1:
        if values.shape[0] != feature_count:
            raise ContractValidationError("SHAP output does not match the expected feature count")
        return values
    if values.ndim == 2:
        if values.shape == (sample_count, feature_count):
            return values[0]
        if values.shape[0] == feature_count:
            return values[:, -1]
        raise ContractValidationError("SHAP output shape is not supported for binary explanations")
    if values.ndim == 3:
        if values.shape[0] == sample_count and values.shape[1] == feature_count:
            return values[0, :, -1]
        if values.shape[0] >= 2 and values.shape[1] == sample_count and values.shape[2] == feature_count:
            return values[-1, 0, :]
        raise ContractValidationError("SHAP output tensor shape is not supported for binary explanations")
    raise ContractValidationError("SHAP output rank is not supported for binary explanations")


def _train_linear_fallback(features: np.ndarray, labels: np.ndarray, *, aggregate_sequences: bool = False) -> dict[str, Any]:
    if aggregate_sequences:
        dense_features = features.mean(axis=1)
    else:
        dense_features = features
    positive = dense_features[labels >= 0.5]
    negative = dense_features[labels < 0.5]
    positive_centroid = positive.mean(axis=0) if len(positive) else np.ones(dense_features.shape[1], dtype=np.float32)
    negative_centroid = negative.mean(axis=0) if len(negative) else np.zeros(dense_features.shape[1], dtype=np.float32)
    weights = (positive_centroid - negative_centroid).astype(np.float32)
    bias = float(-0.5 * np.dot(positive_centroid + negative_centroid, weights))
    return {
        "kind": "linear_fallback",
        "input_size": int(dense_features.shape[1]),
        "weights": weights.tolist(),
        "bias": bias,
        "aggregate_sequences": aggregate_sequences,
    }


def _predict_linear_fallback(payload: dict[str, Any], features: np.ndarray) -> np.ndarray:
    dense_features = features.mean(axis=1) if payload.get("aggregate_sequences") else features
    weights = np.asarray(payload["weights"], dtype=np.float32)
    bias = float(payload["bias"])
    return _sigmoid(dense_features @ weights + bias).astype(np.float32)


def _train_event_cnn(features: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
    if torch is None or EventCnnBinaryClassifier is None:
        return _train_linear_fallback(features, labels)
    model = EventCnnBinaryClassifier(input_size=features.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = torch.nn.BCELoss()
    tensor_x = torch.tensor(features[:, None, :], dtype=torch.float32)
    tensor_y = torch.tensor(labels[:, None], dtype=torch.float32)
    for _ in range(18):
        optimizer.zero_grad()
        predictions = model(tensor_x)
        loss = criterion(predictions, tensor_y)
        loss.backward()
        optimizer.step()
    return {"state_dict": model.state_dict(), "input_size": features.shape[1]}


def _train_sequence_branch(sequences: np.ndarray, labels: np.ndarray, input_size: int) -> dict[str, Any]:
    if torch is None or SequenceLstmBinaryClassifier is None:
        payload = _train_linear_fallback(sequences, labels, aggregate_sequences=True)
        payload["hidden_size"] = 24
        return payload
    model = SequenceLstmBinaryClassifier(input_size=input_size)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = torch.nn.BCELoss()
    tensor_x = torch.tensor(sequences, dtype=torch.float32)
    tensor_y = torch.tensor(labels[:, None], dtype=torch.float32)
    for _ in range(16):
        optimizer.zero_grad()
        predictions = model(tensor_x)
        loss = criterion(predictions, tensor_y)
        loss.backward()
        optimizer.step()
    return {"state_dict": model.state_dict(), "input_size": input_size, "hidden_size": 24}


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


def _cross_validation_report(feature_frame: pd.DataFrame, labels: np.ndarray) -> dict[str, Any]:
    class_counts = np.bincount(labels.astype(int))
    min_class_count = int(class_counts.min()) if len(class_counts) > 1 else 0
    if min_class_count < 2:
        return {"folds": [], "notes": "Cross-validation skipped because the dataset does not contain enough samples per class."}

    n_splits = min(3, min_class_count)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    sampled_x = feature_frame
    sampled_y = labels
    if len(feature_frame) > 5000:
        label_series = pd.Series(labels)
        sample_size = int(min(2500, label_series.value_counts().min()))
        sample_indices = label_series.groupby(label_series).sample(n=sample_size, random_state=42).index.sort_values()
        sampled_x = feature_frame.iloc[sample_indices].reset_index(drop=True)
        sampled_y = labels[sample_indices.to_numpy()]

    folds = []
    for fold_index, (train_indices, test_indices) in enumerate(skf.split(sampled_x, sampled_y), start=1):
        x_train = sampled_x.iloc[train_indices]
        x_test = sampled_x.iloc[test_indices]
        y_train = sampled_y[train_indices]
        y_test = sampled_y[test_indices]
        rf = RandomForestClassifier(n_estimators=80, random_state=42)
        xgb = XGBClassifier(
            n_estimators=30,
            max_depth=4,
            learning_rate=0.1,
            subsample=1.0,
            colsample_bytree=1.0,
            objective="binary:logistic",
            eval_metric="logloss",
        )
        rf.fit(x_train, y_train)
        xgb.fit(x_train, y_train)
        fusion_probability = (rf.predict_proba(x_test)[:, 1] + xgb.predict_proba(x_test)[:, 1]) / 2.0
        folds.append({"fold": fold_index, **compute_binary_metrics(y_test, fusion_probability)})

    return {"folds": folds, "n_splits": n_splits, "notes": "Cross-validation report uses an event-level fusion proxy."}


class HybridTrainer:
    def train(
        self,
        normalized_path: str,
        manifest: DatasetManifest,
        request: dict[str, Any],
        feature_schema: FeatureSchemaDefinition,
        reports_dir: str | None = None,
    ) -> dict[str, Any]:
        frame = _read_normalized_frame(normalized_path)
        feature_frame, labels, metadata, expanded_feature_columns = prepare_training_frame(frame, feature_schema)
        if len(np.unique(labels)) < 2:
            raise ContractValidationError("Training requires at least two classes in the normalized dataset")

        indices = np.arange(len(feature_frame))
        train_indices, test_indices = train_test_split(
            indices,
            test_size=0.25,
            random_state=42,
            stratify=labels,
        )

        x_train = feature_frame.iloc[train_indices].reset_index(drop=True)
        x_test = feature_frame.iloc[test_indices].reset_index(drop=True)
        y_train = labels[train_indices]
        y_test = labels[test_indices]
        meta_train = metadata.iloc[train_indices].reset_index(drop=True)
        meta_test = metadata.iloc[test_indices].reset_index(drop=True)

        random_forest = RandomForestClassifier(n_estimators=120, random_state=42)
        random_forest.fit(x_train, y_train)

        xgb = XGBClassifier(
            n_estimators=60,
            max_depth=4,
            learning_rate=0.1,
            subsample=1.0,
            colsample_bytree=1.0,
            objective="binary:logistic",
            eval_metric="logloss",
        )
        xgb.fit(x_train, y_train)

        cnn_payload = _train_event_cnn(x_train.to_numpy(dtype=np.float32), y_train.astype(np.float32))
        train_sequences, train_sequence_labels, _ = build_sequence_windows(
            x_train,
            y_train,
            meta_train,
            request.get("sequence_length", 50),
            request.get("sequence_stride", 10),
        )
        lstm_payload = _train_sequence_branch(train_sequences, train_sequence_labels, x_train.shape[1])

        rf_prob = random_forest.predict_proba(x_test)[:, 1]
        xgb_prob = xgb.predict_proba(x_test)[:, 1]
        if cnn_payload.get("kind") == "linear_fallback":
            cnn_prob = _predict_linear_fallback(cnn_payload, x_test.to_numpy(dtype=np.float32))
        else:
            cnn_prob = predict_event_cnn(cnn_payload, x_test.to_numpy(dtype=np.float32))
        test_sequences, _, representative_indices = build_sequence_windows(
            x_test,
            y_test,
            meta_test,
            request.get("sequence_length", 50),
            request.get("sequence_stride", 10),
        )
        if lstm_payload.get("kind") == "linear_fallback":
            lstm_window_prob = _predict_linear_fallback(lstm_payload, test_sequences)
        else:
            lstm_window_prob = predict_sequence_lstm(lstm_payload, test_sequences)
        lstm_prob = _map_sequence_probabilities(representative_indices, lstm_window_prob, len(x_test))

        fusion_prob = np.vstack([rf_prob, xgb_prob, cnn_prob, lstm_prob]).mean(axis=0)

        branch_metrics = {
            "random_forest": compute_binary_metrics(y_test, rf_prob),
            "xgboost": compute_binary_metrics(y_test, xgb_prob),
            "cnn": compute_binary_metrics(y_test, cnn_prob),
            "lstm": compute_binary_metrics(y_test, lstm_prob),
            "fusion": compute_binary_metrics(y_test, fusion_prob),
        }
        metrics = {**branch_metrics["fusion"], "branch_metrics": branch_metrics}

        reports: dict[str, str] = {}
        cv_report = _cross_validation_report(feature_frame, labels)
        ablation_report = {
            "branch_metrics": branch_metrics,
            "notes": "Ablation compares individual branches against late fusion on the holdout split.",
        }
        if reports_dir:
            reports_path = Path(reports_dir)
            reports_path.mkdir(parents=True, exist_ok=True)
            cv_path = reports_path / f"{Path(normalized_path).stem}-cv.json"
            cv_path.write_text(json.dumps(_json_safe(cv_report), indent=2), encoding="utf-8")
            reports["cross_validation_report_path"] = str(cv_path)
            ablation_path = reports_path / f"{Path(normalized_path).stem}-ablation.json"
            ablation_path.write_text(json.dumps(_json_safe(ablation_report), indent=2), encoding="utf-8")
            reports["ablation_report_path"] = str(ablation_path)

        return {
            "metrics": metrics,
            "feature_columns": expanded_feature_columns,
            "required_feature_columns": feature_schema.required_columns,
            "feature_schema": feature_schema.model_dump(mode="json"),
            "reports": reports,
            "cross_validation": cv_report,
            "ablation": ablation_report,
            "models": {
                "random_forest": random_forest,
                "xgboost": xgb,
                "cnn": cnn_payload,
                "lstm": lstm_payload,
            },
        }

    def explain_record(self, model_bundle: dict[str, Any], feature_payload: dict[str, Any], top_k: int = 10) -> dict[str, Any]:
        required_feature_columns = model_bundle["required_feature_columns"]
        feature_columns = model_bundle["feature_columns"]
        frame = pd.DataFrame([feature_payload]).fillna(0.0)
        frame = align_inference_features(frame, required_feature_columns, feature_columns)
        pairs = self._build_explanation_pairs(model_bundle, frame, feature_columns)
        pairs.sort(key=lambda item: abs(item[1]), reverse=True)

        top_positive = [{"feature": name, "contribution": value} for name, value in pairs if value >= 0][:top_k]
        top_negative = [{"feature": name, "contribution": value} for name, value in pairs if value < 0][:top_k]
        feature_families = model_bundle.get("feature_schema", {}).get("feature_families", [])
        mitre_tactic_hints = sorted(set(model_bundle.get("feature_schema", {}).get("mitre_tactics", {}).values()))
        summary = (
            "SHAP explanations are generated from the promoted random forest branch within the hybrid pipeline."
            if shap is not None
            else "SHAP is unavailable in the current runtime, so the explanation falls back to random-forest feature importances."
        )
        return {
            "top_positive": top_positive,
            "top_negative": top_negative,
            "summary": summary,
            "model_branch": "random_forest",
            "feature_family_hints": feature_families,
            "mitre_tactic_hints": mitre_tactic_hints,
        }

    def _build_explanation_pairs(
        self,
        model_bundle: dict[str, Any],
        frame: pd.DataFrame,
        feature_columns: list[str],
    ) -> list[tuple[str, float]]:
        """Return per-feature contributions for explanation payloads.

        Falls back to feature importances when the optional SHAP dependency is
        not available in the current Python runtime.
        """

        if shap is not None:
            explainer = shap.TreeExplainer(model_bundle["models"]["random_forest"])
            shap_values = explainer.shap_values(frame)
            raw_payload = shap_values[1] if isinstance(shap_values, list) and len(shap_values) > 1 else shap_values
            raw_values = _extract_shap_row_values(raw_payload, len(frame), len(feature_columns))
            return list(zip(feature_columns, raw_values.tolist(), strict=True))

        importances = model_bundle["models"]["random_forest"].feature_importances_.tolist()
        row_values = frame.iloc[0].to_numpy(dtype=float)
        fallback_scores = [float(value) * float(weight) for value, weight in zip(row_values, importances, strict=True)]
        return list(zip(feature_columns, fallback_scores, strict=True))
