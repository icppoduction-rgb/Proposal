from __future__ import annotations

import asyncio
import logging
import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pandas as pd
from sqlalchemy import select

from cybersec_platform.contracts.api import ArtifactStatus, DatasetManifest, FeatureSchemaDefinition, InferenceRequest, JobStatus, ValidationStatus
from cybersec_platform.db import (
    AutoTrainingArchive,
    AutoTrainingJob,
    Dataset,
    DetectionResult,
    ExplanationJob,
    ExplanationResult,
    FeatureSchema,
    InboxMessage,
    InferenceJob,
    ModelArtifact,
    TaskRecord,
    TrainingRun,
)
from cybersec_platform.db.session import async_session_factory, get_settings
from cybersec_platform.ml.auto_training import build_auto_feature_schema_definition, discover_archive_training_inputs, extract_archive
from cybersec_platform.ml.inference import InferenceEngine, load_model_bundle
from cybersec_platform.ml.normalization import CORE_EVENT_COLUMNS, ContractValidationError, NormalizationEngine
from cybersec_platform.ml.training import HybridTrainer
from cybersec_platform.observability import configure_logging, log_event, observed, request_context
from cybersec_platform.storage import ArtifactStore
from cybersec_platform.tasks import celery_app

configure_logging("training-service")
logger = logging.getLogger(__name__)
_worker_loop: asyncio.AbstractEventLoop | None = None


def _utc_now() -> datetime:
    """EN: Return a naive UTC timestamp compatible with database columns stored without timezone.
    RU: Возвращает naive UTC-отметку времени, совместимую с колонками БД без timezone.
    """

    return datetime.now(UTC).replace(tzinfo=None)


async def _get_latest_task_record(session, object_type: str, object_id: str) -> TaskRecord | None:
    """EN: Fetch the newest task record linked to a domain object.
    RU: Получает самую новую task-запись, связанную с доменным объектом.
    """

    result = await session.execute(
        select(TaskRecord)
        .where(TaskRecord.object_type == object_type, TaskRecord.object_id == object_id)
        .order_by(TaskRecord.created_at.desc(), TaskRecord.id.desc())
    )
    return result.scalars().first()


def _extract_task_headers(task) -> dict[str, str]:
    request = getattr(task, "request", None)
    raw_headers = getattr(request, "headers", None) or {}
    headers = {str(key): str(value) for key, value in dict(raw_headers).items() if value is not None}
    request_id = getattr(request, "id", None)
    if request_id and "message_id" not in headers:
        headers["message_id"] = str(request_id)
    return headers


async def _has_processed_message(session, *, consumer_name: str, message_id: str | None) -> bool:
    if not message_id:
        return False
    result = await session.execute(
        select(InboxMessage).where(InboxMessage.consumer_name == consumer_name, InboxMessage.message_id == message_id)
    )
    return result.scalar_one_or_none() is not None


async def _store_processed_message(
    session,
    *,
    consumer_name: str,
    message_id: str | None,
    topic: str,
    payload: dict,
    detail: dict,
) -> None:
    if not message_id:
        return
    session.add(
        InboxMessage(
            consumer_name=consumer_name,
            message_id=message_id,
            topic=topic,
            status="processed",
            payload=payload,
            detail=detail,
        )
    )


async def _list_model_artifacts(session, training_run_id: str) -> list[ModelArtifact]:
    result = await session.execute(
        select(ModelArtifact)
        .where(ModelArtifact.training_run_id == training_run_id)
        .order_by(ModelArtifact.created_at.asc(), ModelArtifact.id.asc())
    )
    return result.scalars().all()


async def _list_detection_results(session, inference_job_id: str) -> list[DetectionResult]:
    result = await session.execute(
        select(DetectionResult)
        .where(DetectionResult.inference_job_id == inference_job_id)
        .order_by(DetectionResult.created_at.asc(), DetectionResult.id.asc())
    )
    return result.scalars().all()


async def _get_explanation_result(session, explanation_job_id: str) -> ExplanationResult | None:
    result = await session.execute(
        select(ExplanationResult).where(ExplanationResult.explanation_job_id == explanation_job_id)
    )
    return result.scalar_one_or_none()


def _ordered_auto_training_columns(columns: set[str]) -> list[str]:
    ordered: list[str] = [column for column in CORE_EVENT_COLUMNS if column in columns]
    ordered.extend(sorted(column for column in columns if column not in set(ordered)))
    return ordered


def _prefix_auto_training_entities(normalized_output_path: str | Path, archive_name: str) -> list[str]:
    frame = pd.read_csv(normalized_output_path)
    archive_prefix = Path(archive_name).stem
    frame["entity_id"] = frame["entity_id"].map(lambda value: f"{archive_prefix}:{value}")
    frame.to_csv(normalized_output_path, index=False)
    return list(frame.columns)


