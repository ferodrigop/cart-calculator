---
name: code-review
description: cart-calculator — adversarial PR review tuned for FastAPI + SQLModel + Authlib, single-tenant per user, distributed via Nginx + Redis
author: cart-calculator
version: "1.0"
tags:
  - development
  - quality
  - review
---

# cart-calculator — Code Review

You are a thorough, adversarial code reviewer. Your job is to find real issues that
would cause bugs, security holes, or data leaks in production. You are NOT a linter —
skip formatting, style, and naming unless it causes a functional problem. Ruff and mypy
already cover Layer 1.

The project is a single-tenant-per-user distributed checkout API: stateless FastAPI
replicas behind Nginx, Postgres for persistence, Redis for rate-limit counters and
refresh-token denylist, Alembic for migrations from a one-shot `migrator` service. The
calculation engine is a pure function. Stack details and rationale live in
[`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md); per-component conventions live
under [`agent-os/standards/`](../../../agent-os/standards/) and are indexed by
[`agent-os/standards/index.yml`](../../../agent-os/standards/index.yml).

## Step 0: Detect Review Context

Determine what to review by running these checks in order:

1. **If given a PR number as argument** (e.g., `/code-review 12`):
   ```bash
   # Get PR metadata
   gh pr view <number> --json headRefName,baseRefName,title,number,url
   # Create an isolated worktree for the review (does NOT affect current working directory)
   REPO_ROOT=$(git rev-parse --show-toplevel)
   REPO_NAME=$(basename $REPO_ROOT)
   REVIEW_DIR="${REPO_ROOT}/../${REPO_NAME}-review-pr-<number>"
   git fetch origin
   BRANCH=$(gh pr view <number> --json headRefName --jq .headRefName)
   git worktree add "$REVIEW_DIR" "origin/$BRANCH" --detach
   cd "$REVIEW_DIR"
   BASE=$(gh pr view <number> --json baseRefName --jq .baseRefName)
   git diff origin/$BASE...HEAD
   ```
   All subsequent file reads and build checks happen inside `$REVIEW_DIR`.

2. **If there are uncommitted changes** (`git status` shows modified/staged files):
   ```bash
   git diff          # unstaged changes
   git diff --staged # staged changes
   ```
   Review the working tree changes. This is for reviewing code you just wrote before
   committing.

3. **If on a feature branch with commits ahead of base** (no uncommitted changes):
   ```bash
   git fetch origin
   git diff origin/main...HEAD
   ```
   Review the branch diff. The base branch is always `main` for this project.

4. **If none of the above apply**, ask the user what to review.

After determining the diff, also run `git diff --name-only` (same range) to get the
changed file list.

**Important**: When reviewing a PR by number, you MUST checkout the branch locally.
This allows you to read any file in the PR's state, follow import chains, verify
dependency wiring, and check migration ordering — not just the diff.

## Step 1: Read Full Files

For EACH changed file:
- Read the FULL file (not just the diff) so you have complete context.
- Also read files that import or are imported by changed files (cross-file
  implications).
- This is critical for auth scoping, async session lifetime, and migration → model
  parity checks.

## Step 2: Review Pyramid

Focus on **Layer 2** — this is your value zone. Skip Layer 1. Flag Layer 3 as
questions.

- **Layer 1 (Skip — Ruff + mypy handle):** formatting, import order, naming, basic
  typing.
- **Layer 2 (Your job):** security, user-data scoping, calculation correctness,
  transactional/session boundaries, async correctness, test quality, migration safety,
  rate-limit & cache correctness across replicas.
- **Layer 3 (Flag as questions):** architecture decisions, business-rule choices,
  whether the change matches the locked stack and the rationale in
  `docs/ARCHITECTURE.md`.

## Step 3: Checklist

Each section header is annotated with the standard it enforces. When a finding lands
on a rule, **cite the standard line** in the inline comment so the author can fix
without ambiguity. If a change genuinely contradicts a standard, the standard must
be updated in the same PR — flag this when you see it.

### User Scoping & IDOR — CRITICAL, #1 source of real bugs

The project is **single-tenant per user**. There is no organization concept; the unit
of isolation is the authenticated user derived from the JWT (per
[`backend/auth.md`](../../../agent-os/standards/backend/auth.md) §2: `sub` is the
immutable user UUID).

- Every `select(Model)` that touches user-owned data has
  `.where(Model.user_id == current_user.id)` (or joins through a relationship that
  enforces the same scope). One unscoped query is a data leak.
- Every endpoint that accepts a resource id in the path (e.g. `/checkouts/{id}`)
  verifies ownership before reading or mutating — never trust the path id alone.
- `user_id` flows from `Depends(get_current_user)`, **never** from a request body,
  query param, or path. `request.json()["user_id"]` is a red flag.
- Pagination filters by `user_id` **inside** the SQL query, before `LIMIT/OFFSET`.
  Filtering after loading rows is both wrong (wrong page contents) and a leak.
- Redis cache keys for per-user data include the user id:
  `cache:checkout:{user_id}:{checkout_id}`. A key without `user_id` is shared across
  every authenticated caller.
- Cross-user negative test exists: User A creates a resource, User B requests it,
  expect 404 (preferred over 403 — don't reveal existence). Without this test, the
  scope is not enforced; it only happens to work today.

### Calculation Engine Correctness — `services/checkout.py`

Rules are locked in [`agent-os/product/roadmap.md`](../../../agent-os/product/roadmap.md):
`subtotal = Σ(unit_price × quantity)`, `taxes = 13% of subtotal`,
`discount = 10% of subtotal if subtotal > 100 else 0`,
`total = subtotal + taxes − discount`.

- The engine is a **pure function**: no DB, no Redis, no `request`, no
  `datetime.now()`, no `time.time()`. Side effects belong to the calling service.
  An engine that imports `AsyncSession` is a layering bug
  ([`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md) §5).
