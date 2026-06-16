"""Batch runners for targeted Stage Two normalization commands."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.orm import Session

from scripts.db.models import DatasetFile, NormalizedArtifact
from scripts.db.models.constants import BRANCH_VALUES, ROLE_VALUES
from scripts.db.repositories import DatasetFileRepository
from scripts.stage_two.normalization.dns_service import DnsNormalizationService
from scripts.stage_two.normalization.host_service import HostNormalizationService
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


ServiceFactory = Callable[[Session], BranchNormalizationService]


class NormalizeFormatRunner:
    """Normalize READY_FOR_PARSING files for one branch/role/source_format."""

    def __init__(
        self,
        session: Session,
        *,
        service_factories: Mapping[str, ServiceFactory] | None = None,
    ) -> None:
        """Initialize the runner with an externally managed transaction."""
        self.session = session
        self.file_repository = DatasetFileRepository(session)
        self.resolver = ParserResolver(session)
        self.service_factories: Mapping[str, ServiceFactory] = service_factories or {
            "dns": DnsNormalizationService,
            "host": HostNormalizationService,
        }

    def normalize_format(self, request: NormalizeFormatRequest) -> NormalizeFormatResult:
        """Normalize only matching READY_FOR_PARSING files."""
        _validate_request(request)
        files = self.file_repository.get_files_ready_for_parsing(
            branch=request.branch,
            role=request.role,
            source_format=request.source_format,
            limit=request.limit,
        )
        resolution = self.resolver.resolve_with_diagnostics(
            branch=request.branch,
            role=request.role,
            source_format=request.source_format,
        )
        parser = resolution.parser
        if parser is None:
            file_results = tuple(self._mark_unsupported(file) for file in files)
            return _build_result(
                request=request,
                status="UNSUPPORTED_FORMAT",
                parser_name=None,
                parser_class=None,
                file_results=file_results,
                diagnostics=_parser_diagnostics(resolution.diagnostics),
            )

        service_factory = self.service_factories.get(request.branch)
        if service_factory is None:
            raise ValueError("normalize-format supports only dns and host branches")

        service = service_factory(self.session)
        file_results = tuple(self._normalize_one(service, file) for file in files)
        return _build_result(
            request=request,
            status="SUCCESS" if not _has_failed_file(file_results) else "PARTIAL_SUCCESS",
            parser_name=parser.parser_name,
            parser_class=parser.parser_class,
            file_results=file_results,
            diagnostics=_parser_diagnostics(resolution.diagnostics),
        )

    def _normalize_one(
        self,
        service: BranchNormalizationService,
        file: DatasetFile,
    ) -> NormalizeFileResult:
        try:
            with self.session.begin_nested():
                artifact = service.normalize_file(file)
                return NormalizeFileResult(
                    file_id=file.id,
                    file_path=file.file_path,
                    status=file.status,
                    artifact_id=getattr(artifact, "id", None),
                    error=file.error_message,
                )
        except Exception as exc:
            return self._mark_failed(file, str(exc))

    def _mark_unsupported(self, file: DatasetFile) -> NormalizeFileResult:
        try:
            with self.session.begin_nested():
                self.file_repository.mark_file_status(file, "UNSUPPORTED_FORMAT")
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
                error=str(exc),
            )

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


def _validate_request(request: NormalizeFormatRequest) -> None:
    if request.branch not in BRANCH_VALUES:
        allowed = ", ".join(BRANCH_VALUES)
        raise ValueError(f"normalize-format branch must be one of: {allowed}")
    if request.branch not in SUPPORTED_NORMALIZATION_BRANCHES:
        allowed = ", ".join(SUPPORTED_NORMALIZATION_BRANCHES)
        raise ValueError(f"normalize-format branch must be one of: {allowed}")
    if request.role not in ROLE_VALUES:
        allowed = ", ".join(ROLE_VALUES)
        raise ValueError(f"normalize-format role must be one of: {allowed}")
    if not request.source_format.strip():
        raise ValueError("normalize-format format must not be empty")
    if request.limit is not None and request.limit < 0:
        raise ValueError("normalize-format limit must be a non-negative integer")


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
    return any(file.status in {"FAILED", "SKIPPED", "UNSUPPORTED_FORMAT"} for file in file_results)


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