def _build_combined_auto_training_frame(
    normalized_paths: list[str | Path],
    combined_output_path: str | Path,
) -> tuple[pd.DataFrame, dict[str, int]]:
    paths = [Path(path) for path in normalized_paths]
    if not paths:
        raise ContractValidationError("Automatic training did not produce any normalized inputs")

    all_columns: set[str] = set()
    for path in paths:
        frame = pd.read_csv(path, nrows=0)
        all_columns.update(str(column) for column in frame.columns)

    ordered_columns = _ordered_auto_training_columns(all_columns)
    combined_path = Path(combined_output_path)
    combined_path.parent.mkdir(parents=True, exist_ok=True)
    if combined_path.exists():
        combined_path.unlink()

    label_counter: Counter[int] = Counter()
    wrote_any_rows = False
    for index, path in enumerate(paths, start=1):
        frame = pd.read_csv(path)
        if frame.empty:
            continue
        frame = frame.reindex(columns=ordered_columns)
        labels = pd.to_numeric(frame["label"], errors="coerce").dropna().astype(int)
        label_counter.update(int(value) for value in labels.tolist())
        frame.to_csv(combined_path, mode="a", header=index == 1, index=False)
        wrote_any_rows = True

    if not wrote_any_rows:
        raise ContractValidationError("Automatic training dataset is empty after normalization")

    return pd.read_csv(combined_path), {str(key): int(value) for key, value in sorted(label_counter.items())}


def _run_async(coroutine):
    """EN: Execute a coroutine on a single reusable event loop per worker process.
    RU: Выполняет coroutine в одном переиспользуемом event loop на процесс воркера.
    """

    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop.run_until_complete(coroutine)


def _find_task(records: list[TaskRecord], object_type: str, object_id: str) -> TaskRecord | None:
    """EN: Find the first task record attached to the requested object.
    RU: Находит первую task-запись, связанную с запрошенным объектом.
    """

    for record in records:
        if record.object_type == object_type and record.object_id == object_id:
            return record
    return None


async def _refresh_auto_training_progress(
    session,
    job: AutoTrainingJob,
    task_record: TaskRecord | None,
    *,
    status: str | None = None,
    progress_percent: float | None = None,
    current_step: str | None = None,
    detail_patch: dict | None = None,
    error_message: str | None = None,
) -> None:
    if status is not None:
        job.status = status
        if task_record is not None:
            task_record.status = status
    if progress_percent is not None:
        job.progress_percent = float(max(0.0, min(progress_percent, 100.0)))
    if current_step is not None:
        job.current_step = current_step
    if detail_patch:
        job.detail = {**(job.detail or {}), **detail_patch}
        if task_record is not None:
            task_record.detail = {**(task_record.detail or {}), **detail_patch}
    if error_message is not None:
        job.error_message = error_message
        if task_record is not None:
            task_record.detail = {**(task_record.detail or {}), "error": error_message}
    await session.flush()


