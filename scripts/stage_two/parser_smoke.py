"""Direct parser smoke runner for Stage Two parser groups.

The runner builds tiny synthetic files in a temporary directory and invokes
parser classes directly. It intentionally avoids PostgreSQL, catalog ingestion,
Parquet writers, and real raw datasets.
"""

from __future__ import annotations

import json
import struct
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.stage_two.labels import LabelResolver, UnlabeledLabelResolver
from scripts.stage_two.parsers import (
    DnsCsvParser,
    DnsPacketCaptureParser,
    DnsPcapCsvParser,
    DnsTxtDomainListParser,
    HostBsonSandboxParser,
    HostCsvParser,
    HostJsonLinesParser,
    HostLineLogParser,
    HostMetricbeatParser,
    HostNetflowParser,
    HostPacketCaptureParser,
    HostSyscallTraceParser,
    HostXmlParser,
    ParserContext,
    ParserResult,
)
from scripts.stage_two.parsers.base import REQUIRED_NORMALIZED_FIELDS


EXPECTED_PARSER_SMOKE_GROUPS: tuple[str, ...] = (
    "dns_csv",
    "dns_pcap_csv",
    "dns_txt",
    "packet_capture_pcap",
    "packet_capture_cap",
    "packet_capture_pcapng",
    "host_csv",
    "host_json",
    "host_line_log",
    "host_metrics",
    "host_syscall_trace",
    "host_bson",
    "host_netflow_day",
    "host_netflow_ids",
    "host_wls_day",
    "host_xml",
)


