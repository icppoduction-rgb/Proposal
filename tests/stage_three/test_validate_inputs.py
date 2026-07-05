from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy.exc import SQLAlchemyError

from scripts.db.models import Dataset, DatasetFile, NormalizedArtifact, ParserRun
from scripts.stage_three.cli import _database_failure_result
from scripts.stage_three.readiness.report import TASK04_REPORT_FILENAME, save_validate_inputs_reports
from scripts.stage_three.readiness.validator import (
    FAIL,
    PASS,
    WARN,
    _ArtifactRow,
    validate_stage_three_inputs,
)
from scripts.stage_three.requests import ValidateInputsRequest


class StageThreeValidateInputsTest(unittest.TestCase):
    def test_validate_inputs_passes_for_readable_successful_normalized_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_root = Path(temp_dir)
            relative_path = "parquet/normalized/dns/TRAIN/events/sample/schema=v1/part.parquet"
            _write_normalized_parquet(storage_root / relative_path)
            schema_paths = _write_schema_files(storage_root)
            rows = [_artifact_row(relative_path=relative_path)]

            with patch(
                "scripts.stage_three.readiness.validator._fetch_normalized_rows",
                return_value=rows,
            ):
                result = validate_stage_three_inputs(
                    _request(role="TRAIN"),
                    session=object(),  # type: ignore[arg-type]
                    storage_root=storage_root,
                    feature_schema_path=schema_paths[0],
                    model_ready_schema_path=schema_paths[1],
                )

            self.assertEqual(result.status, PASS)
            self.assertEqual(result.normalized_artifact_count, 1)
            self.assertEqual(result.blocking_issues, [])

    def test_validate_inputs_warns_for_allowed_partial_and_unlabeled_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_root = Path(temp_dir)
            relative_path = "parquet/normalized/dns/TRAIN/events/sample/schema=v1/part.parquet"
            _write_normalized_parquet(storage_root / relative_path, label_status="unlabeled")
            schema_paths = _write_schema_files(storage_root)
            rows = [
                _artifact_row(
                    relative_path=relative_path,
                    artifact_status="PARTIAL_SUCCESS",
                    parser_status="PARTIAL_SUCCESS",
                    file_status="PARTIALLY_PARSED",
                )
            ]

            with patch(
                "scripts.stage_three.readiness.validator._fetch_normalized_rows",
                return_value=rows,
            ):
                result = validate_stage_three_inputs(
                    _request(role="TRAIN"),
                    session=object(),  # type: ignore[arg-type]
                    storage_root=storage_root,
                    feature_schema_path=schema_paths[0],
                    model_ready_schema_path=schema_paths[1],
                )

            self.assertEqual(result.status, WARN)
            self.assertEqual(result.blocking_issues, [])
            self.assertIn("PARTIAL_SUCCESS", result.parser_runs_by_status)

    def test_validate_inputs_fails_when_parquet_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_root = Path(temp_dir)
            schema_paths = _write_schema_files(storage_root)
            rows = [_artifact_row(relative_path="parquet/normalized/dns/TRAIN/missing.parquet")]

            with patch(
                "scripts.stage_three.readiness.validator._fetch_normalized_rows",
                return_value=rows,
            ):
                result = validate_stage_three_inputs(
                    _request(role="TRAIN"),
                    session=object(),  # type: ignore[arg-type]
                    storage_root=storage_root,
                    feature_schema_path=schema_paths[0],
                    model_ready_schema_path=schema_paths[1],
                )

            self.assertEqual(result.status, FAIL)
            self.assertTrue(result.blocking_issues)
            self.assertIn("missing", " ".join(result.blocking_issues).lower())

    def test_test_role_fit_metadata_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_root = Path(temp_dir)
            relative_path = "parquet/normalized/dns/TEST/events/sample/schema=v1/part.parquet"
            _write_normalized_parquet(storage_root / relative_path, role="TEST")
            schema_paths = _write_schema_files(storage_root)
            rows = [
                _artifact_row(
                    relative_path=relative_path,
                    role="TEST",
                    metadata_json={"fit_preprocessing": True},
                )
            ]

            with patch(
                "scripts.stage_three.readiness.validator._fetch_normalized_rows",
                return_value=rows,
            ):
                result = validate_stage_three_inputs(
                    _request(role="TEST"),
                    session=object(),  # type: ignore[arg-type]
                    storage_root=storage_root,
                    feature_schema_path=schema_paths[0],
                    model_ready_schema_path=schema_paths[1],
                )

            self.assertEqual(result.status, FAIL)
            self.assertTrue(
                any("TEST artifacts" in issue for issue in result.blocking_issues),
                result.blocking_issues,
            )

    def test_report_writer_creates_ru_and_en_task04_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_root = Path(temp_dir)
            result = validate_stage_three_inputs_empty_for_report()

            with (
                patch(
                    "scripts.stage_three.reports.path_utils.REPORTS_RU_STAGE_THREE",
                    str(report_root / "reports" / "ru" / "stage-three"),
                ),
                patch(
                    "scripts.stage_three.reports.path_utils.REPORTS_EN_STAGE_THREE",
                    str(report_root / "reports" / "en" / "stage-three"),
                ),
            ):
                written = save_validate_inputs_reports(result)

            self.assertEqual(Path(written.report_paths["ru"]).name, TASK04_REPORT_FILENAME)
            self.assertTrue(Path(written.report_paths["ru"]).exists())
            self.assertTrue(Path(written.report_paths["en"]).exists())
            self.assertIn("Task03-stage-three-cli-skeleton.md", Path(written.report_paths["en"]).read_text())

    def test_database_failure_result_is_blocking_fail(self) -> None:
        result = _database_failure_result(_request(role="TRAIN"), SQLAlchemyError("connection timeout expired"))

        self.assertEqual(result.status, FAIL)
        self.assertEqual(result.normalized_artifact_count, 0)
        self.assertTrue(result.blocking_issues)
        self.assertEqual(result.checks[0].name, "catalog_connection")


