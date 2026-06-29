"""Build Stage Two normalization work units from catalog state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.db.models import DatasetFile, NormalizedArtifact, ParserRun
from scripts.db.models.constants import ACTIVE_CATALOG_SOURCE_GROUP
from scripts.db.repositories import DatasetFileRepository
from scripts.stage_two.execution.work_unit import WorkUnit
from scripts.stage_two.parser_registry import ParserResolver
from scripts.stage_two.parser_registry.seed import ParserClassValidationResult

PACKET_SOURCE_FORMATS: frozenset[str] = frozenset({"cap", "pcap", "pcapng"})


@dataclass(frozen=True)
class WorkUnitPlan:
    """Planner output for one normalization bucket."""

    work_units: tuple[WorkUnit, ...]
    skipped_units: tuple[WorkUnit, ...]
    ready_files: tuple[DatasetFile, ...]
    unsupported_files: tuple[DatasetFile, ...]
    parser_name: str | None
    parser_class: str | None
    diagnostics: tuple[ParserClassValidationResult, ...]


class WorkUnitPlanner:
    """Build safe WorkUnit batches for one role/source_format group."""

    def __init__(
        self,
        session: Session,
        *,
        file_repository: DatasetFileRepository | None = None,
        resolver: ParserResolver | None = None,
    ) -> None:
        self.session = session
        self.file_repository = file_repository or DatasetFileRepository(session)
        self.resolver = resolver or ParserResolver(session)

    def build_format_plan(
        self,
        *,
        branch: str,
        role: str,
        source_format: str,
        limit: int | None,
        file_ids: tuple[int, ...] | None,
        options: Any,
    ) -> WorkUnitPlan:
        """Build work units only for READY_FOR_PARSING files in one exact bucket."""
        file_filters: dict[str, object] = {
            "branch": branch,
            "role": role,
            "source_format": source_format,
            "limit": limit,
        }
        if file_ids is not None:
            file_filters["file_ids"] = file_ids
        else:
            file_filters["source_group"] = ACTIVE_CATALOG_SOURCE_GROUP
        files = self.file_repository.get_files_ready_for_parsing(**file_filters)
        resolution = self.resolver.resolve_with_diagnostics(
            branch=branch,
            role=role,
            source_format=source_format,
        )
        parser = resolution.parser
        if parser is None:
            return WorkUnitPlan(
                work_units=(),
                skipped_units=(),
                ready_files=tuple(files),
                unsupported_files=tuple(files),
                parser_name=None,
                parser_class=None,
                diagnostics=tuple(resolution.diagnostics),
            )

        schema_version = _schema_version_value(parser)
        units: list[WorkUnit] = []
        skipped: list[WorkUnit] = []
        for file in files:
            unit = self._build_work_unit(
                file=file,
                parser_name=str(parser.parser_name),
                parser_version=str(parser.parser_version),
                parser_class=getattr(parser, "parser_class", None),
                schema_version=schema_version,
                engine=options.engine,
                packet_mode=options.packet_mode if source_format.strip().lower() in PACKET_SOURCE_FORMATS else None,
            )
            if options.resume and self._has_successful_artifact(unit):
                skipped.append(unit)
                continue
            units.append(unit)

        return WorkUnitPlan(
            work_units=tuple(units),
            skipped_units=tuple(skipped),
            ready_files=tuple(files),
            unsupported_files=(),
            parser_name=str(parser.parser_name),
            parser_class=getattr(parser, "parser_class", None),
            diagnostics=tuple(resolution.diagnostics),
        )

    def _build_work_unit(
        self,
        *,
        file: DatasetFile,
        parser_name: str,
        parser_version: str,
        parser_class: str | None,
        schema_version: str,
        engine: str,
        packet_mode: str | None,
    ) -> WorkUnit:
        metadata = file.metadata_json or {}
        chunk_id = metadata.get("chunk_id") or metadata.get("part_id")
        if chunk_id is None and metadata.get("parent_file_id") is not None and metadata.get("chunk_index") is not None:
            chunk_id = f"{metadata['parent_file_id']}:{metadata['chunk_index']}"
        return WorkUnit(
            branch=file.branch,
            role=file.role,
            source_format=file.source_format,
            dataset_id=int(file.dataset_id),
            dataset_file_id=int(file.id),
            source_path=file.file_path,
            parser_name=parser_name,
            parser_version=parser_version,
            schema_version=schema_version,
            chunk_id=str(chunk_id) if chunk_id is not None else None,
            estimated_size_bytes=int(file.file_size_bytes or 0),
            engine=engine,  # reserved; current raw normalization workers remain CPU process workers
            packet_mode=packet_mode,
        )

    def _has_successful_artifact(self, unit: WorkUnit) -> bool:
        statement = (
            select(NormalizedArtifact.id)
            .join(ParserRun, NormalizedArtifact.parser_run_id == ParserRun.id)
            .where(
                NormalizedArtifact.file_id == unit.dataset_file_id,
                NormalizedArtifact.status == "SUCCESS",
                NormalizedArtifact.schema_version == unit.schema_version,
                ParserRun.file_id == unit.dataset_file_id,
                ParserRun.parser_name == unit.parser_name,
                ParserRun.parser_version == unit.parser_version,
                ParserRun.status == "SUCCESS",
            )
            .limit(1)
        )
        return self.session.execute(statement).first() is not None


def _schema_version_value(parser: Any) -> str:
    value = getattr(parser, "normalized_schema_version", None)
    if value is not None:
        return str(value)
    return "v1"
