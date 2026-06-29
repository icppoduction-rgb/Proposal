"""Batch runners for targeted Stage Two normalization commands."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
import inspect
from typing import Any, Protocol

from sqlalchemy.orm import Session

from config import (
    STAGE_TWO_DEFAULT_BATCH_SIZE,
    STAGE_TWO_DEFAULT_WORKERS,
    STAGE_TWO_HASH_OUTPUT_ARTIFACTS,
    STAGE_TWO_MAX_OUTPUT_PART_ROWS,
    STAGE_TWO_PACKET_BATCH_SIZE,
    STAGE_TWO_PACKET_PARSE_MODE,
)
from scripts.db.models import DatasetFile, NormalizedArtifact
from scripts.db.models.constants import (
    ACTIVE_CATALOG_SOURCE_GROUP,
    ACTIVE_DATASET_ROLE_VALUES,
    BRANCH_VALUES,
)
from scripts.db.repositories import DatasetFileRepository
from scripts.stage_two.execution import (
    ExecutionRuntimeSettings,
    ProgressReporter,
    RetryPolicy,
    WorkUnit,
    WorkUnitExecutor,
    WorkUnitPlanner,
    WorkUnitResult,
)
from scripts.stage_two.normalization.dns_service import DnsNormalizationService
from scripts.stage_two.normalization.host_service import HostNormalizationService
from scripts.stage_two.normalization.options import NormalizationOptions
from scripts.stage_two.parser_registry import ParserResolver
from scripts.stage_two.parser_registry.seed import ParserClassValidationResult


SUPPORTED_NORMALIZATION_BRANCHES: tuple[str, ...] = ("dns", "host")


class BranchNormalizationService(Protocol):
    """Normalization service protocol shared by DNS and Host services."""

    def normalize_file(self, dataset_file: DatasetFile) -> NormalizedArtifact | None:
        """Normalize one file and update parser/file catalog records."""


@dataclass(frozen=True)
class NormalizeFormatRequest:
    """Filters for a targeted normalization batch."""

    branch: str
    role: str
    source_format: str
    limit: int | None = None
    file_ids: tuple[int, ...] | None = None
    workers: int = STAGE_TWO_DEFAULT_WORKERS
    batch_size: int = STAGE_TWO_DEFAULT_BATCH_SIZE
    max_output_part_rows: int = STAGE_TWO_MAX_OUTPUT_PART_ROWS
    packet_batch_size: int = STAGE_TWO_PACKET_BATCH_SIZE
    resume: bool = False
    packet_mode: str = STAGE_TWO_PACKET_PARSE_MODE
    sample_size: int | None = None
    hash_outputs: bool = STAGE_TWO_HASH_OUTPUT_ARTIFACTS
    resource_profile: str | None = None
    engine: str = "cpu"
    format_policy: str | None = field(default=None, compare=False)
    format_policy_warnings: tuple[str, ...] = field(default_factory=tuple, compare=False)
    runtime_facts: dict[str, Any] | None = field(default=None, compare=False)
    explicit_runtime_overrides: tuple[str, ...] = field(default_factory=tuple, compare=False)


@dataclass(frozen=True)
class NormalizeAllRequest:
    """Filters for branch-wide normalization without role/source format mixing."""

    branch: str
    limit: int | None = None
    workers: int = STAGE_TWO_DEFAULT_WORKERS
    batch_size: int = STAGE_TWO_DEFAULT_BATCH_SIZE
    max_output_part_rows: int = STAGE_TWO_MAX_OUTPUT_PART_ROWS
    packet_batch_size: int = STAGE_TWO_PACKET_BATCH_SIZE
    resume: bool = False
    packet_mode: str = STAGE_TWO_PACKET_PARSE_MODE
    sample_size: int | None = None
    hash_outputs: bool = STAGE_TWO_HASH_OUTPUT_ARTIFACTS
    resource_profile: str | None = None
    engine: str = "cpu"


@dataclass(frozen=True)
class NormalizeFileResult:
    """Per-file normalization outcome."""

    file_id: int | None
    file_path: str
    status: str
    artifact_id: int | None = None
    error: str | None = None


@dataclass(frozen=True)
class NormalizeParserDiagnostic:
    """Parser availability diagnostic exposed in normalize-format reports."""

    parser_module: str | None
    parser_class: str | None
    available: bool
    error: str | None = None


@dataclass(frozen=True)
class NormalizeFormatResult:
    """Count report for a targeted normalization batch."""

    status: str
    branch: str
    role: str
    source_format: str
    limit: int | None
    selected: int
    processed: int
    normalized: int
    parsed: int
    partially_parsed: int
    failed: int
    skipped: int
    unsupported: int
    errors: int
    parser_name: str | None
    parser_class: str | None
    files: tuple[NormalizeFileResult, ...]
    diagnostics: tuple[NormalizeParserDiagnostic, ...] = ()


@dataclass(frozen=True)
class NormalizeAllGroupResult:
    """Per role/source_format group summary for normalize-all."""

    role: str
    source_format: str
    limit: int | None
    selected: int
    processed: int
    normalized: int
    parsed: int
    partially_parsed: int
    failed: int
    skipped: int
    unsupported: int
    errors: int
    status: str
    parser_name: str | None
    parser_class: str | None


@dataclass(frozen=True)
class NormalizeAllResult:
    """Branch-wide normalization summary grouped by role/source_format."""

    status: str
    branch: str
    limit: int | None
    groups_count: int
    selected: int
    processed: int
    normalized: int
    parsed: int
    partially_parsed: int
    failed: int
    skipped: int
    unsupported: int
    errors: int
    groups: tuple[NormalizeAllGroupResult, ...]


ServiceFactory = Callable[..., BranchNormalizationService]
ProgressCallback = Callable[[str, dict[str, Any]], None]


class NormalizeFormatRunner:
    """Normalize READY_FOR_PARSING files for one branch/role/source_format."""

    def __init__(
        self,
        session: Session,
        *,
        service_factories: Mapping[str, ServiceFactory] | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Initialize the runner with an externally managed transaction."""
        self.session = session
        self.file_repository = DatasetFileRepository(session)
        self.resolver = ParserResolver(session)
        self.progress_callback = progress_callback
        self.service_factories: Mapping[str, ServiceFactory] = service_factories or {
            "dns": DnsNormalizationService,
            "host": HostNormalizationService,
        }
        self.executor = WorkUnitExecutor(progress=ProgressReporter(progress_callback))

    def normalize_format(self, request: NormalizeFormatRequest) -> NormalizeFormatResult:
        """Normalize only matching READY_FOR_PARSING files."""
        _validate_request(request)
        options = _options_from_request(request)
        planner = WorkUnitPlanner(
            self.session,
            file_repository=self.file_repository,
            resolver=self.resolver,
        )
        plan = planner.build_format_plan(
            branch=request.branch,
            role=request.role,
            source_format=request.source_format,
            limit=request.limit,
            file_ids=request.file_ids,
            options=options,
        )
        total = len(plan.work_units) + len(plan.skipped_units) + len(plan.unsupported_files)
        self._emit(
            "batch_started",
            branch=request.branch,
            role=request.role,
            source_format=request.source_format,
            total=total,
        )
        if plan.parser_name is None:
            file_results = tuple(
                self._mark_unsupported(file, index=index, total=total)
                for index, file in enumerate(plan.unsupported_files, start=1)
            )
            return _build_result(
                request=request,
                status="UNSUPPORTED_FORMAT",
                parser_name=None,
                parser_class=None,
                file_results=file_results,
                diagnostics=_parser_diagnostics(plan.diagnostics),
            )

        service_factory = self.service_factories.get(request.branch)
        if service_factory is None:
            raise ValueError("normalize-format supports only dns and host branches")

        skipped_results = tuple(
            self._skipped_work_unit_result(unit, index=index, total=total)
            for index, unit in enumerate(plan.skipped_units, start=1)
        )
        start_index = len(skipped_results)
        if request.workers > 1:
            runtime_settings = ExecutionRuntimeSettings.from_options(
                options,
                selected_units=len(plan.work_units),
            )
            work_unit_results = self.executor.execute(
                plan.work_units,
                options=options,
                runtime_settings=runtime_settings,
                retry_policy=RetryPolicy(),
            )
        else:
            service = _create_service(service_factory, self.session, options=options)
            files_by_id = {int(file.id): file for file in plan.ready_files}
            work_unit_results = tuple(
                self._normalize_one_work_unit(
                    service,
                    unit,
                    files_by_id,
                    index=start_index + index,
                    total=total,
                )
                for index, unit in enumerate(plan.work_units, start=1)
            )
        file_results = tuple(_work_unit_to_file_result(result) for result in (*skipped_results, *work_unit_results))
        return _build_result(
            request=request,
            status="SUCCESS" if not _has_failed_file(file_results) else "PARTIAL_SUCCESS",
            parser_name=plan.parser_name,
            parser_class=plan.parser_class,
            file_results=file_results,
            diagnostics=_parser_diagnostics(plan.diagnostics),
        )

    def _normalize_one(
        self,
        service: BranchNormalizationService,
        file: DatasetFile,
        *,
        index: int,
        total: int,
    ) -> NormalizeFileResult:
        try:
            with self.session.begin_nested():
                artifact = service.normalize_file(file)
                result = NormalizeFileResult(
                    file_id=file.id,
                    file_path=file.file_path,
                    status=file.status,
                    artifact_id=getattr(artifact, "id", None),
                    error=file.error_message,
                )
                self._emit_file_processed(result, index=index, total=total)
                return result
        except Exception as exc:
            result = self._mark_failed(file, _exception_message(exc))
            self._emit_file_processed(result, index=index, total=total)
            return result

    def _normalize_one_work_unit(
        self,
        service: BranchNormalizationService,
        unit: WorkUnit,
        files_by_id: dict[int, DatasetFile],
        *,
        index: int,
        total: int,
    ) -> WorkUnitResult:
        file = files_by_id.get(unit.dataset_file_id)
        if file is None:
            result = WorkUnitResult(
                work_unit=unit,
                status="FAILED",
                error="dataset file not found",
            )
            self._emit_file_processed(_work_unit_to_file_result(result), index=index, total=total)
            return result
        file_result = self._normalize_one(service, file, index=index, total=total)
        return WorkUnitResult(
            work_unit=unit,
            status=file_result.status,
            artifact_id=file_result.artifact_id,
            error=file_result.error,
            error_samples=(file_result.error,) if file_result.error else (),
        )

    def _skipped_work_unit_result(self, unit: WorkUnit, *, index: int, total: int) -> WorkUnitResult:
        result = WorkUnitResult(
            work_unit=unit,
            status="SKIPPED",
            error="resume skipped: successful normalized artifact already exists",
        )
        self._emit_file_processed(_work_unit_to_file_result(result), index=index, total=total)
        return result

    def _mark_unsupported(self, file: DatasetFile, *, index: int, total: int) -> NormalizeFileResult:
        try:
            with self.session.begin_nested():
                self.file_repository.mark_file_status(file, "UNSUPPORTED_FORMAT")
                result = NormalizeFileResult(
                    file_id=file.id,
                    file_path=file.file_path,
                    status=file.status,
                    error=file.error_message,
                )
                self._emit_file_processed(result, index=index, total=total)
                return result
        except Exception as exc:
            result = NormalizeFileResult(
                file_id=getattr(file, "id", None),
                file_path=getattr(file, "file_path", ""),
                status="FAILED",
                error=str(exc),
            )
            self._emit_file_processed(result, index=index, total=total)
            return result

    def _mark_failed(self, file: DatasetFile, error_message: str) -> NormalizeFileResult:
        try:
            with self.session.begin_nested():
                self.file_repository.mark_file_status(file, "FAILED", error_message=error_message)
                return NormalizeFileResult(
                    file_id=file.id,
                    file_path=file.file_path,
                    status=file.status,
                    error=file.error_message,
                )
        except Exception as exc:
            return NormalizeFileResult(
                file_id=getattr(file, "id", None),
                file_path=getattr(file, "file_path", ""),
                status="FAILED",
                error=f"{error_message}; failed to mark status: {exc}",
            )

    def _emit_file_processed(
        self,
        result: NormalizeFileResult,
        *,
        index: int,
        total: int,
    ) -> None:
        self._emit(
            "file_processed",
            current=index,
            total=total,
            file_id=result.file_id,
            file_path=result.file_path,
            status=result.status,
            artifact_id=result.artifact_id,
            error=result.error,
        )

    def _emit(self, event: str, **payload: Any) -> None:
        if self.progress_callback is not None:
            self.progress_callback(event, payload)


