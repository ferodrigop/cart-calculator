# Architecture & Decisions

This document captures the architectural decisions made for `cart-calculator`. The guiding
principle is **clarity and correctness over completeness** — pick the right tool, do not
reinvent wheels, and do not over-engineer an MVP.

---

## 1. System Overview

`cart-calculator` is a small, distributed checkout service. The system is composed of:

```
            ┌──────────────┐
            │   Frontend   │  (Vite + React + TS, shadcn/ui)
            │  (optional)  │
            └──────┬───────┘
                   │ HTTP
                   ▼
            ┌──────────────┐
            │    Nginx     │  (reverse proxy / load balancer)
            └──────┬───────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
  ┌──────────┐          ┌──────────┐
  │ FastAPI  │          │ FastAPI  │   (2 stateless replicas)
  │ replica  │          │ replica  │
  └────┬─────┘          └────┬─────┘
       │                     │
       └──────────┬──────────┘
                  │
        ┌─────────┴──────────┐
        ▼                    ▼
  ┌──────────┐         ┌──────────┐
  │ Postgres │         │  Redis   │   (shared state proves
  │   (DB)   │         │  (cache  │    distributed correctness)
  └──────────┘         │ + rate   │
                       │ limit)   │
                       └──────────┘
```

The whole stack runs from a single `docker-compose.yml`.

---

## 2. Stack Decisions

### Backend: FastAPI (Python 3.12)

**Why:** The assignment emphasizes *clarity, correctness, and easy to extend*. FastAPI gives
us automatic OpenAPI/Swagger docs, Pydantic-based validation, async support, and code that
reads almost like the spec itself. The calculation logic is trivial in any language —
language choice is about ergonomics and signal, not raw throughput.

**Rejected:**
- **Go + Gin** — performance is irrelevant for this workload; verbosity hurts the
  "easy to understand" goal.
- **Node + Express** — no clear advantage over FastAPI for an API-first project.
- **Spring Boot** — boilerplate-heavy, works against MVP intent.

### ORM: SQLModel + Alembic

**Why:** SQLModel is authored by the same person as FastAPI (tiangolo) and unifies Pydantic
schemas with SQLAlchemy models — a single source of truth. It is the idiomatic choice in
the FastAPI ecosystem. Alembic is used for migrations because SQLModel is built on top of
SQLAlchemy 2.x and inherits its migration tooling.

**Rejected:**
- **Raw SQLAlchemy 2.0** — verbose; we'd have to define Pydantic schemas separately.
- **Tortoise ORM** — smaller ecosystem, weaker migration story.

### Database: PostgreSQL (runtime) + SQLite (tests)

**Why:** Postgres in `docker-compose` signals production-thinking and matches what most
companies actually run. SQLite for tests keeps the test suite fast and dependency-free.
The split itself is a useful talking point — same SQLAlchemy dialect, different backends,
no code changes.

### Authentication: Authlib + JWT (OAuth2 password flow)

**Why:** Authlib is actively maintained and the recommended replacement for `python-jose`
(now abandoned with unfixed CVEs). The OAuth2 password flow with bearer tokens is the
standard pattern in the FastAPI docs. We hand-roll the small wrapper around
`fastapi.security.OAuth2PasswordBearer` rather than pulling a heavyweight package like
`fastapi-users` — for a checkout MVP, we only need register/login/me.

**Rejected:**
- **fastapi-users** — too much surface area for a 2-endpoint auth need.
- **Auth0 / Clerk / Supabase** — outsourcing the interesting part; signals the wrong thing
  in an interview.

### Settings: pydantic-settings

**Why:** Native to the Pydantic v2 ecosystem already in use. Type-safe, supports `.env`
files, and is the de-facto FastAPI default. Zero added dependency footprint.

### Caching & Rate Limiting: Redis + slowapi

**Why:** Redis is the proof that the system genuinely works in a distributed setup. With
two FastAPI replicas behind Nginx, an in-memory rate limiter would silently fail (each
replica would have its own counter). Redis-backed limiting forces shared state and makes
the distributed claim defensible.

### Edge: Nginx (reverse proxy + load balancer)

