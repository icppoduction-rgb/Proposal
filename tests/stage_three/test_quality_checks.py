from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.stage_three.quality.common import FAIL, PASS, WARN, register_quality_records
from scripts.stage_three.quality.feature_quality import run_feature_quality_checks
from scripts.stage_three.quality.model_ready_quality import run_model_ready_quality_checks
from scripts.stage_three.quality.report import save_stage_three_quality_reports
from scripts.stage_three.quality.runner import TASK18_REPORT_FILENAME, StageThreeQualityResult


class StageThreeQualityChecksTest(unittest.TestCase):
    def test_quality_checks_pass_and_register_data_quality_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feature_artifact = _write_feature_artifact(root)
            model_ready_artifacts = _write_model_ready_artifacts(root)
            _write_class_balance_report(root)

            feature_checks = run_feature_quality_checks([feature_artifact], storage_root=root)
            with (
                patch("scripts.stage_three.reports.path_utils.REPORTS_RU_STAGE_THREE", str(root / "ru")),
                patch("scripts.stage_three.reports.path_utils.REPORTS_EN_STAGE_THREE", str(root / "en")),
            ):
                model_ready_checks = run_model_ready_quality_checks(model_ready_artifacts, storage_root=root)
            checks = [*feature_checks, *model_ready_checks]

            self.assertTrue(checks)
            self.assertTrue(all(check.status == PASS for check in checks), [check.to_dict() for check in checks])

            repository = FakeDataQualityRepository()
            registered = register_quality_records(
                repository,
                checks,
                report_path=str(root / "quality.md"),
                report_paths={"ru": str(root / "ru.md"), "en": str(root / "en.md")},
            )

            self.assertEqual(len(repository.created_values), len(checks))
            self.assertTrue(all(check.quality_report_id is not None for check in registered))
            self.assertTrue(all(values["status"] == "SUCCESS" for values in repository.created_values))

            result = StageThreeQualityResult(
                status=PASS,
                experiment_id="exp-quality",
                branch="dns",
                role=None,
                feature_group="dns_lexical",
                feature_artifact_count=1,
                model_ready_artifact_count=len(model_ready_artifacts),
                preprocessing_artifact_count=0,
                checks=registered,
                quality_report_ids=[int(check.quality_report_id or 0) for check in registered],
            )
            with (
                patch("scripts.stage_three.reports.path_utils.REPORTS_RU_STAGE_THREE", str(root / "ru")),
                patch("scripts.stage_three.reports.path_utils.REPORTS_EN_STAGE_THREE", str(root / "en")),
            ):
                written = save_stage_three_quality_reports(result)

            report = root / "en" / TASK18_REPORT_FILENAME
            self.assertTrue(report.exists())
            text = report.read_text(encoding="utf-8")
            self.assertIn("Task17-model-ready-builder.md", text)
            self.assertIn("PASS/WARN/FAIL Table", text)
            self.assertIn("Quality Report Catalog IDs", text)
            self.assertIn("Blocking Issues", text)
            self.assertIn("en", written.report_paths)

    def test_model_ready_x_forbidden_column_is_blocking_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifacts = _write_model_ready_artifacts(root, x_forbidden_column=True)
            _write_class_balance_report(root)

            with (
                patch("scripts.stage_three.reports.path_utils.REPORTS_RU_STAGE_THREE", str(root / "ru")),
                patch("scripts.stage_three.reports.path_utils.REPORTS_EN_STAGE_THREE", str(root / "en")),
            ):
                checks = run_model_ready_quality_checks(artifacts, storage_root=root)
            forbidden = [
                check
                for check in checks
                if check.check_name == "X_feature_columns_do_not_contain_forbidden_fields"
            ]
            failed_forbidden = [check for check in forbidden if check.status == FAIL]

            self.assertTrue(forbidden)
            self.assertTrue(failed_forbidden)
            self.assertTrue(failed_forbidden[0].blocking)
            self.assertEqual(failed_forbidden[0].leakage_issue_count, 1)

    def test_timestamp_missing_passes_when_feature_group_does_not_require_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feature_artifact = _write_minimal_feature_artifact(root, feature_group="unit_lexical")
            checks = run_feature_quality_checks(
                [feature_artifact],
                storage_root=root,
                feature_catalog=_feature_catalog(source_fields=["domain", "features_json"]),
            )

            timestamp_checks = [check for check in checks if check.check_name == "timestamp_coverage_calculated"]

            self.assertEqual(len(timestamp_checks), 1)
            self.assertEqual(timestamp_checks[0].status, PASS)
            self.assertFalse(timestamp_checks[0].details["timestamp_required"])

    def test_timestamp_missing_warns_when_feature_group_requires_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feature_artifact = _write_minimal_feature_artifact(root, feature_group="unit_temporal")
            checks = run_feature_quality_checks(
                [feature_artifact],
                storage_root=root,
                feature_catalog=_feature_catalog(
                    feature_group="unit_temporal",
                    source_fields=["event_timestamp", "domain"],
                ),
            )

            timestamp_checks = [check for check in checks if check.check_name == "timestamp_coverage_calculated"]

            self.assertEqual(len(timestamp_checks), 1)
            self.assertEqual(timestamp_checks[0].status, WARN)
            self.assertTrue(timestamp_checks[0].details["timestamp_required"])


