from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa

from scripts.stage_three.model_ready.sequence_builder import (
    TASK16_REPORT_FILENAME,
    SequenceOrderingError,
    SequencePolicy,
    build_sequence_windows,
    save_sequence_builder_reports,
    sequence_windows_to_tables,
)


class SequenceWindowBuilderTest(unittest.TestCase):
    def test_builds_timestamp_ordered_windows_with_padding_mask_and_labels(self) -> None:
        policy = SequencePolicy(
            sequence_length=4,
            step=2,
            group_by=("host",),
            feature_columns=("feature_a", "feature_b"),
        )

        result = build_sequence_windows(
            _timestamp_rows(),
            branch="host",
            role="TRAIN",
            policy=policy,
        )

        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(len(result.windows), 3)
        first = result.windows[0]
        second = result.windows[1]
        self.assertEqual(first.ordering_policy, "timestamp")
        self.assertEqual(first.traceability_event_uids, ["e1", "e2", "e3", "e4"])
        self.assertEqual(first.mask, [1, 1, 1, 1])
        self.assertEqual(first.padding_count, 0)
        self.assertEqual(first.y_sequence["label_binary"], 1)
        self.assertEqual(first.y_sequence["label_status"], "conflicting")
        self.assertEqual(second.traceability_event_uids, ["e3", "e4", "e5"])
        self.assertEqual(second.mask, [1, 1, 1, 0])
        self.assertEqual(second.padding_count, 1)
        self.assertEqual(second.X_sequence[-1], {"feature_a": 0, "feature_b": 0})
        self.assertEqual(result.padding_statistics["total_padding_count"], 4)
        self.assertEqual(result.label_distribution, {"0": 2, "1": 1})
        self.assertEqual(result.timestamp_coverage["uses_current_runtime_time"], False)

    def test_missing_timestamps_fall_back_to_reliable_event_order_only(self) -> None:
        policy = SequencePolicy(
            sequence_length=3,
            step=3,
            group_by=("host",),
            feature_columns=("feature_a",),
        )

        result = build_sequence_windows(
            _event_order_rows(),
            branch="host",
            role="VALIDATION",
            policy=policy,
        )

        self.assertEqual(result.windows[0].ordering_policy, "event_order")
        self.assertEqual(result.windows[0].traceability_event_uids, ["o1", "o2", "o3"])
        self.assertEqual(result.ordering_policy, "event_order:1")
        self.assertEqual(result.timestamp_coverage["timestamp_coverage"], 0.0)

    def test_missing_timestamps_without_reliable_event_order_fail(self) -> None:
        policy = SequencePolicy(sequence_length=3, step=3, group_by=("host",))

        with self.assertRaisesRegex(SequenceOrderingError, "event_order"):
            build_sequence_windows(
                [
                    {"host": "h1", "event_uid": "x1", "event_order": 1, "feature_a": 1},
                    {"host": "h1", "event_uid": "x2", "event_order": 1, "feature_a": 2},
                ],
                branch="host",
                role="TRAIN",
                policy=policy,
            )

    def test_traceability_is_outside_model_x(self) -> None:
        policy = SequencePolicy(
            sequence_length=4,
            step=4,
            group_by=("host",),
            feature_columns=("feature_a",),
        )
        result = build_sequence_windows(_timestamp_rows(), branch="host", role="TEST", policy=policy)
        tables = sequence_windows_to_tables(result)

        self.assertIn("X_sequence", tables["X"][0])
        self.assertNotIn("traceability_event_uids", tables["X"][0])
        self.assertIn("traceability_event_uids", tables["traceability"][0])
        self.assertEqual(tables["traceability"][0]["traceability_event_uids"], ["e1", "e2", "e3", "e4"])

    def test_accepts_pyarrow_table_input(self) -> None:
        policy = SequencePolicy(
            sequence_length=3,
            step=3,
            group_by=("host",),
            feature_columns=("feature_a",),
        )
        table = pa.table(
            {
                "host": ["h1", "h1", "h1"],
                "event_uid": ["p1", "p2", "p3"],
                "event_timestamp": [
                    "2026-01-01T00:00:01",
                    "2026-01-01T00:00:02",
                    "2026-01-01T00:00:03",
                ],
                "feature_a": [1, 2, 3],
                "label_binary": [0, 0, 1],
                "label_status": ["explicit_label", "explicit_label", "explicit_label"],
                "label_source": ["fixture", "fixture", "fixture"],
            }
        )

        result = build_sequence_windows(table, branch="host", role="TRAIN", policy=policy)

        self.assertEqual(len(result.windows), 1)
        self.assertEqual(result.windows[0].mask, [1, 1, 1])
        self.assertEqual(result.windows[0].y_sequence["label_binary"], 1)

    def test_report_contains_task16_required_sections(self) -> None:
        policy = SequencePolicy(
            sequence_length=4,
            step=2,
            group_by=("host",),
            feature_columns=("feature_a", "feature_b"),
        )
        result = build_sequence_windows(_timestamp_rows(), branch="host", role="TRAIN", policy=policy)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with (
                patch("scripts.stage_three.reports.path_utils.REPORTS_RU_STAGE_THREE", str(root / "ru")),
                patch("scripts.stage_three.reports.path_utils.REPORTS_EN_STAGE_THREE", str(root / "en")),
            ):
                written = save_sequence_builder_reports(result)

            report = root / "en" / TASK16_REPORT_FILENAME
            self.assertTrue(report.exists())
            text = report.read_text(encoding="utf-8")

        self.assertIn("Task15-class-balance-report-and-train-only-balancing.md", text)
        self.assertIn("Sequence Policy", text)
        self.assertIn("Number of sequences", text)
        self.assertIn("Padding Statistics", text)
        self.assertIn("Label Distribution", text)
        self.assertIn("Ordering and Timestamp Coverage", text)
        self.assertIn("traceability_event_uids", text)
        self.assertIn("en", written.report_paths)


