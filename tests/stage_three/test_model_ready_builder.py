from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.stage_three.model_ready.builder import (
    TASK17_REPORT_FILENAME,
    build_model_ready_artifacts,
)
from scripts.stage_three.model_ready.registry import write_model_ready_row_batches
from scripts.stage_three.model_ready.report import save_model_ready_builder_reports


class ModelReadyBuilderTest(unittest.TestCase):
    def test_builds_separate_artifacts_registers_catalog_rows_and_split_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feature_artifacts = _write_feature_artifacts(root)
            repository = FakeArtifactRepository(feature_artifacts)

            result = build_model_ready_artifacts(
                repository,
                experiment_id="exp-unit",
                branch="dns",
                preprocessing_profile="tree_unscaled",
                target="label_binary",
                storage_root=root,
                resume=False,
            )

            self.assertEqual(result.status, "SUCCESS")
            self.assertEqual(result.roles, ["TRAIN", "VALIDATION", "TEST"])
            self.assertEqual(result.feature_count, 2)
            self.assertEqual(result.x_schema, ["dns_query_length", "dns_entropy"])
            self.assertEqual(len(repository.registered_values), 14)

            train_x = root / "parquet" / "model_ready" / "exp-unit" / "dns" / "tree_unscaled" / "TRAIN" / "X.parquet"
            train_y = train_x.with_name("y.parquet")
            train_metadata = train_x.with_name("metadata.parquet")
            train_traceability = train_x.with_name("traceability.parquet")
            self.assertTrue(train_x.exists())
            self.assertTrue(train_y.exists())
            self.assertTrue(train_metadata.exists())
            self.assertTrue(train_traceability.exists())

            x_table = pq.read_table(train_x)
            self.assertEqual(x_table.schema.names, ["dns_query_length", "dns_entropy"])
            self.assertNotIn("label_binary", x_table.schema.names)
            self.assertNotIn("source_path", x_table.schema.names)

            y_table = pq.read_table(train_y)
            self.assertIn("label_binary", y_table.schema.names)
            self.assertEqual(y_table.num_rows, 2)

            split_index = root / "parquet" / "model_ready" / "exp-unit" / "dns" / "tree_unscaled" / "EXPERIMENTS" / "split_index.parquet"
            preprocessing_metadata = split_index.with_name("preprocessing_metadata.parquet")
            self.assertTrue(split_index.exists())
            self.assertTrue(preprocessing_metadata.exists())
            self.assertEqual(pq.read_table(split_index).num_rows, 6)

            data_types = [values["data_type"] for values in repository.registered_values]
            self.assertEqual(data_types.count("metadata"), 3)
            self.assertEqual(data_types.count("traceability"), 3)
            self.assertIn("split_index", data_types)
            self.assertIn("preprocessing_metadata", data_types)
            self.assertEqual(result.role_results[0].target_distribution, {"0": 1, "1": 1})

    def test_resume_reuses_existing_successful_catalog_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feature_artifacts = _write_feature_artifacts(root)
            repository = FakeArtifactRepository(feature_artifacts)

            first = build_model_ready_artifacts(
                repository,
                experiment_id="exp-resume",
                branch="dns",
                preprocessing_profile="tree_unscaled",
                target="label_binary",
                role="TRAIN",
                storage_root=root,
            )
            first_registered_count = len(repository.registered_values)
            second = build_model_ready_artifacts(
                repository,
                experiment_id="exp-resume",
                branch="dns",
                preprocessing_profile="tree_unscaled",
                target="label_binary",
                role="TRAIN",
                storage_root=root,
                resume=True,
            )

            self.assertEqual(len(repository.registered_values), first_registered_count)
            self.assertTrue(second.role_results[0].artifacts[0].resumed)
            self.assertEqual(
                second.role_results[0].artifacts[0].catalog_id,
                first.role_results[0].artifacts[0].catalog_id,
            )

    def test_fails_on_x_schema_mismatch_between_roles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feature_artifacts = _write_feature_artifacts(root, validation_extra_column=True)
            repository = FakeArtifactRepository(feature_artifacts)

            with self.assertRaisesRegex(ValueError, "X schema mismatch"):
                build_model_ready_artifacts(
                    repository,
                    experiment_id="exp-mismatch",
                    branch="dns",
                    preprocessing_profile="tree_unscaled",
                    target="label_binary",
                    storage_root=root,
                )

    def test_report_contains_task17_required_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feature_artifacts = _write_feature_artifacts(root)
            repository = FakeArtifactRepository(feature_artifacts)
            result = build_model_ready_artifacts(
                repository,
                experiment_id="exp-report",
                branch="dns",
                preprocessing_profile="tree_unscaled",
                target="label_binary",
                role="TRAIN",
                storage_root=root,
            )
            with (
                patch("scripts.stage_three.reports.path_utils.REPORTS_RU_STAGE_THREE", str(root / "ru")),
                patch("scripts.stage_three.reports.path_utils.REPORTS_EN_STAGE_THREE", str(root / "en")),
            ):
                written = save_model_ready_builder_reports(result)

            report = root / "en" / TASK17_REPORT_FILENAME
            self.assertTrue(report.exists())
            text = report.read_text(encoding="utf-8")

        self.assertIn("Task16-sequence-window-builder.md", text)
        self.assertIn("Experiment ID", text)
        self.assertIn("Artifact Paths and Catalog IDs", text)
        self.assertIn("X/y Row Counts", text)
        self.assertIn("Target Distribution", text)
        self.assertIn("Feature count", text)
        self.assertIn("en", written.report_paths)

    def test_streaming_writer_preserves_schema_when_first_batch_is_null(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "y.parquet"
            result = write_model_ready_row_batches(
                [
                    [{"sample_uid": "s1", "label_binary": None}],
                    [{"sample_uid": "s2", "label_binary": 1}],
                ],
                columns=["sample_uid", "label_binary"],
                schema=pa.schema([("sample_uid", pa.string()), ("label_binary", pa.int64())]),
                final_path=path,
                storage_root=temp_dir,
                compression="zstd",
            )

            table = pq.read_table(path)

        self.assertEqual(result.row_count, 2)
        self.assertEqual(table.schema.field("label_binary").type, pa.int64())
        self.assertEqual(table.column("label_binary").to_pylist(), [None, 1])


class FakeArtifactRepository:
    def __init__(self, feature_artifacts: dict[str, list[SimpleNamespace]]) -> None:
        self.feature_artifacts = feature_artifacts
        self.registered_values: list[dict[str, Any]] = []

    def list_successful_feature_artifacts(self, **values: Any) -> list[SimpleNamespace]:
        return list(self.feature_artifacts.get(values["role"], []))

    def find_successful_model_ready_artifact(self, **values: Any) -> SimpleNamespace | None:
        for index, registered in enumerate(self.registered_values, start=1):
            if all(registered.get(key) == values[key] for key in ("branch", "role", "data_type", "artifact_path", "schema_version")):
                return SimpleNamespace(id=9000 + index, sample_count=registered["sample_count"], feature_count=registered["feature_count"])
        return None

    def register_model_ready_artifact(self, **values: Any) -> SimpleNamespace:
        self.registered_values.append(values)
        return SimpleNamespace(id=9000 + len(self.registered_values), **values)


def _write_feature_artifacts(
    root: Path,
    *,
    validation_extra_column: bool = False,
) -> dict[str, list[SimpleNamespace]]:
    artifacts: dict[str, list[SimpleNamespace]] = {}
    for index, role in enumerate(("TRAIN", "VALIDATION", "TEST"), start=1):
        path = root / "parquet" / "features" / "dns_lexical" / "dns" / role / "schema=v1" / "part.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = _feature_rows(role)
        if validation_extra_column and role == "VALIDATION":
            for row in rows:
                row["dns_label_count"] = 3
        pq.write_table(pa.Table.from_pylist(rows), path)
        relative_path = path.relative_to(root).as_posix()
        artifacts[role] = [
            SimpleNamespace(
                id=100 + index,
                feature_path=relative_path,
                metadata_json={"parts": [{"path": relative_path, "row_count": len(rows)}]},
            )
        ]
    return artifacts


def _feature_rows(role: str) -> list[dict[str, object]]:
    return [
        {
            "sample_uid": f"{role.lower()}-s1",
            "event_uid": f"{role.lower()}-e1",
            "dataset_name": "proposal-dns",
            "dataset_role": role,
            "branch": "dns",
            "feature_group": "dns_lexical",
            "source_path": rf"C:\datasets\proposal\{role.lower()}\dns-1.csv",
            "dns_query_length": 11,
            "dns_entropy": 3.2,
            "label_binary": 1,
            "label_status": "explicit_label",
            "label_source": "fixture",
        },
        {
            "sample_uid": f"{role.lower()}-s2",
            "event_uid": f"{role.lower()}-e2",
            "dataset_name": "proposal-dns",
            "dataset_role": role,
            "branch": "dns",
            "feature_group": "dns_lexical",
            "source_path": rf"C:\datasets\proposal\{role.lower()}\dns-2.csv",
            "dns_query_length": 10,
            "dns_entropy": 2.8,
            "label_binary": 0,
            "label_status": "explicit_label",
            "label_source": "fixture",
        },
    ]


if __name__ == "__main__":
    unittest.main()
