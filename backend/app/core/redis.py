from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis

from app.core.config import Settings


def build_redis(settings: Settings) -> Redis:
    return Redis.from_url(
        settings.redis.url.get_secret_value(),
        decode_responses=True,
    )


async def get_redis(request: Request) -> Redis:
    redis: Redis = request.app.state.redis
    return redis


RedisDep = Annotated[Redis, Depends(get_redis)]
