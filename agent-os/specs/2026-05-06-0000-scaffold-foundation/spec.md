# Spec: scaffold-foundation

## Goal

Land the minimum **shared** foundation so three Phase 1 efforts (`feat/auth`,
`feat/checkout`, `feat/frontend`) can branch off `main` and proceed in parallel without
colliding on base configuration files. **No business logic** — no `/checkout`, no auth
routes, no user model.

## Out of scope

- `/checkout` route, calculation engine, or persistence model.
- `User` model, password hashing, JWT issuance, or auth routes.
- Rate-limiter wiring on real endpoints.
- React features (cart UI, login form, queries) — only an empty themed shell.

## Deliverables

### `backend/`

- `pyproject.toml` — uv project; all MVP runtime + dev dependencies stubbed
  (fastapi, sqlmodel, alembic, asyncpg, aiosqlite, pydantic-settings, authlib,
  argon2-cffi, slowapi[redis], redis, python-multipart, pytest, pytest-asyncio,
  pytest-cov, httpx, ruff, mypy). Ruff config (`select`, `format`, per-file-ignores)
  and mypy config blocks per `root/linting`.
- `Dockerfile` — multi-stage uv build, non-root, HEALTHCHECK per `infra/docker`.
- `alembic.ini` — timestamped + slugged `file_template` per `backend/alembic`.
- `alembic/env.py` — async; imports `app.models` so `target_metadata` resolves
  (currently empty — it just exposes `SQLModel.metadata`).
- `alembic/versions/.gitkeep`.
- `app/main.py` — FastAPI app with `lifespan`; only `/healthz` is mounted.
- `app/core/config.py` — `Settings` class via pydantic-settings; `get_settings`
  cached per `backend/settings`.
- `app/core/db.py` — async engine + `async_session_maker` + `get_session`
  dependency stub per `backend/sqlmodel`.
- `app/api/__init__.py` — `api_router = APIRouter()` registering `health`.
- `app/api/health.py` — `GET /healthz` returns `{"status": "ok"}`.
- `app/{models,schemas,services}/__init__.py` — empty packages so Phase 1 branches
  drop in their domain modules without touching `__init__` files first.
- `tests/__init__.py`.
- `tests/conftest.py` — `client` fixture (httpx.AsyncClient + ASGITransport)
  per `backend/testing`.

### `frontend/`

- `package.json` — vite, react, react-dom, typescript, tailwindcss, autoprefixer,
  postcss, class-variance-authority, clsx, tailwind-merge, plus dev scripts.
- `Dockerfile` — multi-stage node → nginx-served static.
- `index.html`, `vite.config.ts`, `tsconfig.json`, `tsconfig.node.json`,
  `tailwind.config.js`, `postcss.config.js`, `components.json` (shadcn config).
- `src/main.tsx`, `src/App.tsx` — empty themed page titled "cart-calculator".
- `src/index.css` — `@tailwind` directives + shadcn CSS variable theme tokens.
- `src/lib/utils.ts` — `cn()` helper.

### `infra/nginx/nginx.conf`

`least_conn` upstream over `api1` + `api2`, forwarded headers, explicit timeouts,
`/healthz` route, gzip + `client_max_body_size 1m`. Per `infra/nginx`.

### Root

- `docker-compose.yml` — postgres, redis, migrator (one-shot
  `alembic upgrade head`), `api1` + `api2`, nginx, frontend; healthchecks; `.env`
  support.
- `.env.example` — `POSTGRES_*`, `REDIS_URL`, `JWT_SECRET`, etc.
- `.gitignore` — extend with `backend/.venv`, `frontend/node_modules`,
  `frontend/dist`, `.env`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache`.

## Acceptance

- `docker compose config` succeeds.
- `cd backend && uv sync && uv run pytest -q` (zero tests collected is fine).
- `cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app`.
- `cd frontend && npm install && npx tsc --noEmit`.
- Stack boots and `curl -fsS http://localhost/healthz` returns `200`.

## Standards followed

`root/linting`, `backend/fastapi`, `backend/settings`, `backend/sqlmodel`,
`backend/alembic`, `backend/testing`, `infra/docker`, `infra/nginx`,
`frontend/vite-react`, `frontend/shadcn-tailwind`.
