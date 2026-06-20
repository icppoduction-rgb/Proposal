"""Packet capture parsers for PCAP, CAP, and PCAPNG normalized summaries."""

from __future__ import annotations

import hashlib
import ipaddress
import struct
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Iterator

from config import STAGE_TWO_PACKET_BATCH_SIZE, STAGE_TWO_PACKET_PARSE_MODE
from scripts.stage_two.labels import LabelResolver, LabelResolverProtocol
from scripts.stage_two.parsers.base import BaseParser, ParserContext, ParserResult
from scripts.stage_two.parsers.input_reader import InputReaderError, UniversalInputReader


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
ETHERTYPE_IPV4 = 0x0800
ETHERTYPE_IPV6 = 0x86DD
ETHERTYPE_VLAN = 0x8100
ETHERTYPE_QINQ = 0x88A8
IP_PROTO_TCP = 6
IP_PROTO_UDP = 17
DNS_PORT = 53
MAX_CAPTURED_PACKET_BYTES = 64 * 1024 * 1024


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
    ttl: int | None
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
        rows_read = 0
        rows_failed = 0
        warnings: list[str] = []
        error_samples: list[str] = []
        bytes_read: int | None = None
        for batch in self.parse_batches(
            path,
            context,
            batch_size=max(STAGE_TWO_PACKET_BATCH_SIZE, 1),
        ):
            rows_read += batch.rows_read
            rows_failed += batch.rows_failed
            events.extend(batch.events)
            warnings.extend(batch.warnings)
            error_samples.extend(batch.error_samples)
            bytes_read = batch.bytes_read
        result = ParserResult(
            rows_read=rows_read,
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            warnings=warnings,
            bytes_read=bytes_read,
            error_samples=error_samples,
            status_override="EMPTY_FILE" if rows_read == 0 and (bytes_read or 0) == 0 else None,
            status_reason="packet capture has no packet records" if rows_read == 0 and (bytes_read or 0) == 0 else None,
        )
        self.validate_result(result)
        return result

    def parse_batches(
        self,
        path: str | Path,
        context: ParserContext,
        *,
        batch_size: int = STAGE_TWO_PACKET_BATCH_SIZE,
        packet_mode: str = STAGE_TWO_PACKET_PARSE_MODE,
        sample_size: int | None = None,
        **_: Any,
    ) -> Iterator[ParserResult]:
        """Parse packet capture records as bounded batches of normalized events."""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        normalized_mode = _normalize_packet_mode(packet_mode)
        events: list[dict[str, Any]] = []
        rows_read = 0
        rows_failed = 0
        warnings: list[str] = []
        error_samples: list[str] = []
        reader = UniversalInputReader(path)
        try:
            for index, record in enumerate(_iter_capture_records(Path(path), reader=reader)):
                rows_read += 1
                try:
                    summary = _summarize_packet(record)
                    if normalized_mode == "dns-only" and not _is_dns_summary(summary):
                        continue
                    events.append(self._record_to_event(record, summary, index, context))
                except Exception as exc:
                    rows_failed += 1
                    message = f"packet {index}: {_exception_message(exc)}"
                    warnings.append(message)
                    error_samples.append(message)
                if len(events) >= batch_size:
                    result = ParserResult(
                        rows_read=rows_read,
                        rows_parsed=len(events),
                        rows_failed=rows_failed,
                        events=events,
                        warnings=warnings,
                        bytes_read=reader.metadata.bytes_read,
                        error_samples=error_samples,
                    )
                    self.validate_result(result)
                    yield result
                    events = []
                    rows_read = 0
                    rows_failed = 0
                    warnings = []
                    error_samples = []
                if normalized_mode == "sample" and sample_size is not None and rows_read >= sample_size:
                    warnings.append(f"sample_mode_limit_reached={sample_size}")
                    break
        except (InputReaderError, ValueError) as exc:
            raise ValueError(f"failed to read packet capture: {_exception_message(exc)}") from exc

        warnings.extend(reader.metadata.warnings)
        result = ParserResult(
            rows_read=rows_read,
            rows_parsed=len(events),
            rows_failed=rows_failed,
            events=events,
            warnings=warnings,
            bytes_read=reader.metadata.bytes_read,
            error_samples=error_samples,
            status_override="EMPTY_FILE" if rows_read == 0 and reader.metadata.bytes_read == 0 else None,
            status_reason=(
                "packet capture has no packet records"
                if rows_read == 0 and reader.metadata.bytes_read == 0
                else None
            ),
        )
        self.validate_result(result)
        yield result

    def _record_to_event(
        self,
        record: PacketRecord,
        summary: PacketSummary,
        index: int,
        context: ParserContext,
    ) -> dict[str, Any]:
        label_fields = self.label_resolver.resolve(summary.metadata, context)
        entity_id = _packet_entity_id(summary)
        event_type = _packet_event_type(summary)
        modality = self._event_modality(summary)
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
            ttl=summary.ttl,
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

    def _event_modality(self, summary: PacketSummary) -> str:
        """Return branch-specific normalized modality for a packet summary."""
        return self.default_modality


