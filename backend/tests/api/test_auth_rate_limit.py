from __future__ import annotations

from httpx import AsyncClient


async def test_login_rate_limit_triggers_after_five_requests(client: AsyncClient) -> None:
    """Composite key falls back to IP when unauthenticated; six identical login
    attempts within a minute share the bucket and the sixth must 429. The first
    five must NOT be 429 — that's what pins the configured 5/min threshold."""
    payload = {"username": "noone@example.com", "password": "wrong"}
    statuses = []
    for _ in range(6):
        r = await client.post("/auth/login", data=payload)
        statuses.append(r.status_code)
    assert all(s != 429 for s in statuses[:5]), statuses
    assert statuses[:5] == [401, 401, 401, 401, 401]
    assert statuses[5] == 429


async def test_refresh_rate_limit_triggers(client: AsyncClient) -> None:
    payload = {"refresh_token": "garbage.token.value"}
    statuses = []
    for _ in range(6):
        r = await client.post("/auth/refresh", json=payload)
        statuses.append(r.status_code)
    assert all(s != 429 for s in statuses[:5]), statuses
    assert statuses[5] == 429


async def test_register_rate_limit_triggers(client: AsyncClient) -> None:
    """Mass-registration brute-force protection — closes the gap called out in
    review (otherwise /auth/register fell back to the global 300/min)."""
    statuses = []
    for i in range(6):
        r = await client.post(
            "/auth/register",
            json={"email": f"rate{i}@example.com", "password": "correct-horse"},
        )
        statuses.append(r.status_code)
    assert all(s != 429 for s in statuses[:5]), statuses
    assert statuses[5] == 429