def _timestamp_rows() -> list[dict[str, object]]:
    return [
        {
            "host": "h1",
            "event_uid": "e3",
            "event_timestamp": "2026-01-01T00:00:03",
            "feature_a": 3,
            "feature_b": 30,
            "label_binary": 0,
            "label_status": "explicit_label",
            "label_source": "fixture",
        },
        {
            "host": "h1",
            "event_uid": "e1",
            "event_timestamp": "2026-01-01T00:00:01",
            "feature_a": 1,
            "feature_b": 10,
            "label_binary": 0,
            "label_status": "explicit_label",
            "label_source": "fixture",
        },
        {
            "host": "h1",
            "event_uid": "e5",
            "event_timestamp": "2026-01-01T00:00:05",
            "feature_a": 5,
            "feature_b": 50,
            "label_binary": 0,
            "label_status": "explicit_label",
            "label_source": "fixture",
        },
        {
            "host": "h1",
            "event_uid": "e2",
            "event_timestamp": "2026-01-01T00:00:02",
            "feature_a": 2,
            "feature_b": 20,
            "label_binary": 1,
            "label_status": "explicit_label",
            "label_source": "fixture",
        },
        {
            "host": "h1",
            "event_uid": "e4",
            "event_timestamp": "2026-01-01T00:00:04",
            "feature_a": 4,
            "feature_b": 40,
            "label_binary": None,
            "label_status": "unlabeled",
            "label_source": "none",
        },
    ]


def _event_order_rows() -> list[dict[str, object]]:
    return [
        {"host": "h1", "event_uid": "o3", "event_order": 3, "feature_a": 3, "label_binary": 1, "label_status": "explicit_label", "label_source": "fixture"},
        {"host": "h1", "event_uid": "o1", "event_order": 1, "feature_a": 1, "label_binary": 0, "label_status": "explicit_label", "label_source": "fixture"},
        {"host": "h1", "event_uid": "o2", "event_order": 2, "feature_a": 2, "label_binary": 0, "label_status": "explicit_label", "label_source": "fixture"},
    ]


if __name__ == "__main__":
    unittest.main()
