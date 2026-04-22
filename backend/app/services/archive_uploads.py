from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cybersec_platform.db.session import get_settings
from cybersec_platform.ml.auto_training import ArchiveExtractionError, detect_archive_format

from backend.app.services.dataset_uploads import UPLOAD_SIZE_LIMIT_BYTES, _safe_join, normalize_relative_path


class ArchiveUploadError(ValueError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def _utcnow() -> datetime:
    return datetime.now(UTC)


def get_archive_root() -> Path:
    settings = get_settings()
    root = Path(settings.archive_data_path)
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def get_archive_upload_root() -> Path:
    settings = get_settings()
    root = Path(settings.tmp_path) / "archive-uploads"
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def _session_dir(session_id: str) -> Path:
    return get_archive_upload_root() / session_id


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
        raise ArchiveUploadError("Archive upload session not found", status_code=404)
    with metadata_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _save_session(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    session_dir = _session_dir(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    with _session_metadata_path(session_id).open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    return payload


def list_archive_files() -> list[dict[str, Any]]:
    root = get_archive_root()
    result: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            archive_format = detect_archive_format(path)
        except ArchiveExtractionError:
            continue
        stat = path.stat()
        result.append(
            {
                "relative_path": path.relative_to(root).as_posix(),
                "file_name": path.name,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime, tz=UTC),
                "format": archive_format,
            }
        )
    return result


def create_archive_upload_session(files: list[dict[str, Any]]) -> dict[str, Any]:
    if not files:
        raise ArchiveUploadError("At least one archive is required")

    total_size_bytes = 0
    normalized_files: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    archive_root = get_archive_root()

    for file in files:
        relative_path = normalize_relative_path(str(file["relative_path"]))
        if relative_path in seen_paths:
            raise ArchiveUploadError(f"Duplicate archive in upload session: {relative_path}")
        seen_paths.add(relative_path)

        size_bytes = int(file["size_bytes"])
        if size_bytes <= 0:
            raise ArchiveUploadError(f"Archive must be non-empty: {relative_path}")
        total_size_bytes += size_bytes
        if total_size_bytes > UPLOAD_SIZE_LIMIT_BYTES:
            raise ArchiveUploadError("Archive upload session exceeds 100 GB limit")

        target_path = _safe_join(archive_root, relative_path)
        if target_path.exists():
            raise ArchiveUploadError(f"Archive already exists: {relative_path}", status_code=409)
        try:
            archive_format = detect_archive_format(relative_path)
        except ArchiveExtractionError as exc:
            raise ArchiveUploadError(str(exc)) from exc

        normalized_files.append(
            {
                "file_id": str(uuid.uuid4()),
                "relative_path": relative_path,
                "size_bytes": size_bytes,
                "uploaded_bytes": 0,
                "content_type": file.get("content_type"),
                "status": "pending",
                "format": archive_format,
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


def get_archive_session_file(session_id: str, file_id: str) -> dict[str, Any]:
    session = _load_session(session_id)
    if session["status"] != "open":
        raise ArchiveUploadError("Archive upload session is not open", status_code=409)
    for file in session["files"]:
        if file["file_id"] == file_id:
            return session
    raise ArchiveUploadError("Archive upload file not found", status_code=404)


def get_archive_session_payload_path(session_id: str, relative_path: str) -> Path:
    return _safe_join(_session_payload_dir(session_id), relative_path)


def update_uploaded_archive_chunk(session_id: str, file_id: str, uploaded_bytes: int) -> dict[str, Any]:
    session = _load_session(session_id)
    for file in session["files"]:
        if file["file_id"] != file_id:
            continue
        if uploaded_bytes > file["size_bytes"]:
            raise ArchiveUploadError("Uploaded bytes exceed declared archive size")
        file["uploaded_bytes"] = uploaded_bytes
        file["status"] = "uploaded" if uploaded_bytes == file["size_bytes"] else "uploading"
        return _save_session(session_id, session)
    raise ArchiveUploadError("Archive upload file not found", status_code=404)


def complete_archive_upload_session(session_id: str) -> dict[str, Any]:
    session = _load_session(session_id)
    if session["status"] != "open":
        raise ArchiveUploadError("Archive upload session is not open", status_code=409)

    archive_root = get_archive_root()
    uploaded_archives: list[dict[str, Any]] = []
    targets: list[tuple[Path, Path, str]] = []

    for file in session["files"]:
        if file["uploaded_bytes"] != file["size_bytes"]:
            raise ArchiveUploadError(f"Archive upload is incomplete: {file['relative_path']}", status_code=409)
        source = get_archive_session_payload_path(session_id, file["relative_path"])
        if not source.exists() or not source.is_file():
            raise ArchiveUploadError(f"Archive payload is missing: {file['relative_path']}", status_code=409)

        target = _safe_join(archive_root, file["relative_path"])
        if target.exists():
            raise ArchiveUploadError(f"Archive already exists: {file['relative_path']}", status_code=409)
        targets.append((source, target, file["format"]))

    for source, target, archive_format in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        source.replace(target)
        stat = target.stat()
        uploaded_archives.append(
            {
                "relative_path": target.relative_to(archive_root).as_posix(),
                "file_name": target.name,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime, tz=UTC),
                "format": archive_format,
            }
        )

    session["status"] = "completed"
    session["completed_at"] = _utcnow().isoformat()
    _save_session(session_id, session)
    return {
        "session_id": session_id,
        "status": session["status"],
        "uploaded_archives": uploaded_archives,
    }


def discard_archive_upload_session(session_id: str) -> None:
    _load_session(session_id)
    _delete_session_dir(session_id)