- Money is `Decimal` end-to-end. Float anywhere in the chain (`0.13`, `subtotal *
  0.10`) silently drifts. Pydantic field types use `Decimal`, not `float`.
- Rounding strategy is explicit: `Decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`
  (or whichever direction is locked) at one well-known boundary, not implicitly via
  `round()` or `f"{x:.2f}"`.
- Discount boundary is tested at **all three** sides: subtotal `99.99`, `100.00`,
  `100.01`. The rule says `> 100`, so `100.00` must produce zero discount — easy
  off-by-one to miss.
- Empty cart is rejected at the schema (`items: list[Item] = Field(min_length=1)`),
  not silently treated as `total = 0` inside the engine.
- Negative / zero unit prices and quantities are rejected at the schema
  (`Field(gt=0)` for price, `Field(ge=1)` for quantity), so the engine can assume
  valid inputs.

### Auth & Authorization — [`backend/auth.md`](../../../agent-os/standards/backend/auth.md)

OAuth2 password flow + Authlib JWTs + Argon2-cffi + Redis-backed `jti` denylist.

- Passwords hash with `argon2-cffi` (via `argon2.PasswordHasher` or
  `passlib[argon2]`). Bcrypt, plain `hashlib`, plaintext, or any hand-rolled scheme
  is a hard reject (§1).
- JWTs encoded with `authlib.jose.jwt`, algorithm `HS256` or `RS256`, **never**
  `alg: none`. `sub` claim is the immutable user UUID — never username, never email
  (§2). Every token includes `exp`, `iat`, `jti`, and a `type` claim (`"access"` or
  `"refresh"`).
- Access TTL ≈ 15 min, refresh TTL 7–14 days (§3). Hardcoded values that drift from
  these defaults need justification.
- Refresh-token rotation: on `/auth/refresh`, the old `jti` is added to the Redis
  denylist **atomically with `SET NX`** so two concurrent refreshes can't both
  succeed (§3). A read-then-write pair is a double-spend.
