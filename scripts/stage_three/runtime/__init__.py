"""Runtime resource controls for Stage Three."""

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
    "STAGE_THREE_RESOURCE_PROFILES",
    "StageThreeAccelerationSettings",
    "StageThreeResourceProfile",
    "StageThreeRuntimeSettings",
    "assert_stage_three_memory_available",
    "get_stage_three_resource_profile",
    "resolve_stage_three_runtime_settings",
]

