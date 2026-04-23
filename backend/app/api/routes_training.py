from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from backend.app.api.deps import SessionDep, get_current_user
from backend.app.schemas.common import TrainingRunOut
from backend.app.services.tasks import dispatch_task, trigger_task_publish
from cybersec_platform.contracts.api import JobStatus, TrainingRequest, ValidationStatus
from cybersec_platform.db import Dataset, FeatureSchema, TrainingRun, User
from cybersec_platform.ml.normalization import PROFILE_SCHEMA_MAP

router = APIRouter(prefix="/training-runs", tags=["training-runs"])


@router.get("", response_model=list[TrainingRunOut], dependencies=[Depends(get_current_user)])
async def list_training_runs(session: SessionDep) -> list[TrainingRunOut]:
    result = await session.execute(select(TrainingRun))
    return [TrainingRunOut.model_validate(item) for item in result.scalars().all()]


@router.post("", response_model=TrainingRunOut, status_code=status.HTTP_201_CREATED)
async def create_training_run(payload: TrainingRequest, session: SessionDep, user: User = Depends(get_current_user)) -> TrainingRunOut:
    dataset = await session.get(Dataset, payload.dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    schema = await session.get(FeatureSchema, payload.feature_schema_id)
    if schema is None:
        raise HTTPException(status_code=404, detail="Feature schema not found")
    if dataset.validation_status != ValidationStatus.VALIDATED.value or not dataset.normalized_path:
        raise HTTPException(status_code=400, detail="Dataset must be validated before training")
    compatible_schemas = PROFILE_SCHEMA_MAP.get(dataset.normalization_profile or "", [])
    if compatible_schemas and schema.name not in compatible_schemas:
        raise HTTPException(
            status_code=400,
            detail=f"Feature schema {schema.name} is not compatible with normalization profile {dataset.normalization_profile}",
        )
    item = TrainingRun(
        dataset_id=payload.dataset_id,
        feature_schema_id=payload.feature_schema_id,
        requested_by_user_id=user.id,
        request_payload=payload.model_dump(mode="json"),
    )
    session.add(item)
    await session.flush()
    record = await dispatch_task(
        session,
        task_name="training.run_training",
        object_type="training_run",
        object_id=item.id,
        queue="training",
        kwargs={"training_run_id": item.id},
    )
    await session.commit()
    await session.refresh(item)
    await trigger_task_publish(session, record)
    return TrainingRunOut.model_validate(item)


@router.get("/{training_run_id}", response_model=TrainingRunOut, dependencies=[Depends(get_current_user)])
async def get_training_run(training_run_id: str, session: SessionDep) -> TrainingRunOut:
    item = await session.get(TrainingRun, training_run_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Training run not found")
    return TrainingRunOut.model_validate(item)


@router.post("/{training_run_id}/cancel", response_model=TrainingRunOut, dependencies=[Depends(get_current_user)])
async def cancel_training_run(training_run_id: str, session: SessionDep) -> TrainingRunOut:
    item = await session.get(TrainingRun, training_run_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Training run not found")
    if item.status in {JobStatus.COMPLETED.value, JobStatus.FAILED.value}:
        raise HTTPException(status_code=400, detail="Training run already finalized")
    item.status = JobStatus.CANCELLED.value
    await session.commit()
    await session.refresh(item)
    return TrainingRunOut.model_validate(item)
