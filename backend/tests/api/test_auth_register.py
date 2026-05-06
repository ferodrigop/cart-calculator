from __future__ import annotations

from httpx import AsyncClient


async def test_register_returns_201_and_user_read(client: AsyncClient) -> None:
    r = await client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "correct-horse"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "alice@example.com"
    assert "id" in body
    assert "created_at" in body
    assert "password_hash" not in body


async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    payload = {"email": "dup@example.com", "password": "correct-horse"}
    r1 = await client.post("/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = await client.post("/auth/register", json=payload)
    assert r2.status_code == 409
    assert "already" in r2.json()["detail"].lower()


async def test_register_short_password_returns_422(client: AsyncClient) -> None:
    r = await client.post(
        "/auth/register",
        json={"email": "short@example.com", "password": "abc"},
    )
    assert r.status_code == 422


async def test_register_normalizes_email_lowercase(client: AsyncClient) -> None:
    r = await client.post(
        "/auth/register",
        json={"email": "Mixed@Example.com", "password": "correct-horse"},
    )
    assert r.status_code == 201
    assert r.json()["email"] == "mixed@example.com"
