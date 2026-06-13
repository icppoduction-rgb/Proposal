"""Model-ready artifact contract helpers for Stage Two."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from scripts.stage_two.features import X_EXCLUDED_COLUMNS


MODEL_READY_SCHEMA_PATH = Path("schemas/model_ready/model_ready_v1.json")
MODEL_READY_SCHEMA_NAME = "model_ready"
MODEL_READY_SCHEMA_VERSION = "v1"
MODEL_READY_DATA_TYPES: tuple[str, ...] = (
    "X",
    "y",
    "sequence",
    "split_index",
    "preprocessing_metadata",
)
TRAIN_FIT_ROLE = "TRAIN"
X_FORBIDDEN_COLUMNS: tuple[str, ...] = X_EXCLUDED_COLUMNS


@dataclass(frozen=True)
class ModelReadyContract:
    """Loaded model-ready artifact contract metadata."""

    schema_name: str
    schema_version: str
    data_types: tuple[str, ...]
    x_forbidden_columns: tuple[str, ...]
    preprocessing_fit_allowed_role: str


def load_model_ready_contract(path: str | Path = MODEL_READY_SCHEMA_PATH) -> ModelReadyContract:
    """Load the model-ready JSON contract."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return ModelReadyContract(
        schema_name=payload["schema_name"],
        schema_version=payload["schema_version"],
        data_types=tuple({artifact["data_type"] for artifact in payload["artifacts"]}),
        x_forbidden_columns=tuple(payload["x_forbidden_columns"]),
        preprocessing_fit_allowed_role=payload["preprocessing"]["fit_allowed_role"],
    )


def validate_model_ready_data_type(data_type: str) -> None:
    """Raise ValueError for unsupported model-ready data types."""
    if data_type not in MODEL_READY_DATA_TYPES:
        allowed = ", ".join(MODEL_READY_DATA_TYPES)
        raise ValueError(f"unsupported model-ready data_type={data_type!r}; allowed values: {allowed}")


def validate_preprocessing_fit_role(fitted_on_role: str) -> None:
    """Enforce TRAIN-only preprocessing fitting."""
    if fitted_on_role != TRAIN_FIT_ROLE:
        raise ValueError("preprocessing artifacts must be fitted_on_role='TRAIN'")


def validate_x_columns(rows: list[dict[str, object]]) -> None:
    """Reject X rows containing label/source leakage columns."""
    forbidden = set(X_FORBIDDEN_COLUMNS)
    present = sorted(set().union(*(row.keys() for row in rows)) & forbidden) if rows else []
    if present:
        columns = ", ".join(present)
        raise ValueError(f"X artifact contains forbidden leakage columns: {columns}")
