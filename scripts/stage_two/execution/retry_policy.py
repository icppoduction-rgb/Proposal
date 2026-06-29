"""Retry and error-sample policy for Stage Two work units."""

from __future__ import annotations

from dataclasses import dataclass

from config import STAGE_TWO_MAX_ERROR_SAMPLES


@dataclass(frozen=True)
class RetryPolicy:
    """Policy object for bounded, explicit parser failure handling."""

    max_attempts: int = 1
    max_error_samples: int = STAGE_TWO_MAX_ERROR_SAMPLES

    def __post_init__(self) -> None:
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be a positive integer")
        if self.max_error_samples <= 0:
            raise ValueError("max_error_samples must be a positive integer")

    def trim_error_samples(self, samples: list[str] | tuple[str, ...]) -> tuple[str, ...]:
        """Limit stored error samples to the configured bound."""
        return tuple(samples[: self.max_error_samples])
