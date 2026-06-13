"""Base parser interfaces for Stage Two normalization."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


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

    @property
    def events_emitted(self) -> int:
        """Return the number of normalized events emitted."""
        return len(self.events)

    @property
    def has_failures(self) -> bool:
        """Return True when at least one input row failed to parse."""
        return self.rows_failed > 0


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
