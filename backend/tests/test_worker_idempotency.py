from __future__ import annotations

import asyncio
from pathlib import Path
import sys

from sqlalchemy.orm import Session

from cybersec_platform.contracts.api import ArtifactStatus, InferenceRequest, JobStatus, SourceType, ValidationStatus
from cybersec_platform.db import (
    Dataset,
    DetectionResult,
    ExplanationJob,
    ExplanationResult,
    FeatureSchema,
    InboxMessage,
    InferenceJob,
    ModelArtifact,
    TrainingRun,
    get_sync_engine,
)

sys.path.append(str(Path.cwd() / "services" / "training_service"))

from app import worker


def _create_training_run(*, suffix: str) -> str:
    engine = get_sync_engine()
    normalized_path = Path.cwd() / "test-data" / "normalized" / f"{suffix}.csv"
    normalized_path.parent.mkdir(parents=True, exist_ok=True)
    normalized_path.write_text("entity_id,event_ts,feature_a,label\nentity-1,2026-01-01T00:00:00Z,1,1\n", encoding="utf-8")

    with Session(engine) as session:
        dataset = Dataset(
            name=f"dataset-{suffix}",
            source_type="network",
            manifest={
                "name": f"dataset-{suffix}",
                "source_type": "network",
                "file_name": normalized_path.name,
                "required_columns": ["feature_a"],
                "feature_families": ["network_flow"],
            },
            storage_path=str(normalized_path),
            normalized_path=str(normalized_path),
            validation_status=ValidationStatus.VALIDATED.value,
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
        session.flush()
        run = TrainingRun(
            dataset_id=dataset.id,
            feature_schema_id=schema.id,
            request_payload={
                "dataset_id": dataset.id,
                "feature_schema_id": schema.id,
                "models": ["random_forest", "xgboost", "fusion"],
                "hyperparameters": {},
                "sequence_length": 50,
                "sequence_stride": 10,
            },
        )
        session.add(run)
        session.commit()
        return run.id


def _create_inference_job(*, suffix: str) -> str:
    engine = get_sync_engine()
    with Session(engine) as session:
        dataset = Dataset(
            name=f"inference-dataset-{suffix}",
            source_type="network",
            manifest={
                "name": f"inference-dataset-{suffix}",
                "source_type": "network",
                "file_name": f"{suffix}.csv",
                "required_columns": ["feature_a"],
                "feature_families": ["network_flow"],
            },
            storage_path=f"test-data/raw/{suffix}.csv",
            normalized_path=f"test-data/normalized/{suffix}.csv",
            validation_status=ValidationStatus.VALIDATED.value,
        )
        schema = FeatureSchema(
            name=f"inference-schema-{suffix}",
            version="1.0.0",
            source_type="network",
            definition={
                "name": f"inference-schema-{suffix}",
                "version": "1.0.0",
                "source_type": "network",
                "required_columns": ["feature_a"],
                "canonical_mappings": {"entity_id": "entity_id", "event_ts": "event_ts"},
                "feature_families": ["network_flow"],
            },
        )
        session.add_all([dataset, schema])
        session.flush()
        training_run = TrainingRun(
            dataset_id=dataset.id,
            feature_schema_id=schema.id,
            request_payload={"sequence_length": 50, "sequence_stride": 10},
            status=JobStatus.COMPLETED.value,
        )
        session.add(training_run)
        session.flush()
        artifact = ModelArtifact(
            training_run_id=training_run.id,
            model_name=f"rf-{suffix}",
            model_type="random_forest",
            status=ArtifactStatus.PROMOTED.value,
            metrics={"f1": 0.9},
            artifact_path=f"test-data/models/{suffix}.joblib",
            artifact_metadata={"feature_columns": ["feature_a"]},
        )
        session.add(artifact)
        session.flush()
        job = InferenceJob(
            model_artifact_id=artifact.id,
            request_payload=InferenceRequest(
                model_artifact_id=artifact.id,
                records=[
                    {
                        "entity_id": f"entity-{suffix}",
                        "event_ts": "2026-01-01T00:00:00Z",
                        "features": {"feature_a": 1.0},
                        "source_type": SourceType.NETWORK,
                    }
                ],
            ).model_dump(mode="json"),
        )
        session.add(job)
        session.commit()
        return job.id


def _create_explanation_job(*, suffix: str) -> str:
    engine = get_sync_engine()
    report_path = Path.cwd() / "test-data" / "models" / f"{suffix}.joblib"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("bundle", encoding="utf-8")

    with Session(engine) as session:
        dataset = Dataset(
            name=f"explanation-dataset-{suffix}",
            source_type="network",
            manifest={
                "name": f"explanation-dataset-{suffix}",
                "source_type": "network",
                "file_name": f"{suffix}.csv",
                "required_columns": ["feature_a"],
                "feature_families": ["network_flow"],
            },
            storage_path=f"test-data/raw/{suffix}.csv",
            normalized_path=f"test-data/normalized/{suffix}.csv",
            validation_status=ValidationStatus.VALIDATED.value,
        )
        schema = FeatureSchema(
            name=f"explanation-schema-{suffix}",
            version="1.0.0",
            source_type="network",
            definition={
                "name": f"explanation-schema-{suffix}",
                "version": "1.0.0",
                "source_type": "network",
                "required_columns": ["feature_a"],
                "canonical_mappings": {"entity_id": "entity_id", "event_ts": "event_ts"},
                "feature_families": ["network_flow"],
            },
        )
        session.add_all([dataset, schema])
        session.flush()
        training_run = TrainingRun(
            dataset_id=dataset.id,
            feature_schema_id=schema.id,
            request_payload={"sequence_length": 50, "sequence_stride": 10},
            status=JobStatus.COMPLETED.value,
        )
        session.add(training_run)
        session.flush()
        artifact = ModelArtifact(
            training_run_id=training_run.id,
            model_name="fusion",
            model_type="fusion",
            status=ArtifactStatus.PROMOTED.value,
            metrics={"f1": 0.9},
            artifact_path=str(report_path),
            artifact_metadata={"feature_columns": ["feature_a"]},
        )
        session.add(artifact)
        session.flush()
        inference_job = InferenceJob(
            model_artifact_id=artifact.id,
            request_payload={
                "model_artifact_id": artifact.id,
                "records": [
                    {
                        "entity_id": f"entity-{suffix}",
                        "event_ts": "2026-01-01T00:00:00Z",
                        "features": {"feature_a": 1.0},
                        "source_type": "network",
                    }
                ],
            },
            status=JobStatus.COMPLETED.value,
        )
        session.add(inference_job)
        session.flush()
        detection = DetectionResult(
            inference_job_id=inference_job.id,
            entity_id=f"entity-{suffix}",
            score=0.9,
            predicted_label=1,
            raw_output={"prediction": {"entity_id": f"entity-{suffix}"}, "features": {"feature_a": 1.0}},
        )
        session.add(detection)
        session.flush()
        job = ExplanationJob(
            model_artifact_id=artifact.id,
            detection_result_id=detection.id,
            request_payload={"model_artifact_id": artifact.id, "detection_result_id": detection.id, "top_k": 5},
        )
        session.add(job)
        session.commit()
        return job.id


def test_run_training_is_idempotent(monkeypatch):
    def fake_train(self, dataset_path, manifest, training_request, schema_definition, reports_dir):
        return {
            "models": {
                "random_forest": {"kind": "rf"},
                "xgboost": {"kind": "xgb"},
            },
            "metrics": {
                "f1": 0.91,
                "branch_metrics": {
                    "random_forest": {"f1": 0.92},
                    "xgboost": {"f1": 0.9},
                },
            },
            "feature_columns": ["feature_a"],
            "required_feature_columns": ["feature_a"],
            "feature_schema": {"required_columns": ["feature_a"]},
            "reports": {"summary_report": "ok"},
        }

    def fake_save_model(self, file_name, payload):
        target = Path.cwd() / "test-data" / "models" / file_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(payload), encoding="utf-8")
        return str(target)

    monkeypatch.setattr(worker.HybridTrainer, "train", fake_train)
    monkeypatch.setattr(worker.ArtifactStore, "save_model", fake_save_model)

    training_run_id = _create_training_run(suffix="worker-training")

    asyncio.run(worker._run_training(training_run_id, task_headers={"message_id": "training-message-1"}))
    asyncio.run(worker._run_training(training_run_id, task_headers={"message_id": "training-message-1"}))
    asyncio.run(worker._run_training(training_run_id, task_headers={"message_id": "training-message-2"}))

    engine = get_sync_engine()
    with Session(engine) as session:
        assert session.query(ModelArtifact).filter(ModelArtifact.training_run_id == training_run_id).count() == 3
        run = session.get(TrainingRun, training_run_id)
        assert run is not None
        assert run.status == JobStatus.COMPLETED.value
        assert session.query(InboxMessage).filter(InboxMessage.consumer_name == "training.run_training").count() == 2


