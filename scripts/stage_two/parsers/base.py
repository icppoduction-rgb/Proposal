"""Base parser interfaces for Stage Two normalization."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config import STAGE_TWO_MAX_ERROR_SAMPLES


REQUIRED_NORMALIZED_FIELDS: frozenset[str] = frozenset(
    {
        "event_uid",
        "dataset_name",
        "dataset_role",
        "branch",
        "source_format",
        "source_file_path",
        "parser_name",
        "parser_version",
        "schema_name",
        "schema_version",
        "timestamp_type",
        "entity_type",
        "event_type",
        "modality",
        "label_source",
        "label_status",
        "created_at",
    }
)


@dataclass(frozen=True)
class ParserCounters:
    """Parser counters used for consistent status calculation."""

    rows_read: int = 0
    rows_parsed: int = 0
    rows_failed: int = 0
    bytes_read: int | None = None
    files_read: int = 1
    warnings_count: int = 0
    parse_errors_count: int = 0

    def __post_init__(self) -> None:
        """Validate that counters never go below zero."""
        for name, value in (
            ("rows_read", self.rows_read),
            ("rows_parsed", self.rows_parsed),
            ("rows_failed", self.rows_failed),
            ("files_read", self.files_read),
            ("warnings_count", self.warnings_count),
            ("parse_errors_count", self.parse_errors_count),
        ):
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.bytes_read is not None and self.bytes_read < 0:
            raise ValueError("bytes_read must be non-negative when provided")


@dataclass(frozen=True)
class ParserStatusDecision:
    """Status mapping for parser code and DB-backed catalog records."""

    status: str
    parser_run_status: str
    file_status: str
    reason: str


@dataclass(frozen=True)
class ParserContext:
    """Catalog and runtime metadata supplied to a parser."""

    dataset_id: int | None
    file_id: int | None
    dataset_name: str
    dataset_role: str
    branch: str
    source_format: str
    source_file_path: str
    source_file_hash: str | None
    parser_run_id: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParserResult:
    """Normalized parser output and parser-level counters."""

    rows_read: int
    rows_parsed: int
    rows_failed: int
    events: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)
    bytes_read: int | None = None
    files_read: int = 1
    error_samples: list[str] = field(default_factory=list)
    parse_errors_count: int | None = None

    def __post_init__(self) -> None:
        """Keep optional counters and error samples bounded and consistent."""
        counters = (
            ("rows_read", self.rows_read),
            ("rows_parsed", self.rows_parsed),
            ("rows_failed", self.rows_failed),
            ("files_read", self.files_read),
        )
        for name, value in counters:
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.bytes_read is not None and self.bytes_read < 0:
            raise ValueError("bytes_read must be non-negative when provided")
        object.__setattr__(self, "error_samples", limit_error_samples(self.error_samples))
        if self.parse_errors_count is None:
            object.__setattr__(
                self,
                "parse_errors_count",
                self.rows_failed if self.rows_failed > 0 else len(self.error_samples),
            )

    @property
    def events_emitted(self) -> int:
        """Return the number of normalized events emitted."""
        return len(self.events)

    @property
    def has_failures(self) -> bool:
        """Return True when at least one input row failed to parse."""
        return self.rows_failed > 0

    @property
    def warnings_count(self) -> int:
        """Return the number of parser warnings."""
        return len(self.warnings)

    @property
    def counters(self) -> ParserCounters:
        """Return normalized counters for this parser result."""
        return build_parser_counters(
            rows_read=self.rows_read,
            rows_parsed=self.rows_parsed,
            rows_failed=self.rows_failed,
            bytes_read=self.bytes_read,
            files_read=self.files_read,
            warnings_count=self.warnings_count,
            parse_errors_count=self.parse_errors_count or 0,
        )

    @property
    def status_decision(self) -> ParserStatusDecision:
        """Return the default status decision inferred from counters."""
        return calculate_parser_status(self.counters)

    @property
    def parser_run_status(self) -> str:
        """Return the DB-safe parser_runs.status value."""
        return self.status_decision.parser_run_status

    @property
    def file_status(self) -> str:
        """Return the DB-safe dataset_files.status value."""
        return self.status_decision.file_status


def limit_error_samples(
    samples: list[str] | tuple[str, ...],
    *,
    max_samples: int = STAGE_TWO_MAX_ERROR_SAMPLES,
) -> list[str]:
    """Return a bounded copy of parser error samples."""
    if max_samples < 0:
        raise ValueError("max_samples must be non-negative")
    return [str(sample) for sample in samples[:max_samples]]


def build_parser_counters(
    *,
    rows_read: int = 0,
    rows_parsed: int = 0,
    rows_failed: int = 0,
    bytes_read: int | None = None,
    files_read: int = 1,
    warnings_count: int = 0,
    parse_errors_count: int = 0,
) -> ParserCounters:
    """Build validated parser counters from parser-local values."""
    return ParserCounters(
        rows_read=rows_read,
        rows_parsed=rows_parsed,
        rows_failed=rows_failed,
        bytes_read=bytes_read,
        files_read=files_read,
        warnings_count=warnings_count,
        parse_errors_count=parse_errors_count,
    )


def calculate_parser_status(
    counters: ParserCounters,
    *,
    read_failed: bool = False,
    skipped: bool = False,
    unsupported_format: bool = False,
    empty_file: bool | None = None,
) -> ParserStatusDecision:
    """Calculate canonical parser status plus DB-safe status mappings."""
    if unsupported_format:
        return ParserStatusDecision(
            status="UNSUPPORTED_FORMAT",
            parser_run_status="SKIPPED",
            file_status="UNSUPPORTED_FORMAT",
            reason="no active parser is available for the file source_format",
        )
    if skipped:
        return ParserStatusDecision(
            status="SKIPPED",
            parser_run_status="SKIPPED",
            file_status="SKIPPED",
            reason="file was intentionally skipped",
        )
    if read_failed:
        return ParserStatusDecision(
            status="FAILED",
            parser_run_status="FAILED",
            file_status="FAILED",
            reason="parser could not read the input file",
        )

    inferred_empty = (
        counters.rows_read == 0
        and counters.rows_parsed == 0
        and counters.rows_failed == 0
        and (counters.bytes_read == 0 if counters.bytes_read is not None else True)
    )
    is_empty_file = empty_file if empty_file is not None else inferred_empty
    if is_empty_file:
        return ParserStatusDecision(
            status="EMPTY_FILE",
            parser_run_status="SKIPPED",
            file_status="EMPTY_FILE",
            reason="input file has no readable content",
        )
    if counters.rows_parsed > 0 and counters.rows_failed == 0:
        return ParserStatusDecision(
            status="SUCCESS",
            parser_run_status="SUCCESS",
            file_status="PARSED",
            reason="all readable rows parsed successfully",
        )
    if counters.rows_parsed > 0 and counters.rows_failed > 0:
        return ParserStatusDecision(
            status="PARTIAL_SUCCESS",
            parser_run_status="PARTIAL_SUCCESS",
            file_status="PARTIALLY_PARSED",
            reason="some rows parsed and some rows failed",
        )
    return ParserStatusDecision(
        status="FAILED",
        parser_run_status="FAILED",
        file_status="FAILED",
        reason="no rows were parsed successfully",
    )


class BaseParser(ABC):
    """Abstract base class for Stage Two normalization parsers."""

    parser_name: str
    parser_version: str = "v1"
    schema_name: str = "normalized_event"
    schema_version: str = "v1"

    @abstractmethod
    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse one raw file and return normalized events."""

    def validate_result(self, result: ParserResult) -> None:
        """Validate that emitted events contain required normalized fields."""
        for index, event in enumerate(result.events):
            missing = REQUIRED_NORMALIZED_FIELDS.difference(event)
            if missing:
                missing_fields = ", ".join(sorted(missing))
                raise ValueError(f"event at index {index} is missing required fields: {missing_fields}")

    def base_event(self, context: ParserContext, **values: Any) -> dict[str, Any]:
        """Build common normalized event fields from parser context."""
        event = {
            "dataset_id": context.dataset_id,
            "file_id": context.file_id,
            "dataset_name": context.dataset_name,
            "dataset_role": context.dataset_role,
            "branch": context.branch,
            "source_format": context.source_format,
            "source_file_path": context.source_file_path,
            "source_file_hash": context.source_file_hash,
            "parser_name": self.parser_name,
            "parser_version": self.parser_version,
            "parser_run_id": context.parser_run_id,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "label_binary": None,
            "label_family": None,
            "label_subtype": None,
            "label_source": "none",
            "label_status": "unlabeled",
            "label_confidence": None,
            "label_mapping_rule_id": None,
            "features_json": None,
            "raw_fields_json": None,
            "metadata_json": None,
        }
        event.update(values)
        return event
