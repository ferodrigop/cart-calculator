from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["dev", "test", "prod"]


class DatabaseSettings(BaseModel):
    url: SecretStr = SecretStr("postgresql+asyncpg://cart:cart@postgres:5432/cart")


class RedisSettings(BaseModel):
    url: SecretStr = SecretStr("redis://redis:6379/0")


class JWTSettings(BaseModel):
    access_secret: SecretStr = SecretStr("change-me-access-change-me-access-change-me")
    refresh_secret: SecretStr = SecretStr("change-me-refresh-change-me-refresh-change-me")
    algorithm: str = "HS256"
    access_ttl_seconds: int = 60 * 15
    refresh_ttl_seconds: int = 60 * 60 * 24 * 7


class RateLimitSettings(BaseModel):
    storage_uri: SecretStr | None = None
    default: str = "300/minute"
    auth_login: str = "5/minute"
    auth_refresh: str = "5/minute"


class PasswordSettings(BaseModel):
    min_length: int = 8


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
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    password: PasswordSettings = Field(default_factory=PasswordSettings)

    @model_validator(mode="after")
    def _resolve_rate_limit_storage(self) -> Settings:
        if self.rate_limit.storage_uri is None:
            self.rate_limit.storage_uri = self.redis.url
        return self

    @model_validator(mode="after")
    def _validate_prod_secrets(self) -> Settings:
        if self.environment != "prod":
            return self
        for label, secret in (
            ("JWT__ACCESS_SECRET", self.jwt.access_secret.get_secret_value()),
            ("JWT__REFRESH_SECRET", self.jwt.refresh_secret.get_secret_value()),
        ):
            if len(secret) < 32 or secret.startswith("change-me"):
                raise ValueError(f"{label} must be a real 32+ char secret in prod")
        if self.jwt.access_secret.get_secret_value() == self.jwt.refresh_secret.get_secret_value():
            raise ValueError("JWT__ACCESS_SECRET and JWT__REFRESH_SECRET must differ in prod")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
