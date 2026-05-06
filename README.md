# cart-calculator

A small, distributed checkout calculation service. A single `POST /checkout` endpoint
computes `subtotal / taxes / discount / total`, persists each checkout, and is fronted
by Nginx load-balancing two stateless FastAPI replicas. Bonus Vite + React + shadcn/ui
SPA included.

> Personal MVP exploring how to build a clean, genuinely-distributed FastAPI service
> end-to-end without over-engineering. Architecture rationale lives in
> [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Per-component standards live under
> [`agent-os/standards/`](agent-os/standards/).

## Stack

- **Backend** — FastAPI + SQLModel + Alembic, OAuth2 password flow with Authlib JWTs,
  Argon2 password hashing, slowapi rate limiting backed by Redis, pydantic-settings,
  Python 3.12, deps managed with [`uv`](https://docs.astral.sh/uv/)
- **Storage** — PostgreSQL at runtime, SQLite in tests, Redis for rate-limit counters
  and the refresh-token `jti` denylist
- **Edge** — Nginx as reverse proxy + load balancer, round-robin across two replicas;
  the same nginx serves the SPA and proxies API routes (single origin, no CORS)
- **Frontend** — Vite + React + TypeScript + Tailwind + shadcn/ui, TanStack Query,
  react-hook-form + zod, single-flight 401 refresh interceptor
- **Tests** — pytest + pytest-asyncio + httpx.AsyncClient, fakeredis for Redis paths,
  SAVEPOINT-per-test isolation
- **Quality** — Ruff (lint + format), mypy strict, TypeScript strict
- **Container** — Docker + docker-compose, dedicated one-shot `migrator` service

## Quick start

```bash
cp .env.example .env       # defaults work locally; rotate JWT secrets for any real use
docker compose up -d --build

open http://localhost      # SPA — register → cart → checkout
```

The full topology (postgres, redis, migrator, api1, api2, nginx, frontend) comes up in
under a minute on a warm cache. Health check:

```bash
curl http://localhost/healthz   # {"status":"ok"}
```

OpenAPI / Swagger docs:

```bash
open http://localhost/docs
```

## Endpoints

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/healthz` | — | Liveness |
| `POST` | `/auth/register` | — | `{email, password}` → user record |
| `POST` | `/auth/login` | — | OAuth2 password flow (form-encoded `username + password`) → `{access_token, refresh_token}` |
| `GET` | `/auth/me` | Bearer | Current user |
| `POST` | `/auth/refresh` | — | Rotates refresh token; old token denylisted via Redis `jti` |
| `POST` | `/checkout` | Bearer | `{items: [{name, unit_price, quantity}]}` → `{subtotal, taxes, discount, total}` |

Calculation rules are fixed for the MVP: taxes = 13 % of subtotal; discount = 10 % when
subtotal > 100, else 0. The engine is a pure function at
[`backend/app/services/checkout.py`](backend/app/services/checkout.py) — new rules
(per-region taxes, coupon codes, tier discounts) plug in there without touching the
HTTP layer.

## Common commands

| Goal | Command |
| --- | --- |
| Bring up the full stack | `docker compose up --build` |
| Backend tests (all) | `cd backend && uv run pytest` |
| Backend tests (single) | `cd backend && uv run pytest tests/api/test_auth_login.py::test_login_with_valid_credentials` |
| Lint Python | `cd backend && uv run ruff check .` |
| Format Python | `cd backend && uv run ruff format .` |
| Type-check Python | `cd backend && uv run mypy app` |
| Create migration | `cd backend && uv run alembic revision --autogenerate -m "<slug>"` |
| Apply migrations | `cd backend && uv run alembic upgrade head` |
| Frontend dev server | `cd frontend && npm run dev` |
| Frontend type-check | `cd frontend && npx tsc --noEmit` |
| Frontend build | `cd frontend && npm run build` |

## Repository layout

```
cart-calculator/
├── backend/                 # FastAPI service
│   ├── app/
│   │   ├── api/             # Routers (health, auth, checkout) + DI deps
│   │   ├── core/            # Settings, db engine, security, redis, rate-limit
│   │   ├── db/              # (reserved)
│   │   ├── models/          # SQLModel models (User, Checkout)
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Pure business logic — calc engine, auth
│   │   └── main.py
│   ├── alembic/             # Migrations
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                # Vite + React SPA
│   ├── src/
│   │   ├── components/ui/   # shadcn primitives
│   │   ├── features/auth/   # login + register pages
│   │   ├── features/cart/   # cart + checkout summary
│   │   ├── lib/             # api client, auth store, query keys, format helpers
│   │   └── routes.tsx
│   └── Dockerfile
├── infra/nginx/nginx.conf   # SPA + API single-origin routing
├── docs/ARCHITECTURE.md     # Decisions and rejected alternatives
├── agent-os/
│   ├── product/             # mission, roadmap, tech stack
│   ├── standards/           # 12 per-topic standards (FastAPI, SQLModel, …)
│   └── specs/               # Per-feature shape-spec output
├── .github/workflows/ci.yml # Ruff + mypy + pytest + tsc + build + compose build
├── docker-compose.yml
└── .env.example
```

## Distributed correctness

The "distributed" claim is provable, not just claimed:

- **Stateless replicas** — two FastAPI containers (`api1`, `api2`) sit behind Nginx
  with round-robin upstream balancing. No request affinity needed.
- **Shared state in Redis** — slowapi rate-limit counters and refresh-token `jti`
  denylist live in Redis. An in-process limiter would silently desync between
  replicas; routing through Redis forces correct shared-state behaviour.
- **One-shot migrations** — Alembic runs from a dedicated `migrator` service whose
  successful exit gates `api1` / `api2` startup. Replicas never race on schema.

Validated end-to-end (`docker compose up -d`):

```bash
# refresh-token rotation works across the upstream balance
curl -X POST localhost/auth/refresh -H 'Content-Type: application/json' \
     -d "{\"refresh_token\":\"$REFRESH\"}"   # 200 — first replica
curl -X POST localhost/auth/refresh -H 'Content-Type: application/json' \
     -d "{\"refresh_token\":\"$REFRESH\"}"   # 401 — denylisted, even if a different replica answers

# rate-limit is shared too
for i in $(seq 1 6); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost/auth/login \
       -d "username=$EMAIL&password=wrong-$i"
done
# → 401 401 401 401 429 429
```

## Standards & conventions

Per-component standards (FastAPI structure, SQLModel patterns, Alembic, auth, settings,
rate-limiting, testing, Ruff, Docker, Nginx, Vite/React, shadcn/Tailwind) live in
[`agent-os/standards/`](agent-os/standards/) and are routed by topic via
[`agent-os/standards/index.yml`](agent-os/standards/index.yml). Apply them when
implementing; if a change contradicts a standard, update the standard in the same
change so the source of truth stays consistent.

## Repo etiquette

- **Conventional commit prefixes:** `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`,
  `test:`.
- **Direct push to `main` is allowed** at this scope; move to PRs once collaborators
  arrive.
- Architectural decisions go into `docs/`; split into per-decision ADRs once they
  accumulate.

## License

MIT.
