"""Packet capture parsers for PCAP, CAP, and PCAPNG normalized summaries."""

from __future__ import annotations

import hashlib
import ipaddress
import struct
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from scripts.stage_two.labels import LabelResolver, LabelResolverProtocol
from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult


PCAP_MAGIC_ENDIAN: dict[bytes, tuple[str, float]] = {
    b"\xd4\xc3\xb2\xa1": ("<", 1_000_000.0),
    b"\xa1\xb2\xc3\xd4": (">", 1_000_000.0),
    b"\x4d\x3c\xb2\xa1": ("<", 1_000_000_000.0),
    b"\xa1\xb2\x3c\x4d": (">", 1_000_000_000.0),
}
PCAPNG_SECTION_HEADER = 0x0A0D0D0A
PCAPNG_INTERFACE_DESCRIPTION = 0x00000001
PCAPNG_ENHANCED_PACKET = 0x00000006
LINKTYPE_ETHERNET = 1
LINKTYPE_RAW = 101
IP_PROTO_TCP = 6
IP_PROTO_UDP = 17
DNS_PORT = 53


@dataclass(frozen=True)
class PacketRecord:
    """One packet record extracted from a capture container."""

    timestamp: datetime | None
    captured_len: int
    original_len: int
    linktype: int
    payload: bytes


@dataclass(frozen=True)
class PacketSummary:
    """Protocol-level packet summary without raw payload retention."""

    src_ip: str | None
    dst_ip: str | None
    src_port: int | None
    dst_port: int | None
    protocol: str | None
    packet_size: int
    tcp_flags: str | None
    domain: str | None
    qtype: str | None
    qclass: str | None
    rcode: str | None
    metadata: dict[str, Any]


class PacketCaptureParser(BaseParser):
    """Base packet capture parser that emits normalized packet summaries."""

    parser_name = "packet_capture_parser"
    default_modality = "packet"

    def __init__(self, label_resolver: LabelResolverProtocol | None = None) -> None:
        """Initialize the parser with an optional label resolver."""
        self.label_resolver = label_resolver or LabelResolver()

    def parse(self, path: str | Path, context: ParserContext) -> ParserResult:
        """Parse packet capture records into normalized summaries."""
        events: list[dict[str, Any]] = []
        rows_failed = 0
        warnings: list[str] = []
        try:
            records = list(_iter_capture_records(Path(path)))
        except ValueError as exc:
            raise ValueError(f"failed to read packet capture: {exc}") from exc

        for index, record in enumerate(records):
            try:
                summary = _summarize_packet(record)
                events.append(self._record_to_event(record, summary, index, context))
            except Exception as exc:
                rows_failed += 1
                warnings.append(f"packet {index}: {exc}")
        result = ParserResult(
            rows_read=len(records),
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            warnings=warnings,
        )
        self.validate_result(result)
        return result

    def _record_to_event(
        self,
        record: PacketRecord,
        summary: PacketSummary,
        index: int,
        context: ParserContext,
    ) -> dict[str, Any]:
        label_fields = self.label_resolver.resolve(summary.metadata, context)
        entity_id = _packet_entity_id(summary)
        event_type = "dns_packet_summary" if summary.domain else "packet_summary"
        modality = "dns" if summary.domain and self.default_modality == "dns" else self.default_modality
        return self.base_event(
            context,
            event_uid=_event_uid(context, index, entity_id),
            timestamp=record.timestamp,
            timestamp_source="capture_header" if record.timestamp else None,
            timestamp_type="absolute" if record.timestamp else "event_order",
            event_index=index,
            entity_type="packet",
            entity_id=entity_id,
            event_type=event_type,
            raw_event_name=None,
            modality=modality,
            src_ip=summary.src_ip,
            dst_ip=summary.dst_ip,
            src_port=summary.src_port,
            dst_port=summary.dst_port,
            protocol=summary.protocol,
            domain=summary.domain,
            query_domain=summary.domain,
            qtype=summary.qtype,
            qclass=summary.qclass,
            rcode=summary.rcode,
            raw_fields_json={
                key: value
                for key, value in {
                    "packet_size": summary.packet_size,
                    "captured_len": record.captured_len,
                    "original_len": record.original_len,
                    "tcp_flags": summary.tcp_flags,
                    **summary.metadata,
                }.items()
                if value not in ("", None)
            },
            created_at=datetime.now(timezone.utc),
            **label_fields,
        )


class DnsPacketCaptureParser(PacketCaptureParser):
    """Packet capture parser configured for DNS branch packet sources."""

    parser_name = "dns_packet_capture_parser"
    default_modality = "dns"


