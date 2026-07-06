"""Atomic Parquet writing helpers for Stage Three feature artifacts."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import pyarrow as pa
import pyarrow.parquet as pq

from config import (
    PARQUET_FEATURES_RELATIVE,
    PATH_DATA_STORAGE,
    STAGE_TWO_PARQUET_COMPRESSION,
)
from scripts.stage_two.parquet.writer import ParquetWriteError


@dataclass(frozen=True)
class AtomicParquetWriteResult:
    """Metadata for one atomically finalized Parquet part."""

    absolute_path: Path
    relative_path: str
    row_count: int
    column_count: int
    file_size_bytes: int
    content_hash_sha256: str
    compression: str
    write_duration_seconds: float


class FeatureArtifactParquetWriter:
    """Write Stage Three feature Parquet outputs with temp-file finalization."""

    def __init__(
        self,
        storage_root: str | Path | None = None,
        *,
        compression: str | None = None,
    ) -> None:
        root = Path(storage_root or PATH_DATA_STORAGE).expanduser()
        if not str(root).strip():
            raise ValueError("PATH_DATA_STORAGE must be configured for Stage Three feature writes.")
        self.storage_root = root
        self.compression = (compression or STAGE_TWO_PARQUET_COMPRESSION or "zstd").strip() or "zstd"

    def feature_part_path(
        self,
        *,
        feature_group: str,
        branch: str,
        role: str,
        schema_version: str,
        run_id: str | int | None = None,
        part_index: int | None = None,
    ) -> Path:
        """Build the Stage Three feature artifact path under PATH_DATA_STORAGE."""
        safe_run_id = _safe_run_id(run_id)
        suffix = f"-{part_index:05d}" if part_index is not None else ""
        return (
            self.storage_root
            / PARQUET_FEATURES_RELATIVE
            / feature_group
            / branch
            / role
            / f"schema={schema_version}"
            / f"part-{safe_run_id}{suffix}.parquet"
        )

    def write_table(
        self,
        table: pa.Table,
        *,
        feature_group: str,
        branch: str,
        role: str,
        schema_version: str,
        run_id: str | int | None = None,
        part_index: int | None = None,
        allow_empty: bool = False,
    ) -> AtomicParquetWriteResult:
        """Write one feature table to the configured feature path atomically."""
        final_path = self.feature_part_path(
            feature_group=feature_group,
            branch=branch,
            role=role,
            schema_version=schema_version,
            run_id=run_id,
            part_index=part_index,
        )
        return write_atomic_parquet_table(
            table,
            final_path=final_path,
            storage_root=self.storage_root,
            compression=self.compression,
            allow_empty=allow_empty,
        )


def write_atomic_parquet_table(
    table: pa.Table,
    *,
    final_path: str | Path,
    storage_root: str | Path | None = None,
    compression: str | None = None,
    allow_empty: bool = False,
) -> AtomicParquetWriteResult:
    """Write a PyArrow table via temp file, validate it, then rename into place."""
    started_at = time.perf_counter()
    resolved_final_path = Path(final_path).expanduser()
    if table.num_rows == 0 and not allow_empty:
        raise ParquetWriteError("refusing to write empty feature Parquet artifact")
    resolved_final_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = _temp_path_for(resolved_final_path)
    _cleanup_stale_temps(resolved_final_path)
    resolved_compression = (compression or STAGE_TWO_PARQUET_COMPRESSION or "zstd").strip() or "zstd"
    try:
        pq.write_table(table, temp_path, compression=resolved_compression)
        _validate_written_file(
            temp_path,
            expected_rows=table.num_rows,
            expected_columns=len(table.schema.names),
            allow_empty=allow_empty,
        )
        _replace_with_retry(temp_path, resolved_final_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return AtomicParquetWriteResult(
        absolute_path=resolved_final_path,
        relative_path=_relative_artifact_path(resolved_final_path, storage_root),
        row_count=table.num_rows,
        column_count=len(table.schema.names),
        file_size_bytes=resolved_final_path.stat().st_size,
        content_hash_sha256=sha256_file(resolved_final_path),
        compression=resolved_compression,
        write_duration_seconds=time.perf_counter() - started_at,
    )


def sha256_file(path: str | Path) -> str:
    """Return a sha256 checksum for a finalized artifact file."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def combined_sha256(values: list[str]) -> str:
    """Return a deterministic checksum over ordered part checksums."""
    digest = hashlib.sha256()
    for value in values:
        digest.update(value.encode("utf-8"))
    return digest.hexdigest()


def _relative_artifact_path(path: Path, storage_root: str | Path | None) -> str:
    root = Path(storage_root or PATH_DATA_STORAGE).expanduser()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _safe_run_id(run_id: str | int | None) -> str:
    if run_id is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    return str(run_id).replace("\\", "-").replace("/", "-").replace(":", "-")


def _temp_path_for(final_path: Path) -> Path:
    return final_path.with_name(f".{final_path.name}.{uuid4().hex}.tmp")


def _cleanup_stale_temps(final_path: Path) -> None:
    for temp_path in final_path.parent.glob(f".{final_path.name}.*.tmp"):
        if temp_path.is_file():
            temp_path.unlink(missing_ok=True)


def _validate_written_file(
    path: Path,
    *,
    expected_rows: int,
    expected_columns: int,
    allow_empty: bool,
) -> None:
    if not path.exists():
        raise ParquetWriteError(f"temporary feature Parquet artifact was not created: {path}")
    try:
        metadata = pq.read_metadata(path)
        schema = pq.read_schema(path)
    except Exception as exc:
        raise ParquetWriteError(f"temporary feature Parquet artifact is not readable: {path}") from exc
    if metadata.num_rows != expected_rows:
        raise ParquetWriteError(
            f"feature Parquet row count mismatch: expected {expected_rows}, got {metadata.num_rows}"
        )
    if metadata.num_rows == 0 and not allow_empty:
        raise ParquetWriteError("refusing to finalize empty feature Parquet artifact")
    if len(schema.names) != expected_columns:
        raise ParquetWriteError(
            f"feature Parquet column count mismatch: expected {expected_columns}, got {len(schema.names)}"
        )


def _replace_with_retry(temp_path: Path, final_path: Path) -> None:
    delay_seconds = 0.1
    attempts = 6
    for attempt in range(1, attempts + 1):
        try:
            temp_path.replace(final_path)
            return
        except OSError as exc:
            if attempt >= attempts or getattr(exc, "winerror", None) not in {32, 33}:
                raise
            time.sleep(delay_seconds)
            delay_seconds *= 2


def parquet_part_metadata(path: str | Path, *, storage_root: str | Path | None = None) -> dict[str, Any]:
    """Return catalog-ready metadata for a finalized feature Parquet part."""
    resolved = Path(path).expanduser()
    metadata = pq.read_metadata(resolved)
    schema = pq.read_schema(resolved)
    return {
        "path": _relative_artifact_path(resolved, storage_root),
        "row_count": metadata.num_rows,
        "column_count": len(schema.names),
        "file_size_bytes": resolved.stat().st_size,
        "content_hash_sha256": sha256_file(resolved),
    }
