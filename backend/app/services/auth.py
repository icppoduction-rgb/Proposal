from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import create_token, verify_password
from cybersec_platform.contracts.api import TokenPair, UserCreate, UserLogin
from cybersec_platform.db import RefreshToken, Role, User
from cybersec_platform.db.session import get_settings


def _db_utc_now() -> datetime:
    """EN: Return a naive UTC datetime compatible with current PostgreSQL timestamp columns.
    RU: Возвращает naive UTC datetime, совместимый с текущими PostgreSQL timestamp-колонками.
    """

    return datetime.now(UTC).replace(tzinfo=None)


async def authenticate_user(session: AsyncSession, payload: UserLogin) -> User:
    result = await session.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return user


async def issue_tokens(session: AsyncSession, user: User) -> TokenPair:
    settings = get_settings()
    access_token = create_token(
        user.id,
        timedelta(minutes=settings.access_token_expire_minutes),
        "access",
    )
    refresh_token = create_token(
        user.id,
        timedelta(minutes=settings.refresh_token_expire_minutes),
        "refresh",
    )
    session.add(
        RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=_db_utc_now() + timedelta(minutes=settings.refresh_token_expire_minutes),
        )
    )
    await session.commit()
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


async def get_role_name(session: AsyncSession, role_id: str) -> str:
    result = await session.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one()
    return role.name
