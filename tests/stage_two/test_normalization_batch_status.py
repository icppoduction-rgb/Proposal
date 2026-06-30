from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.db.models import DatasetFile
from scripts.stage_two.normalization.host_service import HostNormalizationService
from scripts.stage_two.normalization.options import NormalizationOptions
from scripts.stage_two.normalization.performance import NormalizationPerformance
from scripts.stage_two.parsers.base import ParserContext, ParserResult


class NormalizationBatchStatusTest(unittest.TestCase):
    def test_host_service_preserves_skipped_status_from_no_event_batch(self) -> None:
        service = HostNormalizationService.__new__(HostNormalizationService)
        service.options = NormalizationOptions(batch_size=100, max_output_part_rows=100)
        dataset_file = DatasetFile(
            id=1,
            dataset_id=2,
            file_path="helper.txt",
            file_name="helper.txt",
            source_format="txt",
            role="TRAIN",
            branch="host",
            status="READY_FOR_PARSING",
            file_size_bytes=10,
        )
        context = ParserContext(
            dataset_id=2,
            file_id=1,
            dataset_name="host-train-txt",
            dataset_role="TRAIN",
            branch="host",
            source_format="txt",
            source_file_path="helper.txt",
            source_file_hash="hash",
            parser_run_id=3,
        )

        def parse_batches(*_: object, **__: object):
            yield ParserResult(
                rows_read=0,
                rows_parsed=0,
                rows_failed=0,
                events=[],
                warnings=["parser_report_status=SKIPPED"],
                status_override="SKIPPED",
                status_reason="helper file",
            )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "helper.txt"
            path.write_text("helper", encoding="utf-8")
            result, artifact, output_path, _modality = service._parse_and_write_batches(
                parse_batches,
                path,
                context,
                dataset_file=dataset_file,
                parser_run_id=3,
                schema_version_id=4,
                schema_name="normalized_event",
                schema_version="v1",
                performance=NormalizationPerformance(),
            )

        self.assertIsNone(artifact)
        self.assertIsNone(output_path)
        self.assertEqual(result.file_status, "SKIPPED")
        self.assertEqual(result.parser_run_status, "SKIPPED")
        self.assertEqual(result.status_decision.reason, "helper file")


if __name__ == "__main__":
    unittest.main()
