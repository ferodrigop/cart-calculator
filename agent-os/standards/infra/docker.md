# Docker & Compose Standards

Conventions for containerization and local orchestration.

1. **Multi-stage builds, `python:3.12-slim` base.** A `builder` stage installs `uv` and
   resolves wheels into `/opt/venv`. The final stage `COPY --from=builder /opt/venv
   /opt/venv` and contains no compilers. Final image stays under 200MB.
2. **Non-root user.** Always:
   ```dockerfile
   RUN useradd --uid 1000 --create-home app && chown -R app:app /app
   USER app
   ```
   Never run uvicorn as root. Never mount the host Docker socket into the API container.
3. **Layer order: least-to-most-changing.** Copy `pyproject.toml`/`uv.lock` and install
   deps **before** copying application source. Editing app code shouldn't bust the
   dependency layer cache.
4. **HEALTHCHECK in Dockerfile + compose.** In Dockerfile:
   ```dockerfile
   HEALTHCHECK CMD python -c "import httpx; httpx.get('http://localhost:8000/healthz').raise_for_status()" || exit 1
   ```
   In compose: `healthcheck: { interval: 10s, timeout: 3s, retries: 3, start_period: 20s }`.
   Use `depends_on: { db: { condition: service_healthy } }` between services.
5. **Strict `.dockerignore`.** Always include: `.git`, `.venv`, `__pycache__`,
   `.pytest_cache`, `.ruff_cache`, `node_modules`, `tests/`, `*.md`, `.env*`. Both shrinks
   build context and prevents secrets from leaking into images.