class DnsPacketCaptureParser(PacketCaptureParser):
    """Packet capture parser configured for DNS branch packet sources."""

    parser_name = "dns_packet_capture_parser"
    default_modality = "network_packet"

    def _event_modality(self, summary: PacketSummary) -> str:
        """Use DNS modality only when the packet actually carries DNS fields."""
        return "dns_packet" if _is_dns_summary(summary) else "network_packet"


class HostPacketCaptureParser(PacketCaptureParser):
    """Packet capture parser configured for Host validation packet sources."""

    parser_name = "host_packet_capture_parser"
    default_modality = "host_network_packet"


def _iter_capture_records(
    path: Path,
    *,
    reader: UniversalInputReader | None = None,
) -> Iterator[PacketRecord]:
    input_reader = reader or UniversalInputReader(path)
    binary_type = input_reader.detect_binary_type()
    with input_reader.open_binary() as stream:
        if binary_type == "pcap":
            yield from _iter_pcap_records_stream(stream)
            return
        if binary_type == "pcapng":
            yield from _iter_pcapng_records_stream(stream)
            return
        raise ValueError(f"unsupported packet capture binary type: {binary_type}")


def _iter_pcap_records(data: bytes) -> Iterator[PacketRecord]:
    if len(data) < 24:
        raise ValueError("truncated PCAP global header")
    if data[:4] not in PCAP_MAGIC_ENDIAN:
        raise ValueError("unsupported PCAP magic")
    endian, timestamp_scale = PCAP_MAGIC_ENDIAN[data[:4]]
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


def _iter_pcap_records_stream(stream: BinaryIO) -> Iterator[PacketRecord]:
    header = _read_exact_or_eof(stream, 24)
    if header is None:
        raise ValueError("truncated PCAP global header")
    if header[:4] not in PCAP_MAGIC_ENDIAN:
        raise ValueError("unsupported PCAP magic")
    endian, timestamp_scale = PCAP_MAGIC_ENDIAN[header[:4]]
    linktype = struct.unpack(f"{endian}I", header[20:24])[0]
    while True:
        record_header = _read_exact_or_eof(stream, 16)
        if record_header is None:
            break
        ts_sec, ts_frac, captured_len, original_len = struct.unpack(f"{endian}IIII", record_header)
        if captured_len > MAX_CAPTURED_PACKET_BYTES:
            raise ValueError(f"PCAP packet payload is too large: {captured_len} bytes")
        payload = _read_exact(stream, captured_len, "truncated PCAP packet payload")
        timestamp = datetime.fromtimestamp(ts_sec + (ts_frac / timestamp_scale), tz=timezone.utc)
        yield PacketRecord(timestamp, captured_len, original_len, linktype, payload)


def _iter_pcapng_records(data: bytes) -> Iterator[PacketRecord]:
    offset = 0
    endian = "<"
    linktypes: dict[int, int] = {}
    while offset + 12 <= len(data):
        block_type, block_total_length, endian = _pcapng_block_header(data, offset, endian)
        if block_total_length < 12 or offset + block_total_length > len(data):
            break
        body = data[offset + 8 : offset + block_total_length - 4]
        if block_type == PCAPNG_INTERFACE_DESCRIPTION and len(body) >= 8:
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


