"""Smoke checks for the Stage Two PostgreSQL catalog foundation."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from config import (
    NORMALIZED_SCHEMA_PATH,
    PARQUET_FEATURES_RELATIVE,
    PARQUET_MODEL_READY_RELATIVE,
    PARQUET_NORMALIZED_RELATIVE,
)
from scripts.db import create_session_factory, get_engine
from scripts.db.models import Dataset, PreprocessingArtifact
from scripts.db.repositories import (
    ArtifactRepository,
    DataQualityRepository,
    DatasetFileRepository,
    DatasetRepository,
    IngestionRepository,
    ParserRepository,
    PreprocessingRepository,
    SchemaRepository,
)


SMOKE_DATASET_NAME = "stage_two_smoke_dataset"
SMOKE_DATASET_SLUG = "stage-two-smoke-dataset"


@dataclass(frozen=True)
class SmokeCheckResult:
    """Summary of DB smoke checks."""

    checks_passed: tuple[str, ...]


def run_smoke_checks() -> SmokeCheckResult:
    """Run DB foundation smoke checks and roll back all test data."""
    engine = get_engine()
    session_factory = create_session_factory(engine)
    session = session_factory()
    transaction = session.begin()
    checks: list[str] = []

    try:
        dataset_repo = DatasetRepository(session)
        ingestion_repo = IngestionRepository(session)
        file_repo = DatasetFileRepository(session)
        parser_repo = ParserRepository(session)
        schema_repo = SchemaRepository(session)
        artifact_repo = ArtifactRepository(session)
        preprocessing_repo = PreprocessingRepository(session)
        quality_repo = DataQualityRepository(session)

        dataset, created = dataset_repo.get_or_create_dataset(
            name=SMOKE_DATASET_NAME,
            slug=SMOKE_DATASET_SLUG,
            branch="dns",
            role="TRAIN",
            source_group="smoke",
        )
        _assert(created, "dataset was not created")
        checks.append("create dataset")

        _expect_integrity_error(
            session,
            Dataset(
                name=SMOKE_DATASET_NAME,
                slug=SMOKE_DATASET_SLUG,
                branch="dns",
                role="TRAIN",
            ),
        )
        checks.append("unique constraint")

        _expect_integrity_error(
            session,
            Dataset(
                name="invalid_branch_smoke",
                slug="invalid-branch-smoke",
                branch="invalid",
                role="TRAIN",
            ),
        )
        checks.append("check constraint")

        ingestion_run = ingestion_repo.start_run(
            root_path="smoke",
            root_path_kind="synthetic",
            branch="dns",
            role="TRAIN",
        )
        checks.append("create ingestion_run")

        file_repo.bulk_upsert_files(
            [
                {
                    "dataset_id": dataset.id,
                    "ingestion_run_id": ingestion_run.id,
                    "file_path": "smoke/raw.csv",
                    "relative_path": "raw.csv",
                    "file_name": "raw.csv",
                    "file_extension": ".csv",
                    "source_format": "csv",
                    "file_size_bytes": 10,
                    "file_hash_sha256": "0" * 64,
                    "role": "TRAIN",
                    "branch": "dns",
                    "status": "READY_FOR_PARSING",
                }
            ]
        )
        dataset_file = file_repo.get_by_path(dataset.id, "smoke/raw.csv")
        _assert(dataset_file is not None, "dataset_file was not inserted")
        checks.append("insert dataset_file")

        parser_registry = parser_repo.add(
            parser_repo.model(
                parser_name="smoke_dns_csv_parser",
                parser_version="v1",
                branch="dns",
                source_format="csv",
                supported_role="TRAIN",
                normalized_schema_name="normalized_event",
                normalized_schema_version="v1",
                parser_module="scripts.stage_two.parsers.dns",
                parser_class="SmokeDnsCsvParser",
            )
        )
        schema_version = schema_repo.register_schema_version(
            schema_name="normalized_event",
            schema_version="v1",
            layer="normalized",
            branch="dns",
            schema_path=NORMALIZED_SCHEMA_PATH,
        )
        parser_run = parser_repo.create_parser_run(
            file=dataset_file,
            parser_name=parser_registry.parser_name,
            parser_version=parser_registry.parser_version,
            parser_registry=parser_registry,
            schema_version=schema_version,
        )
        parser_repo.finish_parser_run(
            parser_run,
            rows_read=1,
            rows_parsed=1,
            rows_failed=0,
            events_emitted=1,
            output_parquet_path=f"{PARQUET_NORMALIZED_RELATIVE}/dns/TRAIN/smoke/schema=v1/part-smoke.parquet",
        )
        checks.append("parser_run")

        normalized = artifact_repo.register_normalized_artifact(
            artifact_uid=uuid4(),
            dataset_id=dataset.id,
            file_id=dataset_file.id,
            parser_run_id=parser_run.id,
            schema_version_id=schema_version.id,
            role="TRAIN",
            branch="dns",
            modality="dns_query",
            source_format="csv",
            normalized_path=f"{PARQUET_NORMALIZED_RELATIVE}/dns/TRAIN/smoke/schema=v1/part-smoke.parquet",
            schema_name="normalized_event",
            schema_version="v1",
            row_count=1,
            event_count=1,
        )
        checks.append("normalized artifact")

        feature = artifact_repo.register_feature_artifact(
            artifact_uid=uuid4(),
            dataset_id=dataset.id,
            normalized_artifact_id=normalized.id,
            role="TRAIN",
            branch="dns",
            feature_group="dns_features",
            feature_path=f"{PARQUET_FEATURES_RELATIVE}/dns_features/TRAIN/smoke/schema=v1/part-smoke.parquet",
            feature_schema_name="feature_artifact",
            feature_schema_version="v1",
            row_count=1,
            sample_count=1,
            feature_count=1,
        )

        preprocessing = preprocessing_repo.register_preprocessing_artifact(
            artifact_uid=uuid4(),
            branch="dns",
            feature_group="dns_features",
            preprocessing_type="scaler",
            artifact_path=f"{PARQUET_MODEL_READY_RELATIVE}/preprocessing/dns/schema=v1/train.pkl",
            fitted_on_role="TRAIN",
            fitted_on_feature_artifact_id=feature.id,
            schema_version="v1",
            object_version="v1",
        )
        checks.append("preprocessing artifact TRAIN-only")

        _expect_integrity_error(
            session,
            PreprocessingArtifact(
                artifact_uid=uuid4(),
                branch="dns",
                preprocessing_type="scaler",
                artifact_path="invalid-test-fit.pkl",
                fitted_on_role="TEST",
                schema_version="v1",
                object_version="v1",
            ),
        )
        checks.append("preprocessing artifact rejects TEST")

        artifact_repo.register_model_ready_artifact(
            artifact_uid=uuid4(),
            feature_artifact_id=feature.id,
            preprocessing_artifact_id=preprocessing.id,
            role="TRAIN",
            branch="dns",
            data_type="X",
            artifact_path=f"{PARQUET_MODEL_READY_RELATIVE}/tabular/dns/TRAIN/schema=v1/X_train.parquet",
            schema_name="model_ready",
            schema_version="v1",
            sample_count=1,
            feature_count=1,
        )

        quality_repo.create_report(
            report_uid=uuid4(),
            artifact_type="normalized",
            artifact_id=normalized.id,
            check_group="smoke",
            check_name="catalog_foundation",
            status="SUCCESS",
            severity="INFO",
            rows_total=1,
            rows_valid=1,
            rows_failed=0,
        )
        checks.append("data_quality_report")

    finally:
        transaction.rollback()
        session.close()

    _assert(_smoke_dataset_count(session_factory) == 0, "rollback left smoke dataset rows")
    checks.append("rollback")
    return SmokeCheckResult(checks_passed=tuple(checks))


def _expect_integrity_error(session, entity: object) -> None:
    try:
        with session.begin_nested():
            session.add(entity)
            session.flush()
    except IntegrityError:
        return
    raise AssertionError("expected IntegrityError was not raised")


def _smoke_dataset_count(session_factory) -> int:
    with session_factory() as session:
        statement = select(func.count()).select_from(Dataset).where(
            Dataset.slug == SMOKE_DATASET_SLUG
        )
        return int(session.execute(statement).scalar_one())


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    """Run smoke checks from the command line."""
    result = run_smoke_checks()
    print("Smoke checks passed:")
    for check in result.checks_passed:
        print(f"- {check}")


if __name__ == "__main__":
    main()
