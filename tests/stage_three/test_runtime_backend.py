from __future__ import annotations

import tempfile
import types
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.stage_three.cli import router_stage_three
from scripts.stage_three.runtime.backend import (
    CpuFeatureExtractionBackend,
    GpuAvailability,
    select_feature_extraction_backend,
)
from scripts.stage_three.runtime.memory_guard import MemoryGuard, MemoryGuardError
from scripts.stage_three.runtime.report import TASK06_REPORT_FILENAME
from scripts.stage_three.runtime.resources import resolve_stage_three_runtime_settings


class StageThreeRuntimeBackendTest(unittest.TestCase):
    def test_cpu_backend_reads_required_columns_and_writes_bounded_parts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "input.parquet"
            output_dir = root / "parts"
            pq.write_table(
                pa.table(
                    {
                        "required_a": [1, 2, 3],
                        "required_b": ["x", "y", "z"],
                        "ignored": [10, 20, 30],
                    }
                ),
                input_path,
            )
            guard = MemoryGuard(
                reserved_ram_gb=8,
                soft_ram_limit_gb=48,
                hard_ram_limit_gb=56,
                psutil_module=_psutil(available_gb=16, rss_gb=0.2),
            )

            result = CpuFeatureExtractionBackend().extract_to_parquet_parts(
                input_path=input_path,
                output_dir=output_dir,
                required_columns=["required_a", "required_b"],
                batch_rows=2,
                memory_guard=guard,
            )

            self.assertEqual(result.backend_used, "cpu")
            self.assertEqual(result.rows_read, 3)
            self.assertEqual(result.rows_written, 3)
            self.assertEqual(result.batch_count, 2)
            self.assertEqual(len(result.output_parts), 2)
            first_part = pq.read_table(result.output_parts[0])
            self.assertEqual(first_part.column_names, ["required_a", "required_b"])

    def test_gpu_backend_is_optional_and_auto_falls_back_when_cudf_absent(self) -> None:
        settings = resolve_stage_three_runtime_settings(
            backend="auto",
            psutil_module=_psutil(available_gb=16, rss_gb=0.1),
        )
        backend, selection = select_feature_extraction_backend(
            settings=settings,
            gpu_backend=_UnavailableGpuBackend(),
        )

        self.assertEqual(backend.name, "cpu")
        self.assertEqual(selection.selected_backend, "cpu")
        self.assertFalse(selection.gpu_availability.available)
        self.assertIn("cudf", selection.fallback_reason or "")

    def test_auto_mode_falls_back_when_gpu_probe_fails(self) -> None:
        settings = resolve_stage_three_runtime_settings(
            backend="auto",
            psutil_module=_psutil(available_gb=16, rss_gb=0.1),
        )
        backend, selection = select_feature_extraction_backend(
            settings=settings,
            gpu_backend=_FailingProbeGpuBackend(),
        )

        self.assertEqual(backend.name, "cpu")
        self.assertEqual(selection.selected_backend, "cpu")
        self.assertIsNotNone(selection.probe_result)
        self.assertEqual(selection.probe_result.status, "SKIPPED")

    def test_gpu_memory_limit_blocks_gpu_selection(self) -> None:
        settings = resolve_stage_three_runtime_settings(
            backend="gpu",
            psutil_module=_psutil(available_gb=16, rss_gb=0.1),
        )
        backend, selection = select_feature_extraction_backend(
            settings=settings,
            gpu_backend=_LowMemoryGpuBackend(),
        )

        self.assertEqual(backend.name, "cpu")
        self.assertEqual(selection.selected_backend, "cpu")
        self.assertIn("soft limit", selection.fallback_reason or "")

    def test_memory_guard_reduces_or_fails_safely_below_reserved_ram(self) -> None:
        guard = MemoryGuard(
            reserved_ram_gb=8,
            soft_ram_limit_gb=48,
            hard_ram_limit_gb=56,
            min_batch_rows=1_000,
            psutil_module=_psutil(available_gb=4, rss_gb=0.5),
        )

        decision = guard.ensure_batch_allowed(10_000)

        self.assertEqual(decision.action, "reduce")
        self.assertEqual(decision.batch_rows, 5_000)
        with self.assertRaises(MemoryGuardError):
            guard.ensure_batch_allowed(1_000)

    def test_probe_runtime_backend_cli_writes_task06_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_ru = root / "reports" / "ru" / "stage-three"
            report_en = root / "reports" / "en" / "stage-three"
            with (
                patch("scripts.stage_three.cli.PATH_DATA_STORAGE", str(root)),
                patch("scripts.stage_three.reports.path_utils.REPORTS_RU_STAGE_THREE", str(report_ru)),
                patch("scripts.stage_three.reports.path_utils.REPORTS_EN_STAGE_THREE", str(report_en)),
            ):
                output = _capture_router(
                    lambda: router_stage_three(
                        "probe-runtime-backend",
                        extra_args=["--backend", "cpu"],
                    )
                )

            self.assertIn("stage-three probe-runtime-backend", output)
            self.assertIn("cpu", output)
            self.assertTrue((report_ru / TASK06_REPORT_FILENAME).exists())
            self.assertTrue((report_en / TASK06_REPORT_FILENAME).exists())


class _UnavailableGpuBackend:
    name = "gpu"

    def availability(self) -> GpuAvailability:
        return GpuAvailability(available=False, reason="cudf is not installed in test")

    def supports_operation(self, operation: str) -> bool:
        return False


class _FailingProbeGpuBackend:
    name = "gpu"

    def availability(self) -> GpuAvailability:
        return GpuAvailability(available=True, reason="test gpu wrapper")

    def supports_operation(self, operation: str) -> bool:
        return True

    def memory_status(self, *, soft_limit_gb: int, hard_limit_gb: int):
        return {
            "checked": True,
            "ok": True,
            "reason": "test GPU memory is available",
            "soft_limit_gb": soft_limit_gb,
            "hard_limit_gb": hard_limit_gb,
        }

    def probe_transform(self, table: pa.Table) -> pa.Table:
        raise RuntimeError("test probe failure")


class _LowMemoryGpuBackend(_FailingProbeGpuBackend):
    def memory_status(self, *, soft_limit_gb: int, hard_limit_gb: int):
        return {
            "checked": True,
            "ok": False,
            "reason": "free GPU memory is below configured soft limit",
            "soft_limit_gb": soft_limit_gb,
            "hard_limit_gb": hard_limit_gb,
        }


def _psutil(*, available_gb: float, rss_gb: float) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        virtual_memory=lambda: types.SimpleNamespace(
            total=64 * 1024**3,
            available=int(available_gb * 1024**3),
        ),
        Process=lambda _pid: types.SimpleNamespace(
            memory_info=lambda: types.SimpleNamespace(rss=int(rss_gb * 1024**3))
        ),
    )


def _capture_router(callback) -> str:
    buffer = StringIO()
    with redirect_stdout(buffer):
        callback()
    return buffer.getvalue()


if __name__ == "__main__":
    unittest.main()
