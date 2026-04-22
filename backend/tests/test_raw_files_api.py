from __future__ import annotations

from io import BytesIO
from pathlib import Path

from sqlalchemy import select

from cybersec_platform.contracts.api import EditorPageOut, EditorRowOut, EditorSaveOut
from cybersec_platform.db import Dataset, RawFile, get_sync_engine


def _login(client):
    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123456"})
    return response.json()["access_token"]


def _upload_raw_file(client, token: str, relative_path: str, payload: bytes) -> dict:
    session = client.post(
        "/api/datasets/uploads/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"files": [{"relative_path": relative_path, "size_bytes": len(payload), "content_type": "text/csv"}]},
    )
    assert session.status_code == 201
    session_payload = session.json()
    file_id = session_payload["files"][0]["file_id"]

    upload = client.put(
        f"/api/datasets/uploads/sessions/{session_payload['session_id']}/files/{file_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Chunk-Offset": "0",
            "X-Chunk-Length": str(len(payload)),
            "Content-Type": "application/octet-stream",
        },
        content=payload,
    )
    assert upload.status_code == 200

    complete = client.post(
        f"/api/datasets/uploads/sessions/{session_payload['session_id']}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert complete.status_code == 200
    return complete.json()["uploaded_files"][0]


def test_upload_completion_registers_raw_file_in_database(client):
    token = _login(client)
    payload = b"name,score\nalice,1\n"

    uploaded = _upload_raw_file(client, token, "incoming/sample.csv", payload)
    assert uploaded["name"] == "sample.csv"
    assert uploaded["relative_path"] == "incoming/sample.csv"
    assert uploaded["size"] == len(payload)

    engine = get_sync_engine()
    with engine.begin() as connection:
        rows = connection.execute(select(RawFile)).fetchall()
    assert len(rows) == 1


def test_delete_raw_file_removes_fs_and_marks_dataset_failed(client):
    token = _login(client)
    payload = b"name,score\nalice,1\n"
    uploaded = _upload_raw_file(client, token, "incoming/sample.csv", payload)

    registered = client.post(
        "/api/datasets/register",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Uploaded dataset",
            "source_type": "host",
            "file_name": uploaded["relative_path"],
            "required_columns": ["name", "score"],
            "label_column": "label",
            "timestamp_column": "event_ts",
            "entity_id_column": "entity_id",
            "feature_families": ["process"],
            "mitre_mapping": {},
            "lineage": {"source": "test"},
        },
    )
    assert registered.status_code == 201
    dataset_id = registered.json()["id"]

    deleted = client.delete(
        f"/api/datasets/raw-files/{uploaded['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert deleted.status_code == 200

    assert not Path(uploaded["path"]).exists()
    dataset = client.get(f"/api/datasets/{dataset_id}", headers={"Authorization": f"Bearer {token}"})
    assert dataset.status_code == 200
    assert dataset.json()["validation_status"] == "failed"
    assert dataset.json()["validation_errors"]["error"] == "raw source deleted"


def test_delete_all_raw_files_clears_directory_and_invalidates_datasets(client):
    token = _login(client)
    first = _upload_raw_file(client, token, "incoming/one.csv", b"name\nalice\n")
    second = _upload_raw_file(client, token, "incoming/two.csv", b"name\nbob\n")

    for uploaded in (first, second):
        response = client.post(
            "/api/datasets/register",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": uploaded["name"],
                "source_type": "host",
                "file_name": uploaded["relative_path"],
                "required_columns": ["name"],
                "label_column": "label",
                "timestamp_column": "event_ts",
                "entity_id_column": "entity_id",
                "feature_families": ["process"],
                "mitre_mapping": {},
                "lineage": {"source": "test"},
            },
        )
        assert response.status_code == 201

    deleted = client.delete("/api/datasets/raw-files", headers={"Authorization": f"Bearer {token}"})
    assert deleted.status_code == 200

    raw_root = Path.cwd() / "test-data" / "raw"
    assert list(raw_root.rglob("*")) == []

    datasets = client.get("/api/datasets", headers={"Authorization": f"Bearer {token}"})
    assert datasets.status_code == 200
    assert all(item["validation_status"] == "failed" for item in datasets.json())


def test_save_editor_session_updates_size_and_invalidates_dataset(client, monkeypatch):
    token = _login(client)
    uploaded = _upload_raw_file(client, token, "incoming/sample.csv", b"name,score\nalice,1\n")

    registered = client.post(
        "/api/datasets/register",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Editable dataset",
            "source_type": "host",
            "file_name": uploaded["relative_path"],
            "required_columns": ["name", "score"],
            "label_column": "label",
            "timestamp_column": "event_ts",
            "entity_id_column": "entity_id",
            "feature_families": ["process"],
            "mitre_mapping": {},
            "lineage": {"source": "test"},
        },
    )
    assert registered.status_code == 201
    dataset_id = registered.json()["id"]

    engine = get_sync_engine()
    with engine.begin() as connection:
        connection.execute(
            Dataset.__table__.update()
            .where(Dataset.id == dataset_id)
            .values(
                validation_status="validated",
                normalized_path="/tmp/normalized.csv",
                normalization_profile="generic_tabular",
                normalization_summary={"rows": 10},
                normalization_report_path="/tmp/report.json",
            )
        )
        connection.execute(
            RawFile.__table__.update().where(RawFile.id == uploaded["id"]).values(size=1)
        )

    async def fake_get_editor_page(*_args, **_kwargs):
        return EditorPageOut(
            session_id="editor-1",
            file_name="sample.csv",
            file_path=uploaded["path"],
            dataset_format="csv",
            read_only=False,
            page_size=50,
            total_rows=1,
            total_pages=1,
            columns=["name", "score"],
            available_sheets=[],
            active_sheet=None,
            deleted_row_count=0,
            deleted_columns=[],
            pending_cell_count=1,
            page=1,
            rows=[EditorRowOut(row_index=0, values={"name": "alice", "score": "2"})],
        )

    async def fake_save_editor_session(*_args, **_kwargs):
        return EditorSaveOut(
            session_id="editor-1",
            file_path=uploaded["path"],
            size_bytes=128,
            modified_at="2026-01-01T00:00:00Z",
            row_count=1,
            column_count=2,
        )

    monkeypatch.setattr("backend.app.api.routes_datasets.get_editor_page", fake_get_editor_page)
    monkeypatch.setattr("backend.app.api.routes_datasets.save_editor_session", fake_save_editor_session)

    saved = client.post(
        f"/api/datasets/raw-files/{uploaded['id']}/editor-sessions/editor-1/save",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert saved.status_code == 200

    dataset = client.get(f"/api/datasets/{dataset_id}", headers={"Authorization": f"Bearer {token}"})
    assert dataset.status_code == 200
    payload = dataset.json()
    assert payload["validation_status"] == "pending"
    assert payload["normalized_path"] is None
    assert payload["normalization_summary"] == {}
    assert payload["normalization_report_path"] is None

    engine = get_sync_engine()
    with engine.begin() as connection:
        raw_file_size = connection.execute(select(RawFile.size).where(RawFile.id == uploaded["id"])).scalar_one()
    assert raw_file_size == 128