@observed("run_training")
async def _run_training(
    training_run_id: str,
    *,
    task_headers: dict[str, str] | None = None,
    task_name: str = "training.run_training",
) -> None:
    """EN: Execute the hybrid training pipeline and persist resulting artifacts.
    RU: Выполняет гибридный training pipeline и сохраняет итоговые артефакты.
    """

    store = ArtifactStore()
    headers = task_headers or {}
    message_id = headers.get("message_id")
    with request_context({"type": "task", "service": "training-service", "training_run_id": training_run_id}):
        async with async_session_factory() as session:
            run = await session.get(TrainingRun, training_run_id)
            if run is None or run.status == JobStatus.CANCELLED.value:
                log_event(logger, logging.WARNING, "Training run skipped", function="_run_training", training_run_id=training_run_id)
                return
            dataset = await session.get(Dataset, run.dataset_id)
            schema = await session.get(FeatureSchema, run.feature_schema_id)
            task_record = await _get_latest_task_record(session, "training_run", training_run_id)
            task_record_id = task_record.id if task_record else None
            if await _has_processed_message(session, consumer_name=task_name, message_id=message_id):
                log_event(
                    logger,
                    logging.INFO,
                    "Training run duplicate delivery skipped",
                    function="_run_training",
                    training_run_id=training_run_id,
                    message_id=message_id,
                )
                return
            existing_artifacts = await _list_model_artifacts(session, training_run_id)
            if run.status == JobStatus.COMPLETED.value and existing_artifacts:
                artifact_ids = [artifact.id for artifact in existing_artifacts]
                if task_record:
                    task_record.status = JobStatus.COMPLETED.value
                    task_record.detail = {
                        **(task_record.detail or {}),
                        "artifact_ids": artifact_ids,
                        "metrics": run.metrics,
                        "duplicate_delivery": True,
                    }
                await _store_processed_message(
                    session,
                    consumer_name=task_name,
                    message_id=message_id,
                    topic=task_name,
                    payload={"training_run_id": training_run_id},
                    detail={"artifact_ids": artifact_ids, "duplicate_delivery": True},
                )
                await session.commit()
                log_event(
                    logger,
                    logging.INFO,
                    "Training run already completed, reused persisted artifacts",
                    function="_run_training",
                    training_run_id=training_run_id,
                    artifact_ids=artifact_ids,
                )
                return
            run.status = JobStatus.RUNNING.value
            run.started_at = _utc_now()
            if task_record:
                task_record.status = JobStatus.RUNNING.value
            try:
                if dataset is None or not dataset.normalized_path or dataset.validation_status != ValidationStatus.VALIDATED.value:
                    raise ContractValidationError("Dataset must be validated and normalized before training")
                if schema is None:
                    raise ContractValidationError("Feature schema is required for training")
                schema_definition = FeatureSchemaDefinition.model_validate(schema.definition)
                reports_dir = str(Path(store.reports_dir) / "training" / training_run_id)
                training_request = dict(run.request_payload)
                trainer = HybridTrainer()
                training_payload = trainer.train(
                    dataset.normalized_path,
                    DatasetManifest.model_validate(dataset.manifest),
                    training_request,
                    schema_definition,
                    reports_dir=reports_dir,
                )
                run.metrics = training_payload["metrics"]
                artifact_ids: list[str] = []
                for model_name, model_payload in training_payload["models"].items():
                    path = store.save_model(f"{training_run_id}-{model_name}.joblib", model_payload)
                    artifact = ModelArtifact(
                        training_run_id=run.id,
                        model_name=model_name,
                        model_type=model_name,
                        artifact_path=path,
                        metrics=training_payload["metrics"]["branch_metrics"].get(model_name, training_payload["metrics"]),
                        artifact_metadata={
                            "feature_columns": training_payload["feature_columns"],
                            "required_feature_columns": training_payload["required_feature_columns"],
                            "feature_schema": training_payload["feature_schema"],
                            "feature_schema_name": schema.name,
                            "sequence_length": training_request.get("sequence_length", 50),
                            "sequence_stride": training_request.get("sequence_stride", 10),
                            **training_payload["reports"],
                        },
                        status=ArtifactStatus.CANDIDATE.value,
                    )
                    session.add(artifact)
                    await session.flush()
                    artifact_ids.append(artifact.id)
                bundle_path = store.save_model(
                    f"{training_run_id}-fusion.joblib",
                    {
                        "models": training_payload["models"],
                        "feature_columns": training_payload["feature_columns"],
                        "required_feature_columns": training_payload["required_feature_columns"],
                        "feature_schema": training_payload["feature_schema"],
                        "metrics": training_payload["metrics"],
                        "sequence_length": training_request.get("sequence_length", 50),
                        "sequence_stride": training_request.get("sequence_stride", 10),
                    },
                )
                fusion_artifact = ModelArtifact(
                    training_run_id=run.id,
                    model_name="fusion",
                    model_type="fusion",
                    artifact_path=bundle_path,
                    metrics=training_payload["metrics"],
                    artifact_metadata={
                        "feature_columns": training_payload["feature_columns"],
                        "required_feature_columns": training_payload["required_feature_columns"],
                        "feature_schema": training_payload["feature_schema"],
                        "sequence_length": training_request.get("sequence_length", 50),
                        "sequence_stride": training_request.get("sequence_stride", 10),
                        **training_payload["reports"],
                    },
                    status=ArtifactStatus.CANDIDATE.value,
                )
                session.add(fusion_artifact)
                await session.flush()
                artifact_ids.append(fusion_artifact.id)
                run.status = JobStatus.COMPLETED.value
                run.completed_at = _utc_now()
                if task_record:
                    task_record.status = JobStatus.COMPLETED.value
                    task_record.detail = {"artifact_ids": artifact_ids, "metrics": run.metrics, **training_payload["reports"]}
                await _store_processed_message(
                    session,
                    consumer_name=task_name,
                    message_id=message_id,
                    topic=task_name,
                    payload={"training_run_id": training_run_id},
                    detail={"artifact_ids": artifact_ids},
                )
                log_event(
                    logger,
                    logging.INFO,
                    "Training run completed",
                    function="_run_training",
                    training_run_id=training_run_id,
                    artifact_ids=artifact_ids,
                    metrics=run.metrics,
                )
            except Exception as exc:
                await session.rollback()
                run = await session.get(TrainingRun, training_run_id)
                if run is not None:
                    run.status = JobStatus.FAILED.value
                    run.error_message = str(exc)
                    run.completed_at = _utc_now()
                if task_record_id:
                    task_record = await session.get(TaskRecord, task_record_id)
                    if task_record is not None:
                        task_record.status = JobStatus.FAILED.value
                        task_record.detail = {"error": str(exc)}
                logger.exception(
                    "Training run failed",
                    extra={"function": "_run_training", "error": {"type": type(exc).__name__, "message": str(exc)}},
                )
            await session.commit()


