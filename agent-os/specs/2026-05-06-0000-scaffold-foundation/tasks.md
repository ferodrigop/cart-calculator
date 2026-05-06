# Tasks

## Backend

- [ ] `backend/pyproject.toml` with deps + ruff + mypy + pytest config.
- [ ] `backend/Dockerfile` multi-stage, non-root, HEALTHCHECK.
- [ ] `backend/alembic.ini` with timestamped slug `file_template`.
- [ ] `backend/alembic/env.py` async, `target_metadata = SQLModel.metadata`.
- [ ] `backend/alembic/versions/.gitkeep`.
- [ ] `backend/app/main.py` with `lifespan` and `/healthz`.
- [ ] `backend/app/core/config.py` with `Settings` + `get_settings`.
- [ ] `backend/app/core/db.py` with async engine/session stub.
- [ ] `backend/app/api/__init__.py` mounting `health` router.
- [ ] `backend/app/api/health.py` returning `{"status": "ok"}`.
- [ ] `backend/app/{models,schemas,services}/__init__.py`.
- [ ] `backend/tests/__init__.py`, `backend/tests/conftest.py` with client fixture.
- [ ] `backend/.dockerignore`.

## Frontend

- [ ] `frontend/package.json` with dev/build scripts.
- [ ] `frontend/Dockerfile` multi-stage build → nginx static.
- [ ] `frontend/index.html`.
- [ ] `frontend/vite.config.ts` with `@/*` alias.
- [ ] `frontend/tsconfig.json`, `frontend/tsconfig.node.json` strict.
- [ ] `frontend/tailwind.config.js`, `frontend/postcss.config.js`.
- [ ] `frontend/components.json` (shadcn).
- [ ] `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/index.css`.
- [ ] `frontend/src/lib/utils.ts` (`cn`).
- [ ] `frontend/src/vite-env.d.ts` typed `ImportMetaEnv`.
- [ ] `frontend/.dockerignore`.

## Infra & root

- [ ] `infra/nginx/nginx.conf` per `infra/nginx`.
- [ ] `docker-compose.yml`.
- [ ] `.env.example`.
- [ ] Extend `.gitignore`.

## Verify

- [ ] `docker compose config`.
- [ ] `uv sync && uv run pytest -q`.
- [ ] `uv run ruff check . && uv run ruff format --check . && uv run mypy app`.
- [ ] `npm install && npx tsc --noEmit`.
- [ ] `curl -fsS http://localhost/healthz` (with stack up).

## Ship

- [ ] `git commit -m "chore: scaffold foundation"`.
- [ ] `git push -u origin chore/scaffold`.
- [ ] `gh pr create --base main --title "chore: scaffold foundation" --body ...`.
