"""Window and flow label alignment wrappers."""

from __future__ import annotations

from typing import Any

from scripts.stage_three.labels.label_policy import LabelAlignmentOutput, align_grouped_samples


def align_window_samples(
    rows: list[dict[str, Any]],
    *,
    policy: str,
    window_key: str = "window_id",
    min_weak_confidence: float = 0.0,
) -> LabelAlignmentOutput:
    """Align labels for window-level feature samples."""
    return align_grouped_samples(
        rows,
        policy=policy,
        sample_level="window",
        group_key=window_key,
        min_weak_confidence=min_weak_confidence,
    )


def align_flow_samples(
    rows: list[dict[str, Any]],
    *,
    policy: str,
    flow_key: str = "flow_id",
    min_weak_confidence: float = 0.0,
) -> LabelAlignmentOutput:
    """Align labels for flow-level feature samples."""
    return align_grouped_samples(
        rows,
        policy=policy,
        sample_level="flow",
        group_key=flow_key,
        min_weak_confidence=min_weak_confidence,
    )
