"""Repository for raw dataset file catalog records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert

from scripts.db.models import Dataset, DatasetFile
from scripts.db.models.constants import ACTIVE_DATASET_ROLE_VALUES
from scripts.db.repositories.base_repository import BaseRepository
from scripts.stage_two.catalog_exclusions import is_excluded_dataset_file


MAX_BULK_UPSERT_ROWS = 1000


class DatasetFileRepository(BaseRepository[DatasetFile]):
    """Data access methods for `dataset_files`."""

    model = DatasetFile

    def bulk_upsert_files(self, rows: list[dict[str, Any]], *, force_status: bool = False) -> int:
        """Bulk upsert raw file rows by `(dataset_id, file_path)` without committing."""
        if not rows:
            return 0

        total = 0
        deduplicated_rows = self._deduplicate_file_rows(rows)
        for chunk in self._chunk_rows(deduplicated_rows, chunk_size=MAX_BULK_UPSERT_ROWS):
            total += self._bulk_upsert_file_chunk(chunk, force_status=force_status)
        return total

    def _bulk_upsert_file_chunk(self, rows: list[dict[str, Any]], *, force_status: bool = False) -> int:
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
            "status": excluded.status if force_status else case((hash_changed, "CHANGED"), else_=table.c.status),
        }
        result = self.session.execute(
            statement.on_conflict_do_update(
                index_elements=[table.c.dataset_id, table.c.file_path],
                set_=update_values,
            )
        )
        self.session.flush()
        return result.rowcount or 0

    @staticmethod
    def _deduplicate_file_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Keep one row per upsert key to avoid duplicate updates inside one INSERT."""
        deduplicated: dict[tuple[int, str], dict[str, Any]] = {}
        for row in rows:
            key = (int(row["dataset_id"]), str(row["file_path"]))
            deduplicated[key] = row
        return list(deduplicated.values())

    @staticmethod
    def _chunk_rows(
        rows: list[dict[str, Any]],
        *,
        chunk_size: int,
    ) -> list[list[dict[str, Any]]]:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer")
        return [rows[index : index + chunk_size] for index in range(0, len(rows), chunk_size)]

    def get_files_ready_for_parsing(
        self,
        *,
        branch: str | None = None,
        role: str | None = None,
        source_format: str | None = None,
        limit: int | None = None,
        file_ids: tuple[int, ...] | None = None,
        source_group: str | None = None,
    ) -> list[DatasetFile]:
        """Return files marked READY_FOR_PARSING."""
        statement = select(DatasetFile).where(DatasetFile.status == "READY_FOR_PARSING")
        if source_group is not None:
            statement = statement.join(Dataset).where(Dataset.source_group == source_group)
        if branch is not None:
            statement = statement.where(DatasetFile.branch == branch)
        if role is not None:
            statement = statement.where(DatasetFile.role == role)
        if source_format is not None:
            statement = statement.where(DatasetFile.source_format == source_format)
        if file_ids is not None:
            statement = statement.where(DatasetFile.id.in_(file_ids))
        if role is None:
            statement = statement.where(DatasetFile.role.in_(ACTIVE_DATASET_ROLE_VALUES))
        statement = statement.order_by(DatasetFile.id)
        files = list(self.session.execute(statement).scalars())
        filtered_files = [file for file in files if not is_excluded_dataset_file(file)]
        return filtered_files[:limit] if limit is not None else filtered_files

    def get_ready_file_groups(
        self,
        *,
        branch: str,
        source_group: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return READY_FOR_PARSING counts grouped by role and source format."""
        role_order = case(
            *(
                (DatasetFile.role == role, index)
                for index, role in enumerate(ACTIVE_DATASET_ROLE_VALUES)
            ),
            else_=len(ACTIVE_DATASET_ROLE_VALUES),
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
                DatasetFile.role.in_(ACTIVE_DATASET_ROLE_VALUES),
            )
            .group_by(DatasetFile.role, DatasetFile.source_format)
            .order_by(role_order.asc(), DatasetFile.source_format.asc())
        )
        if source_group is not None:
            statement = statement.join(Dataset).where(Dataset.source_group == source_group)
        groups = [
            {
                "role": role,
                "source_format": source_format,
                "files_count": int(files_count),
            }
            for role, source_format, files_count in self.session.execute(statement).all()
        ]
        if branch == "host":
            groups = [
                group
                for group in groups
                if not (
                    (group["role"] == "VALIDATION" and group["source_format"] == "wls_day")
                    or (group["role"] == "TEST" and group["source_format"] in {"netflow_day", "wls_day"})
                )
            ]
            ready_wls_day_files = self.get_files_ready_for_parsing(
                branch=branch,
                role="VALIDATION",
                source_format="wls_day",
                source_group=source_group,
            )
            if ready_wls_day_files:
                groups.append(
                    {
                        "role": "VALIDATION",
                        "source_format": "wls_day",
                        "files_count": len(ready_wls_day_files),
                    }
                )
        return groups

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
