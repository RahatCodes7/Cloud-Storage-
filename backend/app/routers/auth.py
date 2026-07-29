"""Auth endpoints: register, login, me, logout."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    clear_auth_cookie,
    create_access_token,
    get_current_user,
    hash_password,
    set_auth_cookie,
    verify_password,
)
from app.config import get_settings
from app.database import get_session
from app.models import User
from app.telegram_client import create_user_topic
from app.utils.snapshot import push_snapshot

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    is_admin: bool
    created_at: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


@router.post("/register", response_model=AuthResponse)
async def register(
    req: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_session),
):
    settings = get_settings()
    if not settings.allow_public_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration is disabled",
        )

    existing = await db.execute(select(User).where(User.username == req.username))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    try:
        thread_id = await create_user_topic("new", req.username)
    except Exception as e:
        logger.error(f"Failed to create Telegram topic: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create storage topic",
        )

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        is_admin=False,
        telegram_thread_id=thread_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await push_snapshot()

    token = create_access_token(user.id, user.username)
    set_auth_cookie(response, token, settings.jwt_expire_minutes)

    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            is_admin=user.is_admin,
            created_at=user.created_at.isoformat() if user.created_at else None,
        ),
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    req: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(user.id, user.username)
    set_auth_cookie(response, token, get_settings().jwt_expire_minutes)

    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            is_admin=user.is_admin,
            created_at=user.created_at.isoformat() if user.created_at else None,
        ),
    )


@router.post("/logout")
async def logout(response: Response):
    """Clear the auth cookie to log out."""
    clear_auth_cookie(response)
    return {"ok": True}


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "is_admin": current_user.is_admin,
        "telegram_thread_id": current_user.telegram_thread_id,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }
