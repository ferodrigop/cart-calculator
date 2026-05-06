# Tasks

## Settings & dependencies

- [ ] `backend/pyproject.toml` — add `email-validator>=2.0` (runtime),
  `fakeredis>=2.20` (dev); extend mypy `ignore_missing_imports` for `fakeredis.*`.
- [ ] `backend/app/core/config.py` — split `JWTSettings` (`access_secret` +
  `refresh_secret`); add `RateLimitSettings`, `PasswordSettings`; tighten prod
  validator.
- [ ] `.env.example` — split JWT secrets; add `RATE_LIMIT__*` knobs.

## Domain model

- [ ] `backend/app/models/user.py` — `User` SQLModel with UUID PK, unique email,
  hashed password, `created_at` timestamptz.
- [ ] `backend/app/models/__init__.py` — export `User`; apply naming convention.
- [ ] `backend/alembic/versions/20260506_0100_create_users.py` — revision `0001`,
  `down_revision = None`.

## Core primitives

- [ ] `backend/app/core/security.py` — Argon2 hash/verify, JWT encode/decode helpers.
- [ ] `backend/app/core/redis.py` — `build_redis`, `get_redis` dep.
- [ ] `backend/app/core/exceptions.py` — `AuthError` hierarchy.
- [ ] `backend/app/core/rate_limit.py` — `Limiter` + composite key + moving-window.

## Service & API

- [ ] `backend/app/services/auth.py` — register / authenticate /
  issue_token_pair / rotate_refresh.
- [ ] `backend/app/schemas/auth.py` — `UserRegister`, `UserRead`, `TokenPair`,
  `RefreshRequest`.
- [ ] `backend/app/api/deps.py` — `SessionDep`, `RedisDep`, `SettingsDep`,
  `oauth2_scheme`, `get_current_user`, `CurrentUser`.
- [ ] `backend/app/api/auth.py` — register / login / me / refresh routes;
  `5/minute` on login + refresh.
- [ ] `backend/app/api/__init__.py` — register `auth.router`.
- [ ] `backend/app/main.py` — lifespan: redis + limiter; middleware + exception
  handlers.

## Tests

- [ ] `backend/tests/conftest.py` — env vars, engine, session SAVEPOINT, fakeredis,
  app overrides, helper.
- [ ] `backend/tests/factories.py` — `UserFactory`.
- [ ] `backend/tests/api/test_auth_register.py`.
- [ ] `backend/tests/api/test_auth_login.py`.
- [ ] `backend/tests/api/test_auth_me.py`.
- [ ] `backend/tests/api/test_auth_refresh.py`.
- [ ] `backend/tests/api/test_auth_rate_limit.py`.

## Verify

- [ ] `cd backend && uv sync`.
- [ ] `cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app`.
- [ ] `cd backend && uv run pytest -q`.
- [ ] `docker compose up -d --build` then end-to-end curl
  (`/auth/register`, `/auth/login`, `/auth/me`, `/auth/refresh`).

## Ship

- [ ] `git commit -m "feat: authentication"`.
- [ ] `git push -u origin feat/auth`.
- [ ] `gh pr create --base main --title "feat: authentication" --body ...`.
- [ ] STOP. Do not merge — orchestrator merges after review.
