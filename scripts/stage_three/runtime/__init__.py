"""Runtime resource controls for Stage Three."""

from scripts.stage_three.runtime.backend import (
    BackendSelectionResult,
    CpuFeatureExtractionBackend,
    FeatureExtractionRunResult,
    GpuFeatureExtractionBackend,
    select_feature_extraction_backend,
)
from scripts.stage_three.runtime.memory_guard import (
    BatchRuntimeMetric,
    MemoryGuard,
    MemoryGuardDecision,
    MemoryGuardError,
    MemorySnapshot,
)
from scripts.stage_three.runtime.resources import (
    STAGE_THREE_RESOURCE_PROFILES,
    StageThreeAccelerationSettings,
    StageThreeResourceProfile,
    StageThreeRuntimeSettings,
    assert_stage_three_memory_available,
    get_stage_three_resource_profile,
    resolve_stage_three_runtime_settings,
)

__all__ = [
    "BackendSelectionResult",
    "BatchRuntimeMetric",
    "CpuFeatureExtractionBackend",
    "FeatureExtractionRunResult",
    "GpuFeatureExtractionBackend",
    "MemoryGuard",
    "MemoryGuardDecision",
    "MemoryGuardError",
    "MemorySnapshot",
    "STAGE_THREE_RESOURCE_PROFILES",
    "StageThreeAccelerationSettings",
    "StageThreeResourceProfile",
    "StageThreeRuntimeSettings",
    "assert_stage_three_memory_available",
    "get_stage_three_resource_profile",
    "resolve_stage_three_runtime_settings",
    "select_feature_extraction_backend",
]
