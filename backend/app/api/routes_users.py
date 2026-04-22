from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.app.api.deps import SessionDep, require_admin
from backend.app.core.security import get_password_hash
from backend.app.schemas.common import MessageResponse, UserOut
from backend.app.services.auth import get_role_name
from cybersec_platform.contracts.api import UserCreate, UserUpdate
from cybersec_platform.db import Role, User

router = APIRouter(prefix="/users", tags=["users"])


async def _serialize_user(session: SessionDep, item: User) -> UserOut:
    role_name = await get_role_name(session, item.role_id)
    return UserOut(
        id=item.id,
        email=item.email,
        full_name=item.full_name,
        is_active=item.is_active,
        role_name=role_name,
        session_status="active" if item.is_active else "inactive",
        created_at=item.created_at,
    )


async def _resolve_role(session: SessionDep, role_name: str) -> Role:
    role_result = await session.execute(select(Role).where(Role.name == role_name))
    role = role_result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=400, detail="Role not found")
    return role


@router.get("", response_model=list[UserOut], dependencies=[Depends(require_admin)])
async def list_users(session: SessionDep) -> list[UserOut]:
    result = await session.execute(select(User).order_by(User.created_at.desc(), User.id.desc()))
    items = result.scalars().all()
    return [await _serialize_user(session, item) for item in items]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
async def create_user(payload: UserCreate, session: SessionDep) -> UserOut:
    existing_user = await session.execute(select(User.id).where(User.email == payload.email))
    if existing_user.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

    role = await _resolve_role(session, payload.role.value)
    user = User(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        full_name=payload.full_name.strip() if payload.full_name and payload.full_name.strip() else None,
        role_id=role.id,
        is_active=payload.is_active,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists") from exc
    await session.refresh(user)
    return await _serialize_user(session, user)


@router.put("/{user_id}", response_model=UserOut, dependencies=[Depends(require_admin)])
async def update_user(user_id: str, payload: UserUpdate, session: SessionDep) -> UserOut:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.email is not None and payload.email != user.email:
        existing_user = await session.execute(select(User.id).where(User.email == payload.email, User.id != user_id))
        if existing_user.scalar_one_or_none() is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")
        user.email = payload.email

    if payload.password:
        user.password_hash = get_password_hash(payload.password)
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip() if payload.full_name.strip() else None
    if payload.role is not None:
        user.role_id = (await _resolve_role(session, payload.role.value)).id
    if payload.is_active is not None:
        user.is_active = payload.is_active

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists") from exc
    await session.refresh(user)
    return await _serialize_user(session, user)


@router.delete("/{user_id}", response_model=MessageResponse, dependencies=[Depends(require_admin)])
async def delete_user(user_id: str, session: SessionDep) -> MessageResponse:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()
    return MessageResponse(message="User deleted")


@router.post("/{user_id}/deactivate", response_model=MessageResponse, dependencies=[Depends(require_admin)])
async def deactivate_user(user_id: str, session: SessionDep) -> MessageResponse:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await session.commit()
    return MessageResponse(message="User deactivated")
