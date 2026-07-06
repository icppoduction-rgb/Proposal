"""Core Network feature extractors for Stage Three normalized artifacts."""

from __future__ import annotations

import ipaddress
from collections import defaultdict
from typing import Any

import pyarrow as pa

from scripts.stage_three.extraction.common import (
    BASE_NORMALIZED_COLUMNS,
    LABEL_COLUMNS,
    TRACEABILITY_COLUMNS,
    datetime_to_epoch_seconds,
    first_value,
    json_rows,
    labels_payload,
    missing_ratios,
    nullable_values,
    order_values,
    select_existing_columns,
    stable_hash_int,
    string_values,
    timestamp_values,
    traceability_payload,
)


NETWORK_FEATURE_GROUPS: tuple[str, ...] = (
    "network_flow",
    "network_ports",
    "network_protocol",
    "network_direction",
    "network_timing",
)
NETWORK_FEATURES: dict[str, tuple[str, ...]] = {
    "network_flow": ("network_flow_bytes",),
    "network_ports": ("network_dst_port",),
    "network_protocol": ("network_transport_protocol",),
    "network_direction": ("network_direction_code",),
    "network_timing": ("network_flow_duration_ms",),
}
NETWORK_SOURCE_COLUMNS: tuple[str, ...] = (
    *BASE_NORMALIZED_COLUMNS,
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "protocol",
    "flow_id",
    "session_id",
    "metric_name",
    "metric_value",
)


def network_feature_columns(feature_group: str) -> tuple[str, ...]:
    """Return feature columns produced for a Network feature group."""
    try:
        return NETWORK_FEATURES[feature_group]
    except KeyError as exc:
        allowed = ", ".join(NETWORK_FEATURE_GROUPS)
        raise ValueError(f"unsupported Network feature_group={feature_group!r}; allowed: {allowed}") from exc


def required_network_columns(feature_group: str) -> tuple[str, ...]:
    """Return normalized input columns needed for a Network extractor."""
    network_feature_columns(feature_group)
    return NETWORK_SOURCE_COLUMNS


def select_existing_required_columns(schema: pa.Schema, requested_columns: tuple[str, ...]) -> list[str]:
    """Keep Network projection compatible with each normalized artifact schema."""
    selected = select_existing_columns(schema, requested_columns)
    if not selected:
        raise ValueError("normalized Network artifact does not contain any supported normalized-event columns")
    return selected


def extract_network_features_from_table(
    table: pa.Table,
    *,
    feature_group: str,
    normalized_artifact_id: int,
    dataset_id: int,
    role: str,
    source_normalized_path: str,
) -> pa.Table:
    """Extract core Network features for one bounded Arrow table."""
    feature_columns = network_feature_columns(feature_group)
    payload: dict[str, Any] = traceability_payload(
        table=table,
        normalized_artifact_id=normalized_artifact_id,
        dataset_id=dataset_id,
        role=role,
        branch="network",
        feature_group=feature_group,
        source_normalized_path=source_normalized_path,
    )
    context = _NetworkContext.from_table(table)
    if feature_group == "network_flow":
        payload.update({"network_flow_bytes": _flow_bytes(context)})
    elif feature_group == "network_ports":
        payload.update({"network_dst_port": _dst_ports(context)})
    elif feature_group == "network_protocol":
        payload.update({"network_transport_protocol": _protocols(context)})
    elif feature_group == "network_direction":
        payload.update({"network_direction_code": _direction_codes(context)})
    elif feature_group == "network_timing":
        payload.update({"network_flow_duration_ms": _flow_duration_ms(context)})
    payload.update(labels_payload(table))
    ordered = {
        **{column: payload[column] for column in TRACEABILITY_COLUMNS},
        **{column: payload[column] for column in feature_columns},
        **{column: payload[column] for column in LABEL_COLUMNS},
    }
    return pa.table(ordered)


