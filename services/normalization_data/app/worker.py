from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from sqlalchemy import select

from cybersec_platform.contracts.api import DatasetManifest, JobStatus, ValidationStatus
from cybersec_platform.db import Dataset, TaskRecord
from cybersec_platform.db.session import async_session_factory, get_settings
from cybersec_platform.ml.normalization import ContractValidationError, NormalizationEngine, UnsupportedDatasetFormatError
from cybersec_platform.observability import configure_logging, log_event, observed, request_context
from cybersec_platform.tasks import celery_app

configure_logging("normalization-data")
logger = logging.getLogger(__name__)
_worker_loop: asyncio.AbstractEventLoop | None = None


def _run_async(coroutine):
    """EN: Execute a coroutine on a single reusable event loop per worker process.
    RU: Выполняет coroutine в одном переиспользуемом event loop на процесс воркера.
    """

    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop.run_until_complete(coroutine)


@observed("validate_dataset")
async def _validate_dataset(dataset_id: str) -> None:
    """EN: Validate a raw dataset, normalize it, and persist quality metadata.
    RU: Валидирует сырой датасет, нормализует его и сохраняет метаданные качества.
    """

    settings = get_settings()
    with request_context({"type": "task", "service": "normalization-data", "dataset_id": dataset_id}):
        async with async_session_factory() as session:
            dataset = await session.get(Dataset, dataset_id)
            if dataset is None:
                log_event(logger, logging.WARNING, "Dataset validation skipped", function="_validate_dataset", dataset_id=dataset_id)
                return
            task_result = await session.execute(
                select(TaskRecord)
                .where(TaskRecord.object_type == "dataset", TaskRecord.object_id == dataset_id)
                .order_by(TaskRecord.created_at.desc(), TaskRecord.id.desc())
            )
            task_record = task_result.scalars().first()
            if task_record:
                task_record.status = JobStatus.RUNNING.value
            try:
                engine = NormalizationEngine()
                output_path = str(Path(settings.normalized_data_path) / f"{dataset.id}.csv")
                report_path = str(Path(settings.reports_path) / "normalization" / f"{dataset.id}.json")
                payload = engine.validate_and_normalize(
                    dataset.storage_path,
                    DatasetManifest.model_validate(dataset.manifest),
                    output_path,
                    report_path=report_path,
                )
                dataset.validation_status = ValidationStatus.VALIDATED.value
                dataset.validation_errors = {}
                dataset.normalized_path = payload.normalized_path
                dataset.detected_format = payload.detected_format
                dataset.normalization_profile = payload.normalization_profile
                dataset.normalization_summary = payload.normalization_summary
                dataset.normalization_report_path = payload.normalization_report_path
                if task_record:
                    task_record.status = JobStatus.COMPLETED.value
                    task_record.detail = {
                        "row_count": payload.row_count,
                        "columns": payload.columns,
                        "normalization_profile": payload.normalization_profile,
                    }
                log_event(
                    logger,
                    logging.INFO,
                    "Dataset normalization completed",
                    function="_validate_dataset",
                    dataset_id=dataset_id,
                    row_count=payload.row_count,
                    normalization_profile=payload.normalization_profile,
                    detected_format=payload.detected_format,
                )
            except (FileNotFoundError, ContractValidationError, UnsupportedDatasetFormatError) as exc:
                dataset.validation_status = ValidationStatus.FAILED.value
                dataset.validation_errors = {"error": str(exc)}
                dataset.normalized_path = None
                if task_record:
                    task_record.status = JobStatus.FAILED.value
                    task_record.detail = {"error": str(exc)}
                logger.exception(
                    "Dataset normalization failed",
                    extra={"function": "_validate_dataset", "error": {"type": type(exc).__name__, "message": str(exc)}},
                )
            except Exception as exc:
                dataset.validation_status = ValidationStatus.FAILED.value
                dataset.validation_errors = {"error": "Unexpected normalization error", "detail": str(exc)}
                dataset.normalized_path = None
                if task_record:
                    task_record.status = JobStatus.FAILED.value
                    task_record.detail = {"error": str(exc)}
                logger.exception(
                    "Dataset normalization failed with unexpected error",
                    extra={"function": "_validate_dataset", "error": {"type": type(exc).__name__, "message": str(exc)}},
                )
            await session.commit()


@celery_app.task(name="normalization.validate_dataset")
def validate_dataset(dataset_id: str) -> None:
    """EN: Celery entry point for dataset normalization and validation.
    RU: Celery entry point для нормализации и валидации датасета.
    """

    _run_async(_validate_dataset(dataset_id))
