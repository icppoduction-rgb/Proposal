from __future__ import annotations

import unittest
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Any

from scripts.db.models import DatasetFile
from scripts.stage_two.execution import (
    ExecutionRuntimeSettings,
    RetryPolicy,
    WorkUnit,
    WorkUnitExecutor,
    WorkUnitPlanner,
    WorkUnitResult,
)
from scripts.stage_two.execution.executor import WorkerExecutionRequest
from scripts.stage_two.normalization.options import NormalizationOptions


@dataclass(frozen=True)
class _FakeParser:
    parser_name: str = "host_line_log_parser"
    parser_version: str = "v1"
    parser_class: str = "HostLineLogParser"
    normalized_schema_version: str = "v1"


@dataclass(frozen=True)
class _FakeResolution:
    parser: _FakeParser | None
    diagnostics: tuple[Any, ...] = ()


class _FakeResolver:
    def __init__(self, parser: _FakeParser | None = _FakeParser()) -> None:
        self.parser = parser

    def resolve_with_diagnostics(
        self,
        *,
        branch: str,
        role: str,
        source_format: str,
    ) -> _FakeResolution:
        return _FakeResolution(parser=self.parser)


class _FakeFileRepository:
    def __init__(self, files: list[DatasetFile]) -> None:
        self.files = files

    def get_files_ready_for_parsing(
        self,
        *,
        branch: str | None = None,
        role: str | None = None,
        source_format: str | None = None,
        limit: int | None = None,
        file_ids: tuple[int, ...] | None = None,
        source_group: str | None = None,
    ) -> list[DatasetFile]:
        result = [
            file
            for file in self.files
            if file.status == "READY_FOR_PARSING"
            and file.branch == branch
            and file.role == role
            and file.source_format == source_format
            and (file_ids is None or file.id in file_ids)
        ]
        return result[:limit] if limit is not None else result


class _FakeSession:
    pass


class WorkUnitPlannerTest(unittest.TestCase):
    def test_planner_builds_units_only_for_ready_exact_bucket(self) -> None:
        files = [
            _file(1, "one.log", status="READY_FOR_PARSING"),
            _file(2, "two.log", status="PARSED"),
            _file(3, "three.log", status="READY_FOR_PARSING", role="TEST"),
            _file(4, "four.log", status="READY_FOR_PARSING", source_format="syslog"),
        ]
        planner = WorkUnitPlanner(
            _FakeSession(),  # type: ignore[arg-type]
            file_repository=_FakeFileRepository(files),  # type: ignore[arg-type]
            resolver=_FakeResolver(),  # type: ignore[arg-type]
        )

        plan = planner.build_format_plan(
            branch="host",
            role="TRAIN",
            source_format="auth.log",
            limit=None,
            file_ids=None,
            options=NormalizationOptions(),
        )

        self.assertEqual([unit.dataset_file_id for unit in plan.work_units], [1])
        self.assertEqual(plan.parser_name, "host_line_log_parser")
        self.assertEqual(plan.work_units[0].schema_version, "v1")
        self.assertEqual(plan.work_units[0].engine, "cpu")

    def test_planner_resume_skips_existing_successful_artifacts(self) -> None:
        files = [
            _file(1, "done.log", status="READY_FOR_PARSING"),
            _file(2, "todo.log", status="READY_FOR_PARSING"),
        ]
        planner = WorkUnitPlanner(
            _FakeSession(),  # type: ignore[arg-type]
            file_repository=_FakeFileRepository(files),  # type: ignore[arg-type]
            resolver=_FakeResolver(),  # type: ignore[arg-type]
        )
        planner._has_successful_artifact = lambda unit: unit.dataset_file_id == 1  # type: ignore[method-assign]

        plan = planner.build_format_plan(
            branch="host",
            role="TRAIN",
            source_format="auth.log",
            limit=None,
            file_ids=None,
            options=NormalizationOptions(resume=True),
        )

        self.assertEqual([unit.dataset_file_id for unit in plan.skipped_units], [1])
        self.assertEqual([unit.dataset_file_id for unit in plan.work_units], [2])

    def test_planner_builds_chunk_units_and_resume_skips_completed_chunk(self) -> None:
        chunk = _file(10, "large.part-000001.log", status="READY_FOR_PARSING")
        chunk.metadata_json = {
            "parent_file_id": 7,
            "chunk_index": 1,
            "chunk_path": chunk.file_path,
            "original_source_path": "/tmp/large.log",
            "source_order_preserved": True,
        }
        planner = WorkUnitPlanner(
            _FakeSession(),  # type: ignore[arg-type]
            file_repository=_FakeFileRepository([chunk]),  # type: ignore[arg-type]
            resolver=_FakeResolver(),  # type: ignore[arg-type]
        )
        planner._has_successful_artifact = lambda unit: unit.chunk_id == "7:1"  # type: ignore[method-assign]

        plan = planner.build_format_plan(
            branch="host",
            role="TRAIN",
            source_format="auth.log",
            limit=None,
            file_ids=None,
            options=NormalizationOptions(resume=True),
        )

        self.assertEqual(plan.work_units, ())
        self.assertEqual(len(plan.skipped_units), 1)
        self.assertEqual(plan.skipped_units[0].dataset_file_id, 10)
        self.assertEqual(plan.skipped_units[0].chunk_id, "7:1")


