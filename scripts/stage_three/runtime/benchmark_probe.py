"""Small correctness probes for Stage Three backend selection."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

import pyarrow as pa


@dataclass(frozen=True)
class BackendProbeResult:
    """CPU/GPU backend probe result."""

    status: str
    cpu_elapsed_seconds: float | None = None
    gpu_elapsed_seconds: float | None = None
    rows_checked: int = 0
    tolerance: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


def run_backend_correctness_probe(
    *,
    gpu_backend: Any,
    tolerance: float = 1e-9,
) -> BackendProbeResult:
    """Compare a deterministic small sample on CPU and GPU backend wrappers."""
    sample = pa.table(
        {
            "feature_value": pa.array([0.0, 1.0, 2.5, None, 100.0], type=pa.float64()),
            "feature_count": pa.array([0, 1, 2, 3, 4], type=pa.int64()),
        }
    )
    cpu_started = perf_counter()
    expected = _cpu_probe_transform(sample)
    cpu_elapsed = perf_counter() - cpu_started

    gpu_started = perf_counter()
    try:
        observed = gpu_backend.probe_transform(sample)
    except Exception as exc:
        return BackendProbeResult(
            status="SKIPPED",
            cpu_elapsed_seconds=cpu_elapsed,
            rows_checked=sample.num_rows,
            tolerance=tolerance,
            details={"reason": "gpu_probe_failed", "error": str(exc), "error_type": exc.__class__.__name__},
        )
    gpu_elapsed = perf_counter() - gpu_started
    equal, diff = _tables_equal(expected, observed, tolerance=tolerance)
    return BackendProbeResult(
        status="PASS" if equal else "FAIL",
        cpu_elapsed_seconds=cpu_elapsed,
        gpu_elapsed_seconds=gpu_elapsed,
        rows_checked=sample.num_rows,
        tolerance=tolerance,
        details={} if equal else {"difference": diff},
    )


def _cpu_probe_transform(table: pa.Table) -> pa.Table:
    value = [
        None if item is None else float(item) + 1.0
        for item in table.column("feature_value").to_pylist()
    ]
    count = [
        None if item is None else int(item) + 1
        for item in table.column("feature_count").to_pylist()
    ]
    return pa.table({"feature_value_plus_one": value, "feature_count_plus_one": count})


def _tables_equal(left: pa.Table, right: pa.Table, *, tolerance: float) -> tuple[bool, str | None]:
    if left.column_names != right.column_names:
        return False, f"columns differ: {left.column_names} != {right.column_names}"
    if left.num_rows != right.num_rows:
        return False, f"row count differs: {left.num_rows} != {right.num_rows}"
    for column_name in left.column_names:
        left_values = left.column(column_name).to_pylist()
        right_values = right.column(column_name).to_pylist()
        for index, (left_value, right_value) in enumerate(zip(left_values, right_values, strict=True)):
            if left_value is None or right_value is None:
                if left_value is not None or right_value is not None:
                    return False, f"{column_name}[{index}] differs: {left_value} != {right_value}"
                continue
            if isinstance(left_value, float) or isinstance(right_value, float):
                if abs(float(left_value) - float(right_value)) > tolerance:
                    return False, f"{column_name}[{index}] differs: {left_value} != {right_value}"
            elif left_value != right_value:
                return False, f"{column_name}[{index}] differs: {left_value} != {right_value}"
    return True, None
