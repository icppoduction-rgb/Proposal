from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from cybersec_platform.contracts.api import ArtifactStatus, ValidationStatus
from cybersec_platform.db import Dataset, FeatureSchema, ModelArtifact, TrainingRun, get_sync_engine


def _login(client):
    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123456"})
    return response.json()["access_token"]


def _create_training_run(*, suffix: str = "") -> tuple[str, str]:
    engine = get_sync_engine()
    with Session(engine) as session:
        dataset = Dataset(
            name=f"Dataset{suffix}",
            source_type="network",
            manifest={"required_columns": ["feature_a"], "feature_families": ["network_flow"]},
            storage_path=f"test-data/raw/dataset{suffix}.csv",
            normalized_path=f"test-data/normalized/dataset{suffix}.csv",
            validation_status=ValidationStatus.VALIDATED.value,
        )
        schema = FeatureSchema(
            name=f"schema{suffix}",
            version="1.0.0",
            source_type="network",
            definition={
                "name": f"schema{suffix}",
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
            request_payload={"sequence_length": 50, "sequence_stride": 10},
        )
        session.add(run)
        session.commit()
        return run.id, dataset.id


def _create_model_artifact(
    *,
    training_run_id: str,
    model_name: str,
    model_type: str,
    status: str,
    artifact_path: str,
) -> str:
    engine = get_sync_engine()
    with Session(engine) as session:
        artifact = ModelArtifact(
            training_run_id=training_run_id,
            model_name=model_name,
            model_type=model_type,
            status=status,
            metrics={"f1": 0.9},
            artifact_path=artifact_path,
            artifact_metadata={},
        )
        session.add(artifact)
        session.commit()
        return artifact.id


def _read_model_status(artifact_id: str) -> str:
    engine = get_sync_engine()
    with Session(engine) as session:
        artifact = session.get(ModelArtifact, artifact_id)
        assert artifact is not None
        return artifact.status


def test_promote_model_deprecates_only_other_promoted_artifacts(client):
    token = _login(client)
    training_run_id, _ = _create_training_run()
    models_dir = Path.cwd() / "test-data" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    target_path = models_dir / "target.joblib"
    target_path.write_text("target", encoding="utf-8")
    old_path = models_dir / "old.joblib"
    old_path.write_text("old", encoding="utf-8")
    another_path = models_dir / "another.joblib"
    another_path.write_text("another", encoding="utf-8")
    other_type_path = models_dir / "other-type.joblib"
    other_type_path.write_text("other-type", encoding="utf-8")

    old_promoted_id = _create_model_artifact(
        training_run_id=training_run_id,
        model_name="rf-old",
        model_type="random_forest",
        status=ArtifactStatus.PROMOTED.value,
        artifact_path=str(old_path),
    )
    candidate_same_type_id = _create_model_artifact(
        training_run_id=training_run_id,
        model_name="rf-candidate",
        model_type="random_forest",
        status=ArtifactStatus.CANDIDATE.value,
        artifact_path=str(another_path),
    )
    other_type_id = _create_model_artifact(
        training_run_id=training_run_id,
        model_name="xgb-promoted",
        model_type="xgboost",
        status=ArtifactStatus.PROMOTED.value,
        artifact_path=str(other_type_path),
    )
    target_id = _create_model_artifact(
        training_run_id=training_run_id,
        model_name="rf-new",
        model_type="random_forest",
        status=ArtifactStatus.CANDIDATE.value,
        artifact_path=str(target_path),
    )

    response = client.post(f"/api/models/{target_id}/promote", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["status"] == ArtifactStatus.PROMOTED.value
    assert _read_model_status(target_id) == ArtifactStatus.PROMOTED.value
    assert _read_model_status(old_promoted_id) == ArtifactStatus.DEPRECATED.value
    assert _read_model_status(candidate_same_type_id) == ArtifactStatus.CANDIDATE.value
    assert _read_model_status(other_type_id) == ArtifactStatus.PROMOTED.value


def test_promote_model_does_not_deprecate_other_dataset_lineage(client):
    token = _login(client)
    training_run_id, _ = _create_training_run(suffix="-a")
    other_training_run_id, _ = _create_training_run(suffix="-b")
    models_dir = Path.cwd() / "test-data" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    shared_old_path = models_dir / "shared-old.joblib"
    shared_old_path.write_text("shared-old", encoding="utf-8")
    shared_target_path = models_dir / "shared-target.joblib"
    shared_target_path.write_text("shared-target", encoding="utf-8")
    other_dataset_path = models_dir / "other-dataset.joblib"
    other_dataset_path.write_text("other-dataset", encoding="utf-8")

    same_dataset_promoted_id = _create_model_artifact(
        training_run_id=training_run_id,
        model_name="rf-old",
        model_type="random_forest",
        status=ArtifactStatus.PROMOTED.value,
        artifact_path=str(shared_old_path),
    )
    other_dataset_promoted_id = _create_model_artifact(
        training_run_id=other_training_run_id,
        model_name="rf-other-dataset",
        model_type="random_forest",
        status=ArtifactStatus.PROMOTED.value,
        artifact_path=str(other_dataset_path),
    )
    target_id = _create_model_artifact(
        training_run_id=training_run_id,
        model_name="rf-new",
        model_type="random_forest",
        status=ArtifactStatus.CANDIDATE.value,
        artifact_path=str(shared_target_path),
    )

    response = client.post(f"/api/models/{target_id}/promote", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert _read_model_status(target_id) == ArtifactStatus.PROMOTED.value
    assert _read_model_status(same_dataset_promoted_id) == ArtifactStatus.DEPRECATED.value
    assert _read_model_status(other_dataset_promoted_id) == ArtifactStatus.PROMOTED.value


def test_download_model_returns_404_when_artifact_file_is_missing(client):
    token = _login(client)
    training_run_id, _ = _create_training_run()
    missing_id = _create_model_artifact(
        training_run_id=training_run_id,
        model_name="rf-missing",
        model_type="random_forest",
        status=ArtifactStatus.CANDIDATE.value,
        artifact_path=str(Path.cwd() / "test-data" / "models" / "missing.joblib"),
    )

    response = client.get(f"/api/models/{missing_id}/download", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Model artifact file not found"
