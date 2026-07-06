from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.stage_three.labels import (
    LABEL_ALIGNMENT_POLICIES,
    align_event_samples,
    align_flow_samples,
    align_sequence_samples,
    align_window_samples,
)
from scripts.stage_three.labels.label_policy import LABEL_COLUMNS
from scripts.stage_three.labels.report import TASK10_REPORT_FILENAME, save_label_alignment_reports


class LabelAlignmentPolicyTest(unittest.TestCase):
    def test_all_required_policies_are_available(self) -> None:
        self.assertEqual(
            set(LABEL_ALIGNMENT_POLICIES),
            {
                "explicit_only",
                "any_attack_in_window",
                "majority_label",
                "last_event_label",
                "weak_allowed_with_confidence",
            },
        )

    def test_event_explicit_only_keeps_unlabeled_as_unlabeled_and_separates_x(self) -> None:
        result = align_event_samples(_event_rows(), policy="explicit_only")

        self.assertEqual(result.y_rows[0]["label_binary"], 1)
        self.assertIsNone(result.y_rows[2]["label_binary"])
        self.assertEqual(result.y_rows[2]["label_status"], "unlabeled")
        for x_row in result.x_rows:
            self.assertFalse(set(x_row).intersection(LABEL_COLUMNS))
            self.assertNotIn("label_binary", x_row)
        self.assertIn("label_status", result.metadata_rows[0])
        self.assertEqual(result.summary["sample_count"], 4)
        self.assertEqual(result.summary["labeled_count"], 3)
        self.assertEqual(result.summary["unlabeled_count"], 1)

    def test_window_any_attack_marks_conflict_without_overwriting_attack_target(self) -> None:
        result = align_window_samples(_event_rows(), policy="any_attack_in_window")
        rows_by_uid = {row["sample_uid"]: row for row in result.y_rows}
        metadata_by_uid = {row["sample_uid"]: row for row in result.metadata_rows}

        self.assertEqual(rows_by_uid["w1"]["label_binary"], 1)
        self.assertEqual(rows_by_uid["w1"]["label_status"], "conflicting")
        self.assertTrue(metadata_by_uid["w1"]["conflicting"])
        self.assertEqual(metadata_by_uid["w1"]["conflict_values"], [0, 1])
        self.assertEqual(rows_by_uid["w2"]["label_status"], "unlabeled")

    def test_majority_label_tie_is_conflicting_not_silent(self) -> None:
        result = align_window_samples(_tie_rows(), policy="majority_label")

        self.assertIsNone(result.y_rows[0]["label_binary"])
        self.assertEqual(result.y_rows[0]["label_status"], "conflicting")
        self.assertEqual(result.summary["conflicting_count"], 1)

    def test_last_event_label_is_ordered_deterministically(self) -> None:
        result = align_sequence_samples(_unordered_sequence_rows(), policy="last_event_label")

        self.assertEqual(result.y_rows[0]["sample_uid"], "seq-1")
        self.assertEqual(result.y_rows[0]["label_binary"], 1)
        self.assertEqual(result.metadata_rows[0]["source_event_uids"], ["e1", "e2", "e3"])

    def test_weak_labels_require_weak_policy_and_preserve_confidence(self) -> None:
        rows = [
            {
                "sample_uid": "weak-1",
                "event_uid": "weak-1",
                "dns_query_length": 17,
                "label_binary": 1,
                "label_status": "weak_label",
                "label_source": "weak",
                "label_confidence": 0.42,
                "label_mapping_rule_id": "weak-rule",
            }
        ]

        strict = align_event_samples(rows, policy="explicit_only")
        weak = align_event_samples(rows, policy="weak_allowed_with_confidence")

        self.assertIsNone(strict.y_rows[0]["label_binary"])
        self.assertEqual(strict.y_rows[0]["label_status"], "unlabeled")
        self.assertEqual(weak.y_rows[0]["label_binary"], 1)
        self.assertEqual(weak.y_rows[0]["label_confidence"], 0.42)
        self.assertEqual(weak.metadata_rows[0]["label_mapping_rule_id"], "weak-rule")

    def test_flow_level_labels_group_by_flow_id(self) -> None:
        result = align_flow_samples(_flow_rows(), policy="any_attack_in_window")
        rows_by_uid = {row["sample_uid"]: row for row in result.y_rows}

        self.assertEqual(rows_by_uid["flow-a"]["label_binary"], 1)
        self.assertEqual(rows_by_uid["flow-b"]["label_binary"], 0)
        self.assertEqual(result.summary["labeled_count"], 2)

    def test_report_includes_required_task10_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = align_window_samples(_event_rows(), policy="any_attack_in_window")
            with (
                patch("scripts.stage_three.reports.path_utils.REPORTS_RU_STAGE_THREE", str(root / "ru")),
                patch("scripts.stage_three.reports.path_utils.REPORTS_EN_STAGE_THREE", str(root / "en")),
            ):
                written = save_label_alignment_reports(result)

            ru_report = root / "ru" / TASK10_REPORT_FILENAME
            en_report = root / "en" / TASK10_REPORT_FILENAME
            self.assertTrue(ru_report.exists())
            self.assertTrue(en_report.exists())
            text = en_report.read_text(encoding="utf-8")
            self.assertIn("Task09-feature-artifact-writer-and-catalog-registration.md", text)
            self.assertIn("Policy used", text)
            self.assertIn("Label Coverage", text)
            self.assertIn("Unlabeled/Conflicting Counts", text)
            self.assertIn("Label Source/Status Distribution", text)
            self.assertIn("report_paths", written.summary)


