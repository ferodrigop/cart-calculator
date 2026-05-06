# Product Mission

## Problem

Most checkout-style demos either skip distribution entirely (single process, in-memory
state) or jump straight to heavyweight infrastructure (Kubernetes, Kafka, multiple
microservices) that buries the actual learning. There is a gap in the middle: a small,
end-to-end checkout API that is genuinely distributed — stateless replicas behind a load
balancer, sharing state through Postgres and Redis — without the over-engineering. There
is also no clean reference, at this scope, that pairs that distributed posture with
production-grade hygiene: typed config, Alembic migrations run from a dedicated one-shot
service, OAuth2 + JWT auth via Authlib, Redis-backed rate limiting that proves
cross-replica correctness, and a pure-function calculation engine that is trivial to
extend as business rules grow.

`cart-calculator` exists to fill that gap with the smallest credible implementation.

## Target Users

Primary user is the project author, working through distributed-system design choices
end-to-end on a realistic but bounded domain. Secondary audience is any developer
reviewing the repo as a reference for "what a clean, minimal, distributed FastAPI service
looks like in 2026" — the layout, the choice rationale captured in
[`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md), and the standards under
[`agent-os/standards/`](../standards/) are written to be readable cold.

## Solution

A single `POST /checkout` endpoint computes `subtotal / taxes / discount / total` and
persists each checkout, fronted by Nginx round-robin over two stateless FastAPI replicas.
Distribution is proven, not claimed: Redis-backed rate limiting (via `slowapi`) would
silently desync across replicas if it were in-process — using a shared backend forces
correct behavior. Migrations run from a dedicated `migrator` one-shot service so the two
API replicas never race. The calculation engine is a pure function in
`backend/app/services/checkout.py`, decoupled from the router and the DB, so adding
per-region taxes, coupon codes, or tier discounts later does not touch the HTTP layer.
Auth is OAuth2 password flow with Authlib-issued JWTs and a Redis-backed `jti` denylist
for refresh-token rotation. A bonus Vite + React + shadcn/ui SPA is included so the API
has a usable face without distracting from the backend.

The principle throughout, copied from [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md):
**clarity and correctness over completeness.**
