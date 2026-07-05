from __future__ import annotations

import copy
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts.stage_three.cli import router_stage_three
from scripts.stage_three.feature_catalog.loader import (
    load_feature_catalog,
    save_normalized_catalog_snapshot,
)
from scripts.stage_three.feature_catalog.report import TASK05_REPORT_FILENAME
from scripts.stage_three.feature_catalog.validator import FAIL, PASS, validate_feature_catalog


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = PROJECT_ROOT / "scripts" / "stage_three" / "feature_catalog" / "feature_catalog.yml"
REQUIRED_GROUPS = {
    "dns_lexical",
    "dns_entropy",
    "dns_temporal",
    "dns_protocol",
    "dns_window",
    "dns_exfil_indicators",
    "host_syscall",
    "host_process",
    "host_auth",
    "host_file_access",
    "host_metrics",
    "host_logs",
    "host_windows_sysmon",
    "network_flow",
    "network_ports",
    "network_protocol",
    "network_direction",
    "network_timing",
    "host_network_correlation",
    "auth_network_correlation",
    "staging_exfil_sequence",
    "stage_transition",
    "sequence_basic",
    "sequence_temporal",
    "sequence_token",
}


class FeatureCatalogValidatorTest(unittest.TestCase):
    def test_default_feature_catalog_is_valid_and_covers_required_groups(self) -> None:
        catalog = load_feature_catalog(DEFAULT_CATALOG_PATH)
        result = validate_feature_catalog(catalog)

        self.assertEqual(result.status, PASS, result.issues)
        self.assertEqual(result.catalog_version, "1.0")
        self.assertTrue(REQUIRED_GROUPS.issubset(catalog["feature_groups"]))
        self.assertIn("label_*", result.forbidden_X_columns)
        self.assertIn("dataset_name", result.forbidden_X_columns)
        self.assertGreaterEqual(result.feature_count, len(REQUIRED_GROUPS))

    def test_invalid_forbidden_feature_cannot_be_allowed_in_x(self) -> None:
        catalog = copy.deepcopy(load_feature_catalog(DEFAULT_CATALOG_PATH))
        catalog["feature_groups"]["dns_lexical"]["features"].append(
            {
                "name": "dataset_name",
                "dtype": "categorical",
                "nullable": False,
                "allow_in_X": True,
                "preprocessing": {
                    "missing": "unknown",
                    "scaling": "none",
                    "encoding": "one_hot",
                },
            }
        )

        result = validate_feature_catalog(catalog)

        self.assertEqual(result.status, FAIL)
        self.assertIn("forbidden X column", _issue_text(result))

    def test_invalid_dtype_strategy_combination_fails(self) -> None:
        catalog = copy.deepcopy(load_feature_catalog(DEFAULT_CATALOG_PATH))
        feature = catalog["feature_groups"]["dns_protocol"]["features"][0]
        feature["preprocessing"]["scaling"] = "standard"

        result = validate_feature_catalog(catalog)

        self.assertEqual(result.status, FAIL)
        self.assertIn("standard is incompatible with categorical", _issue_text(result))

    def test_normalized_catalog_snapshot_is_deterministic_json(self) -> None:
        catalog = load_feature_catalog(DEFAULT_CATALOG_PATH)
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "feature_catalog.normalized.json"
            written = save_normalized_catalog_snapshot(catalog, output_path)
            first = written.read_text(encoding="utf-8")
            save_normalized_catalog_snapshot(catalog, output_path)
            second = written.read_text(encoding="utf-8")

        self.assertEqual(first, second)
        payload = json.loads(first)
        self.assertEqual(payload["version"], "1.0")
        self.assertEqual(sorted(payload["feature_groups"]), sorted(catalog["feature_groups"]))

    def test_build_feature_catalog_cli_writes_reports_and_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            snapshot_path = root / "feature_catalog.normalized.json"
            report_ru = root / "reports" / "ru" / "stage-three"
            report_en = root / "reports" / "en" / "stage-three"

            with (
                patch("scripts.stage_three.cli.PATH_DATA_STORAGE", str(root)),
                patch("scripts.stage_three.cli.STAGE_THREE_FEATURE_CATALOG_PATH", str(DEFAULT_CATALOG_PATH)),
                patch(
                    "scripts.stage_three.cli.save_normalized_catalog_snapshot",
                    side_effect=lambda catalog: save_normalized_catalog_snapshot(catalog, snapshot_path),
                ),
                patch("scripts.stage_three.reports.path_utils.REPORTS_RU_STAGE_THREE", str(report_ru)),
                patch("scripts.stage_three.reports.path_utils.REPORTS_EN_STAGE_THREE", str(report_en)),
            ):
                output = _capture_router(lambda: router_stage_three("build-feature-catalog"))

            self.assertIn("stage-three build-feature-catalog", output)
            self.assertIn("PASS", output)
            self.assertTrue(snapshot_path.exists())
            self.assertTrue((report_ru / TASK05_REPORT_FILENAME).exists())
            self.assertTrue((report_en / TASK05_REPORT_FILENAME).exists())


def _issue_text(result) -> str:
    return " ".join(issue.message for issue in result.issues)


def _capture_router(callback) -> str:
    buffer = StringIO()
    with redirect_stdout(buffer):
        callback()
    return buffer.getvalue()


if __name__ == "__main__":
    unittest.main()
