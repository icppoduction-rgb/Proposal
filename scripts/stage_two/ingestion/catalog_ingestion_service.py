"""Catalog ingestion service for raw and sorted dataset directories."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from config import PATH_FOLDER_DATASETS, PATH_FOLDER_DATASETS_FILTER
from scripts.db import session_scope
from scripts.db.models import IngestionRun
from scripts.db.repositories import DatasetFileRepository, DatasetRepository, IngestionRepository
from scripts.stage_two.ingestion.file_hash_service import FileHashService
from scripts.stage_two.ingestion.scanner import (
    SUPPORTED_SOURCE_FORMATS,
    DatasetFileCandidate,
    DatasetFileScanner,
)


@dataclass(frozen=True)
class CatalogIngestionResult:
    """Summary of a catalog ingestion run."""

    run_id: int
    status: str
    files_seen: int
    files_new: int
    files_existing: int
    files_changed: int
    files_failed: int


class CatalogIngestionService:
    """Register raw dataset files and ingestion run metadata in PostgreSQL."""

    def __init__(
        self,
        session: Session,
        *,
        scanner: DatasetFileScanner | None = None,
        hash_service: FileHashService | None = None,
    ) -> None:
        """Initialize the service with an externally managed SQLAlchemy session."""
        self.session = session
        self.scanner = scanner or DatasetFileScanner()
        self.hash_service = hash_service or FileHashService()
        self.dataset_repository = DatasetRepository(session)
        self.file_repository = DatasetFileRepository(session)
        self.ingestion_repository = IngestionRepository(session)

    def ingest_configured_roots(self) -> list[CatalogIngestionResult]:
        """Ingest configured PATH_FOLDER_DATASETS and PATH_FOLDER_DATASETS_FILTER roots."""
        results: list[CatalogIngestionResult] = []
        for root_kind, root_path in self.configured_roots():
            if not root_path:
                continue
            path = Path(root_path).expanduser()
            if not path.exists():
                continue
            results.append(self.ingest_root(path, root_kind=root_kind))
        return results

    def ingest_root(self, root_path: str | Path, *, root_kind: str) -> CatalogIngestionResult:
        """Scan one root and register discovered files."""
        root = Path(root_path).expanduser().resolve()
        ingestion_run = self.ingestion_repository.start_run(
            root_path=str(root),
            root_path_kind=root_kind,
        )

        try:
            candidates = self.scanner.scan(root)
            counters = self._register_candidates(ingestion_run, candidates)
            status = "SUCCESS" if counters["files_failed"] == 0 else "PARTIAL_SUCCESS"
            self.ingestion_repository.finish_run(
                ingestion_run,
                status=status,
                files_seen=counters["files_seen"],
                files_new=counters["files_new"],
                files_existing=counters["files_existing"],
                files_changed=counters["files_changed"],
                files_failed=counters["files_failed"],
            )
            return CatalogIngestionResult(run_id=ingestion_run.id, status=status, **counters)
        except Exception as exc:
            self.ingestion_repository.mark_failed(ingestion_run, str(exc))
            raise

    @staticmethod
    def configured_roots() -> tuple[tuple[str, str], ...]:
        """Return configured dataset roots with stable root kind labels."""
        return (
            ("PATH_FOLDER_DATASETS", PATH_FOLDER_DATASETS),
            ("PATH_FOLDER_DATASETS_FILTER", PATH_FOLDER_DATASETS_FILTER),
        )

    def _register_candidates(
        self,
        ingestion_run: IngestionRun,
        candidates: list[DatasetFileCandidate],
    ) -> dict[str, int]:
        counters = {
            "files_seen": len(candidates),
            "files_new": 0,
            "files_existing": 0,
            "files_changed": 0,
            "files_failed": 0,
        }
        rows: list[dict[str, Any]] = []

        for candidate in candidates:
            try:
                dataset, _created = self.dataset_repository.get_or_create_dataset(
                    name=candidate.dataset_name,
                    slug=candidate.dataset_slug,
                    branch=candidate.branch,
                    role=candidate.role,
                    source_group=ingestion_run.root_path_kind,
                )
                file_stat = candidate.path.stat()
                file_hash = self.hash_service.sha256(candidate.path)
                existing = self.file_repository.get_by_path(dataset.id, str(candidate.path))
                if existing is None:
                    counters["files_new"] += 1
                elif existing.file_hash_sha256 != file_hash:
                    counters["files_changed"] += 1
                else:
                    counters["files_existing"] += 1

                rows.append(
                    self._build_dataset_file_row(
                        candidate,
                        dataset_id=dataset.id,
                        ingestion_run_id=ingestion_run.id,
                        file_size_bytes=file_stat.st_size,
                        file_modified_at=datetime.fromtimestamp(
                            file_stat.st_mtime,
                            tz=timezone.utc,
                        ),
                        file_hash_sha256=file_hash,
                    )
                )
            except OSError:
                counters["files_failed"] += 1

        self.file_repository.bulk_upsert_files(rows)
        return counters

    def _build_dataset_file_row(
        self,
        candidate: DatasetFileCandidate,
        *,
        dataset_id: int,
        ingestion_run_id: int,
        file_size_bytes: int,
        file_modified_at: datetime,
        file_hash_sha256: str,
    ) -> dict[str, Any]:
        status = "REGISTERED"
        if file_size_bytes == 0:
            status = "EMPTY_FILE"
        elif candidate.source_format not in SUPPORTED_SOURCE_FORMATS:
            status = "UNSUPPORTED_FORMAT"

        return {
            "dataset_id": dataset_id,
            "ingestion_run_id": ingestion_run_id,
            "file_path": str(candidate.path),
            "relative_path": str(candidate.relative_path),
            "file_name": candidate.path.name,
            "file_extension": candidate.path.suffix.lower() or None,
            "source_format": candidate.source_format,
            "file_size_bytes": file_size_bytes,
            "file_hash_sha256": file_hash_sha256,
            "file_modified_at": file_modified_at,
            "role": candidate.role,
            "branch": candidate.branch,
            "status": status,
            "metadata_json": {
                "root_path": str(candidate.root_path),
                "root_relative_path": str(candidate.relative_path),
            },
        }


def ingest_configured_catalog_roots() -> list[CatalogIngestionResult]:
    """Ingest configured roots in a managed transaction."""
    with session_scope() as session:
        return CatalogIngestionService(session).ingest_configured_roots()
