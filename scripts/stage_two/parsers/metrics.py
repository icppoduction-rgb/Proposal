"""Host Metricbeat-like system metrics parser."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import STAGE_TWO_DEFAULT_BATCH_SIZE
from scripts.stage_two.labels import LabelResolver, LabelResolverProtocol
from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult, collect_parser_batches
from scripts.stage_two.parsers.common import merge_json_objects
from scripts.stage_two.parsers.input_reader import UniversalInputReader
from scripts.stage_two.parsers.json_utils import compact_json_row, flatten_json_object


HOST_METRIC_SOURCE_FORMATS: frozenset[str] = frozenset(
    {
        "cpu.log",
        "diskio.log",
        "filesystem.log",
        "fsstat.log",
        "load.log",
        "memory.log",
        "network.log",
        "process.log",
        "process.summary.log",
        "service.log",
        "socket.summary.log",
        "uptime.log",
    }
)

FORMAT_DATASETS: dict[str, str] = {
    "cpu.log": "system.cpu",
    "diskio.log": "system.diskio",
    "filesystem.log": "system.filesystem",
    "fsstat.log": "system.fsstat",
    "load.log": "system.load",
    "memory.log": "system.memory",
    "network.log": "system.network",
    "process.log": "system.process",
    "process.summary.log": "system.process.summary",
    "service.log": "system.service",
    "socket.summary.log": "system.socket.summary",
    "uptime.log": "system.uptime",
}

FORMAT_METRIC_PREFIXES: dict[str, tuple[str, ...]] = {
    "cpu.log": ("system.cpu.",),
    "diskio.log": ("system.diskio.",),
    "filesystem.log": ("system.filesystem.",),
    "fsstat.log": ("system.fsstat.",),
    "load.log": ("system.load.",),
    "memory.log": ("system.memory.",),
    "network.log": ("system.network.",),
    "process.log": ("process.cpu.", "process.memory.", "process.fd.", "process.threads.", "system.process."),
    "process.summary.log": ("system.process.summary.",),
    "service.log": ("system.service.",),
    "socket.summary.log": ("system.socket.summary.",),
    "uptime.log": ("system.uptime.",),
}

GENERIC_METRIC_PREFIXES: tuple[str, ...] = (
    "system.cpu.",
    "system.diskio.",
    "system.filesystem.",
    "system.fsstat.",
    "system.load.",
    "system.memory.",
    "system.network.",
    "system.process.",
    "system.service.",
    "system.socket.",
    "system.uptime.",
    "process.cpu.",
    "process.memory.",
    "process.fd.",
    "process.threads.",
)
NON_METRIC_EXACT_KEYS: frozenset[str] = frozenset(
    {
        "process.pid",
        "process.ppid",
        "process.parent.pid",
        "system.process.pid",
        "system.process.ppid",
        "system.process.cgroup.id",
        "system.network.name",
        "system.diskio.name",
        "system.filesystem.device_name",
        "system.filesystem.mount_point",
        "system.service.name",
        "system.service.state",
    }
)
NON_METRIC_SUFFIXES: tuple[str, ...] = (
    ".id",
    ".ids",
    ".pid",
    ".ppid",
    ".uid",
    ".gid",
    ".name",
    ".state",
    ".status",
    ".type",
    ".path",
    ".mount_point",
    ".device_name",
    ".serial_number",
)
ANNOTATION_KEYS: frozenset[str] = frozenset(
    {
        "annotation",
        "annotations",
        "comment",
        "description",
        "ground_truth",
        "label",
        "labels",
        "label_binary",
        "target",
    }
)
TEST_LABEL_FIELDS: frozenset[str] = frozenset(
    {
        "label_binary",
        "label",
        "labels",
        "target",
        "class",
        "is_attack",
        "is_malicious",
        "malicious",
        "attack",
        "attack_cat",
        "attack_category",
        "attack_subcat",
        "alert",
        "is_executing_exploit",
        "exploit",
    }
)
TIMESTAMP_FIELDS: tuple[str, ...] = (
    "@timestamp",
    "timestamp",
    "event.timestamp",
    "event.created",
    "event.ingested",
)


@dataclass(frozen=True)
class MetricPoint:
    """One normalized metric value extracted from a Metricbeat JSON row."""

    name: str
    value: float | None
    source_key: str | None
    metadata: dict[str, Any]


class HostMetricbeatParser(BaseParser):
    """Parser for Metricbeat-like Host system metrics JSON-lines."""

    parser_name = "host_metricbeat_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or LabelResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse Metricbeat-like JSON-lines into normalized host metric events."""
        return collect_parser_batches(self.parse_batches(path, context))

    def parse_batches(
        self,
        path: str | Path,
        context: ParserContext,
        *,
        batch_size: int = STAGE_TWO_DEFAULT_BATCH_SIZE,
        **_: Any,
    ) -> Iterator[ParserResult]:
        """Parse Metricbeat-like JSON-lines as bounded batches."""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        events: list[dict[str, Any]] = []
        rows_read = 0
        rows_failed = 0
        annotation_rows = 0
        error_samples: list[str] = []
        reader = UniversalInputReader(path)

        with reader.iter_lines(keepends=False, skip_empty=False) as lines:
            for line_index, line in enumerate(lines):
                if not line.strip():
                    continue
                rows_read += 1
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    rows_failed += 1
                    error_samples.append(f"json line {line_index + 1}: {exc.msg}")
                    continue
                if not isinstance(record, dict):
                    rows_failed += 1
                    error_samples.append(f"json line {line_index + 1}: expected JSON object")
                    continue

                row = flatten_json_object(record)
                row["_json_source_type"] = "metric_json_line"
                row["_json_record_index"] = line_index

                if _is_annotation_row(row):
                    annotation_rows += 1
                    continue

                try:
                    points = _metric_points(row, context)
                    if not points:
                        if _has_metric_signal(row, context):
                            points = [_missing_metric_point(row, context)]
                        else:
                            annotation_rows += 1
                            continue
                    for point_index, point in enumerate(points):
                        events.append(
                            _metric_event_from_point(
                                self,
                                row,
                                context,
                                line_index=line_index,
                                point_index=point_index,
                                point=point,
                            )
                        )
                except Exception as exc:
                    rows_failed += 1
                    error_samples.append(_error_sample(row, exc))
                if len(events) >= batch_size:
                    result = ParserResult(
                        rows_read=rows_read,
                        rows_parsed=len(events),
                        rows_failed=rows_failed,
                        events=events,
                        error_samples=error_samples,
                    )
                    self.validate_result(result)
                    yield result
                    events = []
                    rows_read = 0
                    rows_failed = 0
                    error_samples = []

        reader_metadata = reader.metadata_snapshot()
        warnings = [
            *reader_metadata.warnings,
            *(f"reader error: {error}" for error in reader_metadata.errors),
        ]
        if reader_metadata.base64_detected:
            warnings.append("base64_detected=True")
        if annotation_rows:
            warnings.append(f"annotation_rows_skipped={annotation_rows}")

        result = ParserResult(
            rows_read=rows_read,
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            warnings=warnings,
            bytes_read=reader_metadata.bytes_read,
            error_samples=error_samples,
        )
        self.validate_result(result)
        yield result