- Denylist TTL ≥ remaining refresh-token TTL — otherwise an attacker can replay an
  expired-from-Redis-but-not-from-JWT token.
- `/auth/login` accepts `OAuth2PasswordRequestForm` and returns
  `{"access_token", "refresh_token", "token_type": "bearer"}` — exact key shape
  (§5). Custom shapes break standard OAuth2 clients.
- Protected routes use the `CurrentUser = Annotated[User, Depends(get_current_user)]`
  alias, not inline `Depends(...)` per route (§5;
  [`backend/fastapi.md`](../../../agent-os/standards/backend/fastapi.md) §3).
- JWT secret comes from `pydantic-settings` `SecretStr` (§4). A `@field_validator`
  enforces ≥ 32 chars in production. Old-and-new secret rotation pair must be
  supported when keys roll.
- Logging never echoes `SecretStr.get_secret_value()`, JWTs, refresh tokens, or the
  raw login/register request body.

### FastAPI Conventions — [`backend/fastapi.md`](../../../agent-os/standards/backend/fastapi.md)

- New domain owns its own folder: `router.py`, `service.py`, `schemas.py`,
  `models.py`, `dependencies.py`. A second domain shoved into an existing folder is
  a refactor signal (§1).
- Engine, Redis pool, and any HTTP client are initialized inside the
  `@asynccontextmanager async def lifespan(app)` and stored on `app.state`. Module-
  scope `client = httpx.AsyncClient(...)` outside `lifespan` is a bug (§2).
- Recurring dependencies have a typed alias in `app/api/deps.py` (e.g. `SessionDep`,
  `CurrentUser`). Routes use `Annotated[T, Depends(...)]`, not bare `Depends(...)`
  in the default position (§3).
- Every route declares both `response_model=...` and `status_code=...`. Routes that
  return raw dicts or omit `status_code` violate the standard (§5).
- Each `APIRouter` sets `prefix=` and `tags=`. Inclusion happens **only** in
  `app/api/__init__.py`. `app.include_router(...)` calls scattered across modules
  are a bug (§5).
- Services raise domain errors (`CheckoutError`, `AuthError`, `NotFoundError`)
  registered via `@app.exception_handler(...)`. A raw `raise HTTPException(...)`
  inside `app/services/` is a layering violation (§4).

### Settings & Secrets — [`backend/settings.md`](../../../agent-os/standards/backend/settings.md)

- One `Settings` class is the single source of typed config (§1). The
  `SettingsConfigDict` declares `env_file=(".env", ".env.local")`,
  `env_file_encoding="utf-8"`, `extra="ignore"`, `case_sensitive=False`.
- Every secret is `SecretStr`; `.get_secret_value()` is called only at the single
  site that needs the raw value (§2). Loose `str` for a JWT secret or DB password
  is a leak waiting to happen.
- Nested groups use `env_nested_delimiter="__"` so env vars stay flat (`DB__URL`,
  `JWT__SECRET`) but Python access is structured (§3). One-off flat env vars defeat
  the layering.
- `@field_validator` / `@model_validator(mode="after")` enforce: JWT secret length
  in production, `environment: Literal["dev", "test", "prod"]`, and any other
  invariant the standard calls out (§4).
- `Settings()` is **not** instantiated at module import. Access goes through
  `@lru_cache get_settings()` so tests can override via
  `app.dependency_overrides[get_settings] = ...` (§5).

### Async / Session / Transactional Boundaries — [`backend/sqlmodel.md`](../../../agent-os/standards/backend/sqlmodel.md)

- Async stack only: `asyncpg` for Postgres, `aiosqlite` for tests,
  `create_async_engine`, `async_sessionmaker(class_=AsyncSession,
  expire_on_commit=False)`. Any sync engine, sync session, or `expire_on_commit=True`
  in this codebase is a bug (§1).