@observed("run_auto_training")
async def _run_auto_training(auto_training_job_id: str) -> None:
    store = ArtifactStore()
    workspace_root = Path(store.tmp_dir) / "auto-training" / auto_training_job_id

    with request_context({"type": "task", "service": "training-service", "auto_training_job_id": auto_training_job_id}):
        async with async_session_factory() as session:
            job = await session.get(AutoTrainingJob, auto_training_job_id)
            if job is None:
                log_event(
                    logger,
                    logging.WARNING,
                    "Automatic training job skipped",
                    function="_run_auto_training",
                    auto_training_job_id=auto_training_job_id,
                )
                return

            task_record = await _get_latest_task_record(session, "auto_training_job", auto_training_job_id)
            task_record_id = task_record.id if task_record else None
            try:
                archives_result = await session.execute(
                    select(AutoTrainingArchive).where(AutoTrainingArchive.id.in_(job.archive_ids)).order_by(AutoTrainingArchive.name.asc())
                )
                archives = archives_result.scalars().all()
                if not archives:
                    raise ContractValidationError("Automatic training requires at least one uploaded archive")

                job.started_at = _utc_now()
                await _refresh_auto_training_progress(
                    session,
                    job,
                    task_record,
                    status=JobStatus.RUNNING.value,
                    progress_percent=5,
                    current_step="extracting_archives",
                    detail_patch={
                        "archive_count": len(archives),
                        "archive_names": [archive.name for archive in archives],
                    },
                )
                await session.commit()

                discovered_inputs = []
                skipped_files: list[dict[str, str]] = []
                source_type_counts: dict[str, int] = {}
                archive_summaries: list[dict[str, object]] = []
                for index, archive in enumerate(archives, start=1):
                    extraction_root = workspace_root / "extracted" / archive.id
                    extraction_root.mkdir(parents=True, exist_ok=True)
                    extracted_files = extract_archive(archive.path, extraction_root)
                    discovery = discover_archive_training_inputs(extraction_root, archive.name, archive.path)
                    discovered_inputs.extend(discovery.trainable_files)
                    skipped_files.extend(
                        [{**item, "archive_name": archive.name} for item in discovery.skipped_files]
                    )
                    if discovery.source_type is not None:
                        source_type_counts[discovery.source_type.value] = source_type_counts.get(discovery.source_type.value, 0) + len(
                            discovery.trainable_files
                        )
                    archive_summaries.append(
                        {
                            "archive_name": archive.name,
                            "extracted_file_count": len(extracted_files),
                            "trainable_file_count": len(discovery.trainable_files),
                            "skipped_file_count": len(discovery.skipped_files),
                            "source_type": discovery.source_type.value if discovery.source_type is not None else None,
                            "metadata": discovery.metadata,
                        }
                    )
                    await _refresh_auto_training_progress(
                        session,
                        job,
                        task_record,
                        progress_percent=5 + (25 * index / len(archives)),
                        detail_patch={"archive_summaries": archive_summaries},
                    )
                    await session.commit()

                if not discovered_inputs:
                    raise ContractValidationError("Uploaded archives did not yield any trainable files")

                selected_source_type = max(source_type_counts.items(), key=lambda item: (item[1], item[0]))[0] if source_type_counts else discovered_inputs[0].source_type.value
                selected_inputs = [item for item in discovered_inputs if item.source_type.value == selected_source_type]
                if not selected_inputs:
                    raise ContractValidationError("Unable to select trainable files for automatic training")

                await _refresh_auto_training_progress(
                    session,
                    job,
                    task_record,
                    progress_percent=35,
                    current_step="normalizing_archives",
                    detail_patch={
                        "selected_source_type": selected_source_type,
                        "selected_file_count": len(selected_inputs),
                        "skipped_file_count": len(skipped_files),
                    },
                )
                await session.commit()

                engine = NormalizationEngine()
                normalized_output_paths: list[str] = []
                normalized_reports: list[dict[str, object]] = []
                for index, input_file in enumerate(selected_inputs, start=1):
                    normalized_output_path = workspace_root / "normalized" / f"{index:04d}-{Path(input_file.extracted_path).stem}.csv"
                    report_path = Path(store.reports_dir) / "auto-training" / auto_training_job_id / f"{index:04d}-{Path(input_file.extracted_path).stem}.json"
                    await _refresh_auto_training_progress(
                        session,
                        job,
                        task_record,
                        progress_percent=35 + (30 * (index - 1) / len(selected_inputs)),
                        detail_patch={
                            "normalized_inputs": normalized_reports,
                            "current_normalization_input": {
                                "archive_name": input_file.archive_name,
                                "relative_path": input_file.relative_path,
                                "dataset_format": input_file.dataset_format,
                            },
                        },
                    )
                    await session.commit()
                    manifest = DatasetManifest(
                        name=f"auto-{Path(input_file.extracted_path).stem}",
                        source_type=input_file.source_type,
                        description=f"Automatically prepared from archive {input_file.archive_name}",
                        file_name=Path(input_file.extracted_path).name,
                        required_columns=["entity_id"],
                        feature_families=["process"] if input_file.source_type.value == "host" else ["network_flow"],
                        lineage={
                            "mode": "automatic_training",
                            "archive_name": input_file.archive_name,
                            "archive_relative_path": input_file.relative_path,
                        },
                        default_label=input_file.default_label,
                        default_attack_stage=input_file.default_attack_stage,
                    )
                    payload = await asyncio.to_thread(
                        engine.validate_and_normalize,
                        input_file.extracted_path,
                        manifest,
                        str(normalized_output_path),
                        str(report_path),
                    )
                    await asyncio.to_thread(_prefix_auto_training_entities, normalized_output_path, input_file.archive_name)
                    normalized_output_paths.append(str(normalized_output_path))
                    normalized_reports.append(
                        {
                            "archive_name": input_file.archive_name,
                            "relative_path": input_file.relative_path,
                            "dataset_format": input_file.dataset_format,
                            "normalization_profile": payload.normalization_profile,
                            "row_count": payload.row_count,
                            "report_path": payload.normalization_report_path,
                            "quality_warnings": input_file.quality_warnings,
                        }
                    )
                    await _refresh_auto_training_progress(
                        session,
                        job,
                        task_record,
                        progress_percent=35 + (30 * index / len(selected_inputs)),
                        detail_patch={
                            "normalized_inputs": normalized_reports,
                            "current_normalization_input": None,
                        },
                    )
                    await session.commit()

                combined_output_path = Path(store.normalized_dir) / "auto-training" / f"{auto_training_job_id}.csv"
                combined_frame, label_distribution = await asyncio.to_thread(
                    _build_combined_auto_training_frame,
                    normalized_output_paths,
                    combined_output_path,
                )
                labels = pd.to_numeric(combined_frame["label"], errors="coerce").dropna().astype(int)
                if labels.nunique() < 2:
                    raise ContractValidationError(
                        "Automatic training requires at least two label classes across the prepared dataset"
                    )

                await _refresh_auto_training_progress(
                    session,
                    job,
                    task_record,
                    progress_percent=70,
                    current_step="building_feature_schema",
                    detail_patch={"label_distribution": label_distribution},
                )
                await session.commit()

                schema_name = f"auto-{selected_source_type}-{auto_training_job_id[:8]}"
                feature_schema_definition = build_auto_feature_schema_definition(
                    combined_frame,
                    source_type=selected_inputs[0].source_type,
                    name=schema_name,
                )
                auto_training_report_path = store.save_json_report(
                    "auto-training",
                    f"{auto_training_job_id}.json",
                    {
                        "archive_names": [archive.name for archive in archives],
                        "selected_source_type": selected_source_type,
                        "selected_file_count": len(selected_inputs),
                        "skipped_files": skipped_files,
                        "normalized_inputs": normalized_reports,
                        "label_distribution": label_distribution,
                        "feature_schema": feature_schema_definition.model_dump(mode="json"),
                        "normalized_path": str(combined_output_path),
                    },
                )

                dataset_manifest = DatasetManifest(
                    name=f"auto-dataset-{auto_training_job_id[:8]}",
                    source_type=selected_inputs[0].source_type,
                    description="Automatically prepared dataset from uploaded archives",
                    file_name=combined_output_path.name,
                    required_columns=feature_schema_definition.required_columns,
                    feature_families=feature_schema_definition.feature_families,
                    lineage={
                        "mode": "automatic_training",
                        "archive_ids": job.archive_ids,
                        "selected_source_type": selected_source_type,
                    },
                )
                dataset = Dataset(
                    name=dataset_manifest.name,
                    source_type=dataset_manifest.source_type.value,
                    description=dataset_manifest.description,
                    manifest=dataset_manifest.model_dump(mode="json"),
                    storage_path=str(combined_output_path),
                    normalized_path=str(combined_output_path),
                    detected_format="csv",
                    normalization_profile="generic_tabular",
                    normalization_summary={
                        "row_count": int(len(combined_frame)),
                        "missing_values": int(combined_frame.isna().sum().sum()),
                        "warnings": sorted(
                            {
                                warning
                                for item in normalized_reports
                                for warning in item.get("quality_warnings", [])
                                if isinstance(warning, str)
                            }
                        ),
                        "label_distribution": label_distribution,
                    },
                    normalization_report_path=auto_training_report_path,
                    validation_status=ValidationStatus.VALIDATED.value,
                    validation_errors={},
                    lineage=dataset_manifest.lineage,
                )
                session.add(dataset)
                await session.flush()

                schema = FeatureSchema(
                    name=feature_schema_definition.name,
                    version=feature_schema_definition.version,
                    source_type=feature_schema_definition.source_type.value,
                    definition=feature_schema_definition.model_dump(mode="json"),
                )
                session.add(schema)
                await session.flush()

                training_run = TrainingRun(
                    dataset_id=dataset.id,
                    feature_schema_id=schema.id,
                    requested_by_user_id=job.requested_by_user_id,
                    request_payload={
                        "dataset_id": dataset.id,
                        "feature_schema_id": schema.id,
                        "models": ["random_forest", "xgboost", "cnn", "lstm", "fusion"],
                        "hyperparameters": {},
                        "sequence_length": 50,
                        "sequence_stride": 10,
                        "notes": "Automatically generated from uploaded archives",
                    },
                )
                session.add(training_run)
                await session.flush()

                job.source_type = selected_source_type
                job.dataset_id = dataset.id
                job.feature_schema_id = schema.id
                job.training_run_ids = [training_run.id]
                await _refresh_auto_training_progress(
                    session,
                    job,
                    task_record,
                    progress_percent=82,
                    current_step="training_models",
                    detail_patch={
                        "dataset_id": dataset.id,
                        "feature_schema_id": schema.id,
                        "training_run_ids": [training_run.id],
                        "normalization_report_path": auto_training_report_path,
                    },
                )
                await session.commit()

                await _run_training(training_run.id)

                await session.refresh(job)
                await session.refresh(training_run)
                artifact_result = await session.execute(
                    select(ModelArtifact).where(ModelArtifact.training_run_id == training_run.id).order_by(ModelArtifact.created_at.asc())
                )
                artifacts = artifact_result.scalars().all()
                if training_run.status != JobStatus.COMPLETED.value:
                    raise ContractValidationError(training_run.error_message or "Automatic training failed during model training")

                job.model_artifact_ids = [artifact.id for artifact in artifacts]
                job.completed_at = _utc_now()
                await _refresh_auto_training_progress(
                    session,
                    job,
                    task_record,
                    status=JobStatus.COMPLETED.value,
                    progress_percent=100,
                    current_step="completed",
                    detail_patch={
                        "model_artifact_ids": job.model_artifact_ids,
                        "metrics": training_run.metrics,
                    },
                )
                log_event(
                    logger,
                    logging.INFO,
                    "Automatic training job completed",
                    function="_run_auto_training",
                    auto_training_job_id=auto_training_job_id,
                    dataset_id=dataset.id,
                    training_run_id=training_run.id,
                    model_artifact_ids=job.model_artifact_ids,
                )
            except Exception as exc:
                await session.rollback()
                job = await session.get(AutoTrainingJob, auto_training_job_id)
                if job is not None:
                    job.status = JobStatus.FAILED.value
                    job.current_step = "failed"
                    job.error_message = str(exc)
                    job.progress_percent = float(min(job.progress_percent or 0.0, 99.0))
                    job.completed_at = _utc_now()
                if task_record_id:
                    task_record = await session.get(TaskRecord, task_record_id)
                    if task_record is not None:
                        task_record.status = JobStatus.FAILED.value
                        task_record.detail = {**(task_record.detail or {}), "error": str(exc)}
                logger.exception(
                    "Automatic training job failed",
                    extra={"function": "_run_auto_training", "error": {"type": type(exc).__name__, "message": str(exc)}},
                )
            finally:
                await session.commit()
                shutil.rmtree(workspace_root, ignore_errors=True)


