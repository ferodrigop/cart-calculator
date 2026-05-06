from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal

from app.schemas.checkout import CheckoutBreakdown, CheckoutItem

TAX_RATE = Decimal("0.13")
DISCOUNT_RATE = Decimal("0.10")
DISCOUNT_THRESHOLD = Decimal("100")
_QUANTUM = Decimal("0.01")
_ZERO = Decimal("0.00")


def _money(value: Decimal) -> Decimal:
    return value.quantize(_QUANTUM, rounding=ROUND_HALF_UP)


def calculate_totals(items: Iterable[CheckoutItem]) -> CheckoutBreakdown:
    subtotal = _money(sum((item.unit_price * item.quantity for item in items), Decimal("0")))
    taxes = _money(subtotal * TAX_RATE)
    discount = _money(subtotal * DISCOUNT_RATE) if subtotal > DISCOUNT_THRESHOLD else _ZERO
    total = _money(subtotal + taxes - discount)
    return CheckoutBreakdown(subtotal=subtotal, taxes=taxes, discount=discount, total=total)
