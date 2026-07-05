from __future__ import annotations

import types
import unittest

from scripts.stage_three.reports.path_utils import build_stage_three_task_report_paths
from scripts.stage_three.runtime.resources import (
    StageThreeResourceProfile,
    StageThreeRuntimeSettings,
    get_stage_three_resource_profile,
    resolve_stage_three_runtime_settings,
)


class StageThreeRuntimeConfigTest(unittest.TestCase):
    def test_resolves_runtime_settings_without_db_connection(self) -> None:
        settings = resolve_stage_three_runtime_settings(psutil_module=_psutil(total_gb=64, available_gb=16))

        self.assertEqual(settings.profile_name, "balanced")
        self.assertEqual(settings.acceleration.backend, "auto")
        self.assertEqual(settings.resource_profile.reserved_ram_gb, 8)
        self.assertEqual(settings.total_ram_gb, 64)
        self.assertEqual(settings.memory_probe, "psutil")

    def test_static_memory_fallback_when_psutil_is_missing(self) -> None:
        settings = resolve_stage_three_runtime_settings(psutil_module=False)

        self.assertGreaterEqual(settings.total_ram_gb, 64)
        self.assertIn("psutil", " ".join(settings.warnings).lower())

    def test_rejects_reserved_ram_below_required_floor(self) -> None:
        profile = get_stage_three_resource_profile("safe")
        invalid = StageThreeResourceProfile(
            name=profile.name,
            default_workers=profile.default_workers,
            max_workers=profile.max_workers,
            db_workers=profile.db_workers,
            batch_rows=profile.batch_rows,
            parquet_row_group_size=profile.parquet_row_group_size,
            reserved_ram_gb=4,
            soft_ram_limit_gb=profile.soft_ram_limit_gb,
            hard_ram_limit_gb=profile.hard_ram_limit_gb,
            gpu_memory_soft_limit_gb=profile.gpu_memory_soft_limit_gb,
            gpu_memory_hard_limit_gb=profile.gpu_memory_hard_limit_gb,
        )

        with self.assertRaisesRegex(ValueError, "reserved_ram_gb"):
            StageThreeRuntimeSettings(
                resource_profile=invalid,
                acceleration=resolve_stage_three_runtime_settings(
                    psutil_module=_psutil(total_gb=64, available_gb=16)
                ).acceleration,
                total_ram_gb=64,
                available_ram_gb=16,
                memory_probe="psutil",
            )

    def test_rejects_hard_ram_limit_that_consumes_reserved_ram(self) -> None:
        profile = get_stage_three_resource_profile("balanced")
        invalid = StageThreeResourceProfile(
            name=profile.name,
            default_workers=profile.default_workers,
            max_workers=profile.max_workers,
            db_workers=profile.db_workers,
            batch_rows=profile.batch_rows,
            parquet_row_group_size=profile.parquet_row_group_size,
            reserved_ram_gb=8,
            soft_ram_limit_gb=56,
            hard_ram_limit_gb=60,
            gpu_memory_soft_limit_gb=profile.gpu_memory_soft_limit_gb,
            gpu_memory_hard_limit_gb=profile.gpu_memory_hard_limit_gb,
        )

        with self.assertRaisesRegex(ValueError, "total_ram_gb - reserved_ram_gb"):
            invalid.validate(total_ram_gb=64)

    def test_rejects_invalid_worker_relationships(self) -> None:
        profile = get_stage_three_resource_profile("safe")
        invalid = StageThreeResourceProfile(
            name=profile.name,
            default_workers=8,
            max_workers=4,
            db_workers=2,
            batch_rows=profile.batch_rows,
            parquet_row_group_size=profile.parquet_row_group_size,
            reserved_ram_gb=profile.reserved_ram_gb,
            soft_ram_limit_gb=profile.soft_ram_limit_gb,
            hard_ram_limit_gb=profile.hard_ram_limit_gb,
            gpu_memory_soft_limit_gb=profile.gpu_memory_soft_limit_gb,
            gpu_memory_hard_limit_gb=profile.gpu_memory_hard_limit_gb,
        )

        with self.assertRaisesRegex(ValueError, "default_workers"):
            invalid.validate(total_ram_gb=64)

    def test_builds_stage_three_report_paths_from_config(self) -> None:
        paths = build_stage_three_task_report_paths("Task01-stage-three-config-resource-profile.md")

        self.assertEqual(paths.ru.name, "Task01-stage-three-config-resource-profile.md")
        self.assertEqual(paths.en.name, "Task01-stage-three-config-resource-profile.md")
        self.assertIn("stage-three", str(paths.ru))
        self.assertIn("stage-three", str(paths.en))


def _psutil(*, total_gb: int, available_gb: int) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        virtual_memory=lambda: types.SimpleNamespace(
            total=total_gb * 1024**3,
            available=available_gb * 1024**3,
        )
    )


if __name__ == "__main__":
    unittest.main()
