# Product Roadmap

## Phase 1: MVP

The MVP is the smallest credible distributed checkout service. Scope is locked to what
proves the architecture and the calculation contract.

- **`POST /checkout` endpoint** accepting a list of items (`name`, `unit_price`,
  `quantity`) and returning `subtotal / taxes / discount / total`.
- **Calculation engine** as a pure function in `backend/app/services/checkout.py`:
  - `subtotal = Σ(unit_price × quantity)`
  - `taxes = 13% of subtotal`
  - `discount = 10% of subtotal if subtotal > 100, else 0`
  - `total = subtotal + taxes − discount`
- **Persistence** of every checkout (request items + computed totals + owning user +
  timestamp) in PostgreSQL via SQLModel, with Alembic migrations applied by a dedicated
  one-shot `migrator` compose service.
- **Authentication** via OAuth2 password flow with Authlib-issued JWTs:
  `POST /auth/register`, `POST /auth/login`, `GET /auth/me`. Refresh-token rotation
  uses a Redis-backed `jti` denylist.
- **Distributed topology** via `docker-compose`: Nginx reverse proxy round-robin in
  front of two stateless FastAPI replicas, sharing Postgres and Redis.
- **Redis-backed rate limiting** (slowapi, moving-window) on auth and checkout
  endpoints — the concrete proof that cross-replica state works.
- **Health endpoint** (`GET /health`) so the load balancer and compose healthchecks
  have something deterministic to hit.
- **Test suite**: pytest + pytest-asyncio + httpx.AsyncClient covering the calculation
  engine, the `/checkout` route, and the auth flow, running against SQLite for speed.
- **Quality gates**: Ruff (lint + format) and mypy clean on `backend/app`.
- **Bonus SPA**: Vite + React + TS + shadcn/ui + Tailwind that signs in, builds a cart,
  and calls `POST /checkout` to render the breakdown.

## Phase 2: Post-Launch

Picked specifically to exercise the extension points the MVP architecture was designed
for, without breaking the locked stack.

- **Per-region tax rules** plugged into the calculation engine without changing the
  router or DB layer.
- **Coupon codes and tier discounts** as additional pure rules in the engine.
- **Checkout history**: `GET /checkouts` (per authenticated user), paginated.
- **Observability**: structured JSON logs, `/metrics` endpoint, OpenTelemetry traces
  through Nginx → API → DB.
- **Operational hardening**: per-user rate limits in addition to per-IP; password reset
  flow; account lockout on repeated auth failures.
- **Frontend polish**: form validation, optimistic UI for the cart, proper auth state
  handling and refresh-token rotation in the client.
- **CI**: GitHub Actions running Ruff, mypy, and pytest on every push, plus a build of
  the full compose stack.
