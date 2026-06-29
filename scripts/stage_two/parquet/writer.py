"""Partitioned Parquet writer for normalized/features/model-ready artifacts."""

from __future__ import annotations

import hashlib
import json
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
    PARQUET_MODEL_READY_RELATIVE,
    PARQUET_NORMALIZED_RELATIVE,
    PATH_DATA_STORAGE,
    STAGE_TWO_HASH_OUTPUT_ARTIFACTS,
)
from scripts.db.models import FeatureArtifact, ModelReadyArtifact, NormalizedArtifact
from scripts.db.repositories import ArtifactRepository
from scripts.stage_two.parsers.base import REQUIRED_NORMALIZED_FIELDS


JSON_FIELD_SUFFIX = "_json"


class ParquetWriteError(RuntimeError):
    """Raised when an output Parquet artifact cannot be safely written."""


@dataclass(frozen=True)
class ParquetWriteResult:
    """Metadata returned after writing a Parquet artifact."""

    absolute_path: Path
    relative_path: str
    row_count: int
    file_size_bytes: int
    content_hash_sha256: str
    write_duration_seconds: float


class ParquetArtifactWriter:
    """Write Stage Two generated artifacts to partitioned Parquet paths."""

    def __init__(
        self,
        storage_root: str | Path | None = None,
        *,
        compression: str = "zstd",
        hash_outputs: bool = STAGE_TWO_HASH_OUTPUT_ARTIFACTS,
    ) -> None:
        """Initialize the writer with PATH_DATA_STORAGE or an explicit storage root."""
        root = Path(storage_root or PATH_DATA_STORAGE).expanduser()
        if not str(root).strip():
            raise ValueError("PATH_DATA_STORAGE must be configured for Parquet writes.")
        self.storage_root = root
        self.compression = compression
        self.hash_outputs = hash_outputs

    def write_normalized(
        self,
        rows: list[dict[str, Any]],
        *,
        branch: str,
        role: str,
        modality: str,
        dataset_slug: str,
        schema_version: str,
        run_id: str | int | None = None,
        columns: list[str] | None = None,
        allow_empty: bool = False,
    ) -> ParquetWriteResult:
        """Write normalized events to the normalized Parquet layer."""
        relative_path = (
            Path(PARQUET_NORMALIZED_RELATIVE)
            / branch
            / role
            / modality
            / dataset_slug
            / f"schema={schema_version}"
            / self._part_file_name(run_id)
        )
        return self._write_rows(
            rows,
            relative_path=relative_path,
            columns=columns,
            required_columns=REQUIRED_NORMALIZED_FIELDS,
            allow_empty=allow_empty,
        )

    def write_features(
        self,
        rows: list[dict[str, Any]],
        *,
        feature_group: str,
        role: str,
        dataset_slug: str,
        schema_version: str,
        run_id: str | int | None = None,
        columns: list[str] | None = None,
        allow_empty: bool = False,
    ) -> ParquetWriteResult:
        """Write feature rows to the feature Parquet layer."""
        relative_path = (
            Path(PARQUET_FEATURES_RELATIVE)
            / feature_group
            / role
            / dataset_slug
            / f"schema={schema_version}"
            / self._part_file_name(run_id)
        )
        return self._write_rows(rows, relative_path=relative_path, columns=columns, allow_empty=allow_empty)

    def write_model_ready_table(
        self,
        rows: list[dict[str, Any]],
        *,
        artifact_type: str,
        branch: str,
        role: str,
        schema_version: str,
        file_name: str,
        columns: list[str] | None = None,
        allow_empty: bool = False,
    ) -> ParquetWriteResult:
        """Write model-ready tabular/label/split-index rows."""
        relative_path = (
            Path(PARQUET_MODEL_READY_RELATIVE)
            / artifact_type
            / branch
            / role
            / f"schema={schema_version}"
            / file_name
        )
        return self._write_rows(rows, relative_path=relative_path, columns=columns, allow_empty=allow_empty)

    def register_normalized_artifact(
        self,
        repository: ArtifactRepository,
        result: ParquetWriteResult,
        **metadata: Any,
    ) -> NormalizedArtifact:
        """Register a normalized artifact path through ArtifactRepository."""
        values = {
            "artifact_uid": metadata.pop("artifact_uid", uuid4()),
            "normalized_path": result.relative_path,
            "row_count": result.row_count,
            "file_size_bytes": result.file_size_bytes,
            "content_hash_sha256": result.content_hash_sha256,
            **metadata,
        }
        return repository.register_normalized_artifact(**values)

    def register_feature_artifact(
        self,
        repository: ArtifactRepository,
        result: ParquetWriteResult,
        **metadata: Any,
    ) -> FeatureArtifact:
        """Register a feature artifact path through ArtifactRepository."""
        values = {
            "artifact_uid": metadata.pop("artifact_uid", uuid4()),
            "feature_path": result.relative_path,
            "row_count": result.row_count,
            **metadata,
        }
        return repository.register_feature_artifact(**values)

    def register_model_ready_artifact(
        self,
        repository: ArtifactRepository,
        result: ParquetWriteResult,
        **metadata: Any,
    ) -> ModelReadyArtifact:
        """Register a model-ready artifact path through ArtifactRepository."""
        values = {
            "artifact_uid": metadata.pop("artifact_uid", uuid4()),
            "artifact_path": result.relative_path,
            "sample_count": result.row_count,
            **metadata,
        }
        return repository.register_model_ready_artifact(**values)

    def _write_rows(
        self,
        rows: list[dict[str, Any]],
        *,
        relative_path: Path,
        columns: list[str] | None = None,
        required_columns: frozenset[str] | None = None,
        allow_empty: bool = False,
    ) -> ParquetWriteResult:
        started_at = time.perf_counter()
        normalized_rows = self._normalize_rows(rows, columns)
        if not normalized_rows and not allow_empty:
            raise ParquetWriteError("refusing to write empty Parquet artifact without allow_empty=True")
        absolute_path = self.storage_root / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self._temp_path_for(absolute_path)
        self._cleanup_stale_temps(absolute_path)
        try:
            table = pa.Table.from_pylist(normalized_rows)
            pq.write_table(table, temp_path, compression=self.compression)
            self._validate_written_file(
                temp_path,
                expected_rows=len(normalized_rows),
                required_columns=required_columns,
                allow_empty=allow_empty,
            )
            temp_path.replace(absolute_path)
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise
        return ParquetWriteResult(
            absolute_path=absolute_path,
            relative_path=relative_path.as_posix(),
            row_count=len(normalized_rows),
            file_size_bytes=absolute_path.stat().st_size,
            content_hash_sha256=self._sha256(absolute_path) if self.hash_outputs else "",
            write_duration_seconds=time.perf_counter() - started_at,
        )

    @staticmethod
    def _normalize_rows(
        rows: list[dict[str, Any]],
        columns: list[str] | None,
    ) -> list[dict[str, Any]]:
        selected_rows = rows if columns is None else [
            {column: row.get(column) for column in columns} for row in rows
        ]
        return [
            {
                column: _normalize_parquet_value(column, value)
                for column, value in row.items()
            }
            for row in selected_rows
        ]

    @staticmethod
    def _part_file_name(run_id: str | int | None) -> str:
        if run_id is None:
            run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        safe_run_id = str(run_id).replace("\\", "-").replace("/", "-")
        return f"part-{safe_run_id}.parquet"

    @staticmethod
    def _temp_path_for(final_path: Path) -> Path:
        return final_path.with_name(f".{final_path.name}.{uuid4().hex}.tmp")

    @staticmethod
    def _cleanup_stale_temps(final_path: Path) -> None:
        for temp_path in final_path.parent.glob(f".{final_path.name}.*.tmp"):
            if temp_path.is_file():
                temp_path.unlink(missing_ok=True)

    @staticmethod
    def _validate_written_file(
        path: Path,
        *,
        expected_rows: int,
        required_columns: frozenset[str] | None,
        allow_empty: bool,
    ) -> None:
        if not path.exists():
            raise ParquetWriteError(f"temporary Parquet artifact was not created: {path}")
        try:
            table = pq.read_table(path)
        except Exception as exc:
            raise ParquetWriteError(f"temporary Parquet artifact is not readable: {path}") from exc
        actual_rows = table.num_rows
        if actual_rows != expected_rows:
            raise ParquetWriteError(
                f"Parquet row count mismatch: expected {expected_rows}, got {actual_rows}"
            )
        if actual_rows == 0 and not allow_empty:
            raise ParquetWriteError("refusing to finalize empty Parquet artifact")
        if required_columns is not None:
            missing = sorted(required_columns.difference(table.column_names))
            if missing:
                raise ParquetWriteError(
                    "Parquet artifact is missing required normalized columns: "
                    + ", ".join(missing)
                )

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()


def _normalize_parquet_value(column: str, value: Any) -> Any:
    """Return a PyArrow-safe scalar for values with potentially mixed nested types."""
    if value is None:
        return None
    if column.endswith(JSON_FIELD_SUFFIX):
        return _json_string(value)
    return value


def _json_string(value: Any) -> str:
    """Serialize JSON-like values deterministically before Arrow type inference."""
    if isinstance(value, str):
        return value
    return json.dumps(_json_safe_value(value), ensure_ascii=False, sort_keys=True)


def _json_safe_value(value: Any) -> Any:
    """Convert nested values to JSON-serializable data without dropping raw content."""
    if isinstance(value, dict):
        return {str(key): _json_safe_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe_value(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
