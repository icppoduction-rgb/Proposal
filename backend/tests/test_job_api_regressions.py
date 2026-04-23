from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from cybersec_platform.contracts.api import ArtifactStatus, ValidationStatus
from cybersec_platform.db import (
    Dataset,
    DetectionResult,
    ExplanationJob,
    FeatureSchema,
    InferenceJob,
    ModelArtifact,
    TrainingRun,
    get_sync_engine,
)


def _login(client: TestClient) -> str:
    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123456"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _create_dataset_and_schema(*, suffix: str) -> tuple[str, str]:
    engine = get_sync_engine()
    with Session(engine) as session:
        dataset = Dataset(
            name=f"dataset-{suffix}",
            source_type="network",
            manifest={
                "name": f"dataset-{suffix}",
                "source_type": "network",
                "file_name": f"dataset-{suffix}.csv",
                "required_columns": ["feature_a"],
                "feature_families": ["network_flow"],
            },
            storage_path=f"test-data/raw/dataset-{suffix}.csv",
            normalized_path=f"test-data/normalized/dataset-{suffix}.csv",
            validation_status=ValidationStatus.VALIDATED.value,
            lineage={"suffix": suffix},
        )
        schema = FeatureSchema(
            name=f"schema-{suffix}",
            version="1.0.0",
            source_type="network",
            definition={
                "name": f"schema-{suffix}",
                "version": "1.0.0",
                "source_type": "network",
                "required_columns": ["feature_a"],
                "canonical_mappings": {"entity_id": "entity_id", "event_ts": "event_ts"},
                "feature_families": ["network_flow"],
            },
        )
        session.add_all([dataset, schema])
        session.commit()
        return dataset.id, schema.id


def _create_training_run(*, suffix: str) -> tuple[str, str, str]:
    engine = get_sync_engine()
    dataset_id, schema_id = _create_dataset_and_schema(suffix=suffix)
    with Session(engine) as session:
        training_run = TrainingRun(
            dataset_id=dataset_id,
            feature_schema_id=schema_id,
            request_payload={
                "dataset_id": dataset_id,
                "feature_schema_id": schema_id,
                "models": ["random_forest", "fusion"],
                "hyperparameters": {},
                "sequence_length": 50,
                "sequence_stride": 10,
            },
        )
        session.add(training_run)
        session.commit()
        return training_run.id, dataset_id, schema_id


def _create_model_artifact(
    *,
    training_run_id: str,
    suffix: str,
    model_type: str = "random_forest",
    status: str = ArtifactStatus.PROMOTED.value,
) -> str:
    engine = get_sync_engine()
    with Session(engine) as session:
        artifact = ModelArtifact(
            training_run_id=training_run_id,
            model_name=f"{model_type}-{suffix}",
            model_type=model_type,
            status=status,
            metrics={"f1": 0.9},
            artifact_path=f"test-data/models/{suffix}-{model_type}.joblib",
            artifact_metadata={"feature_columns": ["feature_a"]},
        )
        session.add(artifact)
        session.commit()
        return artifact.id


def _create_inference_context(*, suffix: str) -> tuple[str, str]:
    training_run_id, _, _ = _create_training_run(suffix=suffix)
    artifact_id = _create_model_artifact(training_run_id=training_run_id, suffix=suffix)
    return training_run_id, artifact_id


def _create_detection_result(*, artifact_id: str, suffix: str) -> str:
    engine = get_sync_engine()
    with Session(engine) as session:
        inference_job = InferenceJob(
            model_artifact_id=artifact_id,
            request_payload={
                "model_artifact_id": artifact_id,
                "records": [
                    {
                        "entity_id": f"entity-{suffix}",
                        "event_ts": "2026-01-01T00:00:00Z",
                        "features": {"feature_a": 1.0},
                        "source_type": "network",
                    }
                ],
            },
        )
        session.add(inference_job)
        session.flush()
        detection = DetectionResult(
            inference_job_id=inference_job.id,
            entity_id=f"entity-{suffix}",
            score=0.97,
            predicted_label=1,
            raw_output={"prediction": {"entity_id": f"entity-{suffix}"}, "features": {"feature_a": 1.0}},
        )
        session.add(detection)
        session.commit()
        return detection.id