def _validate_request(request: NormalizeFormatRequest) -> None:
    if request.branch not in BRANCH_VALUES:
        allowed = ", ".join(BRANCH_VALUES)
        raise ValueError(f"normalize-format branch must be one of: {allowed}")
    if request.branch not in SUPPORTED_NORMALIZATION_BRANCHES:
        allowed = ", ".join(SUPPORTED_NORMALIZATION_BRANCHES)
        raise ValueError(f"normalize-format branch must be one of: {allowed}")
    if request.role not in ACTIVE_DATASET_ROLE_VALUES:
        allowed = ", ".join(ACTIVE_DATASET_ROLE_VALUES)
        raise ValueError(f"normalize-format role must be one of: {allowed}")
    if not request.source_format.strip():
        raise ValueError("normalize-format format must not be empty")
    if request.limit is not None and request.limit < 0:
        raise ValueError("normalize-format limit must be a non-negative integer")
    _options_from_request(request)


def _options_from_request(request: NormalizeFormatRequest | NormalizeAllRequest) -> NormalizationOptions:
    return NormalizationOptions(
        workers=request.workers,
        batch_size=request.batch_size,
        max_output_part_rows=request.max_output_part_rows,
        packet_batch_size=request.packet_batch_size,
        resume=request.resume,
        packet_mode=request.packet_mode,
        sample_size=request.sample_size,
        hash_outputs=request.hash_outputs,
        resource_profile=request.resource_profile,
        engine=request.engine,
    )