@observed("run_inference")
async def _run_inference(
    inference_job_id: str,
    *,
    task_headers: dict[str, str] | None = None,
    task_name: str = "training.run_inference",
) -> None:
    """EN: Execute inference against the published model service and persist results.
    RU: Выполняет инференс через сервис опубликованных моделей и сохраняет результаты.
    """

    settings = get_settings()
    headers = task_headers or {}
    message_id = headers.get("message_id")
    with request_context({"type": "task", "service": "training-service", "inference_job_id": inference_job_id}):
        async with async_session_factory() as session:
            job = await session.get(InferenceJob, inference_job_id)
            if job is None:
                log_event(logger, logging.WARNING, "Inference job skipped", function="_run_inference", inference_job_id=inference_job_id)
                return
            task_record = await _get_latest_task_record(session, "inference_job", inference_job_id)
            task_record_id = task_record.id if task_record else None
            if await _has_processed_message(session, consumer_name=task_name, message_id=message_id):
                log_event(
                    logger,
                    logging.INFO,
                    "Inference job duplicate delivery skipped",
                    function="_run_inference",
                    inference_job_id=inference_job_id,
                    message_id=message_id,
                )
                return
            existing_results = await _list_detection_results(session, inference_job_id)
            if job.status == JobStatus.COMPLETED.value and existing_results:
                if task_record:
                    task_record.status = JobStatus.COMPLETED.value
                    task_record.detail = {
                        **(task_record.detail or {}),
                        "prediction_count": len(existing_results),
                        "duplicate_delivery": True,
                    }
                await _store_processed_message(
                    session,
                    consumer_name=task_name,
                    message_id=message_id,
                    topic=task_name,
                    payload={"inference_job_id": inference_job_id},
                    detail={"prediction_count": len(existing_results), "duplicate_delivery": True},
                )
                await session.commit()
                log_event(
                    logger,
                    logging.INFO,
                    "Inference job already completed, reused persisted predictions",
                    function="_run_inference",
                    inference_job_id=inference_job_id,
                    prediction_count=len(existing_results),
                )
                return
            job.status = JobStatus.RUNNING.value
            if task_record:
                task_record.status = JobStatus.RUNNING.value
            try:
                payload = InferenceRequest.model_validate(job.request_payload)
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(f"{settings.inference_service_url}/predict", json=payload.model_dump(mode="json"))
                    response.raise_for_status()
                    predictions = response.json()["predictions"]
                for prediction, record in zip(predictions, payload.records, strict=True):
                    session.add(
                        DetectionResult(
                            inference_job_id=job.id,
                            entity_id=prediction["entity_id"],
                            score=prediction["score"],
                            predicted_label=prediction["predicted_label"],
                            raw_output={"prediction": prediction, "features": record.features},
                        )
                    )
                job.status = JobStatus.COMPLETED.value
                job.completed_at = _utc_now()
                if task_record:
                    task_record.status = JobStatus.COMPLETED.value
                    task_record.detail = {"prediction_count": len(predictions)}
                await _store_processed_message(
                    session,
                    consumer_name=task_name,
                    message_id=message_id,
                    topic=task_name,
                    payload={"inference_job_id": inference_job_id},
                    detail={"prediction_count": len(predictions)},
                )
                log_event(
                    logger,
                    logging.INFO,
                    "Inference job completed",
                    function="_run_inference",
                    inference_job_id=inference_job_id,
                    prediction_count=len(predictions),
                )
            except Exception as exc:
                await session.rollback()
                job = await session.get(InferenceJob, inference_job_id)
                if job is not None:
                    job.status = JobStatus.FAILED.value
                    job.error_message = str(exc)
                    job.completed_at = _utc_now()
                if task_record_id:
                    task_record = await session.get(TaskRecord, task_record_id)
                    if task_record is not None:
                        task_record.status = JobStatus.FAILED.value
                        task_record.detail = {"error": str(exc)}
                logger.exception(
                    "Inference job failed",
                    extra={"function": "_run_inference", "error": {"type": type(exc).__name__, "message": str(exc)}},
                )
            await session.commit()


