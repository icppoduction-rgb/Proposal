from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from jose import ExpiredSignatureError, JWTError
from sqlalchemy import select

from backend.app.api.deps import SessionDep, get_current_user
from backend.app.core.security import decode_token
from backend.app.schemas.common import MessageResponse, UserOut
from backend.app.services.auth import authenticate_user, get_role_name, issue_tokens
from cybersec_platform.contracts.api import TokenPair, UserLogin
from cybersec_platform.db import RefreshToken, User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin, session: SessionDep) -> TokenPair:
    user = await authenticate_user(session, payload)
    return await issue_tokens(session, user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(refresh_token: str, session: SessionDep) -> TokenPair:
    try:
        token_payload = decode_token(refresh_token)
    except ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired") from exc
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc
    if token_payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    result = await session.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
    stored = result.scalar_one_or_none()
    if stored is None or stored.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
    user = await session.get(User, token_payload["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    stored.revoked = True
    await session.commit()
    return await issue_tokens(session, user)


@router.post("/logout", response_model=MessageResponse)
async def logout(refresh_token: str, session: SessionDep) -> MessageResponse:
    result = await session.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
    stored = result.scalar_one_or_none()
    if stored is not None:
        stored.revoked = True
        await session.commit()
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserOut)
async def me(session: SessionDep, user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        role_name=await get_role_name(session, user.role_id),
        session_status="active" if user.is_active else "inactive",
        created_at=user.created_at,
    )
