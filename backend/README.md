# cart-calculator backend

FastAPI + SQLModel + Alembic. Managed with `uv`.

```bash
uv sync
uv run uvicorn app.main:app --reload
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run alembic upgrade head
```

See [`../agent-os/standards/`](../agent-os/standards/) for conventions.