def _create_service(
    factory: ServiceFactory,
    session: Session,
    *,
    options: NormalizationOptions,
) -> BranchNormalizationService:
    parameters = inspect.signature(factory).parameters
    if "options" in parameters:
        return factory(session, options=options)
    return factory(session)


def _build_result(
    *,
    request: NormalizeFormatRequest,
    status: str,
    parser_name: str | None,
    parser_class: str | None,
    file_results: tuple[NormalizeFileResult, ...],
    diagnostics: tuple[NormalizeParserDiagnostic, ...],
) -> NormalizeFormatResult:
    parsed = sum(1 for file in file_results if file.status == "PARSED")
    partially_parsed = sum(1 for file in file_results if file.status == "PARTIALLY_PARSED")
    failed = sum(1 for file in file_results if file.status == "FAILED")
    skipped = sum(1 for file in file_results if file.status == "SKIPPED")
    unsupported = sum(1 for file in file_results if file.status == "UNSUPPORTED_FORMAT")
    errors = sum(1 for file in file_results if file.error)
    return NormalizeFormatResult(
        status=status,
        branch=request.branch,
        role=request.role,
        source_format=request.source_format,
        limit=request.limit,
        selected=len(file_results),
        processed=len(file_results),
        normalized=parsed + partially_parsed,
        parsed=parsed,
        partially_parsed=partially_parsed,
        failed=failed,
        skipped=skipped,
        unsupported=unsupported,
        errors=errors,
        parser_name=parser_name,
        parser_class=parser_class,
        files=file_results,
        diagnostics=diagnostics,
    )