class _NetworkContext:
    """Column and JSON payload view for one Network extraction batch."""

    def __init__(
        self,
        *,
        table: pa.Table,
        features_rows: list[dict[str, Any]],
        raw_rows: list[dict[str, Any]],
        metadata_rows: list[dict[str, Any]],
    ) -> None:
        self.table = table
        self.features_rows = features_rows
        self.raw_rows = raw_rows
        self.metadata_rows = metadata_rows
        self.flow_ids = _flow_ids(table)
        self.src_ips = string_values(table, "src_ip")
        self.dst_ips = string_values(table, "dst_ip")
        self.timestamps = timestamp_values(table)
        self.orders = order_values(table)

    @classmethod
    def from_table(cls, table: pa.Table) -> "_NetworkContext":
        return cls(
            table=table,
            features_rows=json_rows(table, "features_json"),
            raw_rows=json_rows(table, "raw_fields_json"),
            metadata_rows=json_rows(table, "metadata_json"),
        )

    def column_or_payload(self, row_index: int, columns: tuple[str, ...], payload_keys: tuple[str, ...]) -> Any:
        for column in columns:
            value = nullable_values(self.table, column)[row_index] if column in self.table.column_names else None
            if value not in (None, ""):
                return value
        for source in (self.features_rows[row_index], self.raw_rows[row_index], self.metadata_rows[row_index]):
            value = first_value(source, payload_keys)
            if value not in (None, ""):
                return value
        return None


def _flow_ids(table: pa.Table) -> list[str]:
    explicit = string_values(table, "flow_id")
    src_ips = string_values(table, "src_ip")
    dst_ips = string_values(table, "dst_ip")
    src_ports = nullable_values(table, "src_port")
    dst_ports = nullable_values(table, "dst_port")
    protocols = string_values(table, "protocol")
    flow_ids: list[str] = []
    for index, value in enumerate(explicit):
        if value:
            flow_ids.append(value)
            continue
        parts = (src_ips[index], dst_ips[index], src_ports[index], dst_ports[index], protocols[index])
        flow_ids.append("|".join("" if part is None else str(part) for part in parts))
    return flow_ids


def _flow_bytes(context: _NetworkContext) -> list[float]:
    bytes_per_row = [_network_bytes(context, index) for index in range(context.table.num_rows)]
    duckdb_result = _duckdb_group_sum(context.flow_ids, bytes_per_row)
    if duckdb_result is not None:
        return [duckdb_result.get(flow_id, 0.0) for flow_id in context.flow_ids]
    totals: defaultdict[str, float] = defaultdict(float)
    for flow_id, value in zip(context.flow_ids, bytes_per_row):
        totals[flow_id] += value
    return [totals[flow_id] for flow_id in context.flow_ids]


def _network_bytes(context: _NetworkContext, index: int) -> float:
    value = context.column_or_payload(
        index,
        columns=(),
        payload_keys=(
            "network_flow_bytes",
            "bytes",
            "byte_count",
            "flow.bytes",
            "network.bytes",
            "source.bytes",
            "destination.bytes",
        ),
    )
    number = _float_or_none(value)
    if number is not None:
        return max(0.0, number)
    packets = _float_or_none(context.column_or_payload(index, columns=(), payload_keys=("packets", "packet_count")))
    return max(0.0, packets or 0.0)


def _dst_ports(context: _NetworkContext) -> list[int | None]:
    values: list[int | None] = []
    column_values = nullable_values(context.table, "dst_port")
    for index in range(context.table.num_rows):
        value = column_values[index] if "dst_port" in context.table.column_names else None
        if value in (None, ""):
            value = context.column_or_payload(index, columns=(), payload_keys=("dst_port", "destination.port", "server.port"))
        values.append(_int_or_none(value))
    return values


def _protocols(context: _NetworkContext) -> list[int | None]:
    values: list[int | None] = []
    protocols = string_values(context.table, "protocol")
    for index in range(context.table.num_rows):
        protocol = protocols[index] if "protocol" in context.table.column_names else None
        if not protocol:
            protocol = context.column_or_payload(
                index,
                columns=(),
                payload_keys=("protocol", "network.transport", "transport", "ip.proto"),
            )
        values.append(stable_hash_int(protocol, modulo=4096))
    return values


