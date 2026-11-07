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


@pytest.mark.parametrize("raw", ["-", "", "n/a", "0", "0.00", "abc"])
def test_missing_or_invalid_money(raw: str) -> None:
    with pytest.raises(PriceUnavailable):
        parse_price(raw)