def validate_stage_three_inputs_empty_for_report():
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_root = Path(temp_dir)
        schema_paths = _write_schema_files(storage_root)
        with patch(
            "scripts.stage_three.readiness.validator._fetch_normalized_rows",
            return_value=[],
        ):
            return validate_stage_three_inputs(
                _request(role="TRAIN"),
                session=object(),  # type: ignore[arg-type]
                storage_root=storage_root,
                feature_schema_path=schema_paths[0],
                model_ready_schema_path=schema_paths[1],
            )


def _request(*, role: str) -> ValidateInputsRequest:
    return ValidateInputsRequest(command="validate-inputs", branch="dns", role=role)


def _artifact_row(
    *,
    relative_path: str,
    role: str = "TRAIN",
    artifact_status: str = "SUCCESS",
    parser_status: str = "SUCCESS",
    file_status: str = "PARSED",
    metadata_json: dict | None = None,
) -> _ArtifactRow:
    dataset = Dataset(
        id=10,
        name="sample",
        slug="sample",
        branch="dns",
        role=role,
        is_active=True,
    )
    dataset_file = DatasetFile(
        id=20,
        dataset_id=10,
        file_path="raw/sample.csv",
        file_name="sample.csv",
        source_format="csv",
        role=role,
        branch="dns",
        status=file_status,
    )
    parser_run = ParserRun(
        id=30,
        run_uid=uuid4(),
        file_id=20,
        parser_name="DnsCsvParser",
        parser_version="v1",
        status=parser_status,
    )
    artifact = NormalizedArtifact(
        id=40,
        artifact_uid=uuid4(),
        dataset_id=10,
        file_id=20,
        parser_run_id=30,
        role=role,
        branch="dns",
        modality="events",
        source_format="csv",
        normalized_path=relative_path,
        schema_name="normalized_event",
        schema_version="v1",
        row_count=1,
        status=artifact_status,
        metadata_json=metadata_json,
    )
    return _ArtifactRow(
        artifact=artifact,
        parser_run=parser_run,
        dataset_file=dataset_file,
        dataset=dataset,
    )


def _write_schema_files(root: Path) -> tuple[Path, Path]:
    feature_schema = root / "schemas" / "features" / "feature_artifact_v1.json"
    model_ready_schema = root / "schemas" / "model_ready" / "model_ready_v1.json"
    feature_schema.parent.mkdir(parents=True, exist_ok=True)
    model_ready_schema.parent.mkdir(parents=True, exist_ok=True)
    feature_schema.write_text("{}", encoding="utf-8")
    model_ready_schema.write_text("{}", encoding="utf-8")
    return feature_schema, model_ready_schema


def _write_normalized_parquet(path: Path, *, role: str = "TRAIN", label_status: str = "explicit_label") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "event_uid": "event-1",
        "dataset_id": 10,
        "file_id": 20,
        "dataset_name": "sample",
        "dataset_role": role,
        "branch": "dns",
        "source_format": "csv",
        "source_file_path": "raw/sample.csv",
        "parser_name": "DnsCsvParser",
        "parser_version": "v1",
        "parser_run_id": 30,
        "schema_name": "normalized_event",
        "schema_version": "v1",
        "label_binary": 1 if label_status != "unlabeled" else None,
        "label_source": "embedded_column" if label_status != "unlabeled" else "none",
        "label_status": label_status,
    }
    pq.write_table(pa.Table.from_pylist([row]), path)


if __name__ == "__main__":
    unittest.main()