def _direction_codes(context: _NetworkContext) -> list[int | None]:
    return [_direction_code(src_ip, dst_ip) for src_ip, dst_ip in zip(context.src_ips, context.dst_ips)]


def _direction_code(src_ip: str | None, dst_ip: str | None) -> int | None:
    if not src_ip or not dst_ip:
        return None
    try:
        src = ipaddress.ip_address(src_ip)
        dst = ipaddress.ip_address(dst_ip)
    except ValueError:
        return None
    src_private = src.is_private
    dst_private = dst.is_private
    if src_private and dst_private:
        return 3
    if src_private and not dst_private:
        return 1
    if not src_private and dst_private:
        return 2
    return 4


def _flow_duration_ms(context: _NetworkContext) -> list[float | None]:
    explicit = [
        _float_or_none(
            context.column_or_payload(
                index,
                columns=(),
                payload_keys=("network_flow_duration_ms", "flow.duration_ms", "duration_ms", "event.duration"),
            )
        )
        for index in range(context.table.num_rows)
    ]
    if any(value is not None for value in explicit):
        return explicit
    seconds = [datetime_to_epoch_seconds(value) for value in context.timestamps]
    duckdb_result = _duckdb_group_duration(context.flow_ids, seconds)
    if duckdb_result is not None and any(value is not None for value in seconds):
        return [duckdb_result.get(flow_id) for flow_id in context.flow_ids]
    if any(value is not None for value in seconds):
        return _python_group_duration(context.flow_ids, seconds, scale=1000.0)
    order_numbers = [float(value) if value is not None else None for value in context.orders]
    if any(value is not None for value in order_numbers):
        return _python_group_duration(context.flow_ids, order_numbers, scale=1.0)
    return [None] * context.table.num_rows


def _duckdb_group_sum(flow_ids: list[str], values: list[float]) -> dict[str, float] | None:
    try:
        import duckdb
    except ModuleNotFoundError:
        return None
    table = pa.table({"flow_id": flow_ids, "value": values})
    connection = duckdb.connect(database=":memory:")
    try:
        connection.register("batch", table)
        rows = connection.execute("SELECT flow_id, SUM(value) AS total_value FROM batch GROUP BY flow_id").fetchall()
    finally:
        connection.close()
    return {str(flow_id): float(total or 0.0) for flow_id, total in rows}


def _duckdb_group_duration(flow_ids: list[str], seconds: list[float | None]) -> dict[str, float | None] | None:
    try:
        import duckdb
    except ModuleNotFoundError:
        return None
    table = pa.table({"flow_id": flow_ids, "seconds": seconds})
    connection = duckdb.connect(database=":memory:")
    try:
        connection.register("batch", table)
        rows = connection.execute(
            """
            SELECT flow_id,
                   CASE
                       WHEN COUNT(seconds) = 0 THEN NULL
                       ELSE (MAX(seconds) - MIN(seconds)) * 1000.0
                   END AS duration_ms
            FROM batch
            GROUP BY flow_id
            """
        ).fetchall()
    finally:
        connection.close()
    return {str(flow_id): (None if duration is None else float(duration)) for flow_id, duration in rows}


def _python_group_duration(flow_ids: list[str], values: list[float | None], *, scale: float) -> list[float | None]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for flow_id, value in zip(flow_ids, values):
        if value is not None:
            grouped[flow_id].append(value)
    durations = {
        flow_id: (max(group_values) - min(group_values)) * scale if group_values else None
        for flow_id, group_values in grouped.items()
    }
    return [durations.get(flow_id) for flow_id in flow_ids]


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    number = _float_or_none(value)
    if number is None:
        return None
    return int(number)


def network_missing_ratios(table: pa.Table, columns: tuple[str, ...]) -> dict[str, float]:
    """Calculate missing ratios for Network feature columns."""
    return missing_ratios(table, columns)
