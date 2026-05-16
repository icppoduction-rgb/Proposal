import base64
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.convertion.host_convertion import (
    HOST_SPLITS,
    HostConversionConfig,
    build_output_path,
    convert_host_datasets,
    normalize_json_value,
)


class HostConversionTests(unittest.TestCase):
    def test_duplicate_source_names_are_written_to_unique_json_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "datasets" / "host"
            target_root = root / "datasets-new" / "host"
            first = source_root / "TEST" / "DatasetA" / "1" / "analysis.log"
            second = source_root / "TEST" / "DatasetA" / "2" / "analysis.log"
            first.parent.mkdir(parents=True)
            second.parent.mkdir(parents=True)
            first.write_text("first\n", encoding="utf-8")
            second.write_text("second\n", encoding="utf-8")

            summary = convert_host_datasets(
                HostConversionConfig(
                    source_root=source_root,
                    target_root=target_root,
                    splits=("TEST",),
                    workers=1,
                    progress_interval=0,
                )
            )

            outputs = sorted((target_root / "TEST").glob("*.json"))
            self.assertEqual(summary.converted_files, 2)
            self.assertEqual(len(outputs), 2)
            self.assertNotEqual(outputs[0].name, outputs[1].name)

    def test_base64_json_fields_are_converted_to_decoded_previews(self) -> None:
        payload = {
            "content_base64": base64.b64encode(b"human readable").decode("ascii"),
        }

        normalized = normalize_json_value(
            payload,
            config=HostConversionConfig(
                source_root=Path("datasets/host"),
                target_root=Path("datasets-new/host"),
            ),
        )

        decoded = normalized["content_base64"]["decoded"]
        self.assertEqual(normalized["content_base64"]["encoding"], "base64")
        self.assertEqual(decoded["text_preview"], "human readable")
        self.assertEqual(decoded["preview_ascii"], "human readable")

    def test_binary_file_is_written_with_decoded_content_not_raw_base64_only(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_root = root / "datasets" / "host"
            target_root = root / "datasets-new" / "host"
            source_file = source_root / "TRAIN" / "DatasetA" / "sample.bin"
            source_file.parent.mkdir(parents=True)
            source_file.write_bytes(b"\x00\x01ABC")

            summary = convert_host_datasets(
                HostConversionConfig(
                    source_root=source_root,
                    target_root=target_root,
                    splits=("TRAIN",),
                    workers=1,
                    progress_interval=0,
                )
            )

            output_path = build_output_path(source_file, source_root, target_root)
            data = json.loads(output_path.read_text(encoding="utf-8"))["data"]

            self.assertEqual(summary.converted_files, 1)
            self.assertEqual(data["type"], "binary")
            self.assertFalse(data["metadata"]["content_base64_included"])
            self.assertIn("decoded_content", data)
            self.assertEqual(data["decoded_content"]["preview_ascii"], "..ABC")


if __name__ == "__main__":
    unittest.main()
