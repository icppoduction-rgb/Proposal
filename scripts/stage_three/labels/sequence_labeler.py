"""Sequence label alignment wrappers."""

from __future__ import annotations

from typing import Any

from scripts.stage_three.labels.label_policy import LabelAlignmentOutput, align_grouped_samples


def align_sequence_samples(
    rows: list[dict[str, Any]],
    *,
    policy: str,
    sequence_key: str = "sequence_id",
    min_weak_confidence: float = 0.0,
) -> LabelAlignmentOutput:
    """Align labels for sequence-level feature samples."""
    return align_grouped_samples(
        rows,
        policy=policy,
        sample_level="sequence",
        group_key=sequence_key,
        min_weak_confidence=min_weak_confidence,
    )