def _has_failed_file(file_results: tuple[NormalizeFileResult, ...]) -> bool:
    return any(file.status in {"FAILED", "UNSUPPORTED_FORMAT"} for file in file_results)


def _work_unit_to_file_result(result: WorkUnitResult) -> NormalizeFileResult:
    return NormalizeFileResult(
        file_id=result.work_unit.dataset_file_id,
        file_path=result.work_unit.source_path,
        status=result.status,
        artifact_id=result.artifact_id,
        error=result.error,
    )


def _parser_diagnostics(
    diagnostics: tuple[ParserClassValidationResult, ...],
) -> tuple[NormalizeParserDiagnostic, ...]:
    return tuple(
        NormalizeParserDiagnostic(
            parser_module=diagnostic.parser_module,
            parser_class=diagnostic.parser_class,
            available=diagnostic.available,
            error=diagnostic.error,
        )
        for diagnostic in diagnostics
    )


class NormalizeAllRunner:
    """Run branch-wide normalization as ordered role/source_format batches."""

    def __init__(
        self,
        session: Session,
        *,
        service_factories: Mapping[str, ServiceFactory] | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        """Initialize the runner with an externally managed transaction."""
        self.session = session
        self.file_repository = DatasetFileRepository(session)
        self.progress_callback = progress_callback
        self.format_runner = NormalizeFormatRunner(
            session,
            service_factories=service_factories,
            progress_callback=progress_callback,
        )
        self.format_runner.file_repository = self.file_repository

    def normalize_all(self, request: NormalizeAllRequest) -> NormalizeAllResult:
        """Normalize READY_FOR_PARSING files for one branch by role/source_format."""
        _validate_all_request(request)
        _options_from_request(request)
        if request.limit == 0:
            return _build_all_result(request=request, groups=())

        remaining = request.limit
        group_results: list[NormalizeAllGroupResult] = []
        for group in self.file_repository.get_ready_file_groups(
            branch=request.branch,
            source_group=ACTIVE_CATALOG_SOURCE_GROUP,
        ):
            if remaining is not None and remaining <= 0:
                break
            group_limit = min(group["files_count"], remaining) if remaining is not None else None
            format_request = NormalizeFormatRequest(
                branch=request.branch,
                role=group["role"],
                source_format=group["source_format"],
                limit=group_limit,
                workers=request.workers,
                batch_size=request.batch_size,
                max_output_part_rows=request.max_output_part_rows,
                packet_batch_size=request.packet_batch_size,
                resume=request.resume,
                packet_mode=request.packet_mode,
                sample_size=request.sample_size,
                hash_outputs=request.hash_outputs,
                resource_profile=request.resource_profile,
                engine=request.engine,
            )
            self._emit(
                "group_started",
                branch=request.branch,
                role=group["role"],
                source_format=group["source_format"],
                files_count=group["files_count"],
                group_limit=group_limit,
            )
            format_result = self.format_runner.normalize_format(format_request)
            group_result = _format_to_group_result(format_result)
            group_results.append(group_result)
            self._emit(
                "group_finished",
                branch=request.branch,
                role=group_result.role,
                source_format=group_result.source_format,
                selected=group_result.selected,
                parsed=group_result.parsed,
                partially_parsed=group_result.partially_parsed,
                failed=group_result.failed,
                skipped=group_result.skipped,
            )
            if remaining is not None:
                remaining -= group_result.selected
        return _build_all_result(request=request, groups=tuple(group_results))

    def _emit(self, event: str, **payload: Any) -> None:
        if self.progress_callback is not None:
            self.progress_callback(event, payload)


def _validate_all_request(request: NormalizeAllRequest) -> None:
    if request.branch not in BRANCH_VALUES:
        allowed = ", ".join(BRANCH_VALUES)
        raise ValueError(f"normalize-all branch must be one of: {allowed}")
    if request.branch not in SUPPORTED_NORMALIZATION_BRANCHES:
        allowed = ", ".join(SUPPORTED_NORMALIZATION_BRANCHES)
        raise ValueError(f"normalize-all branch must be one of: {allowed}")
    if request.limit is not None and request.limit < 0:
        raise ValueError("normalize-all limit must be a non-negative integer")
    _options_from_request(request)


def _format_to_group_result(format_result: NormalizeFormatResult) -> NormalizeAllGroupResult:
    return NormalizeAllGroupResult(
        role=format_result.role,
        source_format=format_result.source_format,
        limit=format_result.limit,
        selected=format_result.selected,
        processed=format_result.processed,
        normalized=format_result.normalized,
        parsed=format_result.parsed,
        partially_parsed=format_result.partially_parsed,
        failed=format_result.failed,
        skipped=format_result.skipped,
        unsupported=format_result.unsupported,
        errors=format_result.errors,
        status=format_result.status,
        parser_name=format_result.parser_name,
        parser_class=format_result.parser_class,
    )


def _build_all_result(
    *,
    request: NormalizeAllRequest,
    groups: tuple[NormalizeAllGroupResult, ...],
) -> NormalizeAllResult:
    failed = sum(group.failed for group in groups)
    skipped = sum(group.skipped for group in groups)
    unsupported = sum(group.unsupported for group in groups)
    errors = sum(group.errors for group in groups)
    status = "SUCCESS"
    if any(group.status == "UNSUPPORTED_FORMAT" for group in groups):
        status = "PARTIAL_SUCCESS"
    if failed or skipped or unsupported or errors:
        status = "PARTIAL_SUCCESS"
    return NormalizeAllResult(
        status=status,
        branch=request.branch,
        limit=request.limit,
        groups_count=len(groups),
        selected=sum(group.selected for group in groups),
        processed=sum(group.processed for group in groups),
        normalized=sum(group.normalized for group in groups),
        parsed=sum(group.parsed for group in groups),
        partially_parsed=sum(group.partially_parsed for group in groups),
        failed=failed,
        skipped=skipped,
        unsupported=unsupported,
        errors=errors,
        groups=groups,
    )


def _exception_message(exc: BaseException) -> str:
    message = str(exc).strip()
    return message or type(exc).__name__
