from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, RedisDep, SessionDep, SettingsDep
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.schemas.auth import RefreshRequest, TokenPair, UserRead, UserRegister
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

_settings = get_settings()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserRegister,
    session: SessionDep,
) -> UserRead:
    user = await auth_service.register(session, payload.email, payload.password)
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=TokenPair,
    status_code=status.HTTP_200_OK,
)
@limiter.limit(_settings.rate_limit.auth_login)  # type: ignore[untyped-decorator]
async def login(
    request: Request,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
    settings: SettingsDep,
) -> TokenPair:
    user = await auth_service.authenticate(session, form.username, form.password)
    pair = auth_service.issue_token_pair(user, settings)
    return TokenPair(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
async def me(current: CurrentUser) -> UserRead:
    return UserRead.model_validate(current)


@router.post(
    "/refresh",
    response_model=TokenPair,
    status_code=status.HTTP_200_OK,
)
@limiter.limit(_settings.rate_limit.auth_refresh)  # type: ignore[untyped-decorator]
async def refresh(
    request: Request,
    payload: RefreshRequest,
    session: SessionDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> TokenPair:
    pair = await auth_service.rotate_refresh(session, redis, payload.refresh_token, settings)
    return TokenPair(access_token=pair.access_token, refresh_token=pair.refresh_token)
