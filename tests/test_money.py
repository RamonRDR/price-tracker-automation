from decimal import Decimal

import pytest

from price_tracker.errors import PriceUnavailable
from price_tracker.money import parse_price


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("$1,234.56", "1234.5600"),
        ("R$ 1.234,56", "1234.5600"),
        ("€ 1 234,56", "1234.5600"),
        ("USD 79.99", "79.9900"),
        ("1,234", "1234.0000"),
        ("1.234", "1234.0000"),
        ("20", "20.0000"),
        (Decimal("0.1234"), "0.1234"),
    ],
)
def test_money_formats(raw: object, expected: str) -> None:
    assert parse_price(raw) == Decimal(expected)


@pytest.mark.parametrize("raw", ["-", "-10", "$-1.00", "", "n/a", "0", "0.00", "abc"])
def test_missing_or_invalid_money(raw: str) -> None:
    with pytest.raises(PriceUnavailable):
        parse_price(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "2 for $10.00",
        "3 payments of USD 20.00",
        "was $100.00 now $80.00",
        "USD 20.00 / month",
        "2 10.00",
        "1.23.456",
        "1.23,45",
    ],
)
def test_ambiguous_multi_amount_promotions_are_rejected(raw: str) -> None:
    with pytest.raises(PriceUnavailable):
        parse_price(raw)
