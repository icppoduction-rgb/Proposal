"""Split index helpers for Stage Three model-ready datasets."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SplitIndexSummary:
    """Compact summary of the split index created for one experiment."""

    row_count: int
    split_distribution: dict[str, int]


def build_split_index_rows(
    y_rows_by_role: dict[str, list[dict[str, Any]]],
    *,
    experiment_id: str,
    branch: str,
    preprocessing_profile: str,
) -> tuple[list[dict[str, Any]], SplitIndexSummary]:
    """Build a stable sample-to-split index from y rows."""
    rows: list[dict[str, Any]] = []
    distribution: Counter[str] = Counter()
    for role in ("TRAIN", "VALIDATION", "TEST"):
        y_rows = y_rows_by_role.get(role, [])
        for row_index, row in enumerate(y_rows):
            sample_uid = row.get("sample_uid")
            if sample_uid is None or not str(sample_uid).strip():
                raise ValueError(f"y row for role={role} is missing sample_uid at row_index={row_index}")
            rows.append(
                {
                    "experiment_id": experiment_id,
                    "branch": branch,
                    "preprocessing_profile": preprocessing_profile,
                    "role": role,
                    "sample_uid": str(sample_uid),
                    "row_index": row_index,
                }
            )
            distribution[role] += 1
    return rows, SplitIndexSummary(
        row_count=len(rows),
        split_distribution=dict(distribution),
    )


def validate_x_schema_consistency(x_columns_by_role: dict[str, list[str]]) -> list[str]:
    """Validate that X columns match exactly across all provided split roles."""
    if not x_columns_by_role:
        raise ValueError("no X schemas were provided")
    roles = list(x_columns_by_role)
    reference_role = roles[0]
    reference_columns = x_columns_by_role[reference_role]
    for role in roles[1:]:
        columns = x_columns_by_role[role]
        if columns != reference_columns:
            raise ValueError(
                "X schema mismatch between roles: "
                f"{reference_role}={json.dumps(reference_columns)} "
                f"{role}={json.dumps(columns)}"
            )
    return list(reference_columns)
