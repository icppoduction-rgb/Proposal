from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from backend.app.api.deps import SessionDep, get_current_user
from backend.app.schemas.common import FeatureSchemaOut
from cybersec_platform.contracts.api import FeatureSchemaDefinition
from cybersec_platform.db import FeatureSchema

router = APIRouter(prefix="/feature-schemas", tags=["feature-schemas"])


@router.get("", response_model=list[FeatureSchemaOut], dependencies=[Depends(get_current_user)])
async def list_feature_schemas(session: SessionDep) -> list[FeatureSchemaOut]:
    result = await session.execute(select(FeatureSchema))
    return [FeatureSchemaOut.model_validate(item) for item in result.scalars().all()]


@router.post("", response_model=FeatureSchemaOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_user)])
async def create_feature_schema(payload: FeatureSchemaDefinition, session: SessionDep) -> FeatureSchemaOut:
    item = FeatureSchema(
        name=payload.name,
        version=payload.version,
        source_type=payload.source_type.value,
        definition=payload.model_dump(mode="json"),
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return FeatureSchemaOut.model_validate(item)


@router.get("/{schema_id}", response_model=FeatureSchemaOut, dependencies=[Depends(get_current_user)])
async def get_feature_schema(schema_id: str, session: SessionDep) -> FeatureSchemaOut:
    item = await session.get(FeatureSchema, schema_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Feature schema not found")
    return FeatureSchemaOut.model_validate(item)


@router.put("/{schema_id}", response_model=FeatureSchemaOut, dependencies=[Depends(get_current_user)])
async def update_feature_schema(schema_id: str, payload: FeatureSchemaDefinition, session: SessionDep) -> FeatureSchemaOut:
    item = await session.get(FeatureSchema, schema_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Feature schema not found")
    item.name = payload.name
    item.version = payload.version
    item.source_type = payload.source_type.value
    item.definition = payload.model_dump(mode="json")
    await session.commit()
    await session.refresh(item)
    return FeatureSchemaOut.model_validate(item)