def _metric_event_from_point(
    parser: BaseParser,
    row: dict[str, Any],
    context: ParserContext,
    *,
    line_index: int,
    point_index: int,
    point: MetricPoint,
) -> dict[str, Any]:
    timestamp_source, timestamp = _timestamp_from_metric_row(row)
    event_dataset = _event_dataset(row, context)
    host_name = _pick(row, "host.name", "host.hostname", "agent.hostname", "beat.hostname", "hostname")
    process_name = _pick(row, "process.name", "system.process.name")
    process_id = _string_or_none(_pick(row, "process.pid", "system.process.pid"))
    service_name = _pick(row, "service.name", "system.service.name")
    service_state = _pick(row, "service.state", "system.service.state")
    network_interface = _pick(row, "system.network.name", "network.interface.name")
    disk_name = _pick(row, "system.diskio.name", "system.diskio.device_name")
    filesystem_mount = _pick(row, "system.filesystem.mount_point")
    entity_id = (
        process_name
        or service_name
        or network_interface
        or disk_name
        or filesystem_mount
        or host_name
        or point.name
    )
    label_fields = _resolve_metric_labels(parser, row, context)

    return parser.base_event(
        context,
        event_uid=_event_uid(context, line_index, point_index, point.name),
        timestamp=timestamp,
        timestamp_source=timestamp_source if timestamp else None,
        timestamp_type="absolute" if timestamp else "event_order",
        event_index=line_index,
        entity_type="metric",
        entity_id=entity_id,
        event_type="host_metric",
        raw_event_name=event_dataset or point.name,
        modality="host_metric",
        host_name=host_name,
        event_dataset=event_dataset,
        metric_name=point.name,
        metric_value=point.value,
        process_id=process_id,
        process_name=process_name,
        service_name=service_name,
        service_state=service_state,
        network_interface=network_interface,
        raw_fields_json=compact_json_row(row),
        metadata_json=_metric_metadata(
            row,
            context,
            point,
            point_index=point_index,
            event_dataset=event_dataset,
            network_interface=network_interface,
            disk_name=disk_name,
            filesystem_mount=filesystem_mount,
        ),
        created_at=datetime.now(timezone.utc),
        **label_fields,
    )