def _iter_pcapng_records_stream(stream: BinaryIO) -> Iterator[PacketRecord]:
    endian = "<"
    linktypes: dict[int, int] = {}
    while True:
        header = stream.read(8)
        if not header:
            break
        if len(header) != 8:
            raise ValueError("truncated PCAPNG block header")
        little_type, little_length = struct.unpack("<II", header)
        if little_type == PCAPNG_SECTION_HEADER:
            byte_order_magic = _read_exact(stream, 4, "truncated PCAPNG section header")
            if byte_order_magic == b"\x4d\x3c\x2b\x1a":
                endian = "<"
                block_type = little_type
                block_total_length = little_length
            elif byte_order_magic == b"\x1a\x2b\x3c\x4d":
                endian = ">"
                block_type, block_total_length = struct.unpack(">II", header)
            else:
                raise ValueError("unsupported PCAPNG byte order magic")
            if block_total_length < 12:
                raise ValueError("invalid PCAPNG block length")
            rest = _read_exact(
                stream,
                block_total_length - 12,
                "truncated PCAPNG section block",
            )
            body = byte_order_magic + rest[:-4]
        else:
            block_type, block_total_length = struct.unpack(f"{endian}II", header)
            if block_total_length < 12:
                raise ValueError("invalid PCAPNG block length")
            rest = _read_exact(stream, block_total_length - 8, "truncated PCAPNG block")
            body = rest[:-4]

        if block_type == PCAPNG_INTERFACE_DESCRIPTION and len(body) >= 8:
            interface_id = len(linktypes)
            linktypes[interface_id] = struct.unpack(f"{endian}H", body[:2])[0]
        elif block_type == PCAPNG_ENHANCED_PACKET and len(body) >= 20:
            interface_id, ts_high, ts_low, captured_len, original_len = struct.unpack(
                f"{endian}IIIII",
                body[:20],
            )
            if captured_len > MAX_CAPTURED_PACKET_BYTES:
                raise ValueError(f"PCAPNG packet payload is too large: {captured_len} bytes")
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


def _pcapng_block_header(data: bytes, offset: int, current_endian: str) -> tuple[int, int, str]:
    little_type, little_length = struct.unpack("<II", data[offset : offset + 8])
    if little_type == PCAPNG_SECTION_HEADER and offset + 12 <= len(data):
        byte_order_magic = data[offset + 8 : offset + 12]
        if byte_order_magic == b"\x4d\x3c\x2b\x1a":
            return little_type, little_length, "<"
        if byte_order_magic == b"\x1a\x2b\x3c\x4d":
            big_type, big_length = struct.unpack(">II", data[offset : offset + 8])
            return big_type, big_length, ">"
    block_type, block_total_length = struct.unpack(f"{current_endian}II", data[offset : offset + 8])
    return block_type, block_total_length, current_endian


def _summarize_packet(record: PacketRecord) -> PacketSummary:
    packet = record.payload
    metadata: dict[str, Any] = {"linktype": record.linktype}
    if record.linktype == LINKTYPE_ETHERNET:
        if len(packet) < 14:
            return _empty_summary(record, metadata)
        ethertype = struct.unpack("!H", packet[12:14])[0]
        vlan_layers = 0
        packet = packet[14:]
        while ethertype in {ETHERTYPE_VLAN, ETHERTYPE_QINQ} and len(packet) >= 4:
            vlan_layers += 1
            ethertype = struct.unpack("!H", packet[2:4])[0]
            packet = packet[4:]
        metadata["ethertype"] = f"0x{ethertype:04x}"
        if vlan_layers:
            metadata["vlan_layers"] = vlan_layers
        if ethertype not in {ETHERTYPE_IPV4, ETHERTYPE_IPV6}:
            return _empty_summary(record, metadata)
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
    if header_len < 20 or header_len > len(packet):
        return _empty_summary(record, metadata)
    protocol_number = packet[9]
    flags_fragment = struct.unpack("!H", packet[6:8])[0]
    fragment_offset = flags_fragment & 0x1FFF
    more_fragments = bool(flags_fragment & 0x2000)
    src_ip = str(ipaddress.ip_address(packet[12:16]))
    dst_ip = str(ipaddress.ip_address(packet[16:20]))
    if fragment_offset or more_fragments:
        metadata["fragmented"] = True
        metadata["fragment_offset"] = fragment_offset
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
        if DNS_PORT in (src_port, dst_port):
            dns_payload = _tcp_dns_payload(application)
            dns = _parse_dns(dns_payload) if dns_payload else {}
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
        ttl=dns.get("ttl"),
        rcode=dns.get("rcode"),
        metadata={**metadata, **dns},
    )


def _tcp_dns_payload(application: bytes) -> bytes | None:
    if len(application) < 2:
        return None
    dns_length = struct.unpack("!H", application[:2])[0]
    if 0 < dns_length <= len(application) - 2:
        return application[2 : 2 + dns_length]
    return application if len(application) >= 12 else None


