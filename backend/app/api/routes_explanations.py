from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from backend.app.api.deps import SessionDep, get_current_user
from backend.app.schemas.common import ExplanationJobOut, ExplanationResultOut
from backend.app.services.tasks import dispatch_task, trigger_task_publish
from cybersec_platform.contracts.api import ExplanationRequest
from cybersec_platform.db import DetectionResult, ExplanationJob, ExplanationResult, InferenceJob, ModelArtifact

router = APIRouter(prefix="/explanations", tags=["explanations"])


@router.post("", response_model=ExplanationJobOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def request_explanation(payload: ExplanationRequest, session: SessionDep) -> ExplanationJobOut:
    artifact = await session.get(ModelArtifact, payload.model_artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Model artifact not found")
    detection = await session.get(DetectionResult, payload.detection_result_id)
    if detection is None:
        raise HTTPException(status_code=404, detail="Detection result not found")
    inference_job = await session.get(InferenceJob, detection.inference_job_id)
    if inference_job is None:
        raise HTTPException(status_code=409, detail="Detection result is not linked to an inference job")
    detection_artifact = await session.get(ModelArtifact, inference_job.model_artifact_id)
    if detection_artifact is None:
        raise HTTPException(status_code=409, detail="Detection result is not linked to a model artifact")
    if artifact.training_run_id != detection_artifact.training_run_id:
        raise HTTPException(
            status_code=400,
            detail="Explanation model artifact must belong to the same training lineage as the detection result",
        )
    item = ExplanationJob(
        model_artifact_id=payload.model_artifact_id,
        detection_result_id=payload.detection_result_id,
        request_payload=payload.model_dump(mode="json"),
    )
    session.add(item)
    await session.flush()
    record = await dispatch_task(
        session,
        task_name="training.generate_explanation",
        object_type="explanation_job",
        object_id=item.id,
        queue="training",
        kwargs={"explanation_job_id": item.id},
    )
    await session.commit()
    await session.refresh(item)
    await trigger_task_publish(session, record)
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
