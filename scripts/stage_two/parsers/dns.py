"""DNS normalization parsers for CSV, TXT, and pcap.csv sources."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult


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

DOMAIN_FIELDS: tuple[str, ...] = (
    "query_domain",
    "qname",
    "domain",
    "fqdn",
    "FQDN",
    "url",
    "URL",
    "rr_name",
)
QTYPE_FIELDS: tuple[str, ...] = ("qtype", "QTYPE", "rr_type", "dns.qry.type")
QCLASS_FIELDS: tuple[str, ...] = ("qclass", "QCLASS", "dns.qry.class")
TTL_FIELDS: tuple[str, ...] = ("ttl", "TTL", "dns.resp.ttl")
RCODE_FIELDS: tuple[str, ...] = ("rcode", "RCODE", "dns.flags.rcode")
SRC_IP_FIELDS: tuple[str, ...] = ("src_ip", "source_ip", "ip.src", "frame_ip_src")
DST_IP_FIELDS: tuple[str, ...] = ("dst_ip", "destination_ip", "ip.dst", "frame_ip_dst")
SRC_PORT_FIELDS: tuple[str, ...] = ("src_port", "udp.srcport", "tcp.srcport")
DST_PORT_FIELDS: tuple[str, ...] = ("dst_port", "udp.dstport", "tcp.dstport")


class LabelResolverProtocol(Protocol):
    """Protocol for injectable label resolution without parser DB coupling."""

    def resolve(self, row: dict[str, Any], context: ParserContext) -> dict[str, Any]:
        """Return canonical label fields for one source row."""


@dataclass(frozen=True)
class UnlabeledResolver:
    """Default resolver used until canonical LabelResolver is configured."""

    def resolve(self, row: dict[str, Any], context: ParserContext) -> dict[str, Any]:
        """Return an explicit unlabeled label contract."""
        return {
            "label_binary": None,
            "label_family": None,
            "label_subtype": None,
            "label_source": "none",
            "label_status": "unlabeled",
            "label_confidence": None,
            "label_mapping_rule_id": None,
        }


class DnsCsvParser(BaseParser):
    """Schema-aware DNS CSV parser with headerless TEST CSV support."""

    parser_name = "dns_csv_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or UnlabeledResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse DNS CSV rows into normalized DNS events."""
        file_path = Path(path)
        events: list[dict[str, Any]] = []
        rows_failed = 0
        with file_path.open("r", encoding="utf-8", errors="replace", newline="") as file:
            sample = file.read(4096)
            file.seek(0)
            has_header = False if _is_headerless_dns_test(context) else _has_csv_header(sample)
            reader = csv.DictReader(file) if has_header else _headerless_reader(file)
            for index, row in enumerate(reader):
                try:
                    events.append(self._row_to_event(row, index, context, event_type="dns_query"))
                except Exception:
                    rows_failed += 1
        result = ParserResult(
            rows_read=len(events) + rows_failed,
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
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
    ) -> dict[str, Any]:
        query_domain = _first_present(row, DOMAIN_FIELDS)
        label_fields = self.label_resolver.resolve(row, context)
        return self.base_event(
            context,
            event_uid=_event_uid(context, index, query_domain),
            timestamp=_parse_timestamp(_first_present(row, ("timestamp", "time", "frame.time_epoch"))),
            timestamp_source="source_column" if _first_present(row, ("timestamp", "time", "frame.time_epoch")) else None,
            timestamp_type="absolute"
            if _first_present(row, ("timestamp", "time", "frame.time_epoch"))
            else "event_order",
            event_index=index,
            entity_type="domain",
            entity_id=query_domain,
            event_type=event_type,
            raw_event_name=None,
            modality="dns",
            src_ip=_first_present(row, SRC_IP_FIELDS),
            dst_ip=_first_present(row, DST_IP_FIELDS),
            src_port=_parse_int(_first_present(row, SRC_PORT_FIELDS)),
            dst_port=_parse_int(_first_present(row, DST_PORT_FIELDS)),
            protocol=_first_present(row, ("protocol", "_ws.col.Protocol")),
            domain=query_domain,
            query_domain=query_domain,
            qtype=_first_present(row, QTYPE_FIELDS),
            qclass=_first_present(row, QCLASS_FIELDS),
            ttl=_parse_int(_first_present(row, TTL_FIELDS)),
            rcode=_first_present(row, RCODE_FIELDS),
            raw_fields_json=_compact_row(row),
            created_at=datetime.now(timezone.utc),
            **label_fields,
        )


class DnsPcapCsvParser(DnsCsvParser):
    """Parser for CSV exports derived from DNS packet captures."""

    parser_name = "dns_pcap_csv_parser"

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse pcap.csv packet summary rows into normalized DNS events."""
        result = super().parse(path, context)
        events = [{**event, "event_type": "dns_packet_summary"} for event in result.events]
        updated = ParserResult(
            rows_read=result.rows_read,
            rows_parsed=result.rows_parsed,
            rows_failed=result.rows_failed,
            events=events,
            warnings=result.warnings,
        )
        self.validate_result(updated)
        return updated


class DnsTxtDomainListParser(BaseParser):
    """Parser for TXT files containing one domain per line."""

    parser_name = "dns_txt_domain_list_parser"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or UnlabeledResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse a domain-list TXT file into normalized DNS events."""
        events: list[dict[str, Any]] = []
        rows_failed = 0
        with Path(path).open("r", encoding="utf-8", errors="replace") as file:
            for index, line in enumerate(file):
                domain = line.strip()
                if not domain or domain.startswith("#"):
                    continue
                try:
                    row = {"query_domain": domain}
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
                            created_at=datetime.now(timezone.utc),
                            **label_fields,
                        )
                    )
                except Exception:
                    rows_failed += 1
        result = ParserResult(
            rows_read=len(events) + rows_failed,
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
        )
        self.validate_result(result)
        return result


def _headerless_reader(file) -> csv.DictReader:
    return csv.DictReader(file, fieldnames=HEADERLESS_DNS_TEST_COLUMNS)


def _is_headerless_dns_test(context: ParserContext) -> bool:
    return context.dataset_role == "TEST" and context.source_format == "csv"


def _has_csv_header(sample: str) -> bool:
    try:
        return csv.Sniffer().has_header(sample)
    except csv.Error:
        first_line = sample.splitlines()[0] if sample.splitlines() else ""
        return any(field in first_line.lower() for field in ("domain", "qname", "timestamp"))


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
    except ValueError:
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
    return {key: value for key, value in row.items() if value not in ("", None)}


def _event_uid(context: ParserContext, index: int, entity: Any) -> str:
    raw = f"{context.source_file_path}:{index}:{entity or ''}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()
