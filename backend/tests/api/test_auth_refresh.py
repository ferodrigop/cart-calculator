from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import register_and_login


async def test_refresh_returns_new_token_pair(client: AsyncClient) -> None:
    tokens = await register_and_login(client, "gina@example.com", "correct-horse")
    r = await client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert r.status_code == 200
    new_tokens = r.json()
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]


async def test_refresh_token_reuse_is_rejected(client: AsyncClient) -> None:
    tokens = await register_and_login(client, "hank@example.com", "correct-horse")
    r1 = await client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert r1.status_code == 200
    r2 = await client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert r2.status_code == 401
    assert "already" in r2.json()["detail"].lower() or "used" in r2.json()["detail"].lower()


async def test_refresh_with_access_token_is_rejected(client: AsyncClient) -> None:
    tokens = await register_and_login(client, "ivy@example.com", "correct-horse")
    r = await client.post(
        "/auth/refresh",
        json={"refresh_token": tokens["access_token"]},
    )
    assert r.status_code == 401


async def test_refresh_with_tampered_token_is_rejected(client: AsyncClient) -> None:
    tokens = await register_and_login(client, "jane@example.com", "correct-horse")
    original = tokens["refresh_token"]
    suffix = "AAA" if original[-3:] != "AAA" else "BBB"
    tampered = original[:-3] + suffix
    r = await client.post("/auth/refresh", json={"refresh_token": tampered})
    assert r.status_code == 401
