"""Feature extraction backend abstraction for Stage Three."""

from __future__ import annotations

import importlib.util
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from time import perf_counter
from typing import Any

import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from scripts.stage_three.runtime.benchmark_probe import (
    BackendProbeResult,
    run_backend_correctness_probe,
)
from scripts.stage_three.runtime.memory_guard import BatchRuntimeMetric, MemoryGuard
from scripts.stage_three.runtime.resources import StageThreeRuntimeSettings


ArrowTransform = Callable[[pa.Table], pa.Table]


@dataclass(frozen=True)
class BackendCapability:
    """One optional runtime capability."""

    name: str
    available: bool
    detail: str


@dataclass(frozen=True)
class GpuAvailability:
    """GPU library availability check."""

    available: bool
    library: str = "cudf"
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BackendSelectionResult:
    """Backend selection result for cpu/gpu/auto modes."""

    requested_backend: str
    selected_backend: str
    gpu_availability: GpuAvailability
    probe_result: BackendProbeResult | None
    fallback_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


@dataclass(frozen=True)
class FeatureExtractionRunResult:
    """Runtime result for one bounded feature extraction pass."""

    backend_used: str
    input_path: str
    output_dir: str
    required_columns: list[str]
    output_parts: list[str]
    rows_read: int
    rows_written: int
    batch_count: int
    elapsed_seconds: float
    peak_rss_gb: float | None
    batch_metrics: list[BatchRuntimeMetric]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CpuFeatureExtractionBackend:
    """Mandatory CPU backend backed by PyArrow Dataset batch scanning."""

    name = "cpu"

    def capabilities(self) -> list[BackendCapability]:
        """Return available CPU-side feature extraction libraries."""
        return [
            BackendCapability("pyarrow.dataset", True, "required CPU batch scanner"),
            BackendCapability("duckdb", _module_available("duckdb"), "optional SQL/vectorized checks"),
            BackendCapability("polars", _module_available("polars"), "optional lazy-frame transforms"),
        ]

    def extract_to_parquet_parts(
        self,
        *,
        input_path: str | Path,
        output_dir: str | Path,
        required_columns: Sequence[str],
        batch_rows: int,
        memory_guard: MemoryGuard,
        transform: ArrowTransform | None = None,
    ) -> FeatureExtractionRunResult:
        """Read only required columns in bounded batches and write Parquet parts."""
        if not required_columns:
            raise ValueError("required_columns must not be empty")
        if batch_rows <= 0:
            raise ValueError("batch_rows must be positive")
        input_path = Path(input_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        initial_decision = memory_guard.ensure_batch_allowed(batch_rows)
        effective_batch_rows = initial_decision.batch_rows
        dataset = ds.dataset(input_path, format="parquet")
        scanner = dataset.scanner(columns=list(required_columns), batch_size=effective_batch_rows)
        output_parts: list[str] = []
        batch_metrics: list[BatchRuntimeMetric] = []
        rows_read = 0
        rows_written = 0
        started_at = perf_counter()
        for batch_index, record_batch in enumerate(scanner.to_batches()):
            decision = memory_guard.ensure_batch_allowed(effective_batch_rows)
            effective_batch_rows = decision.batch_rows
            memory_guard.start_batch_timer(batch_index)
            table = pa.Table.from_batches([record_batch])
            rows_read += table.num_rows
            output_table = transform(table) if transform is not None else table
            part_path = output_dir / f"part-{batch_index:05d}.parquet"
            pq.write_table(output_table, part_path)
            rows_written += output_table.num_rows
            output_parts.append(str(part_path))
            batch_metrics.append(
                memory_guard.finish_batch_metric(
                    backend=self.name,
                    batch_index=batch_index,
                    batch_rows=output_table.num_rows,
                )
            )
        return FeatureExtractionRunResult(
            backend_used=self.name,
            input_path=str(input_path),
            output_dir=str(output_dir),
            required_columns=list(required_columns),
            output_parts=output_parts,
            rows_read=rows_read,
            rows_written=rows_written,
            batch_count=len(output_parts),
            elapsed_seconds=perf_counter() - started_at,
            peak_rss_gb=memory_guard.peak_rss_gb,
            batch_metrics=batch_metrics,
        )


class GpuFeatureExtractionBackend:
    """Optional RAPIDS/cuDF capability wrapper.

    The wrapper is intentionally conservative: GPU is selected only when cuDF is
    importable and a correctness probe succeeds. Production extraction can still
    fall back to CPU for unsupported operations.
    """

    name = "gpu"

    def availability(self) -> GpuAvailability:
        spec = importlib.util.find_spec("cudf")
        if spec is None:
            return GpuAvailability(available=False, reason="cudf is not installed")
        return GpuAvailability(available=True, reason="cudf import spec found")

    def supports_operation(self, operation: str) -> bool:
        return operation in {"probe"}

    def memory_status(self, *, soft_limit_gb: int, hard_limit_gb: int) -> dict[str, Any]:
        """Check free GPU memory when CuPy is available."""
        if importlib.util.find_spec("cupy") is None:
            return {
                "checked": False,
                "ok": True,
                "reason": "cupy is not installed; GPU memory was not checked",
                "soft_limit_gb": soft_limit_gb,
                "hard_limit_gb": hard_limit_gb,
            }
        try:
            import cupy  # type: ignore[import-not-found]

            free_bytes, total_bytes = cupy.cuda.Device().mem_info
        except Exception as exc:
            return {
                "checked": False,
                "ok": False,
                "reason": f"GPU memory check failed: {exc}",
                "error_type": exc.__class__.__name__,
                "soft_limit_gb": soft_limit_gb,
                "hard_limit_gb": hard_limit_gb,
            }
        free_gb = free_bytes / 1024**3
        total_gb = total_bytes / 1024**3
        return {
            "checked": True,
            "ok": free_gb >= soft_limit_gb,
            "reason": "free GPU memory is within configured limits"
            if free_gb >= soft_limit_gb
            else "free GPU memory is below configured soft limit",
            "free_gb": free_gb,
            "total_gb": total_gb,
            "soft_limit_gb": soft_limit_gb,
            "hard_limit_gb": hard_limit_gb,
        }

    def probe_transform(self, table: pa.Table) -> pa.Table:
        """Run the correctness probe transform through cuDF when available."""
        import cudf  # type: ignore[import-not-found]

        dataframe = cudf.DataFrame.from_arrow(table)
        dataframe["feature_value_plus_one"] = dataframe["feature_value"] + 1.0
        dataframe["feature_count_plus_one"] = dataframe["feature_count"] + 1
        output = dataframe[["feature_value_plus_one", "feature_count_plus_one"]]
        if hasattr(output, "to_arrow"):
            return output.to_arrow()
        if hasattr(output, "to_pandas"):
            return pa.Table.from_pandas(output.to_pandas(), preserve_index=False)
        raise RuntimeError("cuDF output cannot be converted to pyarrow.Table")


def select_feature_extraction_backend(
    *,
    settings: StageThreeRuntimeSettings,
    cpu_backend: CpuFeatureExtractionBackend | None = None,
    gpu_backend: GpuFeatureExtractionBackend | None = None,
    run_probe: bool = True,
) -> tuple[CpuFeatureExtractionBackend | GpuFeatureExtractionBackend, BackendSelectionResult]:
    """Select a safe backend for the configured acceleration mode."""
    cpu = cpu_backend or CpuFeatureExtractionBackend()
    gpu = gpu_backend or GpuFeatureExtractionBackend()
    requested = settings.acceleration.backend
    availability = gpu.availability()

    if requested == "cpu":
        return cpu, BackendSelectionResult(
            requested_backend=requested,
            selected_backend="cpu",
            gpu_availability=availability,
            probe_result=None,
            fallback_reason=None,
        )

    if not availability.available:
        return cpu, BackendSelectionResult(
            requested_backend=requested,
            selected_backend="cpu",
            gpu_availability=availability,
            probe_result=None,
            fallback_reason=availability.reason,
        )

    memory_status = gpu.memory_status(
        soft_limit_gb=settings.resource_profile.gpu_memory_soft_limit_gb,
        hard_limit_gb=settings.resource_profile.gpu_memory_hard_limit_gb,
    )
    availability = replace(
        availability,
        details={**availability.details, "memory_status": memory_status},
    )
    if not bool(memory_status.get("ok")):
        return cpu, BackendSelectionResult(
            requested_backend=requested,
            selected_backend="cpu",
            gpu_availability=availability,
            probe_result=None,
            fallback_reason=str(memory_status.get("reason", "GPU memory check failed")),
        )

    if not gpu.supports_operation("probe"):
        return cpu, BackendSelectionResult(
            requested_backend=requested,
            selected_backend="cpu",
            gpu_availability=availability,
            probe_result=None,
            fallback_reason="gpu backend does not support the correctness probe",
        )

    probe = run_backend_correctness_probe(gpu_backend=gpu) if run_probe else None
    if probe is not None and probe.status != "PASS":
        return cpu, BackendSelectionResult(
            requested_backend=requested,
            selected_backend="cpu",
            gpu_availability=availability,
            probe_result=probe,
            fallback_reason=f"gpu correctness probe did not pass: {probe.status}",
        )

    return gpu, BackendSelectionResult(
        requested_backend=requested,
        selected_backend="gpu",
        gpu_availability=availability,
        probe_result=probe,
        fallback_reason=None,
    )


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None
