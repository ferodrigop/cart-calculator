# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`cart-calculator` is a personal MVP exploration of a clean, distributed checkout API. A
single `POST /checkout` endpoint accepts a list of items, computes
`subtotal / taxes / discount / total`, persists each checkout, and is fronted by an Nginx
load balancer over two stateless FastAPI replicas.

Read [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) before making non-trivial changes — it
captures the stack decisions, what was rejected, and why.

## Stack (locked)

- **Backend:** FastAPI + SQLModel + Alembic + Authlib (JWT, OAuth2 password flow) +
  pydantic-settings, Python 3.12, deps managed with `uv`
- **Storage:** PostgreSQL (runtime), SQLite (tests), Redis (rate-limit + cache)
- **Edge:** Nginx as reverse proxy / load balancer over 2 FastAPI replicas
- **Tests:** pytest + pytest-asyncio + httpx.AsyncClient + pytest-cov
- **Quality:** Ruff (lint + format) + mypy
- **Container:** Docker + docker-compose
- **Frontend (bonus):** Vite + React + TypeScript + shadcn/ui + Tailwind

## Standards (read before implementing)

Project standards live under [`agent-os/standards/`](agent-os/standards/) — 12 files
covering FastAPI structure, SQLModel async patterns, Alembic, auth, settings,
rate-limiting, testing, Ruff, Docker, Nginx, Vite/React, shadcn/Tailwind. Match a standard
to your task via [`agent-os/standards/index.yml`](agent-os/standards/index.yml).

- **Apply standards when implementing.** Don't duplicate the guidance into code comments —
  point at the standard.
- **If a change contradicts a standard, update the standard in the same change** so the
  source of truth stays consistent.
- The Agent OS slash commands (`/discover-standards`, `/inject-standards`,
  `/index-standards`, `/plan-product`, `/shape-spec`) are installed under
  `.claude/commands/agent-os/`.

## Commands

The stack is locked but the backend and frontend are not yet scaffolded. Update this
section as commands materialize.

| Goal | Command (planned) |
| --- | --- |
| Bring up full stack | `docker compose up --build` |
| Backend tests (all) | `cd backend && uv run pytest` |
| Backend tests (single) | `cd backend && uv run pytest tests/path/test_x.py::test_name` |
| Lint Python | `cd backend && uv run ruff check .` |
| Format Python | `cd backend && uv run ruff format .` |
| Type-check Python | `cd backend && uv run mypy app` |
| Create migration | `cd backend && uv run alembic revision --autogenerate -m "<slug>"` |
| Apply migrations | `cd backend && uv run alembic upgrade head` |
| Frontend dev server | `cd frontend && npm run dev` |
| Frontend type-check | `cd frontend && npx tsc --noEmit` |

## Architecture (mental model)

Full design in `docs/ARCHITECTURE.md`. The minimum required model:

- **API replicas are stateless.** Persistent data lives in Postgres, ephemeral
  coordination state (rate-limit counters, optional cache) in Redis. Two replicas behind
  Nginx; round-robin works because no replica owns state.
- **Calculation engine is a pure function** at `backend/app/services/checkout.py`,
  decoupled from the router and the DB. New business rules (per-region tax, coupon codes,
  tier discounts) plug in without touching the HTTP layer.
- **Migrations run from a dedicated one-shot `migrator` service** in compose; never
  concurrently from both API replicas.
- **Auth uses OAuth2 password flow with Authlib JWTs.** Refresh-token rotation is
  Redis-backed via a `jti` denylist.
- **Distributed-correctness proof:** rate limiting via `slowapi` + Redis with a
  moving-window strategy. An in-process limiter would silently desync across replicas;
  Redis forces shared-state behavior.

## Repo etiquette

- **Commit messages** use conventional-commit prefixes: `feat:`, `fix:`, `chore:`,
  `docs:`, `refactor:`, `test:`.
- **Direct push to `main` is allowed** at this scope. Move to PRs once the project gains
  collaborators.
- **Architectural decisions** go into `docs/`. The single `ARCHITECTURE.md` is sufficient
  for now; split into per-decision ADR files once decisions accumulate.