- `table=True` SQLModel classes live in `app/models/`. `XxxCreate` / `XxxRead` /
  `XxxUpdate` Pydantic schemas live in `app/schemas/`. **Returning a `table=True`
  model from a route, or accepting one as a request body, is forbidden** — it leaks
  DB-only fields and bypasses input validation (§2).
- Sessions come from the `get_session` dependency that yields from `async with
  async_session_maker()`. New code calling `async_sessionmaker(...)()` directly in a
  service or route is wrong (§3).
- Routes never call `session.commit()`. Services own the unit of work; the session
  dependency commits/rolls-back at the boundary, except inside explicit
  transactional service methods (§3).
- Queries use `session.exec(select(Model).where(...))`, not `session.execute(...)`
  — `exec` returns properly typed scalars (§4). Relationships crossing the API
  boundary use `selectinload(...)`; lazy access on async sessions raises
  `MissingGreenlet` (§4).
- One engine, centralized in `app/core/db.py`, disposed via `await
  engine.dispose()` in `lifespan` shutdown. Engines instantiated at import time in
  tests, workers, or scripts are a bug (§5).
- `await` discipline: every `session.exec`, `session.get`, `session.commit`,
  `session.rollback`, `session.refresh`, `engine.dispose`, and `redis.*` call must be
  awaited. A missing `await` returns a coroutine that's silently garbage-collected.

### Rate Limiting & Caching — [`backend/rate-limiting.md`](../../../agent-os/standards/backend/rate-limiting.md)

