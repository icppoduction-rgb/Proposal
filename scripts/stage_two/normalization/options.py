"""Runtime options for Stage Two normalization performance tuning."""

from __future__ import annotations

from dataclasses import dataclass

from config import (
    STAGE_TWO_DEFAULT_BATCH_SIZE,
    STAGE_TWO_DEFAULT_WORKERS,
    STAGE_TWO_HASH_OUTPUT_ARTIFACTS,
    STAGE_TWO_MAX_OUTPUT_PART_ROWS,
    STAGE_TWO_PACKET_BATCH_SIZE,
    STAGE_TWO_PACKET_PARSE_MODE,
)


RESOURCE_PROFILE_NAMES: tuple[str, ...] = ("safe", "balanced", "fast", "aggressive")
PACKET_SOURCE_FORMATS: frozenset[str] = frozenset({"cap", "pcap", "pcapng"})
EXECUTION_ENGINE_NAMES: tuple[str, ...] = ("cpu", "gpu", "auto")


@dataclass(frozen=True)
class ResourceProfile:
    """Preset runtime settings for Stage Two normalization."""

    workers: int
    batch_size: int
    max_output_part_rows: int
    packet_batch_size: int
    hash_outputs: bool


RESOURCE_PROFILES: dict[str, ResourceProfile] = {
    "safe": ResourceProfile(
        workers=4,
        batch_size=50_000,
        max_output_part_rows=100_000,
        packet_batch_size=50_000,
        hash_outputs=False,
    ),
    "balanced": ResourceProfile(
        workers=8,
        batch_size=100_000,
        max_output_part_rows=250_000,
        packet_batch_size=50_000,
        hash_outputs=False,
    ),
    "fast": ResourceProfile(
        workers=12,
        batch_size=200_000,
        max_output_part_rows=500_000,
        packet_batch_size=50_000,
        hash_outputs=False,
    ),
    "aggressive": ResourceProfile(
        workers=14,
        batch_size=300_000,
        max_output_part_rows=750_000,
        packet_batch_size=50_000,
        hash_outputs=False,
    ),
}


@dataclass(frozen=True)
class NormalizationOptions:
    """Execution options shared by CLI, runners, and normalization services."""

    workers: int = STAGE_TWO_DEFAULT_WORKERS
    batch_size: int = STAGE_TWO_DEFAULT_BATCH_SIZE
    max_output_part_rows: int = STAGE_TWO_MAX_OUTPUT_PART_ROWS
    packet_batch_size: int = STAGE_TWO_PACKET_BATCH_SIZE
    resume: bool = False
    packet_mode: str = STAGE_TWO_PACKET_PARSE_MODE
    hash_outputs: bool = STAGE_TWO_HASH_OUTPUT_ARTIFACTS
    sample_size: int | None = None
    resource_profile: str | None = None
    engine: str = "cpu"

    def __post_init__(self) -> None:
        if self.workers <= 0:
            raise ValueError("workers must be a positive integer")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be a positive integer")
        if self.max_output_part_rows <= 0:
            raise ValueError("max_output_part_rows must be a positive integer")
        if self.packet_batch_size <= 0:
            raise ValueError("packet_batch_size must be a positive integer")
        if self.resource_profile is not None and self.resource_profile not in RESOURCE_PROFILES:
            allowed = ", ".join(RESOURCE_PROFILE_NAMES)
            raise ValueError(f"resource_profile must be one of: {allowed}")
        if self.packet_mode not in {"packet-summary", "dns-only", "sample"}:
            raise ValueError("packet_mode must be one of: packet-summary, dns-only, sample")
        if self.packet_mode == "sample" and self.sample_size is None:
            raise ValueError("sample_size is required when packet_mode is sample")
        if self.sample_size is not None and self.sample_size <= 0:
            raise ValueError("sample_size must be a positive integer when provided")
        if self.engine not in EXECUTION_ENGINE_NAMES:
            allowed = ", ".join(EXECUTION_ENGINE_NAMES)
            raise ValueError(f"engine must be one of: {allowed}")


def resolve_normalization_options(
    *,
    resource_profile: str | None = None,
    workers: int | None = None,
    batch_size: int | None = None,
    max_output_part_rows: int | None = None,
    packet_batch_size: int | None = None,
    resume: bool = False,
    packet_mode: str | None = None,
    hash_outputs: bool | None = None,
    sample_size: int | None = None,
    engine: str | None = None,
) -> NormalizationOptions:
    """Resolve defaults, optional profile values, and explicit CLI overrides."""
    normalized_profile = _normalize_profile_name(resource_profile)
    profile = RESOURCE_PROFILES.get(normalized_profile) if normalized_profile else None

    return NormalizationOptions(
        workers=workers if workers is not None else (profile.workers if profile else STAGE_TWO_DEFAULT_WORKERS),
        batch_size=(
            batch_size if batch_size is not None else (profile.batch_size if profile else STAGE_TWO_DEFAULT_BATCH_SIZE)
        ),
        max_output_part_rows=(
            max_output_part_rows
            if max_output_part_rows is not None
            else (profile.max_output_part_rows if profile else STAGE_TWO_MAX_OUTPUT_PART_ROWS)
        ),
        packet_batch_size=(
            packet_batch_size
            if packet_batch_size is not None
            else (profile.packet_batch_size if profile else STAGE_TWO_PACKET_BATCH_SIZE)
        ),
        resume=resume,
        packet_mode=packet_mode or STAGE_TWO_PACKET_PARSE_MODE,
        hash_outputs=(
            hash_outputs
            if hash_outputs is not None
            else (profile.hash_outputs if profile else STAGE_TWO_HASH_OUTPUT_ARTIFACTS)
        ),
        sample_size=sample_size,
        resource_profile=normalized_profile,
        engine=engine or "cpu",
    )


def batch_size_for_source_format(source_format: str, options: NormalizationOptions) -> int:
    """Return packet-safe batch size for packet captures, general batch size otherwise."""
    if source_format.strip().lower() in PACKET_SOURCE_FORMATS:
        return options.packet_batch_size
    return options.batch_size


def resource_profile_warning(resource_profile: str | None) -> str | None:
    """Return an operator-facing warning for high-risk profiles."""
    normalized_profile = _normalize_profile_name(resource_profile)
    if normalized_profile == "aggressive":
        return (
            "aggressive profile increases CPU/IO pressure; use only after a smaller "
            "profile passes parser, Parquet, DuckDB, leakage, and traceability checks"
        )
    return None


def _normalize_profile_name(resource_profile: str | None) -> str | None:
    if resource_profile is None or not resource_profile.strip():
        return None
    normalized_profile = resource_profile.strip().lower()
    if normalized_profile not in RESOURCE_PROFILES:
        allowed = ", ".join(RESOURCE_PROFILE_NAMES)
        raise ValueError(f"unknown resource profile '{resource_profile}'; expected one of: {allowed}")
    return normalized_profile