class FakeDataQualityRepository:
    def __init__(self) -> None:
        self.created_values: list[dict[str, Any]] = []

    def create_report(self, **values: Any) -> SimpleNamespace:
        self.created_values.append(values)
        return SimpleNamespace(id=len(self.created_values), **values)


def _write_feature_artifact(root: Path) -> SimpleNamespace:
    path = root / "parquet" / "features" / "dns_lexical" / "dns" / "TRAIN" / "schema=v1" / "part.parquet"
    rows = [
        {
            "sample_uid": "train-s1",
            "event_uid": "train-e1",
            "dataset_name": "proposal-dns",
            "dataset_role": "TRAIN",
            "branch": "dns",
            "feature_group": "dns_lexical",
            "role": "TRAIN",
            "source_normalized_path": "parquet/normalized/dns/train/part-1.parquet",
            "source_path": r"C:\datasets\proposal\train\dns-1.csv",
            "source_event_uid_refs": ["train-e1"],
            "feature_schema_name": "feature_artifact",
            "feature_schema_version": "v1",
            "created_at": "2026-01-01T00:00:00Z",
            "event_timestamp": "2026-01-01T00:00:00Z",
            "dns_query_length": 11,
            "dns_subdomain_length": 5,
            "dns_label_count": 2,
            "dns_label_avg_len": 4.5,
            "dns_label_max_len": 7,
            "dns_digit_count": 1,
            "dns_special_char_count": 0,
            "label_binary": 1,
            "label_status": "explicit_label",
            "label_source": "fixture",
        },
        {
            "sample_uid": "train-s2",
            "event_uid": "train-e2",
            "dataset_name": "proposal-dns",
            "dataset_role": "TRAIN",
            "branch": "dns",
            "feature_group": "dns_lexical",
            "role": "TRAIN",
            "source_normalized_path": "parquet/normalized/dns/train/part-2.parquet",
            "source_path": r"C:\datasets\proposal\train\dns-2.csv",
            "source_event_uid_refs": ["train-e2"],
            "feature_schema_name": "feature_artifact",
            "feature_schema_version": "v1",
            "created_at": "2026-01-01T00:00:01Z",
            "event_timestamp": "2026-01-01T00:00:01Z",
            "dns_query_length": 10,
            "dns_subdomain_length": 4,
            "dns_label_count": 2,
            "dns_label_avg_len": 4.0,
            "dns_label_max_len": 6,
            "dns_digit_count": 0,
            "dns_special_char_count": 0,
            "label_binary": 0,
            "label_status": "explicit_label",
            "label_source": "fixture",
        },
    ]
    _write_rows(path, rows)
    relative_path = path.relative_to(root).as_posix()
    return SimpleNamespace(
        id=101,
        feature_group="dns_lexical",
        feature_path=relative_path,
        metadata_json={"parts": [{"path": relative_path}]},
    )


