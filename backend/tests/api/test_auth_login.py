from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import register


async def test_login_returns_token_pair(client: AsyncClient) -> None:
    await register(client, "bob@example.com", "correct-horse")
    r = await client.post(
        "/auth/login",
        data={"username": "bob@example.com", "password": "correct-horse"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["access_token"] != body["refresh_token"]


async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    await register(client, "carol@example.com", "correct-horse")
    r = await client.post(
        "/auth/login",
        data={"username": "carol@example.com", "password": "wrong-password"},
    )
    assert r.status_code == 401


async def test_login_unknown_email_returns_401(client: AsyncClient) -> None:
    r = await client.post(
        "/auth/login",
        data={"username": "ghost@example.com", "password": "correct-horse"},
    )
    assert r.status_code == 401


async def test_login_is_case_insensitive_on_email(client: AsyncClient) -> None:
    await register(client, "dave@example.com", "correct-horse")
    r = await client.post(
        "/auth/login",
        data={"username": "Dave@Example.com", "password": "correct-horse"},
    )
    assert r.status_code == 200
