"""Encoded/compressed input smokes for Stage Two parsers and reader.

The smoke runner creates synthetic files in a temporary directory, parses them
through UniversalInputReader-backed parser classes, and verifies that raw input
bytes are not modified.
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import struct
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator

import scripts.stage_two.parsers.input_reader as input_reader_module
from scripts.stage_two.labels import LabelResolver, UnlabeledLabelResolver
from scripts.stage_two.parsers import (
    DnsCsvParser,
    DnsPacketCaptureParser,
    DnsPcapCsvParser,
    HostBsonSandboxParser,
    HostCsvParser,
    HostJsonLinesParser,
    HostLineLogParser,
    HostNetflowParser,
    ParserContext,
    ParserResult,
    UniversalInputReader,
)


EXPECTED_INPUT_SMOKE_CASES: tuple[str, ...] = (
    "base64_csv",
    "base64_json_lines",
    "base64_raw_log_line",
    "base64_bson_bytes",
    "base64_pcap_bytes",
    "utf8_csv",
    "utf8_sig_csv",
    "cp1252_csv",
    "latin1_csv",
    "gzip_text",
    "invalid_base64",
    "oversized_base64",
)


@dataclass(frozen=True)
class ParserInputSmokeSummary:
    """Compact result for one encoded/compressed input smoke."""

    case: str
    target: str
    status: str
    rows_read: int | None
    rows_parsed: int | None
    rows_failed: int | None
    raw_hash_unchanged: bool
    read_hints: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable summary."""
        return asdict(self)


class ParserInputSmokeError(RuntimeError):
    """Raised when an encoded/compressed input smoke violates expectations."""


def run_parser_input_smokes() -> list[ParserInputSmokeSummary]:
    """Run encoded/compressed parser smokes and return summaries."""
    with tempfile.TemporaryDirectory(prefix="stage-two-parser-input-smoke-") as directory:
        root = Path(directory)
        return [
            _smoke_base64_csv(root),
            _smoke_base64_json_lines(root),
            _smoke_base64_raw_log_line(root),
            _smoke_base64_bson_bytes(root),
            _smoke_base64_pcap_bytes(root),
            _smoke_utf8_csv(root),
            _smoke_utf8_sig_csv(root),
            _smoke_cp1252_csv(root),
            _smoke_latin1_csv(root),
            _smoke_gzip_text(root),
            _smoke_invalid_base64(root),
            _smoke_oversized_base64(root),
        ]


def _smoke_base64_csv(root: Path) -> ParserInputSmokeSummary:
    csv_text = "Domain,TTL\nencoded.example,60\n"
    path = _write_bytes(root, "base64/dns.csv.b64", base64.b64encode(csv_text.encode("utf-8")))
    before = _sha256(path)
    context = _context(path, branch="dns", source_format="csv", role="TRAIN")
    result = DnsCsvParser(UnlabeledLabelResolver()).parse(path, context)
    _validate_parser_success("base64_csv", result)
    event = _first_event("base64_csv", result)
    _check(event["query_domain"] == "encoded.example", "base64_csv did not decode CSV payload")
    _check("base64_detected=True" in result.warnings, "base64_csv missing base64 warning")
    return _parser_summary("base64_csv", "DnsCsvParser", result, path, before)


def _smoke_base64_json_lines(root: Path) -> ParserInputSmokeSummary:
    row = {
        "@timestamp": "2024-01-01T00:00:00Z",
        "host": {"name": "json-host"},
        "event": {"action": "encoded_exec"},
    }
    encoded = base64.b64encode((json.dumps(row) + "\n").encode("utf-8"))
    path = _write_bytes(root, "base64/events.json.b64", encoded)
    before = _sha256(path)
    context = _context(path, branch="host", source_format="json", role="TRAIN")
    result = HostJsonLinesParser(LabelResolver(config_path=None, enable_filename_heuristics=False)).parse(path, context)
    _validate_parser_success("base64_json_lines", result)
    event = _first_event("base64_json_lines", result)
    _check(event["event_type"] == "encoded_exec", "base64_json_lines did not decode JSON payload")
    _check("base64_detected=True" in result.warnings, "base64_json_lines missing base64 warning")
    return _parser_summary("base64_json_lines", "HostJsonLinesParser", result, path, before)


