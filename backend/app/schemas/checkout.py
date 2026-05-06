from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CheckoutItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    unit_price: Decimal = Field(gt=Decimal("0"), max_digits=12, decimal_places=2)
    quantity: int = Field(ge=1)


class CheckoutCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[CheckoutItem] = Field(min_length=1)


class CheckoutBreakdown(BaseModel):
    subtotal: Decimal
    taxes: Decimal
    discount: Decimal
    total: Decimal