@dataclass(frozen=True)
class ParserSmokeSummary:
    """Compact result for one direct parser smoke."""

    group: str
    parser_name: str
    branch: str
    source_format: str
    rows_read: int
    rows_parsed: int
    rows_failed: int
    parser_run_status: str
    file_status: str

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable summary."""
        return asdict(self)


class ParserSmokeError(RuntimeError):
    """Raised when a direct parser smoke violates the normalized contract."""


def run_parser_smokes() -> list[ParserSmokeSummary]:
    """Run all direct parser smokes and return compact summaries."""
    with tempfile.TemporaryDirectory(prefix="stage-two-parser-smoke-") as directory:
        root = Path(directory)
        return [
            _smoke_dns_csv(root),
            _smoke_dns_pcap_csv(root),
            _smoke_dns_txt(root),
            _smoke_packet_pcap(root),
            _smoke_packet_cap(root),
            _smoke_packet_pcapng(root),
            _smoke_host_csv(root),
            _smoke_host_json(root),
            _smoke_host_line_log(root),
            _smoke_host_metrics(root),
            _smoke_host_syscall_trace(root),
            _smoke_host_bson(root),
            _smoke_host_netflow_day(root),
            _smoke_host_netflow_ids(root),
            _smoke_host_wls_day(root),
            _smoke_host_xml(root),
        ]


def _smoke_dns_csv(root: Path) -> ParserSmokeSummary:
    path = _write_text(root, "dns/sample.csv", "Domain,TTL,custom_col\nexample.org,60,kept\n")
    context = _context(path, branch="dns", source_format="csv", role="TRAIN")
    result = DnsCsvParser(UnlabeledLabelResolver()).parse(path, context)
    _validate_result("dns_csv", result, expected_file_status="PARSED")
    event = _first_event("dns_csv", result)
    _check(event["query_domain"] == "example.org", "dns_csv did not preserve query_domain")
    _check(event["timestamp_type"] == "event_order", "dns_csv timestamp_type should be event_order")
    _check(event["raw_fields_json"]["custom_col"] == "kept", "dns_csv did not preserve raw custom column")
    return _summary("dns_csv", result, context)


def _smoke_dns_pcap_csv(root: Path) -> ParserSmokeSummary:
    content = (
        "frame.time_epoch,ip.src,ip.dst,udp.srcport,udp.dstport,_ws.col.Protocol,"
        "dns.qry.name,dns.qry.type,dns.qry.class,dns.flags.rcode,dns.resp.ttl,frame.len,custom_col\n"
        "1704067200,10.0.0.1,8.8.8.8,53000,53,DNS,example.org,A,IN,,,86,kept\n"
        ",,,,,,,,,,,,bad-only\n"
    )
    path = _write_text(root, "dns/sample.pcap.csv", content)
    context = _context(path, branch="dns", source_format="pcap.csv", role="VALIDATION")
    result = DnsPcapCsvParser(UnlabeledLabelResolver()).parse(path, context)
    _validate_result(
        "dns_pcap_csv",
        result,
        expected_file_status="PARTIALLY_PARSED",
        expected_rows_failed=1,
    )
    event = _first_event("dns_pcap_csv", result)
    _check(event["event_type"] == "dns_query", "dns_pcap_csv event_type should be dns_query")
    _check(event["timestamp_type"] == "absolute", "dns_pcap_csv timestamp_type should be absolute")
    _check(event["raw_fields_json"]["custom_col"] == "kept", "dns_pcap_csv did not preserve raw custom column")
    return _summary("dns_pcap_csv", result, context)


def _smoke_dns_txt(root: Path) -> ParserSmokeSummary:
    path = _write_text(root, "dns/domains.txt", "example.org\n")
    context = _context(path, branch="dns", source_format="txt", role="VALIDATION")
    result = DnsTxtDomainListParser(UnlabeledLabelResolver()).parse(path, context)
    _validate_result("dns_txt", result, expected_file_status="PARSED")
    event = _first_event("dns_txt", result)
    _check(event["event_index"] == 0, "dns_txt event_index should be 0")
    _check(event["timestamp_type"] == "event_order", "dns_txt timestamp_type should be event_order")
    _check(event["raw_fields_json"]["line_number"] == 1, "dns_txt raw_fields_json lost line_number")
    return _summary("dns_txt", result, context)


def _smoke_packet_pcap(root: Path) -> ParserSmokeSummary:
    packet = _ethernet_ipv4_udp_packet(
        src_ip="10.0.0.1",
        dst_ip="8.8.8.8",
        src_port=53000,
        dst_port=53,
        payload=_dns_query("pcap.example"),
    )
    path = _write_bytes(root, "packet/dns-smoke.pcap", _pcap_file([packet]))
    context = _context(path, branch="dns", source_format="pcap", role="VALIDATION")
    result = DnsPacketCaptureParser(UnlabeledLabelResolver()).parse(path, context)
    _validate_result("packet_capture_pcap", result, expected_file_status="PARSED")
    event = _first_event("packet_capture_pcap", result)
    _check(event["modality"] == "dns_packet", "packet_capture_pcap modality should be dns_packet")
    _check(event["query_domain"] == "pcap.example", "packet_capture_pcap lost DNS qname")
    _check("payload" not in event["raw_fields_json"], "packet_capture_pcap must not store payload")
    return _summary("packet_capture_pcap", result, context)


def _smoke_packet_cap(root: Path) -> ParserSmokeSummary:
    packet = _ethernet_ipv4_udp_packet(
        src_ip="10.1.1.10",
        dst_ip="10.1.1.53",
        src_port=40000,
        dst_port=53,
        payload=_dns_query("cap.example"),
    )
    path = _write_bytes(root, "packet/host-smoke.cap", _pcap_file([packet]))
    context = _context(path, branch="host", source_format="cap", role="VALIDATION")
    result = HostPacketCaptureParser(UnlabeledLabelResolver()).parse(path, context)
    _validate_result("packet_capture_cap", result, expected_file_status="PARSED")
    event = _first_event("packet_capture_cap", result)
    _check(event["modality"] == "host_network_packet", "packet_capture_cap modality should be host_network_packet")
    _check(event["query_domain"] == "cap.example", "packet_capture_cap lost DNS qname")
    return _summary("packet_capture_cap", result, context)


def _smoke_packet_pcapng(root: Path) -> ParserSmokeSummary:
    packet = _ethernet_ipv4_tcp_packet(
        src_ip="192.0.2.10",
        dst_ip="198.51.100.20",
        src_port=49152,
        dst_port=443,
        flags=0x02,
    )
    path = _write_bytes(root, "packet/host-smoke.pcapng", _pcapng_file(packet))
    context = _context(path, branch="host", source_format="pcapng", role="VALIDATION")
    result = HostPacketCaptureParser(UnlabeledLabelResolver()).parse(path, context)
    _validate_result("packet_capture_pcapng", result, expected_file_status="PARSED")
    event = _first_event("packet_capture_pcapng", result)
    _check(event["protocol"] == "TCP", "packet_capture_pcapng protocol should be TCP")
    _check(event["raw_fields_json"]["tcp_flags"] == "SYN", "packet_capture_pcapng lost tcp flags")
    return _summary("packet_capture_pcapng", result, context)


def _smoke_host_csv(root: Path) -> ParserSmokeSummary:
    content = (
        "date,time,process_id,path,sys_call,event_id,attack_cat,attack_subcat,label\n"
        "31/03/2016,2:45:01,1830,/usr/bin/python3.4,142,45354,normal,normal,0\n"
    )
    path = _write_text(root, "host/events.csv", content)
    context = _context(path, branch="host", source_format="csv", role="TRAIN")
    result = HostCsvParser(LabelResolver(config_path=None, enable_filename_heuristics=False)).parse(path, context)
    _validate_result("host_csv", result, expected_file_status="PARSED")
    event = _first_event("host_csv", result)
    _check(event["event_type"] == "host_syscall", "host_csv event_type should be host_syscall")
    _check(event["timestamp_type"] == "absolute", "host_csv timestamp_type should be absolute")
    _check(event["raw_fields_json"]["_csv_schema"] == "adfa_9_column", "host_csv lost CSV schema marker")
    return _summary("host_csv", result, context)


def _smoke_host_json(root: Path) -> ParserSmokeSummary:
    row = {
        "@timestamp": "2024-01-01T00:00:00Z",
        "host": {"name": "host-a"},
        "process": {"pid": 123, "name": "bash"},
        "event": {"dataset": "process", "action": "exec"},
        "message": "process started",
    }
    path = _write_text(root, "host/events.json", json.dumps(row) + "\n")
    context = _context(path, branch="host", source_format="json", role="TRAIN")
    result = HostJsonLinesParser(LabelResolver(config_path=None, enable_filename_heuristics=False)).parse(path, context)
    _validate_result("host_json", result, expected_file_status="PARSED")
    event = _first_event("host_json", result)
    _check(event["event_type"] == "exec", "host_json event_type should be exec")
    _check(event["timestamp_type"] == "absolute", "host_json timestamp_type should be absolute")
    _check(event["raw_fields_json"]["host.name"] == "host-a", "host_json lost flattened raw field")
    return _summary("host_json", result, context)


def _smoke_host_line_log(root: Path) -> ParserSmokeSummary:
    line = "Jan 12 08:15:30 web01 sshd[1234]: Accepted password for alice from 10.0.0.5 port 54421 ssh2"
    path = _write_text(root, "host/auth.log", line + "\n")
    context = _context(path, branch="host", source_format="auth.log", role="TRAIN")
    result = HostLineLogParser(LabelResolver(config_path=None, enable_filename_heuristics=False)).parse(path, context)
    _validate_result("host_line_log", result, expected_file_status="PARSED")
    event = _first_event("host_line_log", result)
    _check(event["event_index"] == 0, "host_line_log event_index should be 0")
    _check(event["timestamp_type"] == "event_order", "host_line_log timestamp_type should be event_order")
    _check("_raw_line_sha256" in event["raw_fields_json"], "host_line_log lost raw line hash")
    return _summary("host_line_log", result, context)


def _smoke_host_metrics(root: Path) -> ParserSmokeSummary:
    row = {
        "@timestamp": "2024-01-01T00:00:00Z",
        "host": {"name": "host-a"},
        "event": {"dataset": "system.cpu"},
        "metric_name": "system.cpu.total.norm.pct",
        "metric_value": 0.42,
    }
    path = _write_text(root, "host/cpu.log", json.dumps(row) + "\n")
    context = _context(path, branch="host", source_format="cpu.log", role="TRAIN")
    result = HostMetricbeatParser(LabelResolver(config_path=None, enable_filename_heuristics=False)).parse(path, context)
    _validate_result("host_metrics", result, expected_file_status="PARSED")
    event = _first_event("host_metrics", result)
    _check(event["modality"] == "host_metric", "host_metrics modality should be host_metric")
    _check(event["metric_value"] == 0.42, "host_metrics lost metric value")
    _check(event["raw_fields_json"]["metric_value"] == 0.42, "host_metrics lost raw metric value")
    return _summary("host_metrics", result, context)


def _smoke_host_syscall_trace(root: Path) -> ParserSmokeSummary:
    line = 'pid=1337 uid=1000 openat(AT_FDCWD, "/tmp/a", O_RDONLY) = 3'
    path = _write_text(root, "host/trace.ghc", line + "\n")
    context = _context(path, branch="host", source_format="ghc", role="TRAIN")
    result = HostSyscallTraceParser(LabelResolver(config_path=None, enable_filename_heuristics=False)).parse(path, context)
    _validate_result("host_syscall_trace", result, expected_file_status="PARSED")
    event = _first_event("host_syscall_trace", result)
    _check(event["event_index"] == 0, "host_syscall_trace event_index should be 0")
    _check(event["timestamp_type"] == "event_order", "host_syscall_trace timestamp_type should be event_order")
    _check(event["raw_fields_json"]["arguments"] == 'AT_FDCWD, "/tmp/a", O_RDONLY', "host_syscall_trace lost arguments")
    return _summary("host_syscall_trace", result, context)


def _smoke_host_bson(root: Path) -> ParserSmokeSummary:
    stream = _bson_stream(
        {
            "I": 1001,
            "name": "CreateFileW",
            "type": "api",
            "category": "file",
            "args": [{"name": "path"}, {"name": "desired_access"}],
        },
        {
            "I": 1001,
            "T": 44,
            "t": 12.5,
            "h": 7,
            "pid": 1337,
            "process_name": "sample.exe",
            "args": [r"C:\tmp\a.dll", "GENERIC_READ"],
        },
    )
    path = _write_bytes(root, "host/sample.bson", stream)
    context = _context(path, branch="host", source_format="bson", role="TEST")
    result = HostBsonSandboxParser(LabelResolver(config_path=None, enable_filename_heuristics=False)).parse(path, context)
    _validate_result("host_bson", result, expected_file_status="PARSED", expected_rows_read=2)
    event = _first_event("host_bson", result)
    _check(event["timestamp_type"] == "relative", "host_bson timestamp_type should be relative")
    _check(event["event_index"] == 0, "host_bson event_index should be 0")
    _check(event["raw_fields_json"]["mapped_arguments"]["path"] == r"C:\tmp\a.dll", "host_bson lost mapped arguments")
    return _summary("host_bson", result, context)


def _smoke_host_netflow_day(root: Path) -> ParserSmokeSummary:
    path = _write_text(
        root,
        "host/netflow_day",
        "1,2,Comp1,Comp2,6,Port12345,Port80,10,20,1000,2000\n",
    )
    context = _context(path, branch="host", source_format="netflow_day", role="VALIDATION")
    result = HostNetflowParser(LabelResolver(config_path=None, enable_filename_heuristics=False)).parse(path, context)
    _validate_result("host_netflow_day", result, expected_file_status="PARSED")
    event = _first_event("host_netflow_day", result)
    _check(event["modality"] == "network_flow", "host_netflow_day modality should be network_flow")
    _check(event["timestamp_type"] == "relative", "host_netflow_day timestamp_type should be relative")
    _check(event["features_json"]["bytes"] == 3000.0, "host_netflow_day lost byte features")
    return _summary("host_netflow_day", result, context)


def _smoke_host_netflow_ids(root: Path) -> ParserSmokeSummary:
    row = {
        "timestamp": "2024-01-01T00:00:01Z",
        "event_type": "alert",
        "src_ip": "10.0.0.10",
        "src_port": 51515,
        "dest_ip": "10.0.0.20",
        "dest_port": 80,
        "proto": "TCP",
        "flow": {
            "bytes_toserver": 100,
            "bytes_toclient": 200,
            "pkts_toserver": 2,
            "pkts_toclient": 3,
        },
        "alert": {"category": "Attempted Administrator Privilege Gain", "signature": "Test IDS alert"},
    }
    path = _write_text(root, "host/netflow_ids", json.dumps(row) + "\n")
    context = _context(path, branch="host", source_format="netflow_ids", role="VALIDATION")
    result = HostNetflowParser(LabelResolver(config_path=None, enable_filename_heuristics=False)).parse(path, context)
    _validate_result("host_netflow_ids", result, expected_file_status="PARSED")
    event = _first_event("host_netflow_ids", result)
    _check(event["event_type"] == "ids_alert", "host_netflow_ids event_type should be ids_alert")
    _check(event["timestamp_type"] == "absolute", "host_netflow_ids timestamp_type should be absolute")
    _check(event["metadata_json"]["alert_signature"] == "Test IDS alert", "host_netflow_ids lost alert metadata")
    return _summary("host_netflow_ids", result, context)


def _smoke_host_wls_day(root: Path) -> ParserSmokeSummary:
    row = {
        "EventID": 4624,
        "UserName": "alice",
        "LogHost": "host01",
        "Source": "Microsoft-Windows-Security-Auditing",
        "Time": 42,
        "DomainName": "EXAMPLE",
        "LogonID": "0x123",
        "ProcessName": "lsass.exe",
    }
    path = _write_text(root, "host/wls_day", json.dumps(row) + "\n")
    context = _context(path, branch="host", source_format="wls_day", role="VALIDATION")
    result = HostNetflowParser(LabelResolver(config_path=None, enable_filename_heuristics=False)).parse(path, context)
    _validate_result("host_wls_day", result, expected_file_status="PARSED")
    event = _first_event("host_wls_day", result)
    _check(event["modality"] == "host_eventlog", "host_wls_day modality should be host_eventlog")
    _check(event["event_type"] == "windows_event_4624", "host_wls_day event_type should be windows_event_4624")
    _check(event["metadata_json"]["logon_id"] == "0x123", "host_wls_day lost logon metadata")
    return _summary("host_wls_day", result, context)


def _smoke_host_xml(root: Path) -> ParserSmokeSummary:
    path = _write_text(
        root,
        "host/events.xml",
        """<?xml version="1.0" encoding="utf-8"?>
