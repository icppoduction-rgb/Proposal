from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from cybersec_platform.db.session import get_settings
from cybersec_platform.ml.normalization import (
    ContractValidationError,
    UnsupportedDatasetFormatError,
    detect_dataset_format,
    inspect_dataset_source,
)

UPLOAD_SIZE_LIMIT_BYTES = 100 * 1024 * 1024 * 1024


class DatasetUploadError(ValueError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def _utcnow() -> datetime:
    return datetime.now(UTC)


def normalize_relative_path(value: str) -> str:
    normalized = value.replace("\\", "/").strip("/")
    if not normalized:
        raise DatasetUploadError("Relative path is required")
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise DatasetUploadError(f"Invalid relative path: {value}")
    return path.as_posix()


def _safe_join(root: Path, relative_path: str) -> Path:
    candidate = (root / Path(relative_path)).resolve()
    root_resolved = root.resolve()
    if not candidate.is_relative_to(root_resolved):
        raise DatasetUploadError(f"Invalid relative path: {relative_path}")
    return candidate


def get_raw_root() -> Path:
    settings = get_settings()
    root = Path(settings.raw_data_path)
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def get_upload_root() -> Path:
    settings = get_settings()
    root = Path(settings.tmp_path) / "dataset-uploads"
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def _session_dir(session_id: str) -> Path:
    return get_upload_root() / session_id


def _session_payload_dir(session_id: str) -> Path:
    return _session_dir(session_id) / "payload"


def _session_metadata_path(session_id: str) -> Path:
    return _session_dir(session_id) / "session.json"


def _delete_session_dir(session_id: str) -> None:
    session_dir = _session_dir(session_id)
    if not session_dir.exists():
        return
    for path in sorted(session_dir.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            try:
                path.rmdir()
            except OSError:
                continue
    try:
        session_dir.rmdir()
    except OSError:
        pass


def _load_session(session_id: str) -> dict[str, Any]:
    metadata_path = _session_metadata_path(session_id)
    if not metadata_path.exists():
        raise DatasetUploadError("Upload session not found", status_code=404)
    with metadata_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _save_session(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    session_dir = _session_dir(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    with _session_metadata_path(session_id).open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    return payload


def list_raw_files() -> list[dict[str, Any]]:
    root = get_raw_root()
    result: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            dataset_format = detect_dataset_format(path)
        except UnsupportedDatasetFormatError:
            continue
        stat = path.stat()
        relative_path = path.relative_to(root).as_posix()
        result.append(
            {
                "relative_path": relative_path,
                "file_name": path.name,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                "format": dataset_format,
            }
        )
    return result


def inspect_raw_file(relative_path: str) -> dict[str, Any]:
    normalized_path = normalize_relative_path(relative_path)
    target = _safe_join(get_raw_root(), normalized_path)
    if not target.exists() or not target.is_file():
        raise DatasetUploadError("Raw dataset file not found", status_code=404)

    try:
        inspection = inspect_dataset_source(target)
    except (ContractValidationError, UnsupportedDatasetFormatError) as exc:
        raise DatasetUploadError(str(exc), status_code=400) from exc

    return {
        "relative_path": normalized_path,
        "format": inspection.dataset_format,
        "normalization_profile": inspection.normalization_profile,
        "columns": inspection.columns,
        "suggested_name": inspection.suggested_name,
        "target_columns": inspection.target_columns,
        "quality_warnings": inspection.quality_warnings,
        "supporting_only": inspection.supporting_only,
        "compatible_feature_schemas": inspection.compatible_feature_schemas,
    }


def create_upload_session(files: list[dict[str, Any]]) -> dict[str, Any]:
    if not files:
        raise DatasetUploadError("At least one file is required")

    total_size_bytes = 0
    normalized_files: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    raw_root = get_raw_root()

    for file in files:
        relative_path = normalize_relative_path(str(file["relative_path"]))
        if relative_path in seen_paths:
            raise DatasetUploadError(f"Duplicate file in upload session: {relative_path}")
        seen_paths.add(relative_path)

        size_bytes = int(file["size_bytes"])
        if size_bytes <= 0:
            raise DatasetUploadError(f"File must be non-empty: {relative_path}")
        total_size_bytes += size_bytes
        if total_size_bytes > UPLOAD_SIZE_LIMIT_BYTES:
            raise DatasetUploadError("Upload session exceeds 100 GB limit")

        target_path = _safe_join(raw_root, relative_path)
        if target_path.exists():
            raise DatasetUploadError(f"Raw dataset file already exists: {relative_path}", status_code=409)

        try:
            detect_dataset_format(Path(relative_path))
        except UnsupportedDatasetFormatError as exc:
            raise DatasetUploadError(str(exc)) from exc

        normalized_files.append(
            {
                "file_id": str(uuid.uuid4()),
                "relative_path": relative_path,
                "size_bytes": size_bytes,
                "uploaded_bytes": 0,
                "content_type": file.get("content_type"),
                "status": "pending",
            }
        )

    session_id = str(uuid.uuid4())
    payload = {
        "session_id": session_id,
        "status": "open",
        "created_at": _utcnow().isoformat(),
        "total_size_bytes": total_size_bytes,
        "files": normalized_files,
    }
    _session_payload_dir(session_id).mkdir(parents=True, exist_ok=True)
    return _save_session(session_id, payload)


def get_session_file(session_id: str, file_id: str) -> dict[str, Any]:
    session = _load_session(session_id)
    if session["status"] != "open":
        raise DatasetUploadError("Upload session is not open", status_code=409)
    for file in session["files"]:
        if file["file_id"] == file_id:
            return session
    raise DatasetUploadError("Upload file not found", status_code=404)


def get_session_payload_path(session_id: str, relative_path: str) -> Path:
    return _safe_join(_session_payload_dir(session_id), relative_path)


def update_uploaded_chunk(session_id: str, file_id: str, uploaded_bytes: int) -> dict[str, Any]:
    session = _load_session(session_id)
    for file in session["files"]:
        if file["file_id"] != file_id:
            continue
        if uploaded_bytes > file["size_bytes"]:
            raise DatasetUploadError("Uploaded bytes exceed declared file size")
        file["uploaded_bytes"] = uploaded_bytes
        file["status"] = "uploaded" if uploaded_bytes == file["size_bytes"] else "uploading"
        return _save_session(session_id, session)
    raise DatasetUploadError("Upload file not found", status_code=404)


def complete_upload_session(session_id: str) -> dict[str, Any]:
    session = _load_session(session_id)
    if session["status"] != "open":
        raise DatasetUploadError("Upload session is not open", status_code=409)

    raw_root = get_raw_root()
    uploaded_files: list[dict[str, Any]] = []
    targets: list[tuple[Path, Path]] = []

    for file in session["files"]:
        if file["uploaded_bytes"] != file["size_bytes"]:
            raise DatasetUploadError(f"File upload is incomplete: {file['relative_path']}", status_code=409)
        source = get_session_payload_path(session_id, file["relative_path"])
        if not source.exists() or not source.is_file():
            raise DatasetUploadError(f"Uploaded payload is missing: {file['relative_path']}", status_code=409)

        target = _safe_join(raw_root, file["relative_path"])
        if target.exists():
            raise DatasetUploadError(f"Raw dataset file already exists: {file['relative_path']}", status_code=409)
        targets.append((source, target))

    for source, target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        source.replace(target)
        stat = target.stat()
        uploaded_files.append(
            {
                "relative_path": target.relative_to(raw_root).as_posix(),
                "file_name": target.name,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                "format": detect_dataset_format(target),
            }
        )

    session["status"] = "completed"
    session["completed_at"] = _utcnow().isoformat()
    _save_session(session_id, session)

    return {
        "session_id": session_id,
        "status": session["status"],
        "uploaded_files": uploaded_files,
        "raw_files": list_raw_files(),
    }


def discard_upload_session(session_id: str) -> None:
    _load_session(session_id)
    _delete_session_dir(session_id)
