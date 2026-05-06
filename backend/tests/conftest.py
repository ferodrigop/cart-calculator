from __future__ import annotations

import os

# Set test env vars BEFORE any `app.*` import — `app.core.rate_limit` builds its
# Limiter at import time using `get_settings()` (which is lru_cache'd), so env
# must be in place first.
os.environ["ENVIRONMENT"] = "test"
os.environ["RATE_LIMIT__STORAGE_URI"] = "memory://"
os.environ["JWT__ACCESS_SECRET"] = "test-access-secret-must-be-at-least-32-chars"
os.environ["JWT__REFRESH_SECRET"] = "test-refresh-secret-must-be-at-least-32-chars"
os.environ["DB__URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS__URL"] = "redis://localhost:6379/0"
os.environ["JWT__ACCESS_TTL_SECONDS"] = "900"
os.environ["JWT__REFRESH_TTL_SECONDS"] = "604800"

from collections.abc import AsyncIterator

import fakeredis.aioredis  # type: ignore[import-untyped]
import pytest
from app.api.deps import oauth2_scheme  # noqa: F401  -- ensures schema registers
from app.core.config import get_settings
from app.core.db import get_session
from app.core.redis import get_redis
from app.main import app
from app.models import User  # noqa: F401  -- registers User table
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# Defensive: re-read settings after env mutation in case anything in the import
# chain triggered get_settings() with stale defaults.
get_settings.cache_clear()


@pytest.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """SAVEPOINT-per-test isolation per backend/testing standard #3."""
    async with engine.connect() as conn:
        outer_trans = await conn.begin()
        sess = AsyncSession(bind=conn, expire_on_commit=False)
        await sess.begin_nested()

        @event.listens_for(sess.sync_session, "after_transaction_end")
        def _restart_savepoint(sync_sess: object, trans: object) -> None:
            if getattr(trans, "nested", False) and not getattr(
                getattr(trans, "_parent", None), "nested", True
            ):
                sync_sess.begin_nested()  # type: ignore[attr-defined]

        try:
            yield sess
        finally:
            await sess.close()
            await outer_trans.rollback()


@pytest.fixture
async def fake_redis() -> AsyncIterator[fakeredis.aioredis.FakeRedis]:
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


@pytest.fixture
async def client(
    session: AsyncSession,
    fake_redis: fakeredis.aioredis.FakeRedis,
) -> AsyncIterator[AsyncClient]:
    async def _override_session() -> AsyncIterator[AsyncSession]:
        yield session

    async def _override_redis() -> fakeredis.aioredis.FakeRedis:
        return fake_redis

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_redis] = _override_redis

    # Reset slowapi memory storage between tests so rate-limit windows don't bleed.
    limiter = app.state.limiter
    storage = limiter.limiter.storage
    if hasattr(storage, "reset"):
        storage.reset()

    try:
        async with LifespanManager(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac
    finally:
        app.dependency_overrides.clear()


async def register(
    client: AsyncClient,
    email: str = "alice@example.com",
    password: str = "correct-horse-battery",
) -> dict[str, object]:
    r = await client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    return r.json()


async def login(
    client: AsyncClient,
    email: str = "alice@example.com",
    password: str = "correct-horse-battery",
) -> dict[str, str]:
    r = await client.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


async def register_and_login(
    client: AsyncClient,
    email: str = "alice@example.com",
    password: str = "correct-horse-battery",
) -> dict[str, str]:
    await register(client, email, password)
    return await login(client, email, password)