def _smoke_base64_raw_log_line(root: Path) -> ParserInputSmokeSummary:
    line = "Jan 12 08:15:30 web01 sshd[1234]: Accepted password for alice from 10.0.0.5 port 54421 ssh2"
    path = _write_bytes(root, "base64/auth.log.b64", base64.b64encode((line + "\n").encode("utf-8")))
    before = _sha256(path)
    context = _context(path, branch="host", source_format="auth.log", role="TRAIN")
    result = HostLineLogParser(LabelResolver(config_path=None, enable_filename_heuristics=False)).parse(path, context)
    _validate_parser_success("base64_raw_log_line", result)
    event = _first_event("base64_raw_log_line", result)
    _check(event["event_type"] == "auth_login_success", "base64_raw_log_line did not decode raw log line")
    return _parser_summary("base64_raw_log_line", "HostLineLogParser", result, path, before)


def _smoke_base64_bson_bytes(root: Path) -> ParserInputSmokeSummary:
    stream = _bson_stream(
        {"I": 3001, "name": "ProcessCreate", "type": "api", "category": "process", "args": ["command_line"]},
        {"I": 3001, "t": 3.0, "args": ["cmd.exe /c whoami"]},
    )
    path = _write_bytes(root, "base64/sample.bson.b64", base64.b64encode(stream))
    before = _sha256(path)
    context = _context(path, branch="host", source_format="bson", role="TEST")
    result = HostBsonSandboxParser(LabelResolver(config_path=None, enable_filename_heuristics=False)).parse(path, context)
    _validate_parser_success("base64_bson_bytes", result, expected_rows_read=2)
    event = _first_event("base64_bson_bytes", result)
    _check(event["event_type"] == "ProcessCreate", "base64_bson_bytes did not decode BSON stream")
    _check("base64_detected=True" in result.warnings, "base64_bson_bytes missing base64 warning")
    return _parser_summary("base64_bson_bytes", "HostBsonSandboxParser", result, path, before)


def _smoke_base64_pcap_bytes(root: Path) -> ParserInputSmokeSummary:
    packet = _ethernet_ipv4_udp_packet(
        src_ip="10.0.0.1",
        dst_ip="8.8.8.8",
        src_port=53000,
        dst_port=53,
        payload=_dns_query("pcap64.example"),
    )
    pcap_bytes = _pcap_file([packet])
    path = _write_bytes(root, "base64/dns.pcap.b64", base64.b64encode(pcap_bytes))
    before = _sha256(path)
    context = _context(path, branch="dns", source_format="pcap", role="VALIDATION")
    result = DnsPacketCaptureParser(UnlabeledLabelResolver()).parse(path, context)
    _validate_parser_success("base64_pcap_bytes", result)
    event = _first_event("base64_pcap_bytes", result)
    _check(event["query_domain"] == "pcap64.example", "base64_pcap_bytes did not decode PCAP bytes")
    return _parser_summary("base64_pcap_bytes", "DnsPacketCaptureParser", result, path, before)


def _smoke_utf8_csv(root: Path) -> ParserInputSmokeSummary:
    content = _host_csv_row(path_value="/opt/utf8-tool.exe")
    path = _write_bytes(root, "encoding/utf8.csv", content.encode("utf-8"))
    before = _sha256(path)
    result = _parse_host_csv(path)
    _validate_parser_success("utf8_csv", result)
    _check(_first_event("utf8_csv", result)["file_path"] == "/opt/utf8-tool.exe", "utf8_csv path mismatch")
    return _parser_summary("utf8_csv", "HostCsvParser", result, path, before)


def _smoke_utf8_sig_csv(root: Path) -> ParserInputSmokeSummary:
    content = _host_csv_row(path_value="/opt/utf8sig-tool.exe")
    path = _write_bytes(root, "encoding/utf8-sig.csv", b"\xef\xbb\xbf" + content.encode("utf-8"))
    before = _sha256(path)
    result = _parse_host_csv(path)
    _validate_parser_success("utf8_sig_csv", result)
    event = _first_event("utf8_sig_csv", result)
    _check(event["file_path"] == "/opt/utf8sig-tool.exe", "utf8_sig_csv path mismatch")
    return _parser_summary("utf8_sig_csv", "HostCsvParser", result, path, before)


