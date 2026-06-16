"""DNS normalization parsers for CSV, TXT, and pcap.csv sources."""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult
from scripts.stage_two.parsers.common import merge_json_objects
from scripts.stage_two.parsers.input_reader import UniversalInputReader
from scripts.stage_two.labels import LabelResolver, LabelResolverProtocol, UnlabeledLabelResolver


HEADERLESS_DNS_TEST_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "protocol",
    "query_domain",
    "qtype",
    "qclass",
    "ttl",
    "rcode",
    "answer_count",
    "query_length",
    "subdomain_length",
    "label_count",
    "entropy",
    "resolver",
    "parent_domain",
    "asn",
    "country",
    "label",
    "metadata",
)

HEADERLESS_PHISHTANK_COLUMNS: tuple[str, ...] = (
    "phish_id",
    "url",
    "phish_detail_url",
    "submission_time",
    "verified",
    "verification_time",
    "online",
    "target",
)

DOMAIN_FIELDS: tuple[str, ...] = (
    "query_domain",
    "qname",
    "domain",
    "Domain",
    "domain_name",
    "hostname",
    "host",
    "fqdn",
    "FQDN",
    "rr_name",
    "rr.name",
    "dns.qry.name",
    "dns.question.name",
    "dns.resp.name",
    "query",
    "query_name",
    "parent_domain",
)
URL_FIELDS: tuple[str, ...] = (
    "url",
    "URL",
    "phish_url",
    "phish_detail_url",
    "detail_url",
    "link",
)
TIMESTAMP_FIELDS: tuple[str, ...] = (
    "timestamp",
    "time",
    "frame.time_epoch",
    "frame.time",
    "Time",
    "time_epoch",
    "ts",
    "packet_time",
    "submission_time",
    "verification_time",
    "last_online",
    "date",
    "datetime",
    "created_at",
    "updated_at",
)
QTYPE_FIELDS: tuple[str, ...] = (
    "qtype",
    "QTYPE",
    "rr_type",
    "dns.qry.type",
    "dns.qry.type_name",
    "dns.qry.type.name",
    "dns.resp.type",
    "dns.rr.type",
)
QCLASS_FIELDS: tuple[str, ...] = ("qclass", "QCLASS", "dns.qry.class", "dns.qry.class_name")
TTL_FIELDS: tuple[str, ...] = ("ttl", "TTL", "dns.resp.ttl", "dns.a.ttl", "dns.aaaa.ttl", "dns.rr.ttl")
RCODE_FIELDS: tuple[str, ...] = ("rcode", "RCODE", "dns.flags.rcode", "dns.flags.rcode_name", "response_code")
SRC_IP_FIELDS: tuple[str, ...] = (
    "src_ip",
    "source_ip",
    "source.ip",
    "ip.src",
    "ip.src_host",
    "frame_ip_src",
    "_ws.col.Source",
    "Source",
)
DST_IP_FIELDS: tuple[str, ...] = (
    "dst_ip",
    "destination_ip",
    "destination.ip",
    "ip.dst",
    "ip.dst_host",
    "frame_ip_dst",
    "_ws.col.Destination",
    "Destination",
)
RESOLVER_IP_FIELDS: tuple[str, ...] = ("resolver_ip", "resolver", "dns.resolver", "nameserver", "server_ip")
SRC_PORT_FIELDS: tuple[str, ...] = ("src_port", "source.port", "udp.srcport", "tcp.srcport")
DST_PORT_FIELDS: tuple[str, ...] = ("dst_port", "destination.port", "udp.dstport", "tcp.dstport")
PROTOCOL_FIELDS: tuple[str, ...] = ("protocol", "_ws.col.Protocol", "frame.protocols", "ip.proto")
DNS_FEATURE_FIELDS: tuple[str, ...] = (
    "FQDN_count",
    "upper",
    "lower",
    "numeric",
    "special",
    "labels",
    "labels_max",
    "labels_average",
    "longest_word",
    "sld",
    "len",
    "subdomain",
    "answer_count",
    "query_length",
    "subdomain_length",
    "label_count",
    "entropy",
    "rr",
    "rr_count",
    "rr_name_entropy",
    "rr_name_length",
    "distinct_ns",
    "distinct_ip",
    "unique_country",
    "unique_asn",
    "distinct_domains",
    "reverse_dns",
    "a_records",
    "unique_ttl",
    "ttl_mean",
    "ttl_variance",
    "A_frequency",
    "AAAA_frequency",
    "CNAME_frequency",
    "HINFO_frequency",
    "MX_frequency",
    "NS_frequency",
    "NULL_frequency",
    "OPT_frequency",
    "PTR_frequency",
    "SOA_frequency",
    "SRV_frequency",
    "TXT_frequency",
    "parent_domain",
    "asn",
    "ASN",
    "country",
    "Country",
    "tld",
    "IP",
    "ip",
)
PACKET_SUMMARY_FIELDS: tuple[str, ...] = (
    "frame.number",
    "frame.len",
    "frame.cap_len",
    "packet_length",
    "length",
    "flow_id",
    "stream",
    "tcp.stream",
    "udp.stream",
    "bytes",
    "packets",
    "duration",
)
PCAP_FEATURE_SIGNAL_FIELDS: tuple[str, ...] = (
    "FQDN_count",
    "entropy",
    "labels",
    "rr",
    "rr_count",
    "rr_type",
    "ttl_mean",
    "distinct_ip",
    "frame.len",
    "packet_length",
    "flow_id",
)
KNOWN_CSV_HEADER_FIELDS: frozenset[str] = frozenset(
    field.lower()
    for field in (
        *DOMAIN_FIELDS,
        *URL_FIELDS,
        *TIMESTAMP_FIELDS,
        *QTYPE_FIELDS,
        *QCLASS_FIELDS,
        *TTL_FIELDS,
        *RCODE_FIELDS,
        *SRC_IP_FIELDS,
        *DST_IP_FIELDS,
        *RESOLVER_IP_FIELDS,
        *SRC_PORT_FIELDS,
        *DST_PORT_FIELDS,
        *PROTOCOL_FIELDS,
        *DNS_FEATURE_FIELDS,
        *PACKET_SUMMARY_FIELDS,
        "label",
        "phish_id",
        "verified",
        "online",
    )
)