<Events>
  <Event>
    <Timestamp>2024-01-01T00:00:00Z</Timestamp>
    <Host>host-a</Host>
    <ProcessName>sshd</ProcessName>
    <EventID>1001</EventID>
    <UserName>alice</UserName>
    <Message>login accepted</Message>
  </Event>
</Events>
""",
    )
    context = _context(path, branch="host", source_format="xml", role="TRAIN")
    result = HostXmlParser(LabelResolver(config_path=None, enable_filename_heuristics=False)).parse(path, context)
    _validate_result("host_xml", result, expected_file_status="PARSED")
    event = _first_event("host_xml", result)
    _check(event["timestamp_type"] == "absolute", "host_xml timestamp_type should be absolute")
    _check(event["event_type"] == "host_xml_event_1001", "host_xml event_type should be host_xml_event_1001")
    _check(event["raw_fields_json"]["Message"] == "login accepted", "host_xml lost raw Message")
    return _summary("host_xml", result, context)


def _validate_result(
    group: str,
    result: ParserResult,
    *,
    expected_file_status: str,
    expected_rows_failed: int = 0,
    expected_rows_read: int | None = None,
) -> None:
    _check(result.rows_read > 0, f"{group} rows_read must be positive")
    if expected_rows_read is not None:
        _check(result.rows_read == expected_rows_read, f"{group} rows_read mismatch: {result.rows_read}")
    _check(result.rows_parsed == len(result.events), f"{group} rows_parsed must equal emitted events")
    _check(result.rows_parsed > 0, f"{group} must emit at least one event")
    _check(result.rows_failed == expected_rows_failed, f"{group} rows_failed mismatch: {result.rows_failed}")
    _check(result.file_status == expected_file_status, f"{group} file_status mismatch: {result.file_status}")
    _check(result.parser_run_status in {"SUCCESS", "PARTIAL_SUCCESS"}, f"{group} parser status is not successful")
    for index, event in enumerate(result.events):
        missing = REQUIRED_NORMALIZED_FIELDS.difference(event)
        _check(not missing, f"{group} event {index} missing fields: {sorted(missing)}")
        _check(isinstance(event.get("event_index"), int), f"{group} event {index} has no integer event_index")
        _check(event.get("timestamp_type") in {"absolute", "event_order", "relative"}, f"{group} bad timestamp_type")
        _check(isinstance(event.get("raw_fields_json"), dict), f"{group} event {index} raw_fields_json must be dict")
        _check(event["raw_fields_json"], f"{group} event {index} raw_fields_json must not be empty")


def _first_event(group: str, result: ParserResult) -> dict[str, Any]:
    _check(bool(result.events), f"{group} emitted no events")
    return result.events[0]


def _summary(group: str, result: ParserResult, context: ParserContext) -> ParserSmokeSummary:
    parser_name = result.events[0]["parser_name"] if result.events else "unknown"
    return ParserSmokeSummary(
        group=group,
        parser_name=str(parser_name),
        branch=context.branch,
        source_format=context.source_format,
        rows_read=result.rows_read,
        rows_parsed=result.rows_parsed,
        rows_failed=result.rows_failed,
        parser_run_status=result.parser_run_status,
        file_status=result.file_status,
    )


def _context(
    path: Path,
    *,
    branch: str,
    source_format: str,
    role: str,
) -> ParserContext:
    return ParserContext(
        dataset_id=1,
        file_id=2,
        dataset_name=f"{branch}-{source_format}-smoke",
        dataset_role=role,
        branch=branch,
        source_format=source_format,
        source_file_path=str(path),
        source_file_hash="smoke-hash",
        parser_run_id=3,
        metadata={"scenario_name": "parser-smoke"},
    )


def _write_text(root: Path, relative_path: str, content: str) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_bytes(root: Path, relative_path: str, content: bytes) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise ParserSmokeError(message)


def _pcap_file(packets: list[bytes]) -> bytes:
    header = struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)
    records = []
    for index, packet in enumerate(packets):
        records.append(struct.pack("<IIII", 1_704_067_200 + index, 123456, len(packet), len(packet)))
        records.append(packet)
    return header + b"".join(records)


def _pcapng_file(packet: bytes) -> bytes:
    section_body = struct.pack("<IHHq", 0x1A2B3C4D, 1, 0, -1)
    interface_body = struct.pack("<HHI", 1, 0, 65535)
    timestamp = 1_704_067_200_123456
    enhanced_body = (
        struct.pack(
            "<IIIII",
            0,
            timestamp >> 32,
            timestamp & 0xFFFFFFFF,
            len(packet),
            len(packet),
        )
        + _pad32(packet)
    )
    return (
        _pcapng_block(0x0A0D0D0A, section_body)
        + _pcapng_block(0x00000001, interface_body)
        + _pcapng_block(0x00000006, enhanced_body)
    )


def _pcapng_block(block_type: int, body: bytes) -> bytes:
    total_length = 12 + len(body)
    return struct.pack("<II", block_type, total_length) + body + struct.pack("<I", total_length)


def _pad32(payload: bytes) -> bytes:
    padding = (-len(payload)) % 4
    return payload + (b"\x00" * padding)


def _ethernet_ipv4_udp_packet(
    *,
    src_ip: str,
    dst_ip: str,
    src_port: int,
    dst_port: int,
    payload: bytes,
) -> bytes:
    udp_length = 8 + len(payload)
    udp_header = struct.pack("!HHHH", src_port, dst_port, udp_length, 0)
    return _ethernet_ipv4_packet(src_ip=src_ip, dst_ip=dst_ip, protocol=17, transport=udp_header + payload)


def _ethernet_ipv4_tcp_packet(
    *,
    src_ip: str,
    dst_ip: str,
    src_port: int,
    dst_port: int,
    flags: int,
) -> bytes:
    tcp_header = struct.pack("!HHIIBBHHH", src_port, dst_port, 0, 0, 5 << 4, flags, 8192, 0, 0)
    return _ethernet_ipv4_packet(src_ip=src_ip, dst_ip=dst_ip, protocol=6, transport=tcp_header)


def _ethernet_ipv4_packet(*, src_ip: str, dst_ip: str, protocol: int, transport: bytes) -> bytes:
    ethernet = b"\xaa\xbb\xcc\xdd\xee\xff" + b"\x11\x22\x33\x44\x55\x66" + struct.pack("!H", 0x0800)
    total_length = 20 + len(transport)
    ipv4_header = struct.pack(
        "!BBHHHBBH4s4s",
        0x45,
        0,
        total_length,
        0,
        0,
        64,
        protocol,
        0,
        _ipv4_bytes(src_ip),
        _ipv4_bytes(dst_ip),
    )
    return ethernet + ipv4_header + transport


def _ipv4_bytes(value: str) -> bytes:
    return bytes(int(part) for part in value.split("."))


def _dns_query(domain: str) -> bytes:
    question = _dns_name(domain) + struct.pack("!HH", 1, 1)
    return struct.pack("!HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0) + question


def _dns_name(domain: str) -> bytes:
    labels = domain.split(".")
    return b"".join(bytes([len(label)]) + label.encode("ascii") for label in labels) + b"\x00"


def _bson_stream(*documents: dict[str, Any]) -> bytes:
    return b"".join(_encode_bson_document(document) for document in documents)


def _encode_bson_document(document: dict[str, Any]) -> bytes:
    body = b"".join(_encode_bson_element(key, value) for key, value in document.items()) + b"\x00"
    return struct.pack("<i", len(body) + 4) + body


def _encode_bson_element(key: str, value: Any) -> bytes:
    key_bytes = key.encode("utf-8") + b"\x00"
    if value is None:
        return b"\x0A" + key_bytes
    if isinstance(value, bool):
        return b"\x08" + key_bytes + (b"\x01" if value else b"\x00")
    if isinstance(value, int):
        if -(2**31) <= value < 2**31:
            return b"\x10" + key_bytes + struct.pack("<i", value)
        return b"\x12" + key_bytes + struct.pack("<q", value)
    if isinstance(value, float):
        return b"\x01" + key_bytes + struct.pack("<d", value)
    if isinstance(value, str):
        encoded = value.encode("utf-8") + b"\x00"
        return b"\x02" + key_bytes + struct.pack("<i", len(encoded)) + encoded
    if isinstance(value, dict):
        return b"\x03" + key_bytes + _encode_bson_document(value)
    if isinstance(value, list):
        return b"\x04" + key_bytes + _encode_bson_document({str(index): item for index, item in enumerate(value)})
    if isinstance(value, bytes):
        return b"\x05" + key_bytes + struct.pack("<i", len(value)) + b"\x00" + value
    raise TypeError(f"unsupported BSON smoke value: {value!r}")


def main() -> int:
    """Run parser smokes from the command line."""
    try:
        summaries = run_parser_smokes()
    except ParserSmokeError as exc:
        print(f"parser smoke failed: {exc}", file=sys.stderr)
        return 1

    for summary in summaries:
        print(json.dumps(summary.as_dict(), sort_keys=True))
    print(f"parser smokes passed: {len(summaries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
