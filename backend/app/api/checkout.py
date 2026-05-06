from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import CurrentUserDep
from app.core.db import SessionDep
from app.models.checkout import Checkout
from app.schemas.checkout import CheckoutBreakdown, CheckoutCreate
from app.services.checkout import calculate_totals

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.post("", response_model=CheckoutBreakdown, status_code=status.HTTP_201_CREATED)
async def create_checkout(
    payload: CheckoutCreate,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> CheckoutBreakdown:
    breakdown = calculate_totals(payload.items)
    checkout = Checkout(
        user_id=current_user.id,
        items=[item.model_dump(mode="json") for item in payload.items],
        subtotal=breakdown.subtotal,
        taxes=breakdown.taxes,
        discount=breakdown.discount,
        total=breakdown.total,
    )
    session.add(checkout)
    await session.flush()
    return breakdown