def _write_minimal_feature_artifact(root: Path, *, feature_group: str) -> SimpleNamespace:
    path = root / "parquet" / "features" / feature_group / "dns" / "TRAIN" / "schema=v1" / "part.parquet"
    rows = [
        {"sample_uid": "sample-1", "dns_query_length": 11, "label_binary": 1},
        {"sample_uid": "sample-2", "dns_query_length": 10, "label_binary": 0},
    ]
    _write_rows(path, rows)
    relative_path = path.relative_to(root).as_posix()
    return SimpleNamespace(
        id=102,
        feature_group=feature_group,
        feature_path=relative_path,
        metadata_json={"parts": [{"path": relative_path}]},
    )


def _feature_catalog(
    *,
    source_fields: list[str],
    feature_group: str = "unit_lexical",
) -> dict[str, object]:
    return {
        "feature_groups": {
            feature_group: {
                "extractor_mappings": [
                    {
                        "source_fields": source_fields,
                        "output_features": ["dns_query_length"],
                    }
                ],
                "features": [
                    {
                        "name": "dns_query_length",
                        "dtype": "integer",
                        "nullable": False,
                        "preprocessing": {"missing": "zero"},
                    }
                ],
            }
        }
    }


def _write_model_ready_artifacts(
    root: Path,
    *,
    x_forbidden_column: bool = False,
) -> list[SimpleNamespace]:
    artifacts: list[SimpleNamespace] = []
    artifact_id = 200
    for role in ("TRAIN", "VALIDATION", "TEST"):
        base = root / "parquet" / "model_ready" / "exp-quality" / "dns" / "tree_unscaled" / role
        x_rows = [
            {"dns_query_length": 11, "dns_entropy": 3.2},
            {"dns_query_length": 10, "dns_entropy": 2.8},
        ]
        if x_forbidden_column and role == "TRAIN":
            x_rows[0]["label_binary"] = 1
            x_rows[1]["label_binary"] = 0
        artifacts.append(_write_model_ready_artifact(root, base / "X.parquet", artifact_id, role, "X", x_rows))
        artifact_id += 1
        artifacts.append(
            _write_model_ready_artifact(
                root,
                base / "y.parquet",
                artifact_id,
                role,
                "y",
                [
                    {"sample_uid": f"{role.lower()}-s1", "label_binary": 1},
                    {"sample_uid": f"{role.lower()}-s2", "label_binary": 0},
                ],
            )
        )
        artifact_id += 1
        artifacts.append(
            _write_model_ready_artifact(
                root,
                base / "metadata.parquet",
                artifact_id,
                role,
                "metadata",
                [{"sample_uid": f"{role.lower()}-s1"}, {"sample_uid": f"{role.lower()}-s2"}],
            )
        )
        artifact_id += 1
        artifacts.append(
            _write_model_ready_artifact(
                root,
                base / "traceability.parquet",
                artifact_id,
                role,
                "traceability",
                [{"sample_uid": f"{role.lower()}-s1"}, {"sample_uid": f"{role.lower()}-s2"}],
            )
        )
        artifact_id += 1
    preprocessing_path = (
        root
        / "parquet"
        / "model_ready"
        / "exp-quality"
        / "dns"
        / "tree_unscaled"
        / "EXPERIMENTS"
        / "preprocessing_metadata.parquet"
    )
    artifacts.append(
        _write_model_ready_artifact(
            root,
            preprocessing_path,
            artifact_id,
            "EXPERIMENTS",
            "preprocessing_metadata",
            [{"fitted_on_role": "TRAIN", "target": "label_binary"}],
            metadata_json={"experiment_id": "exp-quality", "target": "label_binary", "fitted_on_role": "TRAIN"},
        )
    )
    return artifacts


def _write_model_ready_artifact(
    root: Path,
    path: Path,
    artifact_id: int,
    role: str,
    data_type: str,
    rows: list[dict[str, object]],
    *,
    metadata_json: dict[str, object] | None = None,
) -> SimpleNamespace:
    _write_rows(path, rows)
    return SimpleNamespace(
        id=artifact_id,
        role=role,
        data_type=data_type,
        artifact_path=path.relative_to(root).as_posix(),
        metadata_json=metadata_json or {"experiment_id": "exp-quality", "target": "label_binary"},
    )


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), path)


def _write_class_balance_report(root: Path) -> None:
    report = root / "ru" / "Task15-class-balance-report-and-train-only-balancing.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("# Task 15\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
