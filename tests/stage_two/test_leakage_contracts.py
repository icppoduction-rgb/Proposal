from __future__ import annotations

import unittest

from scripts.stage_two.features import X_EXCLUDED_COLUMNS, infer_feature_count
from scripts.stage_two.model_ready import X_FORBIDDEN_COLUMNS, validate_x_columns


class LeakageContractsTest(unittest.TestCase):
    def test_raw_label_and_context_columns_are_excluded_from_feature_counts(self) -> None:
        rows = [
            {
                "metric_value": 0.42,
                "label": "malicious",
                "attack_cat": "exploit",
                "target": 1,
                "source_file": "sample.csv",
                "source_format": "csv",
                "scenario_name": "scenario-a",
                "parser_name": "host_csv_parser",
                "parser_version": "v1",
            }
        ]

        self.assertEqual(infer_feature_count(rows), 1)
        for column in (
            "label",
            "attack_cat",
            "target",
            "source_file",
            "source_format",
            "scenario_name",
            "parser_name",
            "parser_version",
        ):
            self.assertIn(column, X_EXCLUDED_COLUMNS)
            self.assertIn(column, X_FORBIDDEN_COLUMNS)

    def test_model_ready_x_rejects_raw_label_like_columns(self) -> None:
        with self.assertRaisesRegex(ValueError, "label"):
            validate_x_columns([{"metric_value": 0.42, "label": 1}])

    def test_model_ready_x_rejects_parser_context_columns(self) -> None:
        with self.assertRaisesRegex(ValueError, "parser_name"):
            validate_x_columns([{"metric_value": 0.42, "parser_name": "dns_csv_parser"}])


if __name__ == "__main__":
    unittest.main()
