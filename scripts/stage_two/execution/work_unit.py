"""Work unit contracts for Stage Two normalization execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ExecutionEngine = Literal["cpu", "gpu", "auto"]


@dataclass(frozen=True)
class WorkUnit:
    """One independently executable normalization unit."""

    branch: str
    role: str
    source_format: str
    dataset_id: int
    dataset_file_id: int
    source_path: str
    parser_name: str
    parser_version: str
    schema_version: str
    chunk_id: str | None = None
    estimated_size_bytes: int = 0
    engine: ExecutionEngine = "cpu"
    packet_mode: str | None = None


@dataclass(frozen=True)
class WorkUnitResult:
    """Normalized execution outcome for one work unit."""

    work_unit: WorkUnit
    status: str
    artifact_id: int | None = None
    error: str | None = None
    error_samples: tuple[str, ...] = ()
