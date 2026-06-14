"""End-to-end dry run for the Stage Two normalization pipeline."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import PATH_DATA_STORAGE, REPORTS_EN_STAGE_TWO, REPORTS_RU_STAGE_TWO, TEMP_DATA_RELATIVE
from scripts.db import session_scope
from scripts.db.models import DatasetFile, NormalizedArtifact
from scripts.db.repositories import ArtifactRepository, DataQualityRepository, DatasetFileRepository
from scripts.stage_two.duckdb import DuckDBAnalyticsService
from scripts.stage_two.features import (
    FEATURE_SCHEMA_NAME,
    FEATURE_SCHEMA_VERSION,
    FeatureArtifactWriter,
    FeatureArtifactWriteResult,
)
from scripts.stage_two.ingestion.catalog_ingestion_service import CatalogIngestionResult, CatalogIngestionService
from scripts.stage_two.model_ready import (
    MODEL_READY_SCHEMA_NAME,
    MODEL_READY_SCHEMA_VERSION,
    ModelReadyRegistryService,
    ModelReadyWriteResult,
)
from scripts.stage_two.normalization.dns_service import DnsNormalizationService
from scripts.stage_two.normalization.host_service import HostNormalizationService
from scripts.stage_two.parquet import ParquetArtifactWriter
from scripts.stage_two.parser_registry.seed import ParserRegistrySeeder
from scripts.stage_two.quality import LeakageChecker
from scripts.stage_two.storage.bootstrap import StorageBootstrapper, bootstrap_stage_two_storage
from scripts.stage_two.traceability import TraceabilityService


DNS_SAMPLE = """timestamp,src_ip,dst_ip,src_port,dst_port,protocol,query_domain,qtype,qclass,ttl,rcode,label
2024-01-01T00:00:00Z,10.0.0.10,8.8.8.8,53000,53,UDP,example.com,A,IN,300,NOERROR,0
2024-01-01T00:00:01Z,10.0.0.11,8.8.4.4,53001,53,UDP,malware.test,A,IN,60,NOERROR,1
"""

HOST_SAMPLE = """timestamp,process_id,process_name,path,sys_call,event_id,event_type,label
2024-01-01T00:00:00Z,100,cmd.exe,C:\\Windows\\System32\\cmd.exe,CreateProcess,4688,process_start,0
2024-01-01T00:00:01Z,101,powershell.exe,C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe,CreateFile,4663,file_access,1
"""


@dataclass(frozen=True)
class StageTwoDryRunResult:
    """Serializable result of the Stage Two end-to-end dry run."""

    status: str
    sample_root: str
    dry_storage_root: str
    raw_hashes_unchanged: bool
    ingestion_runs: list[dict[str, Any]]
    normalized_artifact_ids: list[int]
    feature_artifact_id: int
    model_ready_artifact_id: int
    duckdb_status: str
    duckdb_report_path: str
    leakage_status: str
    leakage_report_paths: dict[str, str]
    trace_dataset_file_id: int
    report_paths: dict[str, str]


def run_stage_two_e2e_dry_run() -> StageTwoDryRunResult:
    """Run a small DNS/Host dry run through Stage Two services."""
    storage_root = _configured_storage_root()
    bootstrap_stage_two_storage(storage_root)

    dry_storage_root = storage_root / TEMP_DATA_RELATIVE / "stage_two_e2e_dry_run" / "storage"
    StorageBootstrapper(dry_storage_root).bootstrap()
    sample_root = dry_storage_root / "raw"
    sample_files = _ensure_sample_files(sample_root)
    hashes_before = {path: _sha256(path) for path in sample_files}

    parquet_writer = ParquetArtifactWriter(dry_storage_root)
    analytics = DuckDBAnalyticsService(storage_root=dry_storage_root, database_path=":memory:")

    with session_scope() as session:
        ingestion_results: CatalogIngestionResult = CatalogIngestionService(session).ingest_root(
            sample_root,
            root_kind="STAGE_TWO_E2E_DRY_RUN",
        )
        ParserRegistrySeeder(session).seed_from_file()
        sample_catalog_files = _sample_catalog_files(session, sample_files)
        _mark_ready_for_parsing(session, sample_catalog_files)

        normalized_artifacts = [
            artifact
            for artifact in (
                _normalize_sample_files(session, sample_catalog_files, parquet_writer)
            )
            if artifact is not None
        ]
        if not normalized_artifacts:
            raise RuntimeError("Dry run produced no normalized artifacts.")

        artifact_repository = ArtifactRepository(session)
        feature_result = _register_sample_feature_artifact(
            artifact_repository,
            parquet_writer,
            normalized_artifacts[0],
        )
        model_ready_result = _register_sample_model_ready_artifact(
            artifact_repository,
            parquet_writer,
            feature_result.artifact.id,
        )

        quality_repository = DataQualityRepository(session)
        duckdb_report = analytics.run_checks()
        analytics.register_report(quality_repository, duckdb_report)
        leakage_report = LeakageChecker(analytics, session=session).run(quality_repository)
        trace = TraceabilityService(session).get_by_model_ready_id(model_ready_result.artifact.id)

        result = StageTwoDryRunResult(
            status="SUCCESS" if duckdb_report.status == "SUCCESS" and leakage_report.status == "SUCCESS" else "FAILED",
            sample_root=str(sample_root),
            dry_storage_root=str(dry_storage_root),
            raw_hashes_unchanged=hashes_before == {path: _sha256(path) for path in sample_files},
            ingestion_runs=[asdict(ingestion_results)],
            normalized_artifact_ids=[artifact.id for artifact in normalized_artifacts],
            feature_artifact_id=feature_result.artifact.id,
            model_ready_artifact_id=model_ready_result.artifact.id,
            duckdb_status=duckdb_report.status,
            duckdb_report_path=duckdb_report.report_path,
            leakage_status=leakage_report.status,
            leakage_report_paths=leakage_report.report_paths,
            trace_dataset_file_id=trace.dataset_file["id"],
            report_paths={},
        )

    report_paths = _save_dry_run_reports(storage_root, result)
    return StageTwoDryRunResult(**{**asdict(result), "report_paths": report_paths})


def _configured_storage_root() -> Path:
    if not PATH_DATA_STORAGE.strip():
        raise ValueError("PATH_DATA_STORAGE must be configured for Stage Two dry run.")
    return Path(PATH_DATA_STORAGE).expanduser()


def _ensure_sample_files(sample_root: Path) -> tuple[Path, Path]:
    dns_path = sample_root / "dns" / "e2e_sample" / "TRAIN" / "dns_sample.csv"
    host_path = sample_root / "host" / "e2e_sample" / "TRAIN" / "host_sample.csv"
    _write_if_missing(dns_path, DNS_SAMPLE)
    _write_if_missing(host_path, HOST_SAMPLE)
    return dns_path, host_path


def _write_if_missing(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    path.write_text(content, encoding="utf-8", newline="")


def _sample_catalog_files(session: Session, sample_files: tuple[Path, ...]) -> list[DatasetFile]:
    file_paths = [str(path.resolve()) for path in sample_files]
    statement = (
        select(DatasetFile)
        .where(DatasetFile.file_path.in_(file_paths))
        .order_by(DatasetFile.branch, DatasetFile.id)
    )
    return list(session.execute(statement).scalars())


def _mark_ready_for_parsing(session: Session, files: list[DatasetFile]) -> None:
    repository = DatasetFileRepository(session)
    for file in files:
        repository.mark_file_status(file, "READY_FOR_PARSING")


def _normalize_sample_files(
    session: Session,
    files: list[DatasetFile],
    parquet_writer: ParquetArtifactWriter,
) -> list[NormalizedArtifact | None]:
    dns_service = DnsNormalizationService(session, writer=parquet_writer)
    host_service = HostNormalizationService(session, writer=parquet_writer)
    artifacts: list[NormalizedArtifact | None] = []
    for file in files:
        if file.branch == "dns":
            artifacts.append(dns_service.normalize_file(file))
        elif file.branch == "host":
            artifacts.append(host_service.normalize_file(file))
    return artifacts


def _register_sample_feature_artifact(
    repository: ArtifactRepository,
    parquet_writer: ParquetArtifactWriter,
    normalized: NormalizedArtifact,
) -> FeatureArtifactWriteResult:
    feature_writer = FeatureArtifactWriter(parquet_writer)
    rows = [
        {
            "sample_uid": f"stage-two-e2e-{normalized.id}",
            "dataset_id": normalized.dataset_id,
            "normalized_artifact_id": normalized.id,
            "role": normalized.role,
            "branch": normalized.branch,
            "feature_group": "dns_features" if normalized.branch == "dns" else "host_eventlog_features",
            "feature_schema_name": FEATURE_SCHEMA_NAME,
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "source_event_uid_refs": json.dumps([]),
            "source_normalized_path": normalized.normalized_path,
            "created_at": datetime.now(timezone.utc),
            "event_count_feature": float(normalized.event_count or 0),
        }
    ]
    return feature_writer.write_and_register(
        repository,
        rows,
        dataset_id=normalized.dataset_id,
        dataset_slug="e2e-sample",
        role=normalized.role,
        branch=normalized.branch,
        feature_group=rows[0]["feature_group"],
        normalized_artifact_id=normalized.id,
        run_id=f"e2e-{normalized.id}",
    )


def _register_sample_model_ready_artifact(
    repository: ArtifactRepository,
    parquet_writer: ParquetArtifactWriter,
    feature_artifact_id: int,
) -> ModelReadyWriteResult:
    registry = ModelReadyRegistryService(parquet_writer)
    return registry.write_table_artifact(
        repository,
        [{"event_count_feature": 2.0}],
        role="TRAIN",
        branch="dns",
        data_type="X",
        artifact_type="tabular",
        file_name="X_train_e2e.parquet",
        feature_artifact_id=feature_artifact_id,
        schema_name=MODEL_READY_SCHEMA_NAME,
        schema_version=MODEL_READY_SCHEMA_VERSION,
    )


def _save_dry_run_reports(storage_root: Path, result: StageTwoDryRunResult) -> dict[str, str]:
    paths: dict[str, str] = {}
    report_roots = {"en": REPORTS_EN_STAGE_TWO, "ru": REPORTS_RU_STAGE_TWO}
    for language, report_root in report_roots.items():
        report_dir = storage_root / report_root
        report_dir.mkdir(parents=True, exist_ok=True)
        path = report_dir / "stage_two_e2e_dry_run_report.json"
        paths[language] = path.relative_to(storage_root).as_posix()
    payload = {**asdict(result), "report_paths": paths}
    for language in ("en", "ru"):
        path = storage_root / paths[language]
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return paths


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    print(json.dumps(asdict(run_stage_two_e2e_dry_run()), indent=2, sort_keys=True))
