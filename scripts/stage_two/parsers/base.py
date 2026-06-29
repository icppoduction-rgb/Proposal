"""Base parser interfaces for Stage Two normalization."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config import STAGE_TWO_DEFAULT_BATCH_SIZE, STAGE_TWO_MAX_ERROR_SAMPLES
from scripts.stage_two.parsers.common import build_normalized_event


ParsedEvent = dict[str, Any]


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
    """One normalized parser result or one bounded parser batch.

    Streaming parsers should emit ParserResult instances from parse_batches()
    without reading the full raw file into memory. Each batch carries only
    batch-local counters and local error samples. Sequence-capable parsers keep
    stable source row identity on emitted events through event_index and, when
    the source has packet identity, raw_fields_json/metadata_json packet fields.
    Unknown source fields must be retained in raw_fields_json or metadata_json.
    """

    rows_read: int
    rows_parsed: int
    rows_failed: int
    events: list[ParsedEvent]
    warnings: list[str] = field(default_factory=list)
    bytes_read: int | None = None
    files_read: int = 1
    error_samples: list[str] = field(default_factory=list)
    parse_errors_count: int | None = None
    emitted_events_count: int | None = None
    status_override: str | None = None
    status_reason: str | None = None

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
        if self.emitted_events_count is not None and self.emitted_events_count < 0:
            raise ValueError("emitted_events_count must be non-negative when provided")
        object.__setattr__(self, "error_samples", limit_error_samples(self.error_samples))
        if self.parse_errors_count is None:
            object.__setattr__(
                self,
                "parse_errors_count",
                self.rows_failed if self.rows_failed > 0 else len(self.error_samples),
            )
        allowed_status_overrides = {None, "EMPTY_FILE", "FAILED", "SKIPPED", "UNSUPPORTED_FORMAT"}
        if self.status_override not in allowed_status_overrides:
            allowed = ", ".join(sorted(value for value in allowed_status_overrides if value is not None))
            raise ValueError(f"status_override must be one of: {allowed}")

    @property
    def events_emitted(self) -> int:
        """Return the number of normalized events emitted."""
        if self.emitted_events_count is not None:
            return self.emitted_events_count
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
        if self.status_override == "SKIPPED":
            return ParserStatusDecision(
                status="SKIPPED",
                parser_run_status="SKIPPED",
                file_status="SKIPPED",
                reason=self.status_reason or "file was intentionally skipped",
            )
        if self.status_override == "EMPTY_FILE":
            decision = calculate_parser_status(self.counters, empty_file=True)
            return _with_status_reason(decision, self.status_reason)
        if self.status_override == "FAILED":
            decision = calculate_parser_status(self.counters, read_failed=True)
            return _with_status_reason(decision, self.status_reason)
        if self.status_override == "UNSUPPORTED_FORMAT":
            decision = calculate_parser_status(self.counters, unsupported_format=True)
            return _with_status_reason(decision, self.status_reason)
        return calculate_parser_status(self.counters)

    @property
    def parser_run_status(self) -> str:
        """Return the DB-safe parser_runs.status value."""
        return self.status_decision.parser_run_status

    @property
    def file_status(self) -> str:
        """Return the DB-safe dataset_files.status value."""
        return self.status_decision.file_status

    @property
    def local_errors(self) -> tuple[str, ...]:
        """Return batch-local parser errors as an immutable tuple."""
        return tuple(self.error_samples)


def limit_error_samples(
    samples: list[str] | tuple[str, ...],
    *,
    max_samples: int = STAGE_TWO_MAX_ERROR_SAMPLES,
) -> list[str]:
    """Return a bounded copy of parser error samples."""
    if max_samples < 0:
        raise ValueError("max_samples must be non-negative")
    return [str(sample) for sample in samples[:max_samples]]


def collect_parser_batches(batches: Iterator[ParserResult]) -> ParserResult:
    """Materialize parser batches for compatibility with the legacy parse() API."""
    rows_read = 0
    rows_parsed = 0
    rows_failed = 0
    events: list[ParsedEvent] = []
    warnings: list[str] = []
    error_samples: list[str] = []
    bytes_read: int | None = None
    files_read = 0
    status_override: str | None = None
    status_reason: str | None = None

    for batch in batches:
        rows_read += batch.rows_read
        rows_parsed += batch.rows_parsed
        rows_failed += batch.rows_failed
        events.extend(batch.events)
        warnings.extend(batch.warnings)
        error_samples.extend(batch.error_samples)
        files_read = max(files_read, batch.files_read)
        if batch.bytes_read is not None:
            bytes_read = batch.bytes_read
        if batch.status_override is not None:
            status_override = batch.status_override
            status_reason = batch.status_reason

    if events or rows_read > 0 or rows_failed > 0:
        status_override = None
        status_reason = None

    return ParserResult(
        rows_read=rows_read,
        rows_parsed=rows_parsed,
        rows_failed=rows_failed,
        events=events,
        warnings=warnings,
        bytes_read=bytes_read,
        files_read=max(files_read, 1),
        error_samples=error_samples,
        status_override=status_override,
        status_reason=status_reason,
    )


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


def _with_status_reason(
    decision: ParserStatusDecision,
    reason: str | None,
) -> ParserStatusDecision:
    """Return a copy of a status decision with an explicit reason when provided."""
    if not reason:
        return decision
    return ParserStatusDecision(
        status=decision.status,
        parser_run_status=decision.parser_run_status,
        file_status=decision.file_status,
        reason=reason,
    )


class BaseParser(ABC):
    """Abstract base class for Stage Two normalization parsers.

    parse_batches() is the preferred execution contract for large files. It
    must stream from the raw source where the format allows it, keep each
    yielded ParserResult bounded by batch_size, and preserve row/event order via
    event_index or source identifiers in raw_fields_json/metadata_json. parse()
    remains available as a compatibility adapter for existing callers.
    """

    parser_name: str
    parser_version: str = "v1"
    schema_name: str = "normalized_event"
    schema_version: str = "v1"

    @abstractmethod
    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse one raw file and return normalized events."""

    def parse_batches(
        self,
        path: str | Path,
        context: ParserContext,
        *,
        batch_size: int = STAGE_TWO_DEFAULT_BATCH_SIZE,
        **_: Any,
    ) -> Iterator[ParserResult]:
        """Return bounded output batches for parsers without a streaming implementation.

        Format-specific parsers for large line-oriented or streamable binary
        inputs should override this method. The fallback is intentionally
        compatibility-only because it materializes parse() output before
        chunking events.
        """
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        result = self.parse(path, context)
        if not result.events:
            yield result
            return
        for start in range(0, len(result.events), batch_size):
            events = result.events[start : start + batch_size]
            yield ParserResult(
                rows_read=result.rows_read if start == 0 else 0,
                rows_parsed=len(events),
                rows_failed=result.rows_failed if start == 0 else 0,
                events=events,
                warnings=result.warnings if start == 0 else [],
                bytes_read=result.bytes_read,
                files_read=result.files_read if start == 0 else 0,
                error_samples=result.error_samples if start == 0 else [],
                parse_errors_count=result.parse_errors_count if start == 0 else 0,
            )

    def validate_result(self, result: ParserResult) -> None:
        """Validate that emitted events contain required normalized fields."""
        for index, event in enumerate(result.events):
            missing = REQUIRED_NORMALIZED_FIELDS.difference(event)
            if missing:
                missing_fields = ", ".join(sorted(missing))
                raise ValueError(f"event at index {index} is missing required fields: {missing_fields}")

    def base_event(self, context: ParserContext, **values: Any) -> dict[str, Any]:
        """Build common normalized event fields from parser context."""
        return build_normalized_event(
            context,
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            schema_name=self.schema_name,
            schema_version=self.schema_version,
            **values,
        )