UnlabeledResolver = UnlabeledLabelResolver


class DnsCsvParser(BaseParser):
    """Schema-aware DNS CSV parser with headerless TEST CSV support."""

    parser_name = "dns_csv_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or LabelResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse DNS CSV rows into normalized DNS events."""
        file_path = Path(path)
        events: list[dict[str, Any]] = []
        rows_failed = 0
        error_samples: list[str] = []
        with file_path.open("r", encoding="utf-8", errors="replace", newline="") as file:
            sample = file.read(4096)
            file.seek(0)
            for index, row in enumerate(_iter_dns_csv_rows(file, sample, context)):
                try:
                    events.append(self._row_to_event(row, index, context, event_type="dns_query"))
                except Exception as exc:
                    rows_failed += 1
                    error_samples.append(_error_sample(row, exc))
        result = ParserResult(
            rows_read=len(events) + rows_failed,
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            error_samples=error_samples,
        )
        self.validate_result(result)
        return result

    def _row_to_event(
        self,
        row: dict[str, Any],
        index: int,
        context: ParserContext,
        *,
        event_type: str,
        allow_feature_only: bool = False,
    ) -> dict[str, Any]:
        query_domain = _extract_query_domain(row)
        timestamp_field, timestamp_value = _first_present_with_name(row, TIMESTAMP_FIELDS)
        timestamp = _parse_timestamp(timestamp_value)
        src_ip = _first_present(row, SRC_IP_FIELDS)
        dst_ip = _first_present(row, DST_IP_FIELDS)
        resolver_ip = _first_present(row, RESOLVER_IP_FIELDS)
        src_ip = src_ip or resolver_ip
        qtype = _first_present(row, QTYPE_FIELDS)
        qclass = _first_present(row, QCLASS_FIELDS)
        ttl = _parse_int(_first_present(row, TTL_FIELDS))
        rcode = _first_present(row, RCODE_FIELDS)
        protocol = _first_present(row, PROTOCOL_FIELDS)
        if not _has_dns_signal(
            query_domain=query_domain,
            src_ip=src_ip,
            dst_ip=dst_ip,
            qtype=qtype,
            qclass=qclass,
            ttl=ttl,
            rcode=rcode,
            protocol=protocol,
            row=row,
            allow_feature_only=allow_feature_only,
        ):
            raise ValueError("row has no usable DNS/domain fields")

        label_fields = self.label_resolver.resolve(row, context)
        return self.base_event(
            context,
            event_uid=_event_uid(context, index, query_domain),
            timestamp=timestamp,
            timestamp_source=timestamp_field if timestamp is not None else None,
            timestamp_type="absolute" if timestamp is not None else "event_order",
            event_index=index,
            entity_type="domain" if query_domain else "dns_observation",
            entity_id=query_domain or src_ip or dst_ip,
            event_type=event_type,
            raw_event_name=None,
            modality="dns",
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=_parse_int(_first_present(row, SRC_PORT_FIELDS)),
            dst_port=_parse_int(_first_present(row, DST_PORT_FIELDS)),
            protocol=protocol,
            domain=query_domain,
            query_domain=query_domain,
            qtype=qtype,
            qclass=qclass,
            ttl=ttl,
            rcode=rcode,
            raw_fields_json=_compact_row(row),
            metadata_json=_dns_metadata(row, resolver_ip=resolver_ip),
            created_at=datetime.now(timezone.utc),
            **label_fields,
        )


