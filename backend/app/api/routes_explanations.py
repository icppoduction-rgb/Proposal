from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from backend.app.api.deps import SessionDep, get_current_user
from backend.app.schemas.common import ExplanationJobOut, ExplanationResultOut
from backend.app.services.tasks import dispatch_task
from cybersec_platform.contracts.api import ExplanationRequest
from cybersec_platform.db import DetectionResult, ExplanationJob, ExplanationResult, ModelArtifact

router = APIRouter(prefix="/explanations", tags=["explanations"])


@router.post("", response_model=ExplanationJobOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def request_explanation(payload: ExplanationRequest, session: SessionDep) -> ExplanationJobOut:
    if await session.get(ModelArtifact, payload.model_artifact_id) is None:
        raise HTTPException(status_code=404, detail="Model artifact not found")
    if await session.get(DetectionResult, payload.detection_result_id) is None:
        raise HTTPException(status_code=404, detail="Detection result not found")
    item = ExplanationJob(
        model_artifact_id=payload.model_artifact_id,
        detection_result_id=payload.detection_result_id,
        request_payload=payload.model_dump(mode="json"),
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    await dispatch_task(
        session,
        task_name="training.generate_explanation",
        object_type="explanation_job",
        object_id=item.id,
        queue="training",
        kwargs={"explanation_job_id": item.id},
    )
    return ExplanationJobOut.model_validate(item)


@router.get("", response_model=list[ExplanationJobOut], dependencies=[Depends(get_current_user)])
async def list_explanation_jobs(session: SessionDep) -> list[ExplanationJobOut]:
    result = await session.execute(select(ExplanationJob))
    return [ExplanationJobOut.model_validate(item) for item in result.scalars().all()]


@router.get("/{job_id}", response_model=ExplanationJobOut, dependencies=[Depends(get_current_user)])
async def get_explanation_job(job_id: str, session: SessionDep) -> ExplanationJobOut:
    item = await session.get(ExplanationJob, job_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Explanation job not found")
    return ExplanationJobOut.model_validate(item)


@router.get("/{job_id}/result", response_model=ExplanationResultOut, dependencies=[Depends(get_current_user)])
async def get_explanation_result(job_id: str, session: SessionDep) -> ExplanationResultOut:
    result = await session.execute(select(ExplanationResult).where(ExplanationResult.explanation_job_id == job_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Explanation result not found")
    return ExplanationResultOut.model_validate(item)
