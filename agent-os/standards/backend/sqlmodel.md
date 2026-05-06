# SQLModel Standards

Conventions for ORM and database access.

1. **Async stack only.** Use `asyncpg` for Postgres and `aiosqlite` for tests with
   `create_async_engine(...)` and
   `async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)`.
   `expire_on_commit=False` is mandatory to avoid surprise lazy-loads after commit.
2. **Separate persistence from API.** `table=True` SQLModel classes live in `models.py`
   and are DB-only. Dedicated `XxxCreate`, `XxxRead`, `XxxUpdate` schemas live in
   `schemas.py`. Never return a `table=True` model directly from a route, and never accept
   one as a request body.
3. **Sessions through a dependency.** Provide `get_session` that yields from
   `async with async_session_maker() as session:` and commits/rolls-back at the boundary.
   Endpoints and services never call `session.commit()` themselves except inside explicit
   transactional service methods.
4. **Use typed `exec()`.** Prefer `session.exec(select(Model).where(...))` over
   `session.execute(...)` — SQLModel's `exec` returns properly typed scalars. For
   relationships crossing the API boundary, use `selectinload(...)` eagerly to prevent
   N+1 queries and `MissingGreenlet` errors.
5. **One engine, disposed at shutdown.** Centralize the engine and session factory in
   `app/db.py`. Dispose the engine in lifespan shutdown via `await engine.dispose()`.
   Never instantiate engines at import time inside test or worker code.
