import struct
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.read_format import FileContentProcessingError, FileFormatReader


class FileFormatReaderTests(unittest.TestCase):
    def test_pcap_csv_is_read_as_csv(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "stateful_features-light_exe.pcap.csv"
            path.write_text("rr,A_frequency\n0.0,1\n", encoding="utf-8")

            result = FileFormatReader().read(path)

        data = result["data"]
        self.assertEqual(data["type"], "csv")
        self.assertEqual(data["metadata"]["rows"], 1)
        self.assertEqual(data["metadata"]["columns"], ["rr", "A_frequency"])
        self.assertEqual(data["content"], [{"rr": "0.0", "A_frequency": "1"}])

    def test_headerless_csv_is_streamed_with_row_limit(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "dataset.csv"
            path.write_text("186.169.253.58,surbl.org\n186.169.253.59,example.org\n", encoding="utf-8")

            result = FileFormatReader(csv_row_limit=1).read(path)

        data = result["data"]
        self.assertEqual(data["type"], "csv")
        self.assertFalse(data["metadata"]["has_header"])
        self.assertEqual(data["metadata"]["rows_returned"], 1)
        self.assertEqual(data["metadata"]["rows_scanned"], 2)
        self.assertTrue(data["metadata"]["rows_truncated"])
        self.assertEqual(data["metadata"]["columns"], ["column_0", "column_1"])
        self.assertEqual(data["content"], [{"column_0": "186.169.253.58", "column_1": "surbl.org"}])

    def test_pcap_is_read_as_base64_preview_with_metadata(self) -> None:
        pcap_header = struct.pack(
            "<IHHIIII",
            0xA1B2C3D4,
            2,
            4,
            0,
            0,
            262144,
            1,
        )
        app_payload = b"data"
        ethernet_header = (
            bytes.fromhex("001122334455")
            + bytes.fromhex("66778899aabb")
            + struct.pack("!H", 0x0800)
        )
        ipv4_header = struct.pack(
            "!BBHHHBBH4s4s",
            0x45,
            0,
            20 + 8 + len(app_payload),
            0,
            0,
            64,
            17,
            0,
            bytes([192, 0, 2, 1]),
            bytes([8, 8, 8, 8]),
        )
        udp_header = struct.pack("!HHHH", 12345, 53, 8 + len(app_payload), 0)
        packet_payload = ethernet_header + ipv4_header + udp_header + app_payload
        packet_header = struct.pack(
            "<IIII",
            1_700_000_000,
            123_456,
            len(packet_payload),
            len(packet_payload),
        )
        payload = pcap_header + packet_header + packet_payload

        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "malware.pcap"
            path.write_bytes(payload)

            result = FileFormatReader().read(path)

        data = result["data"]
        self.assertEqual(data["type"], "pcap")
        self.assertNotIn("content_base64", data)
        self.assertEqual(data["metadata"]["source_bytes"], len(payload))
        self.assertFalse(data["metadata"]["content_base64_included"])
        self.assertEqual(data["metadata"]["magic_hex"], "d4c3b2a1")
        self.assertEqual(data["metadata"]["pcap_type"], "pcap")
        self.assertEqual(data["metadata"]["version"], "2.4")
        self.assertEqual(data["metadata"]["snaplen"], 262144)
        self.assertEqual(data["metadata"]["network"], 1)
        self.assertEqual(data["metadata"]["link_type"], "Ethernet")
        self.assertEqual(data["metadata"]["records"], 1)
        self.assertEqual(data["format"], "pcap")
        self.assertIn("decoded_content", data)
        self.assertEqual(data["decoded_content"]["preview_bytes"], len(payload))
        self.assertEqual(data["decoded_content"]["source_bytes"], len(payload))
        self.assertEqual(data["decoded_content"]["packets_parsed"], 1)
        self.assertEqual(data["records"], data["decoded_content"]["packets_preview"])

        record = data["records"][0]
        self.assertEqual(record["index"], 0)
        self.assertEqual(record["timestamp"], "2023-11-14T22:13:20.123456+00:00")
        self.assertEqual(record["timestamp_seconds"], 1_700_000_000)
        self.assertEqual(record["timestamp_fraction"], 123_456)
        self.assertEqual(record["packet_length"], len(packet_payload))
        self.assertEqual(record["captured_length"], len(packet_payload))
        self.assertEqual(record["original_length"], len(packet_payload))
        self.assertEqual(record["available_payload_bytes"], len(packet_payload))
        self.assertFalse(record["truncated"])
        self.assertEqual(record["link_protocol"], "Ethernet")
        self.assertEqual(record["network_protocol"], "IPv4")
        self.assertEqual(record["src_ip"], "192.0.2.1")
        self.assertEqual(record["dst_ip"], "8.8.8.8")
        self.assertEqual(record["transport_protocol"], "UDP")
        self.assertEqual(record["src_port"], 12345)
        self.assertEqual(record["dst_port"], 53)
        self.assertEqual(record["payload_length"], len(app_payload))
        self.assertTrue(record["has_payload"])
        self.assertEqual(record["payload_hex_preview"], app_payload.hex(" "))
        self.assertEqual(record["payload_ascii_preview"], "data")

    def test_invalid_pcap_raises_content_processing_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "broken.pcap"
            path.write_bytes(b"not-a-pcap")

            with self.assertRaises(FileContentProcessingError):
                FileFormatReader().read(path)

    def test_pcapng_is_read_as_packet_records(self) -> None:
        app_payload = b"ng"
        ethernet_header = (
            bytes.fromhex("001122334455")
            + bytes.fromhex("66778899aabb")
            + struct.pack("!H", 0x0800)
        )
        ipv4_header = struct.pack(
            "!BBHHHBBH4s4s",
            0x45,
            0,
            20 + 8 + len(app_payload),
            0,
            0,
            64,
            17,
            0,
            bytes([10, 0, 0, 1]),
            bytes([1, 1, 1, 1]),
        )
        udp_header = struct.pack("!HHHH", 5353, 53, 8 + len(app_payload), 0)
        packet_payload = ethernet_header + ipv4_header + udp_header + app_payload
        packet_padding = b"\x00" * ((4 - (len(packet_payload) % 4)) % 4)

        section_body = b"\x4d\x3c\x2b\x1a" + struct.pack("<HHq", 1, 0, -1)
        section = struct.pack("<II", 0x0A0D0D0A, 28) + section_body + struct.pack("<I", 28)
        interface_body = struct.pack("<HHI", 1, 0, 262144)
        interface = struct.pack("<II", 1, 20) + interface_body + struct.pack("<I", 20)
        timestamp_value = 1_700_000_000_123_456
        enhanced_body = (
            struct.pack(
                "<IIIII",
                0,
                timestamp_value >> 32,
                timestamp_value & 0xFFFFFFFF,
                len(packet_payload),
                len(packet_payload),
            )
            + packet_payload
            + packet_padding
        )
        enhanced_length = 8 + len(enhanced_body) + 4
        enhanced = struct.pack("<II", 6, enhanced_length) + enhanced_body + struct.pack("<I", enhanced_length)
        payload = section + interface + enhanced

        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "benign.pcap"
            path.write_bytes(payload)

            result = FileFormatReader().read(path)

        data = result["data"]
        self.assertEqual(data["type"], "pcap")
        self.assertEqual(data["metadata"]["pcap_type"], "pcapng")
        self.assertEqual(data["metadata"]["interfaces"], 1)
        self.assertEqual(data["metadata"]["link_type"], "Ethernet")
        self.assertEqual(data["metadata"]["records"], 1)
        self.assertNotIn("content_base64", data)

        record = data["records"][0]
        self.assertEqual(record["interface_id"], 0)
        self.assertEqual(record["timestamp"], "2023-11-14T22:13:20.123456+00:00")
        self.assertEqual(record["network_protocol"], "IPv4")
        self.assertEqual(record["src_ip"], "10.0.0.1")
        self.assertEqual(record["dst_ip"], "1.1.1.1")
        self.assertEqual(record["transport_protocol"], "UDP")
        self.assertEqual(record["src_port"], 5353)
        self.assertEqual(record["dst_port"], 53)
        self.assertEqual(record["payload_length"], len(app_payload))
        self.assertEqual(record["payload_ascii_preview"], "ng")


if __name__ == "__main__":
    unittest.main()
