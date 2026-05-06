from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Settings
from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    RefreshTokenReusedError,
    UserNotFoundError,
)
from app.core.security import (
    decode_token,
    hash_password,
    mint_access,
    mint_refresh,
    verify_password,
)
from app.models.user import User


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.exec(select(User).where(User.email == _normalize_email(email)))
    return result.first()


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise UserNotFoundError
    return user


async def register(session: AsyncSession, email: str, password: str) -> User:
    user = User(email=_normalize_email(email), password_hash=hash_password(password))
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise EmailAlreadyExistsError from exc
    await session.refresh(user)
    return user


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(session, email)
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError
    return user


def issue_token_pair(user: User, settings: Settings) -> TokenPair:
    return TokenPair(
        access_token=mint_access(user.id, settings),
        refresh_token=mint_refresh(user.id, settings),
    )


async def rotate_refresh(
    session: AsyncSession,
    redis: Redis,
    refresh_token: str,
    settings: Settings,
) -> TokenPair:
    claims = decode_token(
        refresh_token,
        settings.jwt.refresh_secret.get_secret_value(),
        expected_type="refresh",
    )
    user_id = UUID(str(claims["sub"]))
    jti = str(claims["jti"])
    exp = int(claims["exp"])

    from datetime import UTC, datetime

    remaining = exp - int(datetime.now(UTC).timestamp())
    ttl = max(remaining, 1)

    stored: bool | int | None = await redis.set(f"denylist:jti:{jti}", "1", nx=True, ex=ttl)
    if not stored:
        raise RefreshTokenReusedError

    user = await get_user_by_id(session, user_id)
    return issue_token_pair(user, settings)
