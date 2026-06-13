"""Repository for ingestion run lifecycle operations."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from scripts.db.models import IngestionRun
from scripts.db.repositories.base_repository import BaseRepository


class IngestionRepository(BaseRepository[IngestionRun]):
    """Data access methods for `ingestion_runs`."""

    model = IngestionRun

    def start_run(
        self,
        *,
        root_path: str,
        root_path_kind: str,
        branch: str | None = None,
        role: str | None = None,
    ) -> IngestionRun:
        """Create a RUNNING ingestion run."""
        run = IngestionRun(
            run_uid=uuid4(),
            root_path=root_path,
            root_path_kind=root_path_kind,
            branch=branch,
            role=role,
            status="RUNNING",
        )
        return self.add(run)

    def finish_run(
        self,
        run: IngestionRun,
        *,
        status: str = "SUCCESS",
        files_seen: int | None = None,
        files_new: int | None = None,
        files_existing: int | None = None,
        files_changed: int | None = None,
        files_failed: int | None = None,
        report_path: str | None = None,
    ) -> IngestionRun:
        """Mark an ingestion run as finished without committing."""
        run.status = status
        run.finished_at = datetime.now(timezone.utc)
        if files_seen is not None:
            run.files_seen = files_seen
        if files_new is not None:
            run.files_new = files_new
        if files_existing is not None:
            run.files_existing = files_existing
        if files_changed is not None:
            run.files_changed = files_changed
        if files_failed is not None:
            run.files_failed = files_failed
        if report_path is not None:
            run.report_path = report_path
        self.session.flush()
        return run

    def mark_partial_success(self, run: IngestionRun, error_message: str | None = None) -> IngestionRun:
        """Mark an ingestion run as PARTIAL_SUCCESS."""
        run.status = "PARTIAL_SUCCESS"
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = error_message
        self.session.flush()
        return run

    def mark_failed(self, run: IngestionRun, error_message: str) -> IngestionRun:
        """Mark an ingestion run as FAILED."""
        run.status = "FAILED"
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = error_message
        self.session.flush()
        return run
