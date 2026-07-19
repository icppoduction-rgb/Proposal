from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.stage_three.extraction.artifact_writer import FeatureArtifactParquetWriter
from scripts.stage_three.extraction.base import (
    FeatureExtractionArtifact,
    FeatureExtractionResult,
    NormalizedArtifactInput,
)
from scripts.stage_three.extraction.registry import (
    FEATURE_ARTIFACT_SCHEMA_VERSION,
    FeatureArtifactRegistryService,
)


class FeatureArtifactRegistrationTest(unittest.TestCase):
    def test_atomic_writer_uses_stage_three_path_zstd_and_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            writer = FeatureArtifactParquetWriter(storage_root=root, compression="zstd")
            result = writer.write_table(
                _feature_table(),
                feature_group="dns_lexical",
                branch="dns",
                role="TRAIN",
                schema_version=FEATURE_ARTIFACT_SCHEMA_VERSION,
                run_id="unit",
            )

            expected = (
                root
                / "parquet"
                / "features"
                / "dns_lexical"
                / "dns"
                / "TRAIN"
                / "schema=v1"
                / "part-unit.parquet"
            )
            self.assertEqual(result.absolute_path, expected)
            self.assertEqual(result.relative_path, "parquet/features/dns_lexical/dns/TRAIN/schema=v1/part-unit.parquet")
            self.assertTrue(expected.exists())
            self.assertEqual(pq.read_table(expected).num_rows, 2)
            self.assertEqual(result.row_count, 2)
            self.assertEqual(result.column_count, 3)
            self.assertEqual(len(result.content_hash_sha256), 64)
            self.assertFalse(list(expected.parent.glob("*.tmp")))
            compression = pq.read_metadata(expected).row_group(0).column(0).compression
            self.assertEqual(compression, "ZSTD")

    def test_registry_records_catalog_row_with_traceability_and_part_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            writer = FeatureArtifactParquetWriter(storage_root=root)
            part = writer.write_table(
                _feature_table(),
                feature_group="dns_lexical",
                branch="dns",
                role="TRAIN",
                schema_version=FEATURE_ARTIFACT_SCHEMA_VERSION,
                run_id="unit",
                part_index=0,
            )
            source = NormalizedArtifactInput(
                artifact_id=101,
                dataset_id=202,
                role="TRAIN",
                branch="dns",
                normalized_path="parquet/normalized/dns/TRAIN/source.parquet",
                row_count=2,
            )
            output = FeatureExtractionArtifact(
                normalized_artifact_id=101,
                feature_group="dns_lexical",
                feature_path=str(part.absolute_path.parent),
                parts=[str(part.absolute_path)],
                rows_read=2,
                rows_written=2,
                columns_created=["dns_query_length", "dns_label_length"],
                missing_ratios={"dns_query_length": 0.0, "dns_label_length": 0.0},
                runtime_seconds=0.01,
                peak_rss_gb=None,
            )
            result = FeatureExtractionResult(
                status="SUCCESS",
                branch="dns",
                role="TRAIN",
                feature_group="dns_lexical",
                input_normalized_artifacts=[source],
                output_feature_artifacts=[output],
                rows_read=2,
                rows_written=2,
                columns_created=["dns_query_length", "dns_label_length"],
                missing_ratios={"dns_query_length": 0.0, "dns_label_length": 0.0},
                runtime_seconds=0.01,
                backend_used="cpu",
                peak_rss_gb=None,
            )
            repository = FakeArtifactRepository()

            annotated, summary = FeatureArtifactRegistryService(storage_root=root).register_result(
                repository,
                result,
            )

            self.assertEqual(summary.registered_catalog_ids, [9001])
            self.assertEqual(annotated.registered_catalog_ids, [9001])
            self.assertEqual(annotated.output_feature_artifacts[0].catalog_artifact_id, 9001)
            values = repository.registered_values[0]
            self.assertIsNotNone(values["artifact_uid"])
            self.assertEqual(values["dataset_id"], 202)
            self.assertEqual(values["normalized_artifact_id"], 101)
            self.assertEqual(values["feature_group"], "dns_lexical")
            self.assertEqual(values["feature_schema_version"], "v1")
            self.assertEqual(values["row_count"], 2)
            self.assertEqual(values["feature_count"], 2)
            self.assertEqual(values["metadata_json"]["source_artifact_ids"], [101])
            self.assertEqual(values["metadata_json"]["parts"][0]["row_count"], 2)
            self.assertEqual(len(values["metadata_json"]["parts"][0]["content_hash_sha256"]), 64)
            self.assertEqual(len(values["metadata_json"]["content_hash_sha256"]), 64)

    def test_resume_filters_successful_matching_feature_artifacts(self) -> None:
        artifacts = [
            NormalizedArtifactInput(artifact_id=101, dataset_id=202, role="TRAIN", branch="dns", normalized_path="a.parquet"),
            NormalizedArtifactInput(artifact_id=102, dataset_id=202, role="TRAIN", branch="dns", normalized_path="b.parquet"),
        ]
        repository = FakeArtifactRepository(
            existing={
                101: SimpleNamespace(
                    id=7001,
                    feature_path="parquet/features/dns_lexical/dns/TRAIN/schema=v1/part-existing.parquet",
                )
            }
        )

        pending, skipped = FeatureArtifactRegistryService().filter_resume_inputs(
            repository,
            artifacts,
            branch="dns",
            role="TRAIN",
            feature_group="dns_lexical",
            schema_version="v1",
            resume=True,
        )

        self.assertEqual([artifact.artifact_id for artifact in pending], [102])
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0].catalog_artifact_id, 7001)
        self.assertEqual(skipped[0].normalized_artifact_id, 101)

    def test_resume_registers_complete_existing_disk_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "parquet" / "features" / "dns_lexical" / "dns" / "TRAIN" / "schema=v1"
            output_dir.mkdir(parents=True)
            part_path = output_dir / "part-exp-resume-artifact-101-00000.parquet"
            pq.write_table(_feature_table(), part_path, compression="zstd")
            artifacts = [
                NormalizedArtifactInput(
                    artifact_id=101,
                    dataset_id=202,
                    role="TRAIN",
                    branch="dns",
                    normalized_path="a.parquet",
                    row_count=2,
                ),
            ]
            repository = FakeArtifactRepository()

            pending, skipped = FeatureArtifactRegistryService(storage_root=root).filter_resume_inputs(
                repository,
                artifacts,
                branch="dns",
                role="TRAIN",
                feature_group="dns_lexical",
                schema_version="v1",
                resume=True,
                run_id="exp-resume",
                columns_created=["dns_query_length", "dns_label_length"],
                recover_disk_outputs=True,
            )

            self.assertEqual(pending, [])
            self.assertEqual(len(skipped), 1)
            self.assertEqual(skipped[0].normalized_artifact_id, 101)
            self.assertEqual(skipped[0].reason, "existing complete feature parquet output registered during resume")
            self.assertEqual(len(repository.registered_values), 1)
            values = repository.registered_values[0]
            self.assertEqual(values["normalized_artifact_id"], 101)
            self.assertEqual(values["row_count"], 2)
            self.assertEqual(values["feature_path"], "parquet/features/dns_lexical/dns/TRAIN/schema=v1")

    def test_resume_does_not_register_incomplete_existing_disk_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "parquet" / "features" / "dns_lexical" / "dns" / "TRAIN" / "schema=v1"
            output_dir.mkdir(parents=True)
            part_path = output_dir / "part-exp-resume-artifact-101-00000.parquet"
            pq.write_table(_feature_table(), part_path, compression="zstd")
            artifacts = [
                NormalizedArtifactInput(
                    artifact_id=101,
                    dataset_id=202,
                    role="TRAIN",
                    branch="dns",
                    normalized_path="a.parquet",
                    row_count=3,
                ),
            ]
            repository = FakeArtifactRepository()

            pending, skipped = FeatureArtifactRegistryService(storage_root=root).filter_resume_inputs(
                repository,
                artifacts,
                branch="dns",
                role="TRAIN",
                feature_group="dns_lexical",
                schema_version="v1",
                resume=True,
                run_id="exp-resume",
                columns_created=["dns_query_length", "dns_label_length"],
                recover_disk_outputs=True,
            )

            self.assertEqual([artifact.artifact_id for artifact in pending], [101])
            self.assertEqual(skipped, [])
            self.assertEqual(repository.registered_values, [])


class FakeArtifactRepository:
    def __init__(self, existing: dict[int, SimpleNamespace] | None = None) -> None:
        self.existing = existing or {}
        self.registered_values: list[dict[str, Any]] = []

    def find_successful_feature_artifact(self, **values: Any) -> SimpleNamespace | None:
        return self.existing.get(int(values["normalized_artifact_id"]))

    def register_feature_artifact(self, **values: Any) -> SimpleNamespace:
        self.registered_values.append(values)
        return SimpleNamespace(id=9000 + len(self.registered_values), metadata_json=values["metadata_json"])


def _feature_table() -> pa.Table:
    return pa.table(
        {
            "sample_uid": ["s1", "s2"],
            "dns_query_length": [12, 24],
            "dns_label_length": [3, 5],
        }
    )


if __name__ == "__main__":
    unittest.main()
