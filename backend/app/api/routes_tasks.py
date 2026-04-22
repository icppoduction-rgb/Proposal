from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from backend.app.api.deps import SessionDep, get_current_user
from backend.app.schemas.common import TaskRecordOut
from cybersec_platform.db import TaskRecord

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRecordOut], dependencies=[Depends(get_current_user)])
async def list_tasks(session: SessionDep) -> list[TaskRecordOut]:
    result = await session.execute(select(TaskRecord))
    return [TaskRecordOut.model_validate(item) for item in result.scalars().all()]


@router.get("/{task_id}", response_model=TaskRecordOut, dependencies=[Depends(get_current_user)])
async def get_task(task_id: str, session: SessionDep) -> TaskRecordOut:
    item = await session.get(TaskRecord, task_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskRecordOut.model_validate(item)
