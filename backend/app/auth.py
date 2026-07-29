"""JWT creation/verification and password hashing.

Supports both httpOnly cookie (primary) and Authorization: Bearer header (fallback)
for backwards compatibility with API clients.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_session
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

COOKIE_NAME = "access_token"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, username: str) -> str:
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "username": username,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def set_auth_cookie(response: Response, token: str, max_age_minutes: int) -> None:
    """Set the JWT as an httpOnly cookie on the response.

    httpOnly=True prevents JavaScript from reading the cookie (XSS protection).
    samesite='lax' prevents CSRF while allowing top-level navigation.
    secure=True is used when the origin is HTTPS (production on Render).
    """
    settings = get_settings()
    is_secure = not settings.cors_origins.startswith("http://localhost")
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=max_age_minutes * 60,
        httponly=True,
        samesite="lax",
        secure=is_secure,
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """Remove the auth cookie by setting an expired one."""
    settings = get_settings()
    is_secure = not settings.cors_origins.startswith("http://localhost")
    response.set_cookie(
        key=COOKIE_NAME,
        value="",
        max_age=0,
        httponly=True,
        samesite="lax",
        secure=is_secure,
        path="/",
    )


def _extract_token(request: Request) -> Optional[str]:
    """Extract JWT from cookie (primary) or Authorization header (fallback)."""
    # Try httpOnly cookie first
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token

    # Fall back to Authorization: Bearer header
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:]

    return None


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> User:
    token = _extract_token(request)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
