import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.cleanup.cleanup_host_datasets_new import cleanup_host_datasets_new


def write_converted_host_file(path: Path, dataset: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "data": {
                    "type": "text",
                    "metadata": {
                        "dataset": dataset,
                        "split": path.parent.name,
                    },
                    "content": "sample",
                }
            }
        ),
        encoding="utf-8",
    )


class CleanupHostDatasetsNewTests(unittest.TestCase):
    def test_dry_run_reports_unselected_files_without_deleting_them(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "datasets-new" / "host"
            kept = root / "TRAIN" / "adfa.json"
            removed = root / "TEST" / "malware.json"
            write_converted_host_file(kept, "ADFA IDS")
            write_converted_host_file(removed, "Dynamic-Malware-Analysis-Dataset")

            result = cleanup_host_datasets_new(root=root, dry_run=True)

            self.assertEqual(result.scanned_files, 2)
            self.assertEqual(result.kept_files, 1)
            self.assertEqual(result.deleted_files, 1)
            self.assertTrue(kept.exists())
            self.assertTrue(removed.exists())

    def test_apply_deletes_only_unselected_dataset_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "datasets-new" / "host"
            kept = root / "TRAIN" / "lid.json"
            removed = root / "EXPERIMENTS" / "hdfs.json"
            write_converted_host_file(kept, "LID-DS 2021")
            write_converted_host_file(removed, "HDFS-Log-Dataset")

            result = cleanup_host_datasets_new(root=root, dry_run=False)

            self.assertEqual(result.kept_files, 1)
            self.assertEqual(result.deleted_files, 1)
            self.assertTrue(kept.exists())
            self.assertFalse(removed.exists())

    def test_files_without_dataset_metadata_are_kept(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "datasets-new" / "host"
            unknown = root / "TRAIN" / "unknown.json"
            unknown.parent.mkdir(parents=True, exist_ok=True)
            unknown.write_text('{"data": {"metadata": {}}}', encoding="utf-8")

            result = cleanup_host_datasets_new(root=root, dry_run=False)

            self.assertEqual(result.unknown_metadata_files, 1)
            self.assertEqual(result.deleted_files, 0)
            self.assertTrue(unknown.exists())


if __name__ == "__main__":
    unittest.main()
