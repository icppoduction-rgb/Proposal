from __future__ import annotations

from sqlalchemy.orm import Session

from cybersec_platform.db import Dataset, OutboxMessage, TaskRecord, get_sync_engine


def _login(client) -> str:
    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123456"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_dataset_validation_persists_outbox_message_when_publish_fails(client, monkeypatch):
    token = _login(client)

    engine = get_sync_engine()
    with Session(engine) as session:
        dataset = Dataset(
            name="dataset-for-outbox",
            source_type="network",
            description="outbox test",
            manifest={
                "name": "dataset-for-outbox",
                "source_type": "network",
                "description": "outbox test",
                "file_name": "dataset.csv",
                "required_columns": ["entity_id"],
                "feature_families": ["network_flow"],
            },
            storage_path="C:/tmp/dataset.csv",
            lineage={},
        )
        session.add(dataset)
        session.commit()
        dataset_id = dataset.id

    monkeypatch.setattr("backend.app.services.outbox.celery_app.send_task", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("broker down")))

    response = client.post(f"/api/datasets/{dataset_id}/validate", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    with Session(engine) as session:
        task_record = session.query(TaskRecord).filter(TaskRecord.object_id == dataset_id).one()
        outbox_message = session.query(OutboxMessage).filter(OutboxMessage.task_record_id == task_record.id).one()
        assert task_record.celery_task_id is None
        assert task_record.detail["publish_state"] in {"pending", "failed"}
        assert outbox_message.status in {"pending", "failed"}
        assert outbox_message.attempts >= 1
        assert outbox_message.last_error == "broker down"
