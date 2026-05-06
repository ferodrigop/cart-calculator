# FastAPI Standards

Conventions for the FastAPI application in `backend/app/`.

1. **Structure by feature/domain.** Each domain (`auth/`, `checkout/`, `health/`) owns its
   own `router.py`, `service.py`, `schemas.py`, `models.py`, `dependencies.py`. Avoid a
   single mega `dependencies.py` once the project grows past a few endpoints.
2. **Use `lifespan` for startup/shutdown.** Initialize the DB engine, Redis pool, and any
   HTTP clients inside an `@asynccontextmanager async def lifespan(app: FastAPI)` and store
   them on `app.state`. Never put initialization at module scope. Pass
   `lifespan=lifespan` to `FastAPI(...)`.
3. **Annotated dependencies everywhere.** Use `Annotated[T, Depends(...)]` (PEP 593) for
   every dependency, e.g. `SessionDep = Annotated[AsyncSession, Depends(get_session)]`.
   Define one type alias per recurring dependency in `app/api/deps.py` so route signatures
   stay short and readable.
4. **Centralized exception handling.** Define a small hierarchy of domain exceptions
   (`CheckoutError`, `AuthError`, `NotFoundError`) and register handlers via
   `@app.exception_handler(...)`. Services raise domain errors; never raise raw
   `HTTPException` from a service — let handlers translate to HTTP at the boundary.
5. **Pin response models and status codes.** Every route declares `response_model=...`
   and `status_code=...`. Routers use `APIRouter(prefix="/checkout", tags=["checkout"])`
   and are registered from a single `app/api/__init__.py`.