def _smoke_cp1252_csv(root: Path) -> ParserInputSmokeSummary:
    euro_path = "/opt/Euro\\u20acTool.exe".encode("ascii").decode("unicode_escape")
    content = _host_csv_row(path_value=euro_path).encode("cp1252")
    path = _write_bytes(root, "encoding/cp1252.csv", content)
    before = _sha256(path)
    result = _parse_host_csv(path)
    _validate_parser_success("cp1252_csv", result)
    event = _first_event("cp1252_csv", result)
    _check(event["file_path"] == euro_path, "cp1252_csv path mismatch")
    _check(_has_warning(result, "cp1252"), "cp1252_csv did not report cp1252 fallback")
    return _parser_summary("cp1252_csv", "HostCsvParser", result, path, before)


def _smoke_latin1_csv(root: Path) -> ParserInputSmokeSummary:
    content = _host_csv_row(path_value="/opt/\x81tool.exe").encode("latin-1")
    path = _write_bytes(root, "encoding/latin1.csv", content)
    before = _sha256(path)
    result = _parse_host_csv(path)
    _validate_parser_success("latin1_csv", result)
    event = _first_event("latin1_csv", result)
    _check(event["file_path"] == "/opt/\x81tool.exe", "latin1_csv path mismatch")
    _check(_has_warning(result, "latin-1"), "latin1_csv did not report latin-1 fallback")
    return _parser_summary("latin1_csv", "HostCsvParser", result, path, before)


def _smoke_gzip_text(root: Path) -> ParserInputSmokeSummary:
    content = "1,2,Comp1,Comp2,6,Port12345,Port443,1,2,64,128\n"
    path = _write_bytes(root, "compression/netflow_day.gz", gzip.compress(content.encode("utf-8")))
    before = _sha256(path)
    context = _context(path, branch="host", source_format="netflow_day", role="VALIDATION")
    result = HostNetflowParser(LabelResolver(config_path=None, enable_filename_heuristics=False)).parse(path, context)
    _validate_parser_success("gzip_text", result)
    event = _first_event("gzip_text", result)
    _check(event["dst_port"] == 443, "gzip_text did not decompress netflow row")
    _check("compression_hint=gzip" in result.warnings, "gzip_text missing gzip hint")
    return _parser_summary("gzip_text", "HostNetflowParser", result, path, before)


def _smoke_invalid_base64(root: Path) -> ParserInputSmokeSummary:
    path = _write_bytes(root, "negative/invalid-base64.txt", b"QUJDRAAAA\n")
    before = _sha256(path)
    reader = UniversalInputReader(path)
    with reader.iter_lines(keepends=False, skip_empty=False) as lines:
        values = list(lines)
    metadata = reader.metadata_snapshot()
    _check(values == ["QUJDRAAAA"], "invalid_base64 should leave invalid content unchanged")
    _check(any("strict validation" in warning for warning in metadata.warnings), "invalid_base64 missing warning")
    return _reader_summary("invalid_base64", path, before, metadata, status="WARNING")


def _smoke_oversized_base64(root: Path) -> ParserInputSmokeSummary:
    payload = b"Domain,TTL\noversized.example,60\n"
    path = _write_bytes(root, "negative/oversized-base64.txt", base64.b64encode(payload))
    before = _sha256(path)
    with _temporary_base64_limit(8):
        reader = UniversalInputReader(path)
        with reader.iter_lines(keepends=False, skip_empty=False) as lines:
            values = list(lines)
        metadata = reader.metadata_snapshot()
    _check(values == [base64.b64encode(payload).decode("ascii")], "oversized_base64 should remain encoded")
    _check(
        any("exceeds limit" in warning for warning in metadata.warnings),
        "oversized_base64 missing size-limit warning",
    )
    return _reader_summary("oversized_base64", path, before, metadata, status="WARNING")


def _parse_host_csv(path: Path) -> ParserResult:
    context = _context(path, branch="host", source_format="csv", role="TRAIN")
    return HostCsvParser(LabelResolver(config_path=None, enable_filename_heuristics=False)).parse(path, context)


def _validate_parser_success(
    case: str,
    result: ParserResult,
    *,
    expected_rows_read: int | None = None,
) -> None:
    if expected_rows_read is not None:
        _check(result.rows_read == expected_rows_read, f"{case} rows_read mismatch: {result.rows_read}")
    _check(result.rows_read > 0, f"{case} rows_read must be positive")
    _check(result.rows_parsed > 0, f"{case} rows_parsed must be positive")
    _check(result.rows_failed == 0, f"{case} rows_failed mismatch: {result.rows_failed}")
    _check(result.file_status == "PARSED", f"{case} file_status mismatch: {result.file_status}")


