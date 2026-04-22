from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, update

from backend.app.api.deps import SessionDep, get_current_user
from backend.app.schemas.common import ModelArtifactOut
from cybersec_platform.contracts.api import ArtifactStatus
from cybersec_platform.db import ModelArtifact

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[ModelArtifactOut], dependencies=[Depends(get_current_user)])
async def list_models(session: SessionDep) -> list[ModelArtifactOut]:
    result = await session.execute(select(ModelArtifact).order_by(ModelArtifact.created_at.desc(), ModelArtifact.id.desc()))
    return [ModelArtifactOut.model_validate(item) for item in result.scalars().all()]


@router.get("/{artifact_id}", response_model=ModelArtifactOut, dependencies=[Depends(get_current_user)])
async def get_model(artifact_id: str, session: SessionDep) -> ModelArtifactOut:
    item = await session.get(ModelArtifact, artifact_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Model artifact not found")
    return ModelArtifactOut.model_validate(item)


@router.post("/{artifact_id}/promote", response_model=ModelArtifactOut, dependencies=[Depends(get_current_user)])
async def promote_model(artifact_id: str, session: SessionDep) -> ModelArtifactOut:
    item = await session.get(ModelArtifact, artifact_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Model artifact not found")
    await session.execute(
        update(ModelArtifact)
        .where(
            ModelArtifact.model_type == item.model_type,
            ModelArtifact.status == ArtifactStatus.PROMOTED.value,
            ModelArtifact.id != item.id,
        )
        .values(status=ArtifactStatus.DEPRECATED.value)
    )
    item.status = ArtifactStatus.PROMOTED.value
    await session.commit()
    await session.refresh(item)
    return ModelArtifactOut.model_validate(item)


@router.post("/{artifact_id}/deprecate", response_model=ModelArtifactOut, dependencies=[Depends(get_current_user)])
async def deprecate_model(artifact_id: str, session: SessionDep) -> ModelArtifactOut:
    item = await session.get(ModelArtifact, artifact_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Model artifact not found")
    item.status = ArtifactStatus.DEPRECATED.value
    await session.commit()
    await session.refresh(item)
    return ModelArtifactOut.model_validate(item)


@router.get("/{artifact_id}/download", dependencies=[Depends(get_current_user)])
async def download_model(artifact_id: str, session: SessionDep) -> FileResponse:
    item = await session.get(ModelArtifact, artifact_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Model artifact not found")
    artifact_path = Path(item.artifact_path)
    if not artifact_path.is_file():
        raise HTTPException(status_code=404, detail="Model artifact file not found")
    return FileResponse(artifact_path, filename=artifact_path.name)
