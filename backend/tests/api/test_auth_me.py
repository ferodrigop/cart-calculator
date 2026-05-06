from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import register_and_login


async def test_me_returns_current_user(client: AsyncClient) -> None:
    tokens = await register_and_login(client, "eve@example.com", "correct-horse")
    r = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "eve@example.com"
    assert "id" in body
    assert "password_hash" not in body


async def test_me_without_bearer_returns_401(client: AsyncClient) -> None:
    r = await client.get("/auth/me")
    assert r.status_code == 401


async def test_me_with_refresh_token_returns_401(client: AsyncClient) -> None:
    tokens = await register_and_login(client, "frank@example.com", "correct-horse")
    r = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )
    assert r.status_code == 401


async def test_me_with_garbage_token_returns_401(client: AsyncClient) -> None:
    r = await client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not.a.real.token"},
    )
    assert r.status_code == 401
