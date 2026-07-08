"""Stage Three resource profiles and runtime safety checks."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from config import (
    STAGE_THREE_ACCELERATION_BACKEND,
    STAGE_THREE_BATCH_ROWS,
    STAGE_THREE_DB_WORKERS,
    STAGE_THREE_DEFAULT_PROFILE,
    STAGE_THREE_DEFAULT_WORKERS,
    STAGE_THREE_GPU_MEMORY_HARD_LIMIT_GB,
    STAGE_THREE_GPU_MEMORY_SOFT_LIMIT_GB,
    STAGE_THREE_HARD_RAM_LIMIT_GB,
    STAGE_THREE_MAX_WORKERS,
    STAGE_THREE_PARQUET_ROW_GROUP_SIZE,
    STAGE_THREE_RESERVED_RAM_GB,
    STAGE_THREE_SOFT_RAM_LIMIT_GB,
)


RESOURCE_PROFILE_NAMES: tuple[str, ...] = ("safe", "balanced", "fast", "aggressive")
ACCELERATION_BACKENDS: tuple[str, ...] = ("auto", "cpu", "gpu")
FALLBACK_TOTAL_RAM_GB = 64


@dataclass(frozen=True)
class StageThreeResourceProfile:
    """Bounded CPU, memory, and IO settings for Stage Three jobs."""

    name: str
    default_workers: int
    max_workers: int
    db_workers: int
    batch_rows: int
    parquet_row_group_size: int
    reserved_ram_gb: int
    soft_ram_limit_gb: int
    hard_ram_limit_gb: int
    gpu_memory_soft_limit_gb: int
    gpu_memory_hard_limit_gb: int

    def validate(self, *, total_ram_gb: int) -> None:
        """Validate resource limits against the observed or conservative RAM total."""
        if self.name not in RESOURCE_PROFILE_NAMES:
            allowed = ", ".join(RESOURCE_PROFILE_NAMES)
            raise ValueError(f"resource profile must be one of: {allowed}")
        if self.reserved_ram_gb < 8:
            raise ValueError("reserved_ram_gb must be at least 8")
        if self.hard_ram_limit_gb > total_ram_gb - self.reserved_ram_gb:
            raise ValueError(
                "hard_ram_limit_gb must be less than or equal to "
                "total_ram_gb - reserved_ram_gb"
            )
        if self.soft_ram_limit_gb > self.hard_ram_limit_gb:
            raise ValueError("soft_ram_limit_gb must be less than or equal to hard_ram_limit_gb")
        if self.default_workers > self.max_workers:
            raise ValueError("default_workers must be less than or equal to max_workers")
        if self.db_workers > self.default_workers:
            raise ValueError("db_workers must be less than or equal to default_workers")
        if self.default_workers <= 0 or self.max_workers <= 0 or self.db_workers <= 0:
            raise ValueError("worker counts must be positive integers")
        if self.batch_rows <= 0 or self.parquet_row_group_size <= 0:
            raise ValueError("batch_rows and parquet_row_group_size must be positive integers")
        if self.gpu_memory_soft_limit_gb > self.gpu_memory_hard_limit_gb:
            raise ValueError(
                "gpu_memory_soft_limit_gb must be less than or equal to "
                "gpu_memory_hard_limit_gb"
            )


@dataclass(frozen=True)
class StageThreeAccelerationSettings:
    """CPU/GPU backend selection for optional Stage Three acceleration."""

    backend: str = STAGE_THREE_ACCELERATION_BACKEND

    def __post_init__(self) -> None:
        if self.backend not in ACCELERATION_BACKENDS:
            allowed = ", ".join(ACCELERATION_BACKENDS)
            raise ValueError(f"acceleration backend must be one of: {allowed}")


@dataclass(frozen=True)
class StageThreeRuntimeSettings:
    """Resolved Stage Three runtime settings loaded without opening a DB connection."""

    resource_profile: StageThreeResourceProfile
    acceleration: StageThreeAccelerationSettings
    total_ram_gb: int
    available_ram_gb: float | None
    memory_probe: str
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self.resource_profile.validate(total_ram_gb=self.total_ram_gb)

    @property
    def profile_name(self) -> str:
        return self.resource_profile.name


STAGE_THREE_RESOURCE_PROFILES: dict[str, StageThreeResourceProfile] = {
    "safe": StageThreeResourceProfile(
        name="safe",
        default_workers=2,
        max_workers=4,
        db_workers=1,
        batch_rows=50_000,
        parquet_row_group_size=50_000,
        reserved_ram_gb=8,
        soft_ram_limit_gb=24,
        hard_ram_limit_gb=32,
        gpu_memory_soft_limit_gb=8,
        gpu_memory_hard_limit_gb=10,
    ),
    "balanced": StageThreeResourceProfile(
        name="balanced",
        default_workers=8,
        max_workers=12,
        db_workers=4,
        batch_rows=250_000,
        parquet_row_group_size=250_000,
        reserved_ram_gb=8,
        soft_ram_limit_gb=48,
        hard_ram_limit_gb=56,
        gpu_memory_soft_limit_gb=12,
        gpu_memory_hard_limit_gb=14,
    ),
    "fast": StageThreeResourceProfile(
        name="fast",
        default_workers=12,
        max_workers=16,
        db_workers=4,
        batch_rows=400_000,
        parquet_row_group_size=400_000,
        reserved_ram_gb=8,
        soft_ram_limit_gb=48,
        hard_ram_limit_gb=56,
        gpu_memory_soft_limit_gb=12,
        gpu_memory_hard_limit_gb=14,
    ),
    "aggressive": StageThreeResourceProfile(
        name="aggressive",
        default_workers=16,
        max_workers=20,
        db_workers=6,
        batch_rows=750_000,
        parquet_row_group_size=750_000,
        reserved_ram_gb=8,
        soft_ram_limit_gb=52,
        hard_ram_limit_gb=56,
        gpu_memory_soft_limit_gb=14,
        gpu_memory_hard_limit_gb=15,
    ),
}


def get_stage_three_resource_profile(name: str) -> StageThreeResourceProfile:
    """Return a predefined Stage Three resource profile by name."""
    normalized_name = name.strip().lower()
    try:
        return STAGE_THREE_RESOURCE_PROFILES[normalized_name]
    except KeyError as exc:
        allowed = ", ".join(RESOURCE_PROFILE_NAMES)
        raise ValueError(f"unknown Stage Three resource profile '{name}'; expected one of: {allowed}") from exc


def resolve_stage_three_runtime_settings(
    *,
    profile_name: str | None = None,
    backend: str | None = None,
    psutil_module: Any | None = None,
    batch_rows: int | None = None,
    reserved_ram_gb: int | None = None,
    soft_ram_limit_gb: int | None = None,
    hard_ram_limit_gb: int | None = None,
) -> StageThreeRuntimeSettings:
    """Resolve config-backed Stage Three runtime settings without touching the DB."""
    profile = _configured_profile(
        profile_name or STAGE_THREE_DEFAULT_PROFILE,
        batch_rows=batch_rows,
        reserved_ram_gb=reserved_ram_gb,
        soft_ram_limit_gb=soft_ram_limit_gb,
        hard_ram_limit_gb=hard_ram_limit_gb,
    )
    memory_probe = _probe_memory(psutil_module=psutil_module)
    warnings = tuple(memory_probe["warnings"])
    profile = _clamp_memory_limits_to_host(profile=profile, total_ram_gb=memory_probe["total_ram_gb"])

    settings = StageThreeRuntimeSettings(
        resource_profile=profile,
        acceleration=StageThreeAccelerationSettings(backend=backend or STAGE_THREE_ACCELERATION_BACKEND),
        total_ram_gb=memory_probe["total_ram_gb"],
        available_ram_gb=memory_probe["available_ram_gb"],
        memory_probe=memory_probe["source"],
        warnings=warnings,
    )
    assert_stage_three_memory_available(settings)
    return settings


def assert_stage_three_memory_available(settings: StageThreeRuntimeSettings) -> None:
    """Fail before starting work if available RAM is already below the reserved floor."""
    if settings.available_ram_gb is None:
        return
    if settings.available_ram_gb < settings.resource_profile.reserved_ram_gb:
        raise RuntimeError(
            "available RAM is below the Stage Three reserved floor: "
            f"{settings.available_ram_gb:.2f} GB available, "
            f"{settings.resource_profile.reserved_ram_gb} GB required"
        )


def _configured_profile(
    profile_name: str,
    *,
    batch_rows: int | None = None,
    reserved_ram_gb: int | None = None,
    soft_ram_limit_gb: int | None = None,
    hard_ram_limit_gb: int | None = None,
) -> StageThreeResourceProfile:
    base_profile = get_stage_three_resource_profile(profile_name)
    return replace(
        base_profile,
        default_workers=STAGE_THREE_DEFAULT_WORKERS,
        max_workers=STAGE_THREE_MAX_WORKERS,
        db_workers=STAGE_THREE_DB_WORKERS,
        batch_rows=_resolve_positive_override(batch_rows, "batch_rows", fallback=STAGE_THREE_BATCH_ROWS),
        parquet_row_group_size=_resolve_positive_override(
            batch_rows,
            "batch_rows",
            fallback=STAGE_THREE_PARQUET_ROW_GROUP_SIZE,
        ),
        reserved_ram_gb=_resolve_positive_override(reserved_ram_gb, "reserved_ram_gb", fallback=STAGE_THREE_RESERVED_RAM_GB),
        soft_ram_limit_gb=_resolve_positive_override(soft_ram_limit_gb, "soft_ram_limit_gb", fallback=STAGE_THREE_SOFT_RAM_LIMIT_GB),
        hard_ram_limit_gb=_resolve_positive_override(hard_ram_limit_gb, "hard_ram_limit_gb", fallback=STAGE_THREE_HARD_RAM_LIMIT_GB),
        gpu_memory_soft_limit_gb=STAGE_THREE_GPU_MEMORY_SOFT_LIMIT_GB,
        gpu_memory_hard_limit_gb=STAGE_THREE_GPU_MEMORY_HARD_LIMIT_GB,
    )


def _resolve_positive_override(value: int | None, name: str, *, fallback: int) -> int:
    if value is None:
        return fallback
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _clamp_memory_limits_to_host(profile: StageThreeResourceProfile, total_ram_gb: int) -> StageThreeResourceProfile:
    max_processing_gb = max(0, total_ram_gb - profile.reserved_ram_gb)
    hard_ram_limit_gb = min(profile.hard_ram_limit_gb, max_processing_gb)
    soft_ram_limit_gb = min(profile.soft_ram_limit_gb, hard_ram_limit_gb)
    if hard_ram_limit_gb == 0:
        raise ValueError(
            "reserved RAM is too large for the host; reduce reserved-ram-gb "
            f"or keep the default STAGE_THREE_RESERVED_RAM_GB={STAGE_THREE_RESERVED_RAM_GB}"
        )
    return replace(profile, hard_ram_limit_gb=hard_ram_limit_gb, soft_ram_limit_gb=soft_ram_limit_gb)


def _probe_memory(*, psutil_module: Any | None) -> dict[str, object]:
    warnings: list[str] = []
    module = psutil_module
    psutil_disabled = module is False
    if module is False:
        module = None
        warnings.append("psutil is explicitly disabled for this runtime resolution")
    if module is None and not psutil_disabled:
        try:
            import psutil as module  # type: ignore[import-not-found]
        except ImportError:
            module = None

    if module is None:
        warnings.append(
            "psutil is not installed; using conservative static RAM total "
            f"{FALLBACK_TOTAL_RAM_GB} GB and skipping live available-RAM check"
        )
        return {
            "total_ram_gb": FALLBACK_TOTAL_RAM_GB,
            "available_ram_gb": None,
            "source": "static-fallback",
            "warnings": warnings,
        }

    virtual_memory = module.virtual_memory()
    total_ram_gb = round(virtual_memory.total / 1024**3)
    available_ram_gb = virtual_memory.available / 1024**3
    return {
        "total_ram_gb": int(total_ram_gb),
        "available_ram_gb": float(available_ram_gb),
        "source": "psutil",
        "warnings": warnings,
    }
