from __future__ import annotations

from decimal import Decimal

import pytest
from app.schemas.checkout import CheckoutItem
from app.services.checkout import calculate_totals


def _item(name: str, unit_price: str, quantity: int) -> CheckoutItem:
    return CheckoutItem(name=name, unit_price=Decimal(unit_price), quantity=quantity)


@pytest.mark.parametrize(
    ("items", "subtotal", "taxes", "discount", "total"),
    [
        # empty cart yields zeros
        ([], "0.00", "0.00", "0.00", "0.00"),
        # subtotal exactly $100 — no discount (rule: strictly > 100)
        ([_item("a", "100.00", 1)], "100.00", "13.00", "0.00", "113.00"),
        # subtotal one cent over — discount kicks in
        (
            [_item("a", "100.01", 1)],
            "100.01",
            "13.00",
            "10.00",
            "103.01",
        ),
        # quantity multiplies price
        ([_item("a", "10.00", 5)], "50.00", "6.50", "0.00", "56.50"),
        # multiple items combine
        (
            [_item("a", "33.33", 1), _item("b", "0.01", 1)],
            "33.34",
            "4.33",
            "0.00",
            "37.67",
        ),
        # half-up rounding: 50.50 * 0.13 = 6.5650 → 6.57
        ([_item("a", "50.50", 1)], "50.50", "6.57", "0.00", "57.07"),
        # large cart with discount
        (
            [_item("a", "200.00", 2)],
            "400.00",
            "52.00",
            "40.00",
            "412.00",
        ),
    ],
)
def test_calculate_totals(
    items: list[CheckoutItem],
    subtotal: str,
    taxes: str,
    discount: str,
    total: str,
) -> None:
    breakdown = calculate_totals(items)
    assert breakdown.subtotal == Decimal(subtotal)
    assert breakdown.taxes == Decimal(taxes)
    assert breakdown.discount == Decimal(discount)
    assert breakdown.total == Decimal(total)


def test_calculate_totals_returns_two_decimal_places() -> None:
    breakdown = calculate_totals([_item("a", "0.10", 3)])
    assert breakdown.subtotal.as_tuple().exponent == -2
    assert breakdown.taxes.as_tuple().exponent == -2
    assert breakdown.discount.as_tuple().exponent == -2
    assert breakdown.total.as_tuple().exponent == -2
