# Testing Standards

Conventions for pytest + pytest-asyncio + httpx.AsyncClient.

1. **Auto async mode.** Configure in `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   asyncio_mode = "auto"
   ```
   Every `async def test_...` is awaited automatically — no per-test
   `@pytest.mark.asyncio` decorator clutter.
2. **`AsyncClient` + `ASGITransport`, not `TestClient`.** Build a session-scoped `client`
   fixture that yields
   `httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test")`. Wrap in
   `asgi_lifespan.LifespanManager(app)` so startup/shutdown hooks fire during tests.
3. **SAVEPOINT-per-test isolation.** Create the schema once per test session, then wrap
   each test in `async with session.begin_nested(): ... await session.rollback()` for
   true isolation. Avoid `drop_all`/`create_all` per test — it's 10-100× slower.
4. **Override dependencies, never mutate globals.** Use
   `app.dependency_overrides[get_session] = lambda: test_session` inside fixtures and
   clear with `app.dependency_overrides.clear()` in teardown. Same pattern for
   `get_settings`, Redis, etc.
5. **Factories for model fixtures.** Use `polyfactory` (or hand-rolled factory functions)
   in `tests/factories.py`: `UserFactory.build()`, `CheckoutFactory.build(items=[...])`.
   This beats hand-rolled dict literals for readability and forces schemas to stay in
   sync.
