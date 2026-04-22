from __future__ import annotations

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

from backend.app.services.archive_uploads import (
    complete_archive_upload_session,
    create_archive_upload_session,
    get_archive_session_payload_path,
    update_uploaded_archive_chunk,
)
from backend.app.services.dataset_uploads import (
    complete_upload_session,
    create_upload_session,
    get_session_payload_path,
    update_uploaded_chunk,
)

def _build_zip_archive_bytes() -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("trace.json", '{"exploit": false, "exploit_name": "default"}')
        archive.writestr("trace.res", "timestamp,cpu_usage\n1631222507.309,0.11\n")
    return buffer.getvalue()


@pytest.fixture()
def relative_archive_roots(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    settings = SimpleNamespace(archive_data_path="app-data/archives", tmp_path="app-data/tmp")
    monkeypatch.setattr("backend.app.services.archive_uploads.get_settings", lambda: settings)
    return tmp_path


@pytest.fixture()
def relative_raw_roots(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    settings = SimpleNamespace(raw_data_path="app-data/raw", tmp_path="app-data/tmp")
    monkeypatch.setattr("backend.app.services.dataset_uploads.get_settings", lambda: settings)
    return tmp_path


def test_archive_upload_completion_supports_relative_storage_root(relative_archive_roots: Path):
    payload = _build_zip_archive_bytes()
    session = create_archive_upload_session(
        [
            {
                "relative_path": "model-tranning/abundant_allen_6746.zip",
                "size_bytes": len(payload),
                "content_type": "application/zip",
            }
        ]
    )
    file_id = session["files"][0]["file_id"]
    payload_path = get_archive_session_payload_path(session["session_id"], "model-tranning/abundant_allen_6746.zip")
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_bytes(payload)
    update_uploaded_archive_chunk(session["session_id"], file_id, len(payload))

    completed = complete_archive_upload_session(session["session_id"])

    assert completed["uploaded_archives"][0]["relative_path"] == "model-tranning/abundant_allen_6746.zip"
    assert (relative_archive_roots / "app-data/archives/model-tranning/abundant_allen_6746.zip").exists()


def test_raw_upload_completion_supports_relative_storage_root(relative_raw_roots: Path):
    payload = b"name,score\nalice,1\n"
    session = create_upload_session(
        [
            {
                "relative_path": "incoming/sample.csv",
                "size_bytes": len(payload),
                "content_type": "text/csv",
            }
        ]
    )
    file_id = session["files"][0]["file_id"]
    payload_path = get_session_payload_path(session["session_id"], "incoming/sample.csv")
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_bytes(payload)
    update_uploaded_chunk(session["session_id"], file_id, len(payload))

    completed = complete_upload_session(session["session_id"])

    assert completed["uploaded_files"][0]["relative_path"] == "incoming/sample.csv"
    assert (relative_raw_roots / "app-data/raw/incoming/sample.csv").exists()