def _parse_dns(payload: bytes) -> dict[str, Any]:
    if len(payload) < 12:
        return {}
    dns_id, flags, qdcount, ancount, nscount, arcount = struct.unpack("!HHHHHH", payload[:12])
    result: dict[str, Any] = {
        "dns_id": dns_id,
        "dns_is_response": bool(flags & 0x8000),
        "dns_qdcount": qdcount,
        "dns_ancount": ancount,
        "dns_nscount": nscount,
        "dns_arcount": arcount,
        "rcode": str(flags & 0x000F),
    }
    offset = 12
    for question_index in range(qdcount):
        name, offset = _read_dns_name(payload, offset)
        if name and question_index == 0:
            result["query_domain"] = name
        if offset + 4 > len(payload):
            return result
        qtype, qclass = struct.unpack("!HH", payload[offset : offset + 4])
        offset += 4
        if question_index == 0:
            result["qtype"] = str(qtype)
            result["qclass"] = str(qclass)
    for answer_index in range(ancount):
        answer_name, offset = _read_dns_name(payload, offset)
        if offset + 10 > len(payload):
            return result
        rr_type, rr_class, ttl, rdlength = struct.unpack("!HHIH", payload[offset : offset + 10])
        offset += 10
        if answer_index == 0:
            result.setdefault("query_domain", answer_name)
            result["answer_type"] = str(rr_type)
            result["answer_class"] = str(rr_class)
            result["ttl"] = ttl
        offset += rdlength
        if offset > len(payload):
            return result
    return result


def _read_dns_name(payload: bytes, offset: int, *, depth: int = 0) -> tuple[str | None, int]:
    if depth > 8:
        return None, offset
    labels: list[str] = []
    current_offset = offset
    next_offset = offset
    jumped = False
    while current_offset < len(payload):
        length = payload[current_offset]
        current_offset += 1
        if length == 0:
            if not jumped:
                next_offset = current_offset
            return ".".join(labels) if labels else None, next_offset
        if length & 0xC0 == 0xC0:
            if current_offset >= len(payload):
                return ".".join(labels) if labels else None, len(payload)
            pointer = ((length & 0x3F) << 8) | payload[current_offset]
            current_offset += 1
            if not jumped:
                next_offset = current_offset
            pointed_name, _ = _read_dns_name(payload, pointer, depth=depth + 1)
            if pointed_name:
                labels.append(pointed_name)
            return ".".join(labels) if labels else None, next_offset
        if length & 0xC0:
            return ".".join(labels) if labels else None, current_offset
        if current_offset + length > len(payload):
            return ".".join(labels) if labels else None, len(payload)
        labels.append(payload[current_offset : current_offset + length].decode("utf-8", errors="replace"))
        current_offset += length
        if not jumped:
            next_offset = current_offset
    return ".".join(labels) if labels else None, next_offset


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
        ttl=None,
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


def _packet_event_type(summary: PacketSummary) -> str:
    if _is_dns_summary(summary):
        return "dns_response" if summary.metadata.get("dns_is_response") else "dns_query"
    return "network_packet_summary"


def _is_dns_summary(summary: PacketSummary) -> bool:
    return (
        summary.domain is not None
        or summary.qtype is not None
        or summary.rcode is not None
        or DNS_PORT in {summary.src_port, summary.dst_port}
    )


def _event_uid(context: ParserContext, index: int, entity_id: Any) -> str:
    raw = f"{context.source_file_path}:{index}:{entity_id or ''}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()


def _normalize_packet_mode(value: str | None) -> str:
    mode = (value or "packet-summary").strip().lower()
    if mode not in {"packet-summary", "dns-only", "sample"}:
        raise ValueError("packet_mode must be one of: packet-summary, dns-only, sample")
    return mode


def _read_exact(stream: BinaryIO, size: int, error_message: str) -> bytes:
    data = stream.read(size)
    if len(data) != size:
        raise ValueError(error_message)
    return data


def _read_exact_or_eof(stream: BinaryIO, size: int) -> bytes | None:
    data = stream.read(size)
    if not data:
        return None
    if len(data) != size:
        raise ValueError("truncated packet capture record header")
    return data


def _exception_message(exc: BaseException) -> str:
    message = str(exc).strip()
    return message or type(exc).__name__