def _first_event(case: str, result: ParserResult) -> dict[str, Any]:
    _check(bool(result.events), f"{case} emitted no events")
    return result.events[0]


def _parser_summary(
    case: str,
    target: str,
    result: ParserResult,
    path: Path,
    before_hash: str,
) -> ParserInputSmokeSummary:
    raw_hash_unchanged = before_hash == _sha256(path)
    _check(raw_hash_unchanged, f"{case} mutated raw input bytes")
    return ParserInputSmokeSummary(
        case=case,
        target=target,
        status=result.file_status,
        rows_read=result.rows_read,
        rows_parsed=result.rows_parsed,
        rows_failed=result.rows_failed,
        raw_hash_unchanged=raw_hash_unchanged,
        read_hints=_read_hints_from_warnings(result.warnings),
    )


def _reader_summary(
    case: str,
    path: Path,
    before_hash: str,
    metadata: Any,
    *,
    status: str,
) -> ParserInputSmokeSummary:
    raw_hash_unchanged = before_hash == _sha256(path)
    _check(raw_hash_unchanged, f"{case} mutated raw input bytes")
    return ParserInputSmokeSummary(
        case=case,
        target="UniversalInputReader",
        status=status,
        rows_read=None,
        rows_parsed=None,
        rows_failed=None,
        raw_hash_unchanged=raw_hash_unchanged,
        read_hints={
            "encoding_hint": metadata.encoding_hint,
            "compression_hint": metadata.compression_hint,
            "base64_detected": metadata.base64_detected,
            "decode_strategy": metadata.decode_strategy,
            "warnings": list(metadata.warnings),
            "errors": list(metadata.errors),
        },
    )


def _read_hints_from_warnings(warnings: list[str]) -> dict[str, Any]:
    return {
        "base64_detected": "base64_detected=True" in warnings,
        "compression_hint": _first_warning_value(warnings, "compression_hint="),
        "warnings": list(warnings),
    }


def _first_warning_value(warnings: list[str], prefix: str) -> str | None:
    for warning in warnings:
        if warning.startswith(prefix):
            return warning.removeprefix(prefix)
    return None


def _has_warning(result: ParserResult, text: str) -> bool:
    return any(text in warning for warning in result.warnings)


def _host_csv_row(*, path_value: str) -> str:
    return (
        "date,time,process_id,path,sys_call,event_id,attack_cat,attack_subcat,label\n"
        f"31/03/2016,2:45:01,1830,{path_value},142,45354,normal,normal,0\n"
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
        dataset_name=f"{branch}-{source_format}-input-smoke",
        dataset_role=role,
        branch=branch,
        source_format=source_format,
        source_file_path=str(path),
        source_file_hash=_sha256(path),
        parser_run_id=3,
        metadata={"scenario_name": "parser-input-smoke"},
    )


def _write_bytes(root: Path, relative_path: str, content: bytes) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise ParserInputSmokeError(message)


@contextmanager
def _temporary_base64_limit(limit: int) -> Iterator[None]:
    original = input_reader_module.STAGE_TWO_MAX_BASE64_DECODE_BYTES
    input_reader_module.STAGE_TWO_MAX_BASE64_DECODE_BYTES = limit
    try:
        yield
    finally:
        input_reader_module.STAGE_TWO_MAX_BASE64_DECODE_BYTES = original


def _pcap_file(packets: list[bytes]) -> bytes:
    header = struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)
    records = []
    for index, packet in enumerate(packets):
        records.append(struct.pack("<IIII", 1_704_067_200 + index, 123456, len(packet), len(packet)))
        records.append(packet)
    return header + b"".join(records)


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
    """Run encoded/compressed parser smokes from the command line."""
    try:
        summaries = run_parser_input_smokes()
    except ParserInputSmokeError as exc:
        print(f"parser input smoke failed: {exc}", file=sys.stderr)
        return 1

    for summary in summaries:
        print(json.dumps(summary.as_dict(), sort_keys=True))
    print(f"parser input smokes passed: {len(summaries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