@observed("generate_explanation")
async def _generate_explanation(
    explanation_job_id: str,
    *,
    task_headers: dict[str, str] | None = None,
    task_name: str = "training.generate_explanation",
) -> None:
    """EN: Build SHAP-style explanation payloads for stored detections.
    RU: Формирует SHAP-подобные explanation-payloads для сохранённых детекций.
    """

    store = ArtifactStore()
    headers = task_headers or {}
    message_id = headers.get("message_id")
    with request_context({"type": "task", "service": "training-service", "explanation_job_id": explanation_job_id}):
        async with async_session_factory() as session:
            job = await session.get(ExplanationJob, explanation_job_id)
            if job is None:
                log_event(
                    logger,
                    logging.WARNING,
                    "Explanation job skipped",
                    function="_generate_explanation",
                    explanation_job_id=explanation_job_id,
                )
                return
            task_record = await _get_latest_task_record(session, "explanation_job", explanation_job_id)
            task_record_id = task_record.id if task_record else None
            if await _has_processed_message(session, consumer_name=task_name, message_id=message_id):
                log_event(
                    logger,
                    logging.INFO,
                    "Explanation job duplicate delivery skipped",
                    function="_generate_explanation",
                    explanation_job_id=explanation_job_id,
                    message_id=message_id,
                )
                return
            existing_result = await _get_explanation_result(session, explanation_job_id)
            if job.status == JobStatus.COMPLETED.value and existing_result is not None:
                if task_record:
                    task_record.status = JobStatus.COMPLETED.value
                    task_record.detail = {
                        **(task_record.detail or {}),
                        "report_path": existing_result.report_path,
                        "duplicate_delivery": True,
                    }
                await _store_processed_message(
                    session,
                    consumer_name=task_name,
                    message_id=message_id,
                    topic=task_name,
                    payload={"explanation_job_id": explanation_job_id},
                    detail={"report_path": existing_result.report_path, "duplicate_delivery": True},
                )
                await session.commit()
                log_event(
                    logger,
                    logging.INFO,
                    "Explanation job already completed, reused persisted report",
                    function="_generate_explanation",
                    explanation_job_id=explanation_job_id,
                    report_path=existing_result.report_path,
                )
                return
            job.status = JobStatus.RUNNING.value
            if task_record:
                task_record.status = JobStatus.RUNNING.value
            try:
                artifact = await session.get(ModelArtifact, job.model_artifact_id)
                detection = await session.get(DetectionResult, job.detection_result_id)
                if artifact is None or detection is None:
                    raise ContractValidationError("Explanation requires a valid artifact and detection result")
                if artifact.model_type != "fusion":
                    fallback_result = await session.execute(
                        select(ModelArtifact).where(
                            ModelArtifact.training_run_id == artifact.training_run_id,
                            ModelArtifact.model_type == "fusion",
                        )
                    )
                    artifact = fallback_result.scalar_one_or_none() or artifact
                bundle = load_model_bundle(artifact.artifact_path)
                payload = HybridTrainer().explain_record(
                    bundle,
                    detection.raw_output["features"],
                    top_k=job.request_payload.get("top_k", 10),
                )
                payload.update(
                    {
                        "model_artifact_id": artifact.id,
                        "detection_result_id": detection.id,
                        "generated_at": _utc_now().isoformat(),
                    }
                )
                report_path = store.save_explanation(f"{job.id}.json", payload)
                payload["report_path"] = report_path
                session.add(ExplanationResult(explanation_job_id=job.id, payload=payload, report_path=report_path))
                job.status = JobStatus.COMPLETED.value
                job.completed_at = _utc_now()
                if task_record:
                    task_record.status = JobStatus.COMPLETED.value
                    task_record.detail = {"report_path": report_path}
                await _store_processed_message(
                    session,
                    consumer_name=task_name,
                    message_id=message_id,
                    topic=task_name,
                    payload={"explanation_job_id": explanation_job_id},
                    detail={"report_path": report_path},
                )
                log_event(
                    logger,
                    logging.INFO,
                    "Explanation job completed",
                    function="_generate_explanation",
                    explanation_job_id=explanation_job_id,
                    report_path=report_path,
                )
            except Exception as exc:
                await session.rollback()
                job = await session.get(ExplanationJob, explanation_job_id)
                if job is not None:
                    job.status = JobStatus.FAILED.value
                    job.error_message = str(exc)
                    job.completed_at = _utc_now()
                if task_record_id:
                    task_record = await session.get(TaskRecord, task_record_id)
                    if task_record is not None:
                        task_record.status = JobStatus.FAILED.value
                        task_record.detail = {"error": str(exc)}
                logger.exception(
                    "Explanation job failed",
                    extra={"function": "_generate_explanation", "error": {"type": type(exc).__name__, "message": str(exc)}},
                )
            await session.commit()