class DnsPcapCsvParser(DnsCsvParser):
    """Parser for CSV exports derived from DNS packet captures."""

    parser_name = "dns_pcap_csv_parser"

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse pcap.csv packet summary rows into normalized DNS events."""
        events: list[dict[str, Any]] = []
        rows_failed = 0
        error_samples: list[str] = []
        reader = UniversalInputReader(path)
        with reader.iter_lines(keepends=True, skip_empty=False) as lines:
            csv_reader = csv.DictReader(lines)
            for index, row in enumerate(csv_reader):
                normalized_row = _normalize_dict_row(row)
                try:
                    events.append(
                        self._row_to_event(
                            normalized_row,
                            index,
                            context,
                            event_type=_infer_pcap_csv_event_type(normalized_row),
                            allow_feature_only=True,
                        )
                    )
                except Exception as exc:
                    rows_failed += 1
                    error_samples.append(_error_sample(normalized_row, exc))

        reader_metadata = reader.metadata_snapshot()
        warnings = [
            *reader_metadata.warnings,
            *(f"reader error: {error}" for error in reader_metadata.errors),
        ]
        result = ParserResult(
            rows_read=len(events) + rows_failed,
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            warnings=warnings,
            bytes_read=reader_metadata.bytes_read,
            error_samples=error_samples,
        )
        self.validate_result(result)
        return result


class DnsTxtDomainListParser(BaseParser):
    """Parser for TXT files containing one domain per line."""

    parser_name = "dns_txt_domain_list_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or LabelResolver(enable_filename_heuristics=False)

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse a domain-list TXT file into normalized DNS events."""
        events: list[dict[str, Any]] = []
        rows_failed = 0
        error_samples: list[str] = []
        skipped_blank_lines = 0
        skipped_comment_lines = 0
        rows_read = 0
        reader = UniversalInputReader(path)
        with reader.iter_lines(keepends=False, skip_empty=False) as lines:
            for index, line in enumerate(lines):
                rows_read += 1
                item = line.strip()
                if not item:
                    skipped_blank_lines += 1
                    continue
                if item.startswith("#"):
                    skipped_comment_lines += 1
                    continue
                try:
                    domain = _normalize_domain_or_url(item)
                    if not domain:
                        raise ValueError("line is not a valid domain/list item")
                    line_number = index + 1
                    row = {"query_domain": domain, "line_number": line_number}
                    label_fields = self.label_resolver.resolve(row, context)
                    events.append(
                        self.base_event(
                            context,
                            event_uid=_event_uid(context, index, domain),
                            timestamp=None,
                            timestamp_source=None,
                            timestamp_type="event_order",
                            event_index=index,
                            entity_type="domain",
                            entity_id=domain,
                            event_type="dns_domain_observation",
                            raw_event_name=None,
                            modality="dns",
                            domain=domain,
                            query_domain=domain,
                            qtype=None,
                            qclass=None,
                            ttl=None,
                            rcode=None,
                            raw_fields_json=row,
                            metadata_json=_txt_metadata(reader, line_number=line_number),
                            created_at=datetime.now(timezone.utc),
                            **label_fields,
                        )
                    )
                except Exception as exc:
                    rows_failed += 1
                    error_samples.append(_error_sample({"line_number": index + 1, "raw_line": item}, exc))
        reader_metadata = reader.metadata_snapshot()
        warnings = [
            *reader_metadata.warnings,
            *(f"reader error: {error}" for error in reader_metadata.errors),
            f"skipped_blank_lines={skipped_blank_lines}",
            f"skipped_comment_lines={skipped_comment_lines}",
        ]
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
        return result


