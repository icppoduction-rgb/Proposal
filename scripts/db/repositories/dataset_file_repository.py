"""Repository for raw dataset file catalog records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert

from scripts.db.models import DatasetFile
from scripts.db.models.constants import ROLE_VALUES
from scripts.db.repositories.base_repository import BaseRepository


class DatasetFileRepository(BaseRepository[DatasetFile]):
    """Data access methods for `dataset_files`."""

    model = DatasetFile

    def bulk_upsert_files(self, rows: list[dict[str, Any]]) -> int:
        """Bulk upsert raw file rows by `(dataset_id, file_path)` without committing."""
        if not rows:
            return 0

        table = DatasetFile.__table__
        statement = insert(table).values(rows)
        excluded = statement.excluded
        hash_changed = (
            table.c.file_hash_sha256.is_distinct_from(excluded.file_hash_sha256)
        )
        update_values = {
            "ingestion_run_id": excluded.ingestion_run_id,
            "relative_path": excluded.relative_path,
            "file_name": excluded.file_name,
            "file_extension": excluded.file_extension,
            "source_format": excluded.source_format,
            "mime_type": excluded.mime_type,
            "file_size_bytes": excluded.file_size_bytes,
            "file_hash_sha256": excluded.file_hash_sha256,
            "file_modified_at": excluded.file_modified_at,
            "parser_hint": excluded.parser_hint,
            "has_embedded_label": excluded.has_embedded_label,
            "label_source_hint": excluded.label_source_hint,
            "timestamp_source_hint": excluded.timestamp_source_hint,
            "encoding_hint": excluded.encoding_hint,
            "compression_hint": excluded.compression_hint,
            "row_count_hint": excluded.row_count_hint,
            "metadata_json": excluded.metadata_json,
            "error_message": excluded.error_message,
            "last_seen_at": func.now(),
            "updated_at": func.now(),
            "status": case((hash_changed, "CHANGED"), else_=table.c.status),
        }
        result = self.session.execute(
            statement.on_conflict_do_update(
                index_elements=[table.c.dataset_id, table.c.file_path],
                set_=update_values,
            )
        )
        self.session.flush()
        return result.rowcount or 0

    def get_files_ready_for_parsing(
        self,
        *,
        branch: str | None = None,
        role: str | None = None,
        source_format: str | None = None,
        limit: int | None = None,
        file_ids: tuple[int, ...] | None = None,
    ) -> list[DatasetFile]:
        """Return files marked READY_FOR_PARSING."""
        statement = select(DatasetFile).where(DatasetFile.status == "READY_FOR_PARSING")
        if branch is not None:
            statement = statement.where(DatasetFile.branch == branch)
        if role is not None:
            statement = statement.where(DatasetFile.role == role)
        if source_format is not None:
            statement = statement.where(DatasetFile.source_format == source_format)
        if file_ids is not None:
            statement = statement.where(DatasetFile.id.in_(file_ids))
        statement = statement.order_by(DatasetFile.id)
        if limit is not None:
            statement = statement.limit(limit)
        return list(self.session.execute(statement).scalars())

    def get_ready_file_groups(self, *, branch: str) -> list[dict[str, Any]]:
        """Return READY_FOR_PARSING counts grouped by role and source format."""
        role_order = case(
            *((DatasetFile.role == role, index) for index, role in enumerate(ROLE_VALUES)),
            else_=len(ROLE_VALUES),
        )
        statement = (
            select(
                DatasetFile.role,
                DatasetFile.source_format,
                func.count(DatasetFile.id).label("files_count"),
            )
            .where(
                DatasetFile.status == "READY_FOR_PARSING",
                DatasetFile.branch == branch,
            )
            .group_by(DatasetFile.role, DatasetFile.source_format)
            .order_by(role_order.asc(), DatasetFile.source_format.asc())
        )
        return [
            {
                "role": role,
                "source_format": source_format,
                "files_count": int(files_count),
            }
            for role, source_format, files_count in self.session.execute(statement).all()
        ]

    def mark_file_status(
        self,
        file: DatasetFile,
        status: str,
        *,
        error_message: str | None = None,
    ) -> DatasetFile:
        """Update raw file status without committing."""
        file.status = status
        file.error_message = error_message
        now = datetime.now(timezone.utc)
        file.last_seen_at = now
        file.updated_at = now
        self.session.flush()
        return file

    def get_by_hash(self, file_hash_sha256: str) -> list[DatasetFile]:
        """Return files with the given SHA-256 hash."""
        statement = select(DatasetFile).where(DatasetFile.file_hash_sha256 == file_hash_sha256)
        return list(self.session.execute(statement).scalars())

    def get_by_path(self, dataset_id: int, file_path: str) -> DatasetFile | None:
        """Return one file by dataset and raw file path."""
        statement = select(DatasetFile).where(
            DatasetFile.dataset_id == dataset_id,
            DatasetFile.file_path == file_path,
        )
        return self.session.execute(statement).scalar_one_or_none()
