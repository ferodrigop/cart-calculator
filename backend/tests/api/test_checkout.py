from __future__ import annotations

from decimal import Decimal

from app.models.checkout import Checkout
from app.models.user import User
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


async def test_create_checkout_persists_and_returns_breakdown(
    authed_client: AsyncClient, session: AsyncSession, test_user: User
) -> None:
    response = await authed_client.post(
        "/checkout",
        json={
            "items": [
                {"name": "Widget", "unit_price": "200.00", "quantity": 2},
            ]
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert Decimal(body["subtotal"]) == Decimal("400.00")
    assert Decimal(body["taxes"]) == Decimal("52.00")
    assert Decimal(body["discount"]) == Decimal("40.00")
    assert Decimal(body["total"]) == Decimal("412.00")

    rows = (await session.exec(select(Checkout))).all()
    assert len(rows) == 1
    persisted = rows[0]
    assert persisted.user_id == test_user.id
    assert persisted.subtotal == Decimal("400.00")
    assert persisted.total == Decimal("412.00")
    assert persisted.items == [{"name": "Widget", "unit_price": "200.00", "quantity": 2}]


async def test_create_checkout_requires_authentication(
    unauth_client: AsyncClient,
) -> None:
    response = await unauth_client.post(
        "/checkout",
        json={"items": [{"name": "Widget", "unit_price": "10.00", "quantity": 1}]},
    )
    assert response.status_code == 401


async def test_create_checkout_validates_payload(authed_client: AsyncClient) -> None:
    response = await authed_client.post(
        "/checkout",
        json={"items": [{"name": "Widget", "unit_price": "-1.00", "quantity": 1}]},
    )
    assert response.status_code == 422


async def test_create_checkout_rejects_empty_cart(authed_client: AsyncClient) -> None:
    response = await authed_client.post("/checkout", json={"items": []})
    assert response.status_code == 422


async def test_create_checkout_rejects_zero_unit_price(authed_client: AsyncClient) -> None:
    response = await authed_client.post(
        "/checkout",
        json={"items": [{"name": "Freebie", "unit_price": "0.00", "quantity": 1}]},
    )
    assert response.status_code == 422