- `Limiter(...)` is configured with `key_func=get_user_or_ip`,
  `storage_uri=settings.redis.url.get_secret_value()`, and
  `strategy="moving-window"` (§1). In-process storage silently desyncs across
  `api1`/`api2` and defeats the distributed correctness claim
  ([`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md) §3).
- The composite key returns `f"user:{user_id}"` when a valid JWT is present, else
  `f"ip:{request.client.host}"` (§2). User-only or IP-only keying lets either token
  theft or shared-IP NAT defeat the limit.
- `request.client.host` reflects the **real** client only when uvicorn runs with
  `--proxy-headers --forwarded-allow-ips=<nginx-ip>` (§3). Bare reads of
  `X-Forwarded-For` are spoofable; trust the value only because Nginx sets it.
- Per-endpoint tier limits hold (§4): `5/minute` on `/auth/login` and
  `/auth/refresh`, `60/minute` on checkout mutations, `300/minute` global default
  applied as middleware. New auth/checkout endpoints without a limit are a bug.
- Application caching uses a **separate** `redis.asyncio.Redis` client (not the
  slowapi-managed one), namespaced under a `cache:` key prefix, with **explicit**
  TTLs on every `set` (§5). `await redis.set(key, val)` without `ex=` is a leak.
  Connections are disposed in `lifespan` shutdown.

### Migrations (Alembic) — [`backend/alembic.md`](../../../agent-os/standards/backend/alembic.md)

- `alembic/env.py` imports `app.models` so autogenerate sees every table, and sets
  `target_metadata = SQLModel.metadata` (§1). A PR adding a new model that doesn't
  surface in `app/models/__init__.py` will produce a broken migration.
- `SQLModel.metadata.naming_convention` is set to the standard's exact dict (§2)
  so constraint names stay stable across autogenerate runs. Renaming this
  convention churns every constraint in the next migration.
- Filename matches the
  `%%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(slug)s` template
  (§4). `down_revision` chains correctly to the current head on `main`.
- Autogenerate ran against **Postgres**, not SQLite (§3). Dialect differences
  (server defaults, JSON, enums, autoincrement) produce wrong migrations even when
  the test suite passes.
- Adding a NOT NULL column on an existing table needs a `server_default` (or a
  three-step add-nullable → backfill → set-not-null migration). On a non-empty
  table, `op.add_column(..., nullable=False)` without a default fails outright.
- Adding an index on a populated table uses `postgresql_concurrently=True`. Concurrent
  index creation cannot run inside a transaction — split into a separate revision
  or set `transactional_ddl = False`.
- Migration matches the SQLModel: column types, nullability, unique constraints,
  default values, and FK cascades all line up. Autogen drift is real — read the
  diff manually before committing.
- Migrations execute **only** from the dedicated `migrator` compose service (§5).
  New code that calls `alembic upgrade head` from `lifespan` startup, a route, or a
  worker is a race condition across `api1` and `api2`.

### Test Quality — [`backend/testing.md`](../../../agent-os/standards/backend/testing.md) — THE MOST IMPORTANT SECTION

**Configuration & infrastructure**
- `pyproject.toml` keeps `[tool.pytest.ini_options] asyncio_mode = "auto"` (§1).
  `@pytest.mark.asyncio` decorators sprinkled on individual tests are a smell — auto
  mode is configured.
- Endpoint tests use the project `client` fixture (httpx.AsyncClient +
  ASGITransport + asgi-lifespan LifespanManager). `from fastapi.testclient import
  TestClient` is a bug — it doesn't fire async lifespan correctly (§2).
- Per-test isolation uses `async with session.begin_nested(): ... await
  session.rollback()` against a session-scoped schema. `drop_all`/`create_all` per
  test is 10–100× slower and a smell (§3).
- Dependency overrides go through `app.dependency_overrides[get_session] = lambda:
  test_session` and are cleared in teardown (§4). Direct mutation of module
  globals or monkey-patching `app.state` leaks across tests.
- Model fixtures use factories in `tests/factories.py` (§5). Hand-rolled dict
  literals scattered across tests rot the moment a schema field is added.

**Business-rule verification**
- Each assertion verifies the business rule, not `status == 200` /
  `response is not None`. If you can delete the implementation and the test still
  passes, the test proves nothing.
- Negative cases covered: cross-user IDOR (User B → User A's resource → 404);
  invalid JWT; expired token; denylisted refresh; rate-limit exhaustion; empty
  cart; calculation boundary at exactly $100; decimal rounding direction.
- The calculation engine has **unit tests that don't touch the DB**, plus
  integration tests of `/checkout` that exercise persistence. One without the
  other is a gap.

**Test smells — flag these**
- **Assertion Roulette:** multiple assertions without messages, can't tell which
  failed.
- **Empty/Unknown Test:** no assertions; passes vacuously.
- **Conditional Test Logic:** `if/for/while` in test body — execution path varies
  per run.
- **Eager Test:** one test calls many production endpoints — unclear what's under
  test.
- **Magic Number Test:** unexplained numeric literals — especially in calculation
  tests (`assert total == Decimal("113.00")` without showing the derivation).
- **Sleepy Test:** `asyncio.sleep` / `time.sleep` to "wait for" something — flaky.
  Use `asyncio.Event`, freezegun, or a deterministic clock fixture.
- **Vacuously True:** `assert response.json()` (truthy on any non-empty dict),
  `assert isinstance(items, list)` (passes when empty).
- **Float-equality on money:** `assert total == 11.30`. Drifts on different
  machines. Use `Decimal` or `pytest.approx(..., abs=Decimal("0.01"))`.
- **Mocked DB pretending to be the DB:** unit tests that mock `AsyncSession` and
  then claim to verify SQL — they verify only the mock.

### Frontend — [`frontend/vite-react.md`](../../../agent-os/standards/frontend/vite-react.md), [`frontend/shadcn-tailwind.md`](../../../agent-os/standards/frontend/shadcn-tailwind.md)

When applicable.

- `tsconfig.json` keeps `strict`, `noUncheckedIndexedAccess`, `noImplicitOverride`,
  `noFallthroughCasesInSwitch`, `noEmit`. PRs silently weakening any of these are a
  regression. `tsc --noEmit` runs in CI as a separate step from `vite build` (§1).
- Absolute imports configured in **both** places: `tsconfig.json` `baseUrl: "./src",
  paths: { "@/*": ["./*"] }` AND `vite.config.ts` `resolve.alias: { "@":
  path.resolve(__dirname, "./src") }`. Doing only one breaks either the IDE or the
  build (§2).
- Env vars accessed only via `import.meta.env.VITE_*`, declared on `ImportMetaEnv`
  in `src/vite-env.d.ts` (§3). Hardcoded `http://localhost/...` or `process.env.*`
  reads are bugs.
- Single `QueryClient` defined at **module scope** (not inside a component), wrapped
  via `<QueryClientProvider>` (§4). A `new QueryClient()` inside a component
  re-creates the cache on every render.
- Query keys live in a typed factory in `src/lib/queryKeys.ts`
  (`checkoutKeys.detail(id)`). Inline string keys (`["checkouts", id]`) are a
  stringly-typed cache-invalidation bug (§4).
- API client centralized in `src/lib/api.ts` (typed `fetch` wrapper or `ky`/`axios`
  instance with JWT attached via interceptor). Per-feature ad-hoc `fetch` calls and
  a global `hooks/` dump are smells (§5). Query/mutation hooks live next to their
  feature: `src/features/checkout/useCheckout.ts`.
- shadcn primitives in `src/components/ui/` are **our code**: edit them in place,
  don't wrap them only to tweak Tailwind classes (§4 of shadcn-tailwind). A wrapper
  component that exists only to add a variant is a refactor signal — edit the
  primitive.
- Theme via CSS custom properties in `src/index.css` (`--background`, `--primary`,
  `--ring`); components reference them via Tailwind utilities (`bg-background
  text-foreground`). Hardcoded hex colors in components are a bug (§2 of
  shadcn-tailwind).
- Forms use shadcn `<Form>` + `react-hook-form` + `zodResolver` (§3 of
  shadcn-tailwind). Hand-rolled `onSubmit` validation that re-implements zod logic
  is a smell.
- `cn()` from `src/lib/utils.ts` for every conditional className (§5 of
  shadcn-tailwind). Hand-concatenated template strings drop the `tailwind-merge`
  precedence handling.

### Infra — [`infra/docker.md`](../../../agent-os/standards/infra/docker.md), [`infra/nginx.md`](../../../agent-os/standards/infra/nginx.md)

When `Dockerfile`, `docker-compose.yml`, or `infra/nginx/nginx.conf` is touched.

**Docker**
- Multi-stage build, `python:3.12-slim` base. The builder stage installs `uv` and
  resolves wheels into `/opt/venv`; the runtime stage `COPY --from=builder
  /opt/venv /opt/venv` and contains no compilers (§1). Anything past ~200 MB on the
  final image needs justification.
- `useradd --uid 1000 --create-home app && chown -R app:app /app` and `USER app`
  before `CMD`. Running uvicorn as root is a bug. Mounting the host Docker socket
  into the API container is a hard reject (§2).
- Layer order is least-to-most-changing: copy `pyproject.toml`/`uv.lock` and
  install deps **before** copying the app source (§3). Editing app code must not
  bust the dependency layer cache.
- `HEALTHCHECK` declared in the Dockerfile **and** in compose
  (`{interval, timeout, retries, start_period}`). Cross-service `depends_on`
  blocks use `condition: service_healthy` (or `service_completed_successfully`
  for the migrator) (§4).
- `.dockerignore` includes at minimum: `.git`, `.venv`, `__pycache__`,
  `.pytest_cache`, `.ruff_cache`, `node_modules`, `tests/`, `*.md` (allow-listing
  `README.md` only if `pyproject.toml` references it), `.env*` (§5). A leaked
  `.env` in a build context is a credential exposure.

**Nginx**
- `upstream cart_api { least_conn; server api1:8000 max_fails=3
  fail_timeout=10s; server api2:8000 ...; keepalive 32; }` (§1). Removing
  `least_conn` or dropping a replica without justification regresses the
  distributed-LB demonstration.
- Forwarded headers preserved: `Host`, `X-Real-IP`, `X-Forwarded-For`,
  `X-Forwarded-Proto`, `proxy_http_version 1.1`, `proxy_set_header Connection ""`
  (§2). Missing the last two breaks upstream keep-alive.
- Explicit timeouts: `proxy_connect_timeout 5s`, `proxy_send_timeout 30s`,
  `proxy_read_timeout 30s` (§3). The 60s default masks slow-query regressions.
- `location = /healthz { proxy_pass http://cart_api/healthz; access_log off; }`
  (§4). Compose healthchecks hit this route.
- `gzip on; gzip_types application/json; gzip_min_length 512; client_max_body_size
  1m;` (§5). Removing the body cap defeats trivial DoS protection.

### Linting Hygiene — [`linting.md`](../../../agent-os/standards/linting.md)

You are not a linter; Ruff and mypy are. But PRs that **weaken** the lint
configuration deserve a finding.

- `pyproject.toml` keeps `line-length = 100`, `target-version = "py312"`, and
  `src = ["app", "tests"]` (§1). Changes to `src` break first-party import
  sorting.
- `[tool.ruff.lint] select` is the curated list
  (`["E", "F", "I", "B", "UP", "SIM", "C4", "PT", "RUF", "ASYNC", "S", "N"]`).
  `select = ["ALL"]` silently enables new rules on every Ruff upgrade (§2).
- `[tool.ruff.format] quote-style = "double"` (§3). The Ruff formatter — not Black
  — is the formatter for this repo.
- Per-file ignores limited to `tests/**` (`S101`, `S105`, `S106`) and
  `alembic/versions/**` (`E501`) (§4). Blanket ignores added to other paths
  ("just to make CI green") are a finding.
- A new lint suppression (`# noqa`, `# type: ignore`) without a specific rule code
  and a one-line justification is a smell.

### Standards Drift

- A change that genuinely contradicts a standard must update the standard in the
  same PR (per [`CLAUDE.md`](../../../CLAUDE.md) §Standards). PRs that diverge from
  a standard without touching the standard file are findings.
- Architectural decisions go in `docs/ARCHITECTURE.md` (or a new file under
  `docs/`), not in code comments (per
  [`CLAUDE.md`](../../../CLAUDE.md) §Repo etiquette).
- Conventional-commit prefix on every commit: `feat:`, `fix:`, `chore:`, `docs:`,
  `refactor:`, `test:` (per [`CLAUDE.md`](../../../CLAUDE.md) §Repo etiquette).

---

## Step 4: Build Verification

If any findings relate to wiring, type errors, missing dependencies, migration
conflicts, or compose topology, attempt the project's actual checks:

```bash
# Backend
cd backend
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest -q

# Frontend (if frontend/ is touched)
cd ../frontend
npm install
npx tsc --noEmit

# Compose topology (if docker-compose.yml or Dockerfiles are touched)
cd ..
docker compose config >/dev/null
```

If any check fails, include the failure in the review — it's a blocking issue. If
they all pass and you ran them, note "Build: PASS" in the verdict.

Skip this step if you are reviewing uncommitted changes (Step 0.2) or if no findings
warrant it.

## Step 5: Post Inline Review and Cleanup

Only when reviewing a PR by number. Skip this step for uncommitted changes (Step 0.2)
or branch diffs (Step 0.3).

### 5a — Collect the HEAD SHA

```bash
FULL_SHA=$(git rev-parse HEAD)
```

### 5b — Map findings to diff positions

Each finding must anchor to a line that appears in the PR diff. Before posting,
confirm the target line is reachable:

```bash
# Check that path + line appear in the diff
git diff origin/main...HEAD -- <path/to/file.py> | grep -n "^[+\-]" | head -40
```

- Use the **right-side line number** (the new file) for added/changed lines
  (`side: RIGHT`).
- Use the **left-side line number** for removed lines (`side: LEFT`).
- If a finding targets a line that is NOT in the diff (e.g., a pre-existing issue
  surfaced by context), post it as a top-level comment in the review body instead
  of an inline comment.

### 5c — Submit the review with inline comments

Use `gh api` to create a single pull request review that contains all inline
comments plus the summary body. Build the `--field comments[]...` flags
dynamically — one set per finding.

```bash
gh api \
  --method POST \
  repos/ferodrigop/cart-calculator/pulls/<number>/reviews \
  --field body='<REVIEW_BODY>' \
  --field event='<EVENT>' \
  --field 'comments[][path]=backend/app/api/checkout.py' \
  --field 'comments[][line]=42' \
  --field 'comments[][side]=RIGHT' \
  --field 'comments[][body]=**issue:** Missing user scope on the SELECT — explanation here.' \
  --field 'comments[][path]=backend/app/services/checkout.py' \
  --field 'comments[][line]=18' \
  --field 'comments[][side]=RIGHT' \
  --field 'comments[][body]=**suggestion:** Use Decimal end-to-end — explanation here.'
```

`<EVENT>` must be one of:
- `REQUEST_CHANGES` — one or more `issue` or `issue (blocking)` findings.
- `APPROVE` — no blocking findings, safe to merge.
- `COMMENT` — questions / suggestions only, no verdict on mergeability.

`<REVIEW_BODY>` contains the Summary, Test Audit, and Verdict (see format below).
Findings go inline — do NOT repeat them in the body.

For multi-line inline comments (spanning a range), add `start_line` and
`start_side`:
```bash
  --field 'comments[][start_line]=42' \
  --field 'comments[][start_side]=RIGHT' \
  --field 'comments[][line]=46' \
  --field 'comments[][side]=RIGHT' \
```

### 5d — Clean up the review worktree (MANDATORY)

```bash
cd "$REPO_ROOT"
git worktree remove "$REVIEW_DIR" --force
```

If the worktree remove fails, report it to the user so they can clean up manually.

---

## Output Format — Conventional Comments

Use these labels on EVERY finding. This is mandatory.

| Label | Meaning | Blocks merge? |
|-------|---------|---------------|
| `issue (blocking):` | Bug, security flaw, data leak, broken migration | Yes |
| `issue:` | Functional problem, likely bug | Yes |
| `suggestion:` | Improvement with reasoning | No |
| `question:` | Needs clarification from author | Soft yes |
| `nitpick:` | Minor, author's judgment | No |
| `praise:` | Something done well | No |

### Inline comment format (per finding)

Each inline comment body:

```
**[label]:** [Short description]

[What's wrong and why it matters — 2-4 sentences max]

[Concrete fix as a code snippet or specific approach, if applicable]
```

Example:

```
**issue (blocking):** Cross-user IDOR — `get_checkout` does not scope by `user_id`.

The query `select(Checkout).where(Checkout.id == checkout_id)` lets any authenticated
user read any checkout by guessing or enumerating ids. The standard in
`agent-os/standards/backend/sqlmodel.md` requires user scoping on every query that
touches user-owned data.

**Fix:** add `.where(Checkout.user_id == current_user.id)` to the select, and assert
404 in a test where User B requests User A's checkout id.
```

### Review body format (top-level — Summary + Verdict only)

```
## Summary
One paragraph: what does this change do, and is it safe to merge?
Findings that could not be anchored to a diff line are listed here.

## Test Audit
For each test file changed:
- **[test file]** — Verifies: [what] — Gaps: [what's missing] — Smells: [any detected]

## Verdict
APPROVE / REQUEST_CHANGES / COMMENT — one-line justification
```

### Rules
- Every finding MUST have a label. No unlabeled bullet points.
- Include at least one `praise:` inline comment if anything is well done.
- Max 3 `nitpick:` comments — you are not a linter.
- If a section has no findings, write "None found" in the body — do NOT fabricate
  issues.
- Explain the "why" — "This could cause X because Y", not just "Fix this".
- When possible, show the concrete fix (code snippet or specific approach).
- The Test Audit section in the review body is mandatory if any test files changed.
- Do NOT duplicate findings in both the body and as inline comments — pick one
  location per finding.