def _metric_points(row: dict[str, Any], context: ParserContext) -> list[MetricPoint]:
    explicit_name = _pick(row, "metric_name", "metric.name")
    explicit_value = _float_or_none(_pick(row, "metric_value", "metric.value"))
    if explicit_name not in ("", None):
        return [
            MetricPoint(
                name=str(explicit_name),
                value=explicit_value,
                source_key="metric_value" if "metric_value" in row else "metric.value",
                metadata={"metric_unit": _metric_unit(str(explicit_name))},
            )
        ]

    prefixes = FORMAT_METRIC_PREFIXES.get(context.source_format, ())
    points: list[MetricPoint] = []
    for key in sorted(row):
        value = row[key]
        metric_value = _float_or_none(value)
        if metric_value is None:
            continue
        if not _is_metric_key(key, prefixes=prefixes):
            continue
        points.append(
            MetricPoint(
                name=key,
                value=metric_value,
                source_key=key,
                metadata={"metric_unit": _metric_unit(key)},
            )
        )
    return points


def _missing_metric_point(row: dict[str, Any], context: ParserContext) -> MetricPoint:
    name = _event_dataset(row, context) or FORMAT_DATASETS.get(context.source_format) or "host.metric"
    return MetricPoint(
        name=name,
        value=None,
        source_key=None,
        metadata={"metric_value_missing": True},
    )


def _is_metric_key(key: str, *, prefixes: tuple[str, ...]) -> bool:
    if key in NON_METRIC_EXACT_KEYS or key.endswith(NON_METRIC_SUFFIXES):
        return False
    if prefixes and key.startswith(prefixes):
        return True
    return key.startswith(GENERIC_METRIC_PREFIXES)


def _has_metric_signal(row: dict[str, Any], context: ParserContext) -> bool:
    del context
    if _explicit_event_dataset(row) not in ("", None):
        return True
    if _pick(row, "metricset.module", "metricset.name") not in ("", None):
        return True
    if any(str(key).startswith(GENERIC_METRIC_PREFIXES) for key in row):
        return True
    return False


def _is_annotation_row(row: dict[str, Any]) -> bool:
    if any(_is_metric_key(key, prefixes=()) for key, value in row.items() if _float_or_none(value) is not None):
        return False
    lower_keys = {key.lower() for key in row if not key.startswith("_")}
    return bool(lower_keys.intersection(ANNOTATION_KEYS)) and not any(
        key.startswith(("system.", "process.", "metricset.", "event.dataset")) for key in row
    )


