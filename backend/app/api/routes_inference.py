from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from backend.app.api.deps import SessionDep, get_current_user
from backend.app.schemas.common import DetectionResultOut, InferenceJobOut
from backend.app.services.tasks import dispatch_task
from cybersec_platform.contracts.api import InferenceRequest
from cybersec_platform.contracts.api import ArtifactStatus
from cybersec_platform.db import DetectionResult, InferenceJob, ModelArtifact

router = APIRouter(prefix="/inference-jobs", tags=["inference-jobs"])


@router.post("", response_model=InferenceJobOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def create_inference_job(payload: InferenceRequest, session: SessionDep) -> InferenceJobOut:
    artifact = await session.get(ModelArtifact, payload.model_artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Model artifact not found")
    if artifact.status != ArtifactStatus.PROMOTED.value:
        raise HTTPException(status_code=400, detail="Only promoted model artifacts can be used for inference")
    item = InferenceJob(model_artifact_id=payload.model_artifact_id, request_payload=payload.model_dump(mode="json"))
    session.add(item)
    await session.commit()
    await session.refresh(item)
    await dispatch_task(
        session,
        task_name="training.run_inference",
        object_type="inference_job",
        object_id=item.id,
        queue="training",
        kwargs={"inference_job_id": item.id},
    )
    return InferenceJobOut.model_validate(item)


@router.get("", response_model=list[InferenceJobOut], dependencies=[Depends(get_current_user)])
async def list_inference_jobs(session: SessionDep) -> list[InferenceJobOut]:
    result = await session.execute(select(InferenceJob))
    return [InferenceJobOut.model_validate(item) for item in result.scalars().all()]


@router.get("/{job_id}", response_model=InferenceJobOut, dependencies=[Depends(get_current_user)])
async def get_inference_job(job_id: str, session: SessionDep) -> InferenceJobOut:
    item = await session.get(InferenceJob, job_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Inference job not found")
    return InferenceJobOut.model_validate(item)


@router.get("/{job_id}/results", response_model=list[DetectionResultOut], dependencies=[Depends(get_current_user)])
async def get_inference_results(job_id: str, session: SessionDep) -> list[DetectionResultOut]:
    result = await session.execute(select(DetectionResult).where(DetectionResult.inference_job_id == job_id))
    return [DetectionResultOut.model_validate(item) for item in result.scalars().all()]