class WorkUnitExecutorTest(unittest.TestCase):
    def test_bounded_executor_does_not_submit_all_futures_at_once(self) -> None:
        recorder = _ExecutorRecorder()
        executor = WorkUnitExecutor(
            worker=_successful_worker,
            executor_factory=recorder.factory,
        )
        units = tuple(_unit(index) for index in range(1, 7))

        results = executor.execute(
            units,
            options=NormalizationOptions(workers=2),
            runtime_settings=ExecutionRuntimeSettings(max_workers=2, max_pending_futures=2),
            retry_policy=RetryPolicy(),
        )

        self.assertEqual(len(results), 6)
        self.assertLessEqual(recorder.max_pending_observed, 2)
        self.assertEqual(recorder.submitted, 6)

    def test_executor_keeps_going_after_one_work_unit_fails(self) -> None:
        executor = WorkUnitExecutor(worker=_partially_failing_worker)
        units = tuple(_unit(index) for index in range(1, 4))

        results = executor.execute(
            units,
            options=NormalizationOptions(workers=1),
            runtime_settings=ExecutionRuntimeSettings(max_workers=1, max_pending_futures=1),
            retry_policy=RetryPolicy(max_error_samples=1),
        )

        self.assertEqual([result.status for result in results], ["PARSED", "FAILED", "PARSED"])
        self.assertEqual(results[1].error_samples, ("parse failed",))


class _ExecutorRecorder:
    def __init__(self) -> None:
        self.submitted = 0
        self.current_pending = 0
        self.max_pending_observed = 0

    def factory(self, *, max_workers: int) -> "_RecordingExecutor":
        return _RecordingExecutor(self, max_workers=max_workers)


class _RecordingExecutor:
    def __init__(self, recorder: _ExecutorRecorder, *, max_workers: int) -> None:
        self.recorder = recorder
        self.max_workers = max_workers

    def __enter__(self) -> "_RecordingExecutor":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        return False

    def submit(
        self,
        worker: Any,
        unit: WorkUnit,
        request: WorkerExecutionRequest,
    ) -> Future[WorkUnitResult]:
        self.recorder.submitted += 1
        self.recorder.current_pending += 1
        self.recorder.max_pending_observed = max(
            self.recorder.max_pending_observed,
            self.recorder.current_pending,
        )
        future: Future[WorkUnitResult] = _RecordedFuture(self.recorder)
        future.set_result(worker(unit, request))
        return future


class _RecordedFuture(Future[WorkUnitResult]):
    def __init__(self, recorder: _ExecutorRecorder) -> None:
        super().__init__()
        self.recorder = recorder
        self.counted = False

    def result(self, timeout: float | None = None) -> WorkUnitResult:
        if not self.counted:
            self.recorder.current_pending -= 1
            self.counted = True
        return super().result(timeout=timeout)


def _successful_worker(unit: WorkUnit, request: WorkerExecutionRequest) -> WorkUnitResult:
    return WorkUnitResult(work_unit=unit, status="PARSED", artifact_id=unit.dataset_file_id)


def _partially_failing_worker(unit: WorkUnit, request: WorkerExecutionRequest) -> WorkUnitResult:
    if unit.dataset_file_id == 2:
        return WorkUnitResult(
            work_unit=unit,
            status="FAILED",
            error="parse failed",
            error_samples=request.retry_policy.trim_error_samples(["parse failed", "ignored"]),
        )
    return WorkUnitResult(work_unit=unit, status="PARSED", artifact_id=unit.dataset_file_id)


def _unit(index: int) -> WorkUnit:
    return WorkUnit(
        branch="host",
        role="TRAIN",
        source_format="auth.log",
        dataset_id=1,
        dataset_file_id=index,
        source_path=f"/tmp/{index}.log",
        parser_name="host_line_log_parser",
        parser_version="v1",
        schema_version="v1",
    )


def _file(
    file_id: int,
    file_name: str,
    *,
    status: str,
    role: str = "TRAIN",
    source_format: str = "auth.log",
) -> DatasetFile:
    return DatasetFile(
        id=file_id,
        dataset_id=1,
        file_path=f"/tmp/{file_name}",
        file_name=file_name,
        source_format=source_format,
        role=role,
        branch="host",
        status=status,
        file_size_bytes=100,
    )


if __name__ == "__main__":
    unittest.main()
