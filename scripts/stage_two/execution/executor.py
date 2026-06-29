"""Bounded WorkUnit execution for Stage Two normalization."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import FIRST_COMPLETED, Future, ProcessPoolExecutor, wait
from dataclasses import dataclass
from typing import Any

from scripts.db.repositories import DatasetFileRepository
from scripts.db.session import session_scope
from scripts.stage_two.execution.progress import ProgressReporter
from scripts.stage_two.execution.retry_policy import RetryPolicy
from scripts.stage_two.execution.runtime_settings import ExecutionRuntimeSettings
from scripts.stage_two.execution.work_unit import WorkUnit, WorkUnitResult


@dataclass(frozen=True)
class WorkerExecutionRequest:
    """Pickle-safe worker payload shared by process workers."""

    options: dict[str, Any]
    retry_policy: RetryPolicy


WorkerCallable = Callable[[WorkUnit, WorkerExecutionRequest], WorkUnitResult]


class WorkUnitExecutor:
    """Execute WorkUnits with bounded ProcessPool submission."""

    def __init__(
        self,
        *,
        worker: WorkerCallable | None = None,
        executor_factory: Callable[..., Any] = ProcessPoolExecutor,
        progress: ProgressReporter | None = None,
    ) -> None:
        self.worker = worker or execute_work_unit_worker
        self.executor_factory = executor_factory
        self.progress = progress or ProgressReporter()

    def execute(
        self,
        work_units: Iterable[WorkUnit],
        *,
        options: Any,
        runtime_settings: ExecutionRuntimeSettings,
        retry_policy: RetryPolicy | None = None,
    ) -> tuple[WorkUnitResult, ...]:
        """Execute units sequentially for one worker, otherwise through a bounded process pool."""
        units = tuple(work_units)
        policy = retry_policy or RetryPolicy()
        if not units:
            return ()
        worker_request = WorkerExecutionRequest(
            options=_options_payload(options),
            retry_policy=policy,
        )
        if runtime_settings.max_workers <= 1:
            return self._execute_sequential(units, worker_request)
        return self._execute_bounded_process_pool(units, worker_request, runtime_settings)

    def _execute_sequential(
        self,
        units: tuple[WorkUnit, ...],
        worker_request: WorkerExecutionRequest,
    ) -> tuple[WorkUnitResult, ...]:
        results: list[WorkUnitResult] = []
        for index, unit in enumerate(units, start=1):
            result = self._call_worker(unit, worker_request)
            results.append(result)
            self.progress.emit_file_processed(result, current=index, total=len(units))
        return tuple(results)

    def _execute_bounded_process_pool(
        self,
        units: tuple[WorkUnit, ...],
        worker_request: WorkerExecutionRequest,
        runtime_settings: ExecutionRuntimeSettings,
    ) -> tuple[WorkUnitResult, ...]:
        results: list[WorkUnitResult] = []
        iterator = iter(units)
        pending: set[Future[WorkUnitResult]] = set()
        submitted = 0

        with self.executor_factory(max_workers=runtime_settings.max_workers) as executor:
            while True:
                while len(pending) < runtime_settings.max_pending_futures:
                    try:
                        unit = next(iterator)
                    except StopIteration:
                        break
                    pending.add(executor.submit(self.worker, unit, worker_request))
                    submitted += 1

                if not pending:
                    break

                done, pending = wait(pending, return_when=FIRST_COMPLETED)
                for future in done:
                    result = future.result()
                    results.append(result)
                    self.progress.emit_file_processed(result, current=len(results), total=len(units))

                if submitted >= len(units) and not pending:
                    break

        return tuple(results)

    def _call_worker(
        self,
        unit: WorkUnit,
        worker_request: WorkerExecutionRequest,
    ) -> WorkUnitResult:
        try:
            return self.worker(unit, worker_request)
        except Exception as exc:
            return WorkUnitResult(
                work_unit=unit,
                status="FAILED",
                error=_exception_message(exc),
                error_samples=worker_request.retry_policy.trim_error_samples([_exception_message(exc)]),
            )


def execute_work_unit_worker(
    unit: WorkUnit,
    request: WorkerExecutionRequest,
) -> WorkUnitResult:
    """Process entrypoint: open an independent DB session and normalize one file."""
    from scripts.stage_two.normalization.dns_service import DnsNormalizationService
    from scripts.stage_two.normalization.host_service import HostNormalizationService
    from scripts.stage_two.normalization.options import NormalizationOptions

    options = NormalizationOptions(**request.options)
    try:
        with session_scope() as session:
            repository = DatasetFileRepository(session)
            dataset_file = repository.get(unit.dataset_file_id)
            if dataset_file is None:
                return WorkUnitResult(
                    work_unit=unit,
                    status="FAILED",
                    error="dataset file not found",
                    error_samples=request.retry_policy.trim_error_samples(["dataset file not found"]),
                )
            service_class = _service_class(unit.branch)
            artifact = service_class(session, options=options).normalize_file(dataset_file)
            return WorkUnitResult(
                work_unit=unit,
                status=dataset_file.status,
                artifact_id=getattr(artifact, "id", None),
                error=dataset_file.error_message,
                error_samples=request.retry_policy.trim_error_samples(
                    [dataset_file.error_message] if dataset_file.error_message else []
                ),
            )
    except Exception as exc:
        error_message = _exception_message(exc)
        _mark_failed_best_effort(unit, error_message)
        return WorkUnitResult(
            work_unit=unit,
            status="FAILED",
            error=error_message,
            error_samples=request.retry_policy.trim_error_samples([error_message]),
        )


def _mark_failed_best_effort(unit: WorkUnit, error_message: str) -> None:
    try:
        with session_scope() as session:
            repository = DatasetFileRepository(session)
            dataset_file = repository.get(unit.dataset_file_id)
            if dataset_file is not None:
                repository.mark_file_status(dataset_file, "FAILED", error_message=error_message)
    except Exception:
        return


def _service_class(branch: str) -> Any:
    from scripts.stage_two.normalization.dns_service import DnsNormalizationService
    from scripts.stage_two.normalization.host_service import HostNormalizationService

    if branch == "dns":
        return DnsNormalizationService
    if branch == "host":
        return HostNormalizationService
    raise ValueError("normalize-format supports only dns and host branches")


def _options_payload(options: Any) -> dict[str, Any]:
    return {
        "workers": options.workers,
        "batch_size": options.batch_size,
        "max_output_part_rows": options.max_output_part_rows,
        "packet_batch_size": options.packet_batch_size,
        "resume": options.resume,
        "packet_mode": options.packet_mode,
        "sample_size": options.sample_size,
        "hash_outputs": options.hash_outputs,
        "resource_profile": options.resource_profile,
        "engine": options.engine,
    }


def _exception_message(exc: BaseException) -> str:
    message = str(exc).strip()
    return message or type(exc).__name__