**Why:** Nginx in front of two FastAPI replicas demonstrates a real-world LB topology.
Round-robin upstream is sufficient for a demo; the point is to show stateless replicas
sharing a DB and a Redis layer.

### Testing: pytest + pytest-asyncio + httpx.AsyncClient

**Why:** The undisputed FastAPI testing stack. `httpx.AsyncClient` with `ASGITransport`
correctly tests async endpoints without spinning up a real server. `pytest-cov` for
coverage reporting.

### Tooling: Ruff + mypy

**Why:** Ruff replaces Black, isort, Flake8, and pyupgrade with a single tool that runs
~100x faster. It is the unambiguous 2026 default — using anything else looks dated. Mypy
adds static type checking on top.

### Containerization: Docker + docker-compose

**Why:** Universal, expected, and cleanly orchestrates the full distributed topology
(2x API + Nginx + Redis + Postgres) in a single command. Reviewers can run the whole
stack with `docker compose up`.

### Frontend (bonus): Vite + React + TS + shadcn/ui + Tailwind

**Why:** A checkout demo is a single-page app that hits the API. Vite gets out of the way
— no SSR ceremony, no Server Components mental overhead. shadcn/ui gives a polished,
modern look with auditable component code we own (rather than an opaque dependency). The
spotlight stays on the backend.

**Rejected:**
- **Next.js App Router** — RSC/SSR adds complexity we do not need for a SPA.
- **MUI** — Material aesthetic looks dated for a modern checkout demo.

---

## 3. Distributed Architecture

The assignment requires that the solution **must work in a distributed architecture**.
We satisfy this in three concrete ways:

1. **Stateless API replicas.** Two FastAPI containers run behind Nginx with
   `deploy.replicas: 2`. No request-affinity is required — any request can hit any replica.
2. **Shared state in external services.** All persistent data lives in Postgres; all
   ephemeral coordination state (rate-limit counters, optional sessions/cache) lives in
   Redis. No in-process state.
3. **Shared-state proof via Redis-backed rate limiting.** A simple in-memory limiter would
   silently desync across replicas; using `slowapi` with a Redis backend forces the system
   to demonstrate correct shared-state behavior.

This is the **minimum credible** distributed setup. Kafka, Celery, and Kubernetes would
all be over-engineering for a take-home.

---

## 4. Repository Layout

```
cart-calculator/
├── backend/                 # FastAPI service
│   ├── app/
│   │   ├── api/             # Routers (auth, checkout, health)
│   │   ├── core/            # Config, security, dependencies
│   │   ├── db/              # Session, init, migrations entry
│   │   ├── models/          # SQLModel models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic (calculation engine)
│   │   └── main.py
│   ├── alembic/             # Migrations
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                # Vite + React (bonus UI)
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── infra/
│   └── nginx/
│       └── nginx.conf
├── docs/
│   └── ARCHITECTURE.md      # this file
├── docker-compose.yml
├── .env.example
└── README.md
```

Backend follows a layered structure: routers stay thin, business rules live in
`services/`, persistence is isolated under `db/` and `models/`. This makes the calculation
engine independently testable and easy to extend (e.g., per-region tax rules,
discount tiers) without touching the HTTP layer.

---

## 5. Extensibility Notes

The assignment specifies fixed rules (13% taxes, 10% discount over $100). The codebase is
structured so these rules are easy to evolve:

- **Calculation engine** is a pure function in `services/checkout.py`, decoupled from
  the router and the DB. New rules (per-item taxes, coupon codes, tiered discounts) can
  be added without changing the API contract.
- **Schemas** are versioned implicitly via Pydantic models; adding optional fields is
  backwards-compatible by default.
- **Migrations** via Alembic give a clean path for schema evolution.

---

## 6. What is Intentionally Out of Scope

- Payment processing, refunds, inventory.
- Multi-currency or i18n.
- Admin UI / role-based access control beyond a simple authenticated user.
- Observability stack (Prometheus, OpenTelemetry) — mentioned in README as a next step.
- Kubernetes manifests — `docker-compose` is sufficient to demonstrate the topology.

These are flagged as future work, not omissions.
