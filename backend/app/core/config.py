from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["dev", "test", "prod"]


class DatabaseSettings(BaseModel):
    url: str = "postgresql+asyncpg://cart:cart@postgres:5432/cart"


class RedisSettings(BaseModel):
    url: str = "redis://redis:6379/0"


class JWTSettings(BaseModel):
    secret: SecretStr = SecretStr("change-me-change-me-change-me-change-me")
    algorithm: str = "HS256"
    access_ttl_seconds: int = 60 * 15
    refresh_ttl_seconds: int = 60 * 60 * 24 * 7


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Environment = "dev"
    app_name: str = "cart-calculator"

    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)

    @property
    def database_url(self) -> str:
        return self.db.url


@lru_cache
def get_settings() -> Settings:
    return Settings()
