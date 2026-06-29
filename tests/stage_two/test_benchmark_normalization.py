from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.stage_two.benchmark import (
    BYTES_PER_GB,
    BenchmarkArtifactSample,
    BenchmarkInputFile,
    BenchmarkNormalizationRequest,
    BenchmarkNormalizationResult,
    BenchmarkReportPaths,
    BenchmarkRuntimeSample,
    calculate_benchmark_metrics,
    save_benchmark_reports,
)
from scripts.stage_two.cli import _parse_benchmark_normalization_args
from scripts.stage_two.normalization.runner import (
    NormalizeFileResult,
    NormalizeFormatRequest,
    NormalizeFormatResult,
)


class BenchmarkMetricsTest(unittest.TestCase):
    def test_calculate_throughput_and_target_projection(self) -> None:
        selected_files = (
            BenchmarkInputFile(file_id=1, file_path="one.txt", size_bytes=2 * BYTES_PER_GB),
            BenchmarkInputFile(file_id=2, file_path="two.txt", size_bytes=3 * BYTES_PER_GB),
            BenchmarkInputFile(file_id=3, file_path="failed.txt", size_bytes=1 * BYTES_PER_GB),
        )
        normalize_result = _normalize_result(
            files=(
                NormalizeFileResult(file_id=1, file_path="one.txt", status="PARSED"),
                NormalizeFileResult(file_id=2, file_path="two.txt", status="PARTIALLY_PARSED"),
                NormalizeFileResult(file_id=3, file_path="failed.txt", status="FAILED"),
            )
        )

        metrics = calculate_benchmark_metrics(
            selected_files=selected_files,
            normalize_result=normalize_result,
            runtime_sample=BenchmarkRuntimeSample(
                elapsed_seconds=3600.0,
                process_cpu_seconds=120.0,
                peak_python_memory_bytes=64 * 1024 * 1024,
            ),
            artifact_sample=BenchmarkArtifactSample(
                rows_read=1000,
                events_emitted=900,
                parquet_output_size=12345,
                parser_time_seconds=12.0,
                write_time_seconds=6.0,
                parser_time_file_count=2,
                write_time_artifact_count=3,
            ),
        )

        self.assertEqual(metrics.input_bytes, 6 * BYTES_PER_GB)
        self.assertEqual(metrics.processed_bytes, 5 * BYTES_PER_GB)
        self.assertEqual(metrics.processed_gb, 5.0)
        self.assertEqual(metrics.gb_per_hour, 5.0)
        self.assertEqual(metrics.estimated_time_for_17gb, 3.4)
        self.assertFalse(metrics.meets_3_hour_target)
        self.assertEqual(metrics.successful_files, 1)
        self.assertEqual(metrics.partial_files, 1)
        self.assertEqual(metrics.failed_files, 1)
        self.assertEqual(metrics.average_parser_time_per_file, 6.0)
        self.assertEqual(metrics.average_write_time_per_artifact, 2.0)

    def test_report_generation_writes_markdown_and_json(self) -> None:
        metrics = calculate_benchmark_metrics(
            selected_files=(BenchmarkInputFile(file_id=1, file_path="one.txt", size_bytes=BYTES_PER_GB),),
            normalize_result=_normalize_result(
                files=(NormalizeFileResult(file_id=1, file_path="one.txt", status="PARSED"),)
            ),
            runtime_sample=BenchmarkRuntimeSample(elapsed_seconds=600.0),
            artifact_sample=BenchmarkArtifactSample(rows_read=10, events_emitted=10, parquet_output_size=100),
        )
        result = BenchmarkNormalizationResult(
            status="SUCCESS",
            request=BenchmarkNormalizationRequest(branch="host", role="TEST", source_format="txt"),
            normalize_request=NormalizeFormatRequest(branch="host", role="TEST", source_format="txt", resume=True),
            selected_files=(BenchmarkInputFile(file_id=1, file_path="one.txt", size_bytes=BYTES_PER_GB),),
            metrics=metrics,
            report_paths=BenchmarkReportPaths("", "", "", ""),
            normalize_result=_normalize_result(
                files=(NormalizeFileResult(file_id=1, file_path="one.txt", status="PARSED"),)
            ),
            resume_forced=True,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            paths = save_benchmark_reports(result, report_root=temp_dir)

            for path in (paths.ru_markdown, paths.en_markdown, paths.ru_json, paths.en_json):
                self.assertTrue(Path(path).exists(), path)

            markdown = Path(paths.en_markdown).read_text(encoding="utf-8")
            self.assertIn("gb_per_hour", markdown)
            self.assertIn("estimated_time_for_17gb_seconds", markdown)
            self.assertIn("failed_files", markdown)

            payload = json.loads(Path(paths.en_json).read_text(encoding="utf-8"))
            self.assertEqual(payload["metrics"]["gb_per_hour"], 6.0)
            self.assertTrue(payload["resume_forced"])

    def test_parse_benchmark_normalization_args(self) -> None:
        benchmark_request, normalize_request = _parse_benchmark_normalization_args(
            [
                "--branch",
                "HOST",
                "--role",
                "test",
                "--format",
                "txt",
                "--limit",
                "10000",
                "--sample-ratio",
                "0.25",
                "--resource-profile",
                "fast",
                "--workers",
                "6",
                "--dry-run",
            ]
        )

        self.assertEqual(benchmark_request.branch, "host")
        self.assertEqual(benchmark_request.role, "TEST")
        self.assertEqual(benchmark_request.source_format, "txt")
        self.assertEqual(benchmark_request.limit, 10000)
        self.assertEqual(benchmark_request.sample_ratio, 0.25)
        self.assertTrue(benchmark_request.dry_run)
        self.assertEqual(normalize_request.resource_profile, "fast")
        self.assertEqual(normalize_request.workers, 6)

    def test_parse_rejects_invalid_sample_ratio(self) -> None:
        with self.assertRaisesRegex(ValueError, "sample-ratio"):
            _parse_benchmark_normalization_args(
                [
                    "--branch",
                    "host",
                    "--role",
                    "TEST",
                    "--format",
                    "txt",
                    "--sample-ratio",
                    "1.5",
                ]
            )


def _normalize_result(*, files: tuple[NormalizeFileResult, ...]) -> NormalizeFormatResult:
    parsed = sum(1 for file in files if file.status == "PARSED")
    partial = sum(1 for file in files if file.status == "PARTIALLY_PARSED")
    failed = sum(1 for file in files if file.status == "FAILED")
    skipped = sum(1 for file in files if file.status == "SKIPPED")
    unsupported = sum(1 for file in files if file.status == "UNSUPPORTED_FORMAT")
    return NormalizeFormatResult(
        status="SUCCESS" if not failed else "PARTIAL_SUCCESS",
        branch="host",
        role="TEST",
        source_format="txt",
        limit=None,
        selected=len(files),
        processed=len(files),
        normalized=parsed + partial,
        parsed=parsed,
        partially_parsed=partial,
        failed=failed,
        skipped=skipped,
        unsupported=unsupported,
        errors=failed,
        parser_name="host_line_log_parser",
        parser_class="HostLineLogParser",
        files=files,
    )


if __name__ == "__main__":
    unittest.main()
