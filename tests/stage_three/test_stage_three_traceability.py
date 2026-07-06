from __future__ import annotations

import unittest
from types import SimpleNamespace

from scripts.stage_three.quality.common import FAIL, PASS
from scripts.stage_three.quality.traceability import (
    TRACEABILITY_BLOCKING_STATUS,
    trace_model_ready_artifact,
)


class StageThreeTraceabilityTest(unittest.TestCase):
    def test_reconstructs_complete_model_ready_chain(self) -> None:
        model_ready = _model_ready(feature_artifact_id=20)
        chain = trace_model_ready_artifact(
            FakeTraceSession(
                (
                    model_ready,
                    _feature(normalized_artifact_id=30),
                    _normalized(parser_run_id=40, file_id=50, dataset_id=60),
                    _parser_run(),
                    _dataset_file(),
                    _dataset(),
                )
            ),
            model_ready_artifact_id=10,
        )

        self.assertEqual(chain.status, PASS)
        self.assertEqual(chain.model_ready_artifact_id, 10)
        self.assertEqual(chain.feature_artifact_id, 20)
        self.assertEqual(chain.normalized_artifact_id, 30)
        self.assertEqual(chain.parser_run_id, 40)
        self.assertEqual(chain.dataset_file_id, 50)
        self.assertEqual(chain.dataset_id, 60)
        self.assertEqual(chain.raw_source_path, r"C:\datasets\raw\dns.csv")
        self.assertEqual(chain.missing_links, [])

    def test_reports_missing_links_and_blocks_artifact(self) -> None:
        model_ready = _model_ready(feature_artifact_id=None)
        chain = trace_model_ready_artifact(
            FakeTraceSession((model_ready, None, None, None, None, None)),
            model_ready_artifact_id=10,
            apply_blocking_status=True,
        )

        self.assertEqual(chain.status, FAIL)
        self.assertIn("feature_artifact", chain.missing_links)
        self.assertIn("raw_source", chain.missing_links)
        self.assertEqual(model_ready.status, TRACEABILITY_BLOCKING_STATUS)


class FakeTraceSession:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self.row = row

    def execute(self, statement: object) -> "FakeTraceResult":
        return FakeTraceResult(self.row)


class FakeTraceResult:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self.row = row

    def first(self) -> tuple[object, ...] | None:
        return self.row


def _model_ready(*, feature_artifact_id: int | None) -> SimpleNamespace:
    return SimpleNamespace(
        id=10,
        feature_artifact_id=feature_artifact_id,
        role="TRAIN",
        branch="dns",
        data_type="X",
        artifact_path="parquet/model_ready/exp/dns/tree_unscaled/TRAIN/X.parquet",
        status="SUCCESS",
    )


def _feature(*, normalized_artifact_id: int | None) -> SimpleNamespace:
    return SimpleNamespace(
        id=20,
        normalized_artifact_id=normalized_artifact_id,
        role="TRAIN",
        branch="dns",
        feature_group="dns_lexical",
        feature_path="parquet/features/dns_lexical/dns/TRAIN/schema=v1/part.parquet",
        status="SUCCESS",
    )


def _normalized(*, parser_run_id: int, file_id: int, dataset_id: int) -> SimpleNamespace:
    return SimpleNamespace(
        id=30,
        parser_run_id=parser_run_id,
        file_id=file_id,
        dataset_id=dataset_id,
        role="TRAIN",
        branch="dns",
        normalized_path="parquet/normalized/dns/TRAIN/part.parquet",
        status="SUCCESS",
    )


def _parser_run() -> SimpleNamespace:
    return SimpleNamespace(id=40, parser_name="DnsCsvParser", parser_version="v1", status="SUCCESS")


def _dataset_file() -> SimpleNamespace:
    return SimpleNamespace(
        id=50,
        role="TRAIN",
        branch="dns",
        file_path=r"C:\datasets\raw\dns.csv",
        file_name="dns.csv",
        status="PARSED",
    )


def _dataset() -> SimpleNamespace:
    return SimpleNamespace(id=60, name="proposal-dns", slug="proposal-dns", role="TRAIN", branch="dns")


if __name__ == "__main__":
    unittest.main()
