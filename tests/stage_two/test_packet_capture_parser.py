from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from scripts.stage_two.labels import UnlabeledLabelResolver
from scripts.stage_two.parsers.base import ParserContext
from scripts.stage_two.parsers.packet import DnsPacketCaptureParser, HostPacketCaptureParser


class PacketCaptureParserTest(unittest.TestCase):
    def test_dns_tiny_pcap_extracts_query_and_response_summary(self) -> None:
        query_packet = _ethernet_ipv4_udp_packet(
            src_ip="10.0.0.1",
            dst_ip="8.8.8.8",
            src_port=53000,
            dst_port=53,
            payload=_dns_query("example.org"),
        )
        response_packet = _ethernet_ipv4_udp_packet(
            src_ip="8.8.8.8",
            dst_ip="10.0.0.1",
            src_port=53,
            dst_port=53000,
            payload=_dns_response("example.org", ttl=60),
        )
        path = _write_binary(self, "dns-smoke.pcap", _pcap_file([query_packet, response_packet]))

        result = DnsPacketCaptureParser(UnlabeledLabelResolver()).parse(
            path,
            _context(path, branch="dns", source_format="pcap"),
        )

        self.assertEqual(result.rows_read, 2)
        self.assertEqual(result.rows_parsed, 2)
        self.assertEqual(result.rows_failed, 0)
        query_event, response_event = result.events
        self.assertEqual(query_event["event_type"], "dns_query")
        self.assertEqual(query_event["modality"], "dns_packet")
        self.assertEqual(query_event["src_ip"], "10.0.0.1")
        self.assertEqual(query_event["dst_ip"], "8.8.8.8")
        self.assertEqual(query_event["src_port"], 53000)
        self.assertEqual(query_event["dst_port"], 53)
        self.assertEqual(query_event["protocol"], "UDP")
        self.assertEqual(query_event["query_domain"], "example.org")
        self.assertEqual(query_event["qtype"], "1")
        self.assertEqual(query_event["rcode"], "0")
        self.assertNotIn("payload", query_event["raw_fields_json"])
        self.assertEqual(response_event["event_type"], "dns_response")
        self.assertEqual(response_event["ttl"], 60)
        self.assertEqual(response_event["raw_fields_json"]["packet_size"], len(response_packet))

    def test_host_tiny_pcapng_extracts_tcp_summary(self) -> None:
        packet = _ethernet_ipv4_tcp_packet(
            src_ip="192.0.2.10",
            dst_ip="198.51.100.20",
            src_port=49152,
            dst_port=443,
            flags=0x02,
        )
        path = _write_binary(self, "host-smoke.pcapng", _pcapng_file(packet))

        result = HostPacketCaptureParser(UnlabeledLabelResolver()).parse(
            path,
            _context(path, branch="host", source_format="pcapng"),
        )

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["event_type"], "network_packet_summary")
        self.assertEqual(event["modality"], "host_network_packet")
        self.assertEqual(event["src_ip"], "192.0.2.10")
        self.assertEqual(event["dst_ip"], "198.51.100.20")
        self.assertEqual(event["src_port"], 49152)
        self.assertEqual(event["dst_port"], 443)
        self.assertEqual(event["protocol"], "TCP")
        self.assertEqual(event["raw_fields_json"]["tcp_flags"], "SYN")
        self.assertNotIn("payload", event["raw_fields_json"])

    def test_cap_extension_is_recognized_as_pcap_compatible(self) -> None:
        packet = _ethernet_ipv4_udp_packet(
            src_ip="10.1.1.10",
            dst_ip="10.1.1.53",
            src_port=40000,
            dst_port=53,
            payload=_dns_query("cap.example"),
        )
        path = _write_binary(self, "dns-smoke.cap", _pcap_file([packet]))

        result = HostPacketCaptureParser(UnlabeledLabelResolver()).parse(
            path,
            _context(path, branch="host", source_format="cap"),
        )

        self.assertEqual(result.rows_read, 1)
        self.assertEqual(result.rows_parsed, 1)
        event = result.events[0]
        self.assertEqual(event["event_type"], "dns_query")
        self.assertEqual(event["modality"], "host_network_packet")
        self.assertEqual(event["query_domain"], "cap.example")

    def test_packet_parser_can_stream_batches_without_changing_parse_contract(self) -> None:
        packets = [
            _ethernet_ipv4_udp_packet(
                src_ip="10.0.0.1",
                dst_ip="8.8.8.8",
                src_port=53000 + index,
                dst_port=53,
                payload=_dns_query(f"batch-{index}.example"),
            )
            for index in range(3)
        ]
        path = _write_binary(self, "dns-batched.pcap", _pcap_file(packets))
        parser = DnsPacketCaptureParser(UnlabeledLabelResolver())
        context = _context(path, branch="dns", source_format="pcap")

        batches = list(parser.parse_batches(path, context, batch_size=2))
        result = parser.parse(path, context)

        self.assertEqual([batch.rows_parsed for batch in batches], [2, 1])
        self.assertEqual(sum(batch.events_emitted for batch in batches), 3)
        self.assertEqual(result.rows_parsed, 3)
        self.assertEqual([event["query_domain"] for event in result.events], [
            "batch-0.example",
            "batch-1.example",
            "batch-2.example",
        ])


def _context(path: Path, *, branch: str, source_format: str) -> ParserContext:
    return ParserContext(
        dataset_id=1,
        file_id=2,
        dataset_name=f"{branch}-packet-smoke",
        dataset_role="VALIDATION",
        branch=branch,
        source_format=source_format,
        source_file_path=str(path),
        source_file_hash="hash",
        parser_run_id=3,
    )


def _write_binary(test_case: unittest.TestCase, file_name: str, content: bytes) -> Path:
    directory = Path(tempfile.mkdtemp(prefix="packet-parser-"))
    test_case.addCleanup(lambda: _cleanup_directory(directory))
    path = directory / file_name
    path.write_bytes(content)
    return path


def _cleanup_directory(directory: Path) -> None:
    for path in sorted(directory.rglob("*"), reverse=True):
        path.unlink()
    directory.rmdir()


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
    enhanced_body = struct.pack(
        "<IIIII",
        0,
        timestamp >> 32,
        timestamp & 0xFFFFFFFF,
        len(packet),
        len(packet),
    ) + _pad32(packet)
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


def _dns_response(domain: str, *, ttl: int) -> bytes:
    question = _dns_name(domain) + struct.pack("!HH", 1, 1)
    answer = b"\xc0\x0c" + struct.pack("!HHIH", 1, 1, ttl, 4) + b"\x01\x02\x03\x04"
    return struct.pack("!HHHHHH", 0x1234, 0x8180, 1, 1, 0, 0) + question + answer


def _dns_name(domain: str) -> bytes:
    labels = domain.split(".")
    return b"".join(bytes([len(label)]) + label.encode("ascii") for label in labels) + b"\x00"


if __name__ == "__main__":
    unittest.main()
