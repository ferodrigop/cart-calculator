from __future__ import annotations

from typing import Any

from starlette.requests import Request

from app.core.config import Settings, get_settings


def user_or_ip_key(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    client = request.client
    host = client.host if client else "unknown"
    return f"ip:{host}"


def _build_limiter() -> Any:
    """Construct the slowapi Limiter using current settings.

    Imported lazily so test environments can set env vars before settings are
    instantiated by `get_settings()`.
    """
    from slowapi import Limiter

    settings: Settings = get_settings()
    storage_uri = (
        settings.rate_limit.storage_uri.get_secret_value()
        if settings.rate_limit.storage_uri is not None
        else settings.redis.url.get_secret_value()
    )
    return Limiter(
        key_func=user_or_ip_key,
        storage_uri=storage_uri,
        strategy="moving-window",
        default_limits=[settings.rate_limit.default],
    )


limiter: Any = _build_limiter()
