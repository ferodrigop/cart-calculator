from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import api_router
from app.core.config import get_settings
from app.core.db import build_engine, build_session_maker
from app.core.exceptions import AuthError
from app.core.rate_limit import limiter
from app.core.redis import build_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    engine = build_engine(settings)
    session_maker = build_session_maker(engine)
    redis = build_redis(settings)
    app.state.engine = engine
    app.state.session_maker = session_maker
    app.state.redis = redis
    app.state.limiter = limiter
    try:
        yield
    finally:
        await redis.aclose()
        await engine.dispose()


async def _auth_error_handler(request: Request, exc: Exception) -> JSONResponse:
    err = cast(AuthError, exc)
    return JSONResponse(status_code=err.status_code, content={"detail": err.detail})


async def _rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "rate limit exceeded"})


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(AuthError, _auth_error_handler)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.include_router(api_router)
    return app


app = create_app()
