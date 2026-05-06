# Settings & Config Standards

Conventions for `pydantic-settings`-based configuration.

1. **One `Settings` class in `app/core/config.py`.** Use
   `model_config = SettingsConfigDict(env_file=(".env", ".env.local"), env_file_encoding="utf-8", extra="ignore", case_sensitive=False)`.
   Later files in the tuple override earlier ones — that's the layering strategy.
2. **`SecretStr` for every secret.** JWT secret, DB password, Redis URL with password —
   all wrapped so accidental logging of `settings` doesn't leak them. Call
   `.get_secret_value()` only at the single call site that needs the raw value.
3. **Nested groups via delimiter.** Group settings by domain with nested `BaseModel`
   subclasses and `env_nested_delimiter="__"` (e.g. `DB__URL`, `REDIS__URL`). Env vars
   stay flat; Python access reads as `settings.db.url`.
4. **Validate invariants.** Use `@field_validator` and `@model_validator(mode="after")`
   to enforce: JWT secret ≥ 32 chars in production, `ENVIRONMENT` is one of
   `Literal["dev", "test", "prod"]`, required URLs are reachable.
5. **Cache via `lru_cache`.** Define
   `@lru_cache def get_settings() -> Settings: return Settings()` and inject as a FastAPI
   dependency. Never instantiate `Settings()` at module import time outside `get_settings`
   — this makes `app.dependency_overrides[get_settings]` trivial in tests.
