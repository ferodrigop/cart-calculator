from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

from app.core.config import Settings, get_settings
from app.core.db import SessionDep
from app.core.exceptions import InvalidTokenError
from app.core.redis import RedisDep
from app.core.security import decode_token
from app.models.user import User
from app.services import auth as auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
    settings: SettingsDep,
) -> User:
    claims = decode_token(
        token,
        settings.jwt.access_secret.get_secret_value(),
        expected_type="access",
    )
    try:
        user_id = UUID(str(claims["sub"]))
    except (ValueError, KeyError) as exc:
        raise InvalidTokenError("invalid subject") from exc
    user = await auth_service.get_user_by_id(session, user_id)
    request.state.user_id = str(user.id)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

__all__ = [
    "CurrentUser",
    "RedisDep",
    "SessionDep",
    "SettingsDep",
    "get_current_user",
    "oauth2_scheme",
]