def _event_rows() -> list[dict[str, object]]:
    return [
        {
            "sample_uid": "s1",
            "event_uid": "e1",
            "window_id": "w1",
            "event_order": 1,
            "dns_query_length": 10,
            "label_binary": 1,
            "label_family": "attack",
            "label_subtype": "exfil",
            "label_source": "fixture",
            "label_status": "explicit_label",
            "label_confidence": 1.0,
            "label_mapping_rule_id": "rule-a",
        },
        {
            "sample_uid": "s2",
            "event_uid": "e2",
            "window_id": "w1",
            "event_order": 2,
            "dns_query_length": 12,
            "label_binary": 0,
            "label_family": "benign",
            "label_source": "fixture",
            "label_status": "explicit_label",
            "label_confidence": 1.0,
            "label_mapping_rule_id": "rule-b",
        },
        {
            "sample_uid": "s3",
            "event_uid": "e3",
            "window_id": "w2",
            "event_order": 3,
            "dns_query_length": 15,
            "label_binary": None,
            "label_source": "none",
            "label_status": "unlabeled",
        },
        {
            "sample_uid": "s4",
            "event_uid": "e4",
            "window_id": "w3",
            "event_order": 4,
            "dns_query_length": 20,
            "label_binary": 0,
            "label_family": "benign",
            "label_source": "fixture",
            "label_status": "explicit_label",
            "label_confidence": 1.0,
            "label_mapping_rule_id": "rule-c",
        },
    ]


def _tie_rows() -> list[dict[str, object]]:
    return [
        {**_event_rows()[0], "window_id": "tie"},
        {**_event_rows()[1], "window_id": "tie"},
    ]


def _unordered_sequence_rows() -> list[dict[str, object]]:
    return [
        {
            "sequence_id": "seq-1",
            "event_uid": "e3",
            "event_order": 3,
            "feature": 3,
            "label_binary": 1,
            "label_source": "fixture",
            "label_status": "explicit_label",
        },
        {
            "sequence_id": "seq-1",
            "event_uid": "e1",
            "event_order": 1,
            "feature": 1,
            "label_binary": 0,
            "label_source": "fixture",
            "label_status": "explicit_label",
        },
        {
            "sequence_id": "seq-1",
            "event_uid": "e2",
            "event_order": 2,
            "feature": 2,
            "label_binary": 0,
            "label_source": "fixture",
            "label_status": "explicit_label",
        },
    ]


def _flow_rows() -> list[dict[str, object]]:
    return [
        {**_event_rows()[0], "flow_id": "flow-a"},
        {**_event_rows()[2], "flow_id": "flow-a"},
        {**_event_rows()[1], "flow_id": "flow-b"},
    ]


if __name__ == "__main__":
    unittest.main()