@celery_app.task(name="training.run_training", bind=True)
def run_training(self, training_run_id: str) -> None:
    """EN: Celery entry point for asynchronous model training.
    RU: Celery entry point для асинхронного обучения модели.
    """

    _run_async(_run_training(training_run_id, task_headers=_extract_task_headers(self), task_name=self.name))


@celery_app.task(name="training.run_auto_training", bind=True)
def run_auto_training(self, auto_training_job_id: str) -> None:
    """EN: Celery entry point for automatic archive-based training.
    RU: Celery entry point РґР»СЏ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРѕРіРѕ РѕР±СѓС‡РµРЅРёСЏ РёР· Р°СЂС…РёРІРЅС‹С… РЅР°Р±РѕСЂРѕРІ.
    """

    _run_async(_run_auto_training(auto_training_job_id))


@celery_app.task(name="training.run_inference", bind=True)
def run_inference(self, inference_job_id: str) -> None:
    """EN: Celery entry point for asynchronous inference execution.
    RU: Celery entry point для асинхронного выполнения инференса.
    """

    _run_async(_run_inference(inference_job_id, task_headers=_extract_task_headers(self), task_name=self.name))


@celery_app.task(name="training.generate_explanation", bind=True)
def generate_explanation(self, explanation_job_id: str) -> None:
    """EN: Celery entry point for asynchronous explanation generation.
    RU: Celery entry point для асинхронной генерации объяснений.
    """

    _run_async(_generate_explanation(explanation_job_id, task_headers=_extract_task_headers(self), task_name=self.name))