class HostPacketCaptureParser(PacketCaptureParser):
    """Packet capture parser configured for Host validation packet sources."""

    parser_name = "host_packet_capture_parser"
    default_modality = "packet"


def _iter_capture_records(path: Path) -> Iterator[PacketRecord]:
    with path.open("rb") as file:
        magic = file.read(4)
        file.seek(0)
        if magic in PCAP_MAGIC_ENDIAN:
            yield from _iter_pcap_records(file.read())
            return
        if len(magic) == 4 and struct.unpack("<I", magic)[0] == PCAPNG_SECTION_HEADER:
            yield from _iter_pcapng_records(file.read())
            return
    raise ValueError(f"unsupported packet capture header for {path}")


def _iter_pcap_records(data: bytes) -> Iterator[PacketRecord]:
    endian, timestamp_scale = PCAP_MAGIC_ENDIAN[data[:4]]
    if len(data) < 24:
        raise ValueError("truncated PCAP global header")
    linktype = struct.unpack(f"{endian}I", data[20:24])[0]
    offset = 24
    while offset + 16 <= len(data):
        ts_sec, ts_frac, captured_len, original_len = struct.unpack(f"{endian}IIII", data[offset : offset + 16])
        offset += 16
        if captured_len < 0 or offset + captured_len > len(data):
            raise ValueError("truncated PCAP packet payload")
        payload = data[offset : offset + captured_len]
        offset += captured_len
        timestamp = datetime.fromtimestamp(ts_sec + (ts_frac / timestamp_scale), tz=timezone.utc)
        yield PacketRecord(timestamp, captured_len, original_len, linktype, payload)


def _iter_pcapng_records(data: bytes) -> Iterator[PacketRecord]:
    offset = 0
    endian = "<"
    linktypes: dict[int, int] = {}
    while offset + 12 <= len(data):
        block_type, block_total_length = struct.unpack(f"{endian}II", data[offset : offset + 8])
        if block_total_length < 12 or offset + block_total_length > len(data):
            break
        body = data[offset + 8 : offset + block_total_length - 4]
        if block_type == PCAPNG_SECTION_HEADER and len(body) >= 4:
            byte_order_magic = body[:4]
            if byte_order_magic == b"\x4d\x3c\x2b\x1a":
                endian = "<"
            elif byte_order_magic == b"\x1a\x2b\x3c\x4d":
                endian = ">"
        elif block_type == PCAPNG_INTERFACE_DESCRIPTION and len(body) >= 8:
            interface_id = len(linktypes)
            linktypes[interface_id] = struct.unpack(f"{endian}H", body[:2])[0]
        elif block_type == PCAPNG_ENHANCED_PACKET and len(body) >= 20:
            interface_id, ts_high, ts_low, captured_len, original_len = struct.unpack(f"{endian}IIIII", body[:20])
            payload_start = 20
            payload_end = payload_start + captured_len
            if payload_end <= len(body):
                timestamp_us = (ts_high << 32) | ts_low
                timestamp = datetime.fromtimestamp(timestamp_us / 1_000_000.0, tz=timezone.utc)
                yield PacketRecord(
                    timestamp=timestamp,
                    captured_len=captured_len,
                    original_len=original_len,
                    linktype=linktypes.get(interface_id, LINKTYPE_ETHERNET),
                    payload=body[payload_start:payload_end],
                )
        offset += block_total_length


def _summarize_packet(record: PacketRecord) -> PacketSummary:
    packet = record.payload
    metadata: dict[str, Any] = {"linktype": record.linktype}
    if record.linktype == LINKTYPE_ETHERNET:
        if len(packet) < 14:
            return _empty_summary(record, metadata)
        ethertype = struct.unpack("!H", packet[12:14])[0]
        metadata["ethertype"] = f"0x{ethertype:04x}"
        packet = packet[14:]
    version = packet[0] >> 4 if packet else None
    if record.linktype == LINKTYPE_RAW:
        version = packet[0] >> 4 if packet else None
    if version == 4:
        return _summarize_ipv4(packet, record, metadata)
    if version == 6:
        return _summarize_ipv6(packet, record, metadata)
    return _empty_summary(record, metadata)


def _summarize_ipv4(packet: bytes, record: PacketRecord, metadata: dict[str, Any]) -> PacketSummary:
    if len(packet) < 20:
        return _empty_summary(record, metadata)
    header_len = (packet[0] & 0x0F) * 4
    protocol_number = packet[9]
    src_ip = str(ipaddress.ip_address(packet[12:16]))
    dst_ip = str(ipaddress.ip_address(packet[16:20]))
    transport = packet[header_len:]
    return _summarize_transport(protocol_number, src_ip, dst_ip, transport, record, metadata)


