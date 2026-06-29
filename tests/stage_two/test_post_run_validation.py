from __future__ import annotations

from dataclasses import dataclass
import unittest

from scripts.stage_two.quality.post_run_validation import (
    forbidden_x_columns,
    split_contamination_details,
    trace_chain_errors,
)


class PostRunValidationContractsTest(unittest.TestCase):
    def test_split_contamination_detects_mixed_role_and_source_format(self) -> None:
        details = split_contamination_details(
            expected_branch="host",
            expected_role="TRAIN",
            expected_source_format="txt",
            observed_branch_values={"host"},
            observed_role_values={"TRAIN", "TEST"},
            observed_source_format_values={"txt", "json"},
        )

        self.assertTrue(details["contaminated"])
        self.assertEqual(details["observed"]["dataset_role"], ["TEST", "TRAIN"])
        self.assertEqual(details["observed"]["source_format"], ["json", "txt"])

    def test_forbidden_x_columns_detects_label_and_source_leakage(self) -> None:
        self.assertEqual(
            forbidden_x_columns({"metric_value", "label_binary", "dataset_role", "source_file_path"}),
            ("dataset_role", "label_binary", "source_file_path"),
        )

    def test_trace_chain_reports_broken_parser_link(self) -> None:
        artifact = _Artifact(id=10, parser_run_id=99, file_id=5)

        errors = trace_chain_errors(
            artifact=artifact,
            parser_run=None,
            dataset_file=None,
            dataset=None,
        )

        self.assertIn("parser_run id=99 was not found", errors)

    def test_trace_chain_requires_chunk_parent_metadata(self) -> None:
        artifact = _Artifact(id=10, parser_run_id=7, file_id=5)
        parser_run = _ParserRun(id=7, file_id=5)
        dataset_file = _DatasetFile(
            id=5,
            dataset_id=3,
            file_path="chunk-0001.txt",
            metadata_json={"parent_file_id": 4},
        )
        dataset = _Dataset(id=3)

        errors = trace_chain_errors(
            artifact=artifact,
            parser_run=parser_run,
            dataset_file=dataset_file,
            dataset=dataset,
        )

        self.assertIn("chunk metadata has parent_file_id but no original_source_path", errors)
        self.assertIn("chunk metadata has parent_file_id but no chunk_index", errors)


@dataclass(frozen=True)
class _Artifact:
    id: int
    parser_run_id: int
    file_id: int


@dataclass(frozen=True)
class _ParserRun:
    id: int
    file_id: int


@dataclass(frozen=True)
class _DatasetFile:
    id: int
    dataset_id: int
    file_path: str
    metadata_json: dict[str, object]


@dataclass(frozen=True)
class _Dataset:
    id: int


if __name__ == "__main__":
    unittest.main()