def test_create_training_run_is_atomic_when_dispatch_fails(monkeypatch):
    async def fail_dispatch(*args, **kwargs):
        raise RuntimeError("dispatch failed")

    monkeypatch.setattr("backend.app.api.routes_training.dispatch_task", fail_dispatch)
    dataset_id, schema_id = _create_dataset_and_schema(suffix="atomic-training")

    with TestClient(app, raise_server_exceptions=False) as local_client:
        token = _login(local_client)
        response = local_client.post(
            "/api/training-runs",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "dataset_id": dataset_id,
                "feature_schema_id": schema_id,
                "models": ["random_forest", "fusion"],
                "hyperparameters": {},
                "sequence_length": 50,
                "sequence_stride": 10,
            },
        )

    assert response.status_code == 500
    engine = get_sync_engine()
    with Session(engine) as session:
        assert session.query(TrainingRun).count() == 0


def test_create_inference_job_is_atomic_when_dispatch_fails(monkeypatch):
    async def fail_dispatch(*args, **kwargs):
        raise RuntimeError("dispatch failed")

    monkeypatch.setattr("backend.app.api.routes_inference.dispatch_task", fail_dispatch)
    _, artifact_id = _create_inference_context(suffix="atomic-inference")

    with TestClient(app, raise_server_exceptions=False) as local_client:
        token = _login(local_client)
        response = local_client.post(
            "/api/inference-jobs",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "model_artifact_id": artifact_id,
                "records": [
                    {
                        "entity_id": "entity-1",
                        "event_ts": "2026-01-01T00:00:00Z",
                        "features": {"feature_a": 1.0},
                        "source_type": "network",
                    }
                ],
            },
        )

    assert response.status_code == 500
    engine = get_sync_engine()
    with Session(engine) as session:
        assert session.query(InferenceJob).count() == 0


def test_create_explanation_job_is_atomic_when_dispatch_fails(monkeypatch):
    async def fail_dispatch(*args, **kwargs):
        raise RuntimeError("dispatch failed")

    monkeypatch.setattr("backend.app.api.routes_explanations.dispatch_task", fail_dispatch)
    _, artifact_id = _create_inference_context(suffix="atomic-explanation")
    detection_result_id = _create_detection_result(artifact_id=artifact_id, suffix="atomic-explanation")

    with TestClient(app, raise_server_exceptions=False) as local_client:
        token = _login(local_client)
        response = local_client.post(
            "/api/explanations",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "model_artifact_id": artifact_id,
                "detection_result_id": detection_result_id,
                "top_k": 5,
            },
        )

    assert response.status_code == 500
    engine = get_sync_engine()
    with Session(engine) as session:
        assert session.query(ExplanationJob).count() == 0


def test_explanation_rejects_artifact_from_different_training_lineage(client):
    token = _login(client)
    training_run_a, _, _ = _create_training_run(suffix="explain-a")
    training_run_b, _, _ = _create_training_run(suffix="explain-b")
    artifact_a = _create_model_artifact(training_run_id=training_run_a, suffix="explain-a")
    artifact_b = _create_model_artifact(training_run_id=training_run_b, suffix="explain-b")
    detection_result_id = _create_detection_result(artifact_id=artifact_a, suffix="mismatch")

    response = client.post(
        "/api/explanations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "model_artifact_id": artifact_b,
            "detection_result_id": detection_result_id,
            "top_k": 5,
        },
    )

    assert response.status_code == 400
    assert "same training lineage" in response.json()["detail"]
    engine = get_sync_engine()
    with Session(engine) as session:
        assert session.query(ExplanationJob).count() == 0
