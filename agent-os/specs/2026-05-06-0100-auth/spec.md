# Spec: auth

## Goal

Land the full Phase 1 authentication stack on `feat/auth`. Persistent `User` model,
register / login / me / refresh routes via OAuth2 password flow, Authlib-issued JWTs
with separate access + refresh secrets, Argon2 password hashing, refresh-token
rotation backed by a Redis `jti` denylist, and slowapi-driven rate limiting on
`/auth/*` with the moving-window strategy. Cross-replica correctness is preserved
end-to-end (Redis-backed limiter + denylist).

## Out of scope

- `/checkout` route, calculation engine, persistence beyond the `users` table.
- `GET /auth/users` admin listing or any admin surface.
- Frontend wiring (login form, token storage, refresh rotation in the SPA).
- Password reset, email verification, account lockout on repeated failures.
- Per-user rate limits beyond the IP/user composite key (Phase 2).
- Observability (structured JSON logs, OpenTelemetry, metrics).

## Deliverables

### `backend/app/`

- `models/user.py` — `User(SQLModel, table=True)` with `id: UUID` PK,
  `email: str` unique-indexed (max 255), `password_hash: str`, `created_at: datetime`
  (timestamptz, server default).
- `models/__init__.py` — applies `SQLModel.metadata.naming_convention` and re-exports
  `User` so `alembic/env.py` autogenerate sees it.
- `schemas/auth.py` — `UserRegister`, `UserRead`, `TokenPair`, `RefreshRequest`.
- `core/config.py` — extends `Settings`: split `JWTSettings` into `access_secret` +
  `refresh_secret` (both `SecretStr`); add `RateLimitSettings` (`storage_uri`,
  `default`, `auth_login`, `auth_refresh`); add `PasswordSettings` (`min_length`).
  Production `model_validator` enforces 32+ chars on both JWT secrets.
- `core/security.py` — Argon2 hash/verify; Authlib JWT encode/decode helpers (sub
  is the user UUID, claims include `iat`, `exp`, `jti`, `type`).
- `core/redis.py` — `build_redis(settings)` factory and `get_redis(request)` dep.
- `core/rate_limit.py` — `Limiter` with composite `user:{id}` / `ip:{host}` key,
  Redis storage URI, moving-window strategy.
- `core/exceptions.py` — `AuthError` hierarchy: `EmailAlreadyExists`,
  `InvalidCredentials`, `InvalidTokenError`, `RefreshTokenReused`, `UserNotFound`.
- `services/auth.py` — pure async service functions: `register`, `authenticate`,
  `issue_token_pair`, `rotate_refresh` (with atomic `SET NX` denylist write).
- `api/deps.py` — `SessionDep`, `RedisDep`, `SettingsDep`, `OAuth2PasswordBearer`,
  `get_current_user`, `CurrentUser`.
- `api/auth.py` — `APIRouter(prefix="/auth", tags=["auth"])` with the four routes;
  `5/minute` limit on `/login` and `/refresh`.
- `api/__init__.py` — registers `auth.router` alongside `health.router`.
- `main.py` — extends lifespan to build the Redis client and limiter, attaches
  them to `app.state`, registers `SlowAPIMiddleware`, and registers handlers for
  `RateLimitExceeded` and the `AuthError` hierarchy.

### `backend/alembic/versions/`

- `20260506_0100_create_users.py` — revision id `0001`, `down_revision = None`,
  slug `create_users`. Creates `users` with `Uuid` PK, unique email index,
  timestamptz `created_at` server-defaulted to `now()`.

### `backend/tests/`

- `conftest.py` — sets test env vars at import time (memory rate-limit storage,
  in-memory SQLite, deterministic JWT secrets); session-scoped engine with
  `StaticPool`; SAVEPOINT-per-test session; fakeredis async client; dependency
  overrides for `get_session` and `get_redis`.
- `factories.py` — `UserFactory` build helper.
- `api/test_auth_register.py` — 201 happy / 409 duplicate / 422 short password.
- `api/test_auth_login.py` — 200 happy / 401 wrong password / 401 unknown email.
- `api/test_auth_me.py` — 200 with bearer / 401 missing / 401 wrong type.
- `api/test_auth_refresh.py` — 200 happy / 401 reused (denylist) / 401 tampered.
- `api/test_auth_rate_limit.py` — 5 ok + 6th 429 on `/auth/login`.

### `backend/pyproject.toml`

- Add runtime: `email-validator>=2.0`.
- Add dev: `fakeredis>=2.20`.
- Extend mypy `ignore_missing_imports` to cover `fakeredis.*`.

### Root

- `.env.example` — replace `JWT__SECRET` with `JWT__ACCESS_SECRET` +
  `JWT__REFRESH_SECRET`; add `RATE_LIMIT__*` knobs.

## Acceptance

- `cd backend && uv run pytest -q` — all auth tests pass.
- `cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app` — clean.
- `docker compose up -d --build` then end-to-end:
  - `POST /auth/register` → 201, returns `UserRead`.
  - `POST /auth/login` (form) → 200, returns access + refresh tokens.
  - `GET /auth/me` with bearer access → 200.
  - `POST /auth/refresh` → 200, new pair; replaying the same refresh → 401.
  - 6th login within a minute from the same client → 429.

## Standards followed

- `backend/auth` — Argon2 hashing, Authlib HS256 JWTs, sub=UUID, jti rotation,
  Redis denylist with atomic `SET NX`, `SecretStr` secrets via pydantic-settings.
- `backend/sqlmodel` — async asyncpg/aiosqlite, `expire_on_commit=False`,
  separate models vs schemas, session via dependency, typed `exec()`.
- `backend/settings` — single `Settings` in `core/config.py`, nested groups via
  `__`, `model_validator` for prod invariants, `lru_cache` `get_settings`.
- `backend/rate-limiting` — slowapi + Redis storage_uri, moving-window strategy,
  composite `user/ip` key, 5/min on login + refresh.
- `backend/fastapi` — feature-domain layout, `lifespan` initialization,
  `Annotated` deps, central `AuthError` handler (no raw `HTTPException` in
  services), pinned `response_model` + `status_code`.
- `backend/alembic` — `target_metadata = SQLModel.metadata`, naming convention,
  `revision = "0001"`, autogenerate-compatible diff, runs from one-shot
  `migrator` service.
- `backend/testing` — auto async, `AsyncClient + ASGITransport`,
  SAVEPOINT-per-test, dependency overrides, factory helpers.
- `root/linting` — Ruff curated `select` + format check; per-file ignores for
  tests and migrations already in place.
