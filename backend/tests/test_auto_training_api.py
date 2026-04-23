from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from sqlalchemy.orm import Session

from backend.app.services import archive_uploads
from cybersec_platform.contracts.api import JobStatus
from cybersec_platform.db import AutoTrainingArchive, AutoTrainingJob, OutboxMessage, TaskRecord, get_sync_engine


def _login(client) -> str:
    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123456"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _build_zip_archive_bytes() -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("trace.json", '{"exploit": false, "exploit_name": "default"}')
        archive.writestr("trace.res", "timestamp,cpu_usage\n1631222507.309,0.11\n")
    return buffer.getvalue()


def test_auto_training_archive_upload_and_job_creation(client):
    token = _login(client)
    archive_bytes = _build_zip_archive_bytes()

    create_session = client.post(
        "/api/auto-training/uploads/sessions",
        json={
            "files": [
                {
                    "relative_path": "incoming/session-1.zip",
                    "size_bytes": len(archive_bytes),
                    "content_type": "application/zip",
                }
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_session.status_code == 201
    session_payload = create_session.json()
    file_id = session_payload["files"][0]["file_id"]

    upload_chunk = client.put(
        f"/api/auto-training/uploads/sessions/{session_payload['session_id']}/files/{file_id}",
        content=archive_bytes,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
            "X-Chunk-Offset": "0",
            "X-Chunk-Length": str(len(archive_bytes)),
        },
    )
    assert upload_chunk.status_code == 200
    assert upload_chunk.json()["uploaded_bytes"] == len(archive_bytes)

    complete = client.post(
        f"/api/auto-training/uploads/sessions/{session_payload['session_id']}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert complete.status_code == 200
    complete_payload = complete.json()
    assert len(complete_payload["uploaded_archives"]) == 1
    archive_id = complete_payload["uploaded_archives"][0]["id"]

    listed_archives = client.get("/api/auto-training/archives", headers={"Authorization": f"Bearer {token}"})
    assert listed_archives.status_code == 200
    assert listed_archives.json()[0]["name"] == "session-1.zip"

    start_job = client.post("/api/auto-training/jobs", json={}, headers={"Authorization": f"Bearer {token}"})
    assert start_job.status_code == 201
    job_payload = start_job.json()
    assert job_payload["archive_ids"] == [archive_id]
    assert job_payload["status"] == JobStatus.PENDING.value
    assert "task_id" in job_payload["detail"]

    engine = get_sync_engine()
    with Session(engine) as session:
        task_record = session.query(TaskRecord).filter(TaskRecord.object_type == "auto_training_job").one_or_none()
        assert task_record is not None
        assert task_record.object_id == job_payload["id"]
        assert task_record.celery_task_id == "test-task-id"
        assert task_record.detail["publish_state"] == "published"
        outbox_message = session.query(OutboxMessage).filter(OutboxMessage.task_record_id == task_record.id).one_or_none()
        assert outbox_message is not None
        assert outbox_message.status == "published"
        assert outbox_message.queue_name == "training"


def test_auto_training_completion_does_not_rescan_archive_root(client, monkeypatch):
    token = _login(client)
    archive_bytes = _build_zip_archive_bytes()

    create_session = client.post(
        "/api/auto-training/uploads/sessions",
        json={
            "files": [
                {
                    "relative_path": "incoming/session-2.zip",
                    "size_bytes": len(archive_bytes),
                    "content_type": "application/zip",
                }
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_session.status_code == 201
    session_payload = create_session.json()
    file_id = session_payload["files"][0]["file_id"]

    upload_chunk = client.put(
        f"/api/auto-training/uploads/sessions/{session_payload['session_id']}/files/{file_id}",
        content=archive_bytes,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
            "X-Chunk-Offset": "0",
            "X-Chunk-Length": str(len(archive_bytes)),
        },
    )
    assert upload_chunk.status_code == 200

    def _fail_if_scanned():
        raise AssertionError("complete_archive_upload_session must not rescan the full archive root")

    monkeypatch.setattr(archive_uploads, "list_archive_files", _fail_if_scanned)

    complete = client.post(
        f"/api/auto-training/uploads/sessions/{session_payload['session_id']}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert complete.status_code == 200
    assert complete.json()["uploaded_archives"][0]["name"] == "session-2.zip"


def test_auto_training_blocks_archive_delete_while_job_is_active(client):
    token = _login(client)
    archives_root = Path.cwd() / "test-data" / "archives"
    archives_root.mkdir(parents=True, exist_ok=True)
    archive_path = archives_root / "busy.zip"
    archive_path.write_bytes(_build_zip_archive_bytes())

    engine = get_sync_engine()
    with Session(engine) as session:
        archive = AutoTrainingArchive(
            name="busy.zip",
            path=str(archive_path.resolve()),
            relative_path="busy.zip",
            size=archive_path.stat().st_size,
        )
        session.add(archive)
        session.flush()
        session.add(
            AutoTrainingJob(
                archive_ids=[archive.id],
                status=JobStatus.RUNNING.value,
                current_step="training_models",
                progress_percent=50.0,
                detail={"archive_count": 1},
            )
        )
        session.commit()
        archive_id = archive.id

    delete_response = client.delete(f"/api/auto-training/archives/{archive_id}", headers={"Authorization": f"Bearer {token}"})
    assert delete_response.status_code == 409
    assert delete_response.json()["detail"] == "Archives cannot be removed while automatic training is running"