def _summarize_ipv6(packet: bytes, record: PacketRecord, metadata: dict[str, Any]) -> PacketSummary:
    if len(packet) < 40:
        return _empty_summary(record, metadata)
    protocol_number = packet[6]
    src_ip = str(ipaddress.ip_address(packet[8:24]))
    dst_ip = str(ipaddress.ip_address(packet[24:40]))
    transport = packet[40:]
    return _summarize_transport(protocol_number, src_ip, dst_ip, transport, record, metadata)


def _summarize_transport(
    protocol_number: int,
    src_ip: str,
    dst_ip: str,
    transport: bytes,
    record: PacketRecord,
    metadata: dict[str, Any],
) -> PacketSummary:
    protocol = {IP_PROTO_TCP: "TCP", IP_PROTO_UDP: "UDP"}.get(protocol_number, str(protocol_number))
    src_port: int | None = None
    dst_port: int | None = None
    tcp_flags: str | None = None
    dns: dict[str, Any] = {}
    if protocol_number == IP_PROTO_TCP and len(transport) >= 20:
        src_port, dst_port = struct.unpack("!HH", transport[:4])
        tcp_flags = _tcp_flags(transport[13])
        data_offset = (transport[12] >> 4) * 4
        application = transport[data_offset:]
        if DNS_PORT in (src_port, dst_port) and len(application) > 2:
            dns = _parse_dns(application[2:])
    elif protocol_number == IP_PROTO_UDP and len(transport) >= 8:
        src_port, dst_port = struct.unpack("!HH", transport[:4])
        application = transport[8:]
        if DNS_PORT in (src_port, dst_port):
            dns = _parse_dns(application)
    return PacketSummary(
        src_ip=src_ip,
        dst_ip=dst_ip,
        src_port=src_port,
        dst_port=dst_port,
        protocol=protocol,
        packet_size=record.original_len,
        tcp_flags=tcp_flags,
        domain=dns.get("query_domain"),
        qtype=dns.get("qtype"),
        qclass=dns.get("qclass"),
        rcode=dns.get("rcode"),
        metadata={**metadata, **dns},
    )


def _parse_dns(payload: bytes) -> dict[str, Any]:
    if len(payload) < 12:
        return {}
    flags = struct.unpack("!H", payload[2:4])[0]
    qdcount = struct.unpack("!H", payload[4:6])[0]
    result: dict[str, Any] = {"dns_id": struct.unpack("!H", payload[:2])[0], "rcode": str(flags & 0x000F)}
    if qdcount < 1:
        return result
    offset = 12
    labels: list[str] = []
    while offset < len(payload):
        length = payload[offset]
        offset += 1
        if length == 0:
            break
        if length & 0xC0:
            break
        if offset + length > len(payload):
            return result
        labels.append(payload[offset : offset + length].decode("utf-8", errors="replace"))
        offset += length
    if labels:
        result["query_domain"] = ".".join(labels)
    if offset + 4 <= len(payload):
        qtype, qclass = struct.unpack("!HH", payload[offset : offset + 4])
        result["qtype"] = str(qtype)
        result["qclass"] = str(qclass)
    return result


def _empty_summary(record: PacketRecord, metadata: dict[str, Any]) -> PacketSummary:
    return PacketSummary(
        src_ip=None,
        dst_ip=None,
        src_port=None,
        dst_port=None,
        protocol=None,
        packet_size=record.original_len,
        tcp_flags=None,
        domain=None,
        qtype=None,
        qclass=None,
        rcode=None,
        metadata=metadata,
    )


def _tcp_flags(flags: int) -> str:
    names = [
        ("FIN", 0x01),
        ("SYN", 0x02),
        ("RST", 0x04),
        ("PSH", 0x08),
        ("ACK", 0x10),
        ("URG", 0x20),
        ("ECE", 0x40),
        ("CWR", 0x80),
    ]
    return ",".join(name for name, bit in names if flags & bit) or "0"


def _packet_entity_id(summary: PacketSummary) -> str | None:
    if summary.src_ip and summary.dst_ip:
        ports = ""
        if summary.src_port is not None or summary.dst_port is not None:
            ports = f":{summary.src_port or ''}->{summary.dst_port or ''}"
        return f"{summary.src_ip}->{summary.dst_ip}{ports}:{summary.protocol or 'unknown'}"
    return None


def _event_uid(context: ParserContext, index: int, entity_id: Any) -> str:
    raw = f"{context.source_file_path}:{index}:{entity_id or ''}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()