def test_run_inference_is_idempotent(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "predictions": [
                    {
                        "entity_id": "entity-worker-inference",
                        "score": 0.88,
                        "predicted_label": 1,
                    }
                ]
            }

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json):
            return FakeResponse()

    monkeypatch.setattr(worker.httpx, "AsyncClient", FakeAsyncClient)

    inference_job_id = _create_inference_job(suffix="worker-inference")

    asyncio.run(worker._run_inference(inference_job_id, task_headers={"message_id": "inference-message-1"}))
    asyncio.run(worker._run_inference(inference_job_id, task_headers={"message_id": "inference-message-1"}))
    asyncio.run(worker._run_inference(inference_job_id, task_headers={"message_id": "inference-message-2"}))

    engine = get_sync_engine()
    with Session(engine) as session:
        assert session.query(DetectionResult).filter(DetectionResult.inference_job_id == inference_job_id).count() == 1
        job = session.get(InferenceJob, inference_job_id)
        assert job is not None
        assert job.status == JobStatus.COMPLETED.value
        assert session.query(InboxMessage).filter(InboxMessage.consumer_name == "training.run_inference").count() == 2


def test_generate_explanation_is_idempotent(monkeypatch):
    def fake_load_model_bundle(path):
        return {"path": path}

    def fake_explain_record(self, bundle, features, top_k):
        return {
            "top_positive": [{"feature": "feature_a", "contribution": 0.7}],
            "top_negative": [],
            "summary": "ok",
        }

    def fake_save_explanation(self, file_name, payload):
        target = Path.cwd() / "test-data" / "explanations" / file_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(payload), encoding="utf-8")
        return str(target)

    monkeypatch.setattr(worker, "load_model_bundle", fake_load_model_bundle)
    monkeypatch.setattr(worker.HybridTrainer, "explain_record", fake_explain_record)
    monkeypatch.setattr(worker.ArtifactStore, "save_explanation", fake_save_explanation)

    explanation_job_id = _create_explanation_job(suffix="worker-explanation")

    asyncio.run(worker._generate_explanation(explanation_job_id, task_headers={"message_id": "explanation-message-1"}))
    asyncio.run(worker._generate_explanation(explanation_job_id, task_headers={"message_id": "explanation-message-1"}))
    asyncio.run(worker._generate_explanation(explanation_job_id, task_headers={"message_id": "explanation-message-2"}))

    engine = get_sync_engine()
    with Session(engine) as session:
        assert session.query(ExplanationResult).filter(ExplanationResult.explanation_job_id == explanation_job_id).count() == 1
        job = session.get(ExplanationJob, explanation_job_id)
        assert job is not None
        assert job.status == JobStatus.COMPLETED.value
        assert session.query(InboxMessage).filter(InboxMessage.consumer_name == "training.generate_explanation").count() == 2
