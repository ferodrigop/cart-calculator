# Tech Stack

The stack is locked. Decisions and rejected alternatives are documented in
[`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md); per-component conventions live under
[`agent-os/standards/`](../standards/) and are indexed by
[`agent-os/standards/index.yml`](../standards/index.yml).

## Frontend

- **Vite + React + TypeScript** — SPA, no SSR/RSC ceremony.
- **shadcn/ui + Tailwind CSS** — auditable component code we own, modern aesthetic.
- **Package manager:** npm.

## Backend

- **Python 3.12** with **FastAPI** for routing, validation, and OpenAPI.
- **SQLModel** as the ORM (single source of truth for Pydantic schemas + SQLAlchemy
  models), with **Alembic** for migrations.
- **Authlib** for JWT issuance/verification under an OAuth2 password flow built on
  `fastapi.security.OAuth2PasswordBearer`.
- **pydantic-settings** for typed, `.env`-driven configuration.
- **slowapi** for rate limiting, backed by Redis (cross-replica correctness).
- **Dependency manager:** `uv`.

## Database

- **PostgreSQL** at runtime (in `docker-compose`).
- **SQLite** in tests, via the same SQLAlchemy dialect surface — no code changes needed
  between environments.
- **Redis** for ephemeral coordination state (rate-limit counters, refresh-token `jti`
  denylist, optional response cache).

## Other

- **Edge:** Nginx as reverse proxy / load balancer, round-robin across two stateless
  FastAPI replicas.
- **Containerization:** Docker + `docker-compose`. Migrations execute from a dedicated
  one-shot `migrator` service so API replicas never race on schema changes.
- **Testing:** pytest + pytest-asyncio + httpx.AsyncClient (with `ASGITransport`) +
  pytest-cov.
- **Quality:** Ruff (lint + format, replaces Black/isort/Flake8/pyupgrade) and mypy.
- **Hosting:** local `docker compose up` is the target deployment model for now;
  cloud/Kubernetes are explicitly out of scope (see `docs/ARCHITECTURE.md` §6).