def _metric_metadata(
    row: dict[str, Any],
    context: ParserContext,
    point: MetricPoint,
    *,
    point_index: int,
    event_dataset: str | None,
    network_interface: Any,
    disk_name: Any,
    filesystem_mount: Any,
) -> dict[str, Any] | None:
    metadata = {
        "json_source_type": row.get("_json_source_type"),
        "json_record_index": row.get("_json_record_index"),
        "source_format": context.source_format,
        "event_dataset": event_dataset,
        "metricset_module": _pick(row, "metricset.module"),
        "metricset_name": _pick(row, "metricset.name"),
        "metricset_period": _pick(row, "metricset.period"),
        "metric_source_key": point.source_key,
        "metric_sequence": point_index,
        "metric_unit": point.metadata.get("metric_unit"),
        "metric_value_missing": point.value is None,
        "network_interface": network_interface,
        "disk_name": disk_name,
        "filesystem_mount_point": filesystem_mount,
        "filesystem_device_name": _pick(row, "system.filesystem.device_name"),
        "service_state": _pick(row, "service.state", "system.service.state"),
    }
    metadata.update(point.metadata)
    return merge_json_objects(metadata, empty_as_none=True)


def _resolve_metric_labels(parser: BaseParser, row: dict[str, Any], context: ParserContext) -> dict[str, Any]:
    label_row = row
    if context.dataset_role == "TEST":
        label_row = {
            key: value
            for key, value in row.items()
            if key.lower() not in TEST_LABEL_FIELDS
        }
    return parser.label_resolver.resolve(label_row, context)  # type: ignore[attr-defined]


def _event_dataset(row: dict[str, Any], context: ParserContext) -> str | None:
    return _explicit_event_dataset(row) or FORMAT_DATASETS.get(context.source_format)


def _explicit_event_dataset(row: dict[str, Any]) -> str | None:
    explicit = _pick(row, "event.dataset", "metricset.dataset")
    if explicit not in ("", None):
        return str(explicit)
    module = _pick(row, "metricset.module")
    metricset = _pick(row, "metricset.name")
    if module not in ("", None) and metricset not in ("", None):
        return f"{module}.{metricset}"
    return None


def _timestamp_from_metric_row(row: dict[str, Any]) -> tuple[str | None, datetime | None]:
    for field in TIMESTAMP_FIELDS:
        timestamp = _parse_timestamp(_pick(row, field))
        if timestamp is not None:
            return field, timestamp
    return None, None


def _parse_timestamp(value: Any) -> datetime | None:
    if value in ("", None):
        return None
    text = str(value).strip()
    try:
        return datetime.fromtimestamp(float(text), tz=timezone.utc)
    except ValueError:
        pass
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
    if parsed is not None:
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return None


def _pick(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in ("", None):
            return value
    return None


def _float_or_none(value: Any) -> float | None:
    if value in ("", None) or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _string_or_none(value: Any) -> str | None:
    return None if value in ("", None) else str(value)


def _metric_unit(metric_name: str) -> str | None:
    if metric_name.endswith(".pct"):
        return "pct"
    if metric_name.endswith(".bytes"):
        return "bytes"
    if metric_name.endswith(".count"):
        return "count"
    if metric_name.endswith(".ms"):
        return "ms"
    if metric_name.endswith(".sec") or metric_name.endswith(".seconds"):
        return "seconds"
    if metric_name.endswith(".packets"):
        return "packets"
    return None


def _event_uid(context: ParserContext, line_index: int, point_index: int, metric_name: str) -> str:
    raw = f"{context.source_file_path}:{line_index}:{point_index}:{metric_name}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()


def _error_sample(row: dict[str, Any], exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}; row={compact_json_row(row)}"
