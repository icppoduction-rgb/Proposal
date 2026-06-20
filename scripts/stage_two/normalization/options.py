"""Runtime options for Stage Two normalization performance tuning."""

from __future__ import annotations

from dataclasses import dataclass

from config import (
    STAGE_TWO_DEFAULT_BATCH_SIZE,
    STAGE_TWO_DEFAULT_WORKERS,
    STAGE_TWO_HASH_OUTPUT_ARTIFACTS,
    STAGE_TWO_MAX_OUTPUT_PART_ROWS,
    STAGE_TWO_PACKET_PARSE_MODE,
)


@dataclass(frozen=True)
class NormalizationOptions:
    """Execution options shared by CLI, runners, and normalization services."""

    workers: int = STAGE_TWO_DEFAULT_WORKERS
    batch_size: int = STAGE_TWO_DEFAULT_BATCH_SIZE
    max_output_part_rows: int = STAGE_TWO_MAX_OUTPUT_PART_ROWS
    resume: bool = False
    packet_mode: str = STAGE_TWO_PACKET_PARSE_MODE
    hash_outputs: bool = STAGE_TWO_HASH_OUTPUT_ARTIFACTS
    sample_size: int | None = None

    def __post_init__(self) -> None:
        if self.workers <= 0:
            raise ValueError("workers must be a positive integer")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be a positive integer")
        if self.max_output_part_rows <= 0:
            raise ValueError("max_output_part_rows must be a positive integer")
        if self.packet_mode not in {"packet-summary", "dns-only", "sample"}:
            raise ValueError("packet_mode must be one of: packet-summary, dns-only, sample")
        if self.packet_mode == "sample" and self.sample_size is None:
            raise ValueError("sample_size is required when packet_mode is sample")
        if self.sample_size is not None and self.sample_size <= 0:
            raise ValueError("sample_size must be a positive integer when provided")