def _iter_dns_csv_rows(file: Any, sample: str, context: ParserContext):
    has_header = False if _is_headerless_dns_test(context) else _has_csv_header(sample)
    if has_header:
        reader = csv.DictReader(file)
        for row in reader:
            yield _normalize_dict_row(row)
        return

    reader = csv.reader(file)
    for values in reader:
        if _is_empty_csv_row(values):
            continue
        if _is_headerless_dns_test(context):
            yield _row_from_fieldnames(values, HEADERLESS_DNS_TEST_COLUMNS)
            continue
        if len(values) == 1:
            yield {"query_domain": values[0], "_csv_schema": "domain_list"}
            continue
        if _looks_like_domain_or_url(values[0]):
            row = {"query_domain": values[0], "_csv_schema": "domain_list"}
            if len(values) > 1:
                row["_csv_extra_columns"] = values[1:]
            yield row
            continue
        yield _row_from_fieldnames(values, HEADERLESS_PHISHTANK_COLUMNS)


def _row_from_fieldnames(values: list[str], fieldnames: tuple[str, ...]) -> dict[str, Any]:
    row = {
        field_name: values[index] if index < len(values) else None
        for index, field_name in enumerate(fieldnames)
    }
    if len(values) > len(fieldnames):
        row["_csv_extra_columns"] = values[len(fieldnames) :]
    return _normalize_dict_row(row)


def _normalize_dict_row(row: dict[Any, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in row.items():
        if key is None:
            extras = _compact_extra_columns(value)
            if extras:
                normalized["_csv_extra_columns"] = extras
            continue
        normalized[str(key)] = value
    return normalized


def _is_headerless_dns_test(context: ParserContext) -> bool:
    return context.dataset_role == "TEST" and context.source_format == "csv"


def _has_csv_header(sample: str) -> bool:
    rows = [row for row in csv.reader(sample.splitlines()) if not _is_empty_csv_row(row)]
    if rows:
        first_row = rows[0]
        lowered = {value.strip().lower() for value in first_row}
        if lowered.intersection(KNOWN_CSV_HEADER_FIELDS):
            return True
        if len(first_row) == 1 and _looks_like_domain_or_url(first_row[0]):
            return False
        if first_row and _looks_like_domain_or_url(first_row[0]):
            return False
    try:
        return csv.Sniffer().has_header(sample)
    except csv.Error:
        first_line = sample.splitlines()[0] if sample.splitlines() else ""
        return any(
            field in first_line.lower()
            for field in ("domain", "qname", "timestamp", "url", "phish_id", "ttl")
        )


def _is_empty_csv_row(values: list[str]) -> bool:
    return not values or all(value.strip() == "" for value in values)


def _compact_extra_columns(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return [] if value in ("", None) else [value]
    return [item for item in value if item not in ("", None)]


def _extract_query_domain(row: dict[str, Any]) -> str | None:
    domain_value = _first_present(row, DOMAIN_FIELDS)
    domain = _normalize_domain_or_url(domain_value)
    if domain:
        return domain
    url_value = _first_present(row, URL_FIELDS)
    return _normalize_domain_or_url(url_value)


def _normalize_domain_or_url(value: Any) -> str | None:
    if value in ("", None):
        return None
    text = str(value).strip().strip("\"'")
    if not text:
        return None
    parsed_domain = _domain_from_url(text)
    candidate = parsed_domain or text
    candidate = candidate.strip().strip(".").lower()
    if not candidate:
        return None
    if "/" in candidate or " " in candidate:
        return None
    return candidate


def _domain_from_url(value: str) -> str | None:
    text = value.strip()
    if "://" not in text and not text.startswith("//") and "/" not in text:
        return None
    parsed = urlparse(text if "://" in text or text.startswith("//") else f"//{text}")
    hostname = parsed.hostname
    if hostname:
        return hostname.strip(".").lower()
    return None


def _looks_like_domain_or_url(value: Any) -> bool:
    domain = _normalize_domain_or_url(value)
    if not domain:
        return False
    return "." in domain or domain.startswith("localhost")


def _first_present_with_name(row: dict[str, Any], fields: tuple[str, ...]) -> tuple[str | None, Any]:
    lowered = {key.lower(): (key, value) for key, value in row.items()}
    for field in fields:
        if field in row and row[field] not in ("", None):
            return field, row[field]
        resolved = lowered.get(field.lower())
        if resolved and resolved[1] not in ("", None):
            return str(resolved[0]), resolved[1]
    return None, None


def _first_present(row: dict[str, Any], fields: tuple[str, ...]) -> Any:
    lowered = {key.lower(): value for key, value in row.items()}
    for field in fields:
        if field in row and row[field] not in ("", None):
            return row[field]
        value = lowered.get(field.lower())
        if value not in ("", None):
            return value
    return None


def _parse_int(value: Any) -> int | None:
    if value in ("", None):
        return None
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def _parse_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


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
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _compact_row(row: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key, value in row.items():
        if key is None:
            extras = _compact_extra_columns(value)
            if extras:
                compact["_csv_extra_columns"] = extras
            continue
        if value in ("", None):
            continue
        if isinstance(value, list):
            extras = _compact_extra_columns(value)
            if extras:
                compact[str(key)] = extras
            continue
        compact[str(key)] = value
    return compact


def _dns_metadata(row: dict[str, Any], *, resolver_ip: Any) -> dict[str, Any] | None:
    metadata: dict[str, Any] = {}
    if resolver_ip:
        metadata["resolver_ip"] = resolver_ip
    for field in (*DNS_FEATURE_FIELDS, *PACKET_SUMMARY_FIELDS):
        value = _first_present(row, (field,))
        if value not in ("", None):
            metadata[field] = _metadata_value(field, value)
    extras = _first_present(row, ("_csv_extra_columns",))
    if extras:
        metadata["csv_extra_columns_count"] = len(extras) if isinstance(extras, list) else 1
    return merge_json_objects(metadata, empty_as_none=True)


def _txt_metadata(reader: UniversalInputReader, *, line_number: int) -> dict[str, Any] | None:
    metadata = reader.metadata
    return merge_json_objects(
        {
            "line_number": line_number,
            "encoding_hint": metadata.encoding_hint,
            "compression_hint": metadata.compression_hint,
            "base64_detected": metadata.base64_detected or None,
            "decode_strategy": metadata.decode_strategy if metadata.decode_strategy != "plain" else None,
        },
        empty_as_none=True,
    )


def _metadata_value(field: str, value: Any) -> Any:
    field_lower = field.lower()
    integer_fields = {
        "answer_count",
        "query_length",
        "subdomain_length",
        "label_count",
        "asn",
        "fqdn_count",
        "upper",
        "lower",
        "numeric",
        "special",
        "labels",
        "labels_max",
        "longest_word",
        "len",
        "subdomain",
        "rr_count",
        "rr_name_length",
        "distinct_ns",
        "a_records",
        "frame.number",
        "frame.len",
        "frame.cap_len",
        "packet_length",
        "length",
        "bytes",
        "packets",
    }
    float_fields = {
        "entropy",
        "labels_average",
        "rr",
        "rr_name_entropy",
        "ttl_mean",
        "ttl_variance",
        "duration",
    }
    if field_lower.endswith("_frequency") or field_lower in integer_fields:
        parsed_int = _parse_int(value)
        return value if parsed_int is None else parsed_int
    if field_lower in float_fields:
        parsed_float = _parse_float(value)
        return value if parsed_float is None else parsed_float
    return value


def _infer_pcap_csv_event_type(row: dict[str, Any]) -> str:
    response_flag = _first_present(row, ("dns.flags.response", "is_response", "response"))
    if response_flag is not None:
        flag_text = str(response_flag).strip().lower()
        if flag_text in {"1", "true", "yes", "response"}:
            return "dns_response"
        if flag_text in {"0", "false", "no", "query"}:
            return "dns_query"
    if _first_present(row, (*RCODE_FIELDS, *TTL_FIELDS, "rr_type", "rr_count", "answer_count")) is not None:
        return "dns_response"
    if _extract_query_domain(row) or _first_present(row, (*QTYPE_FIELDS, *QCLASS_FIELDS)) is not None:
        return "dns_query"
    return "network_packet_summary"


def _has_pcap_feature_signal(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    return any(_first_present(row, (field,)) not in ("", None) for field in PCAP_FEATURE_SIGNAL_FIELDS)


def _has_dns_signal(
    *,
    query_domain: Any,
    src_ip: Any,
    dst_ip: Any,
    qtype: Any,
    qclass: Any,
    ttl: Any,
    rcode: Any,
    protocol: Any,
    row: dict[str, Any] | None = None,
    allow_feature_only: bool = False,
) -> bool:
    del ttl, protocol
    if any(value not in ("", None) for value in (query_domain, src_ip, dst_ip, qtype, qclass, rcode)):
        return True
    return allow_feature_only and _has_pcap_feature_signal(row)


def _error_sample(row: dict[str, Any], exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}; row={_compact_row(row)}"


def _event_uid(context: ParserContext, index: int, entity: Any) -> str:
    raw = f"{context.source_file_path}:{index}:{entity or ''}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()
