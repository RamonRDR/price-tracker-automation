"""Locale-tolerant price parsing without binary floating-point arithmetic."""

import re
from decimal import Decimal, InvalidOperation

from price_tracker.errors import PriceUnavailable

_GROUP = re.compile(r"[^0-9.,\u00a0\s]")
_SPACES = re.compile(r"[\s\u00a0\u202f]")


def parse_price(raw: str | int | float | Decimal) -> Decimal:
    """Parse common comma/dot conventions; reject missing and non-positive values.

    Mixed separators use the rightmost separator as the decimal mark.
    With a single type of separator, three trailing digits mean thousands,
    except for decimal values explicitly passed as Decimal.
    """
    if "-" in str(raw):
        raise PriceUnavailable("Negative prices are not allowed")
    if isinstance(raw, Decimal):
        amount = raw
    elif isinstance(raw, int):
        amount = Decimal(raw)
    elif isinstance(raw, float):
        amount = Decimal(str(raw))
    else:
        text = _SPACES.sub("", _GROUP.sub("", str(raw)))
        if not text or not any(c.isdigit() for c in text):
            raise PriceUnavailable("Price is missing or is not numeric")
        if "," in text and "." in text:
            decimal_mark = "," if text.rfind(",") > text.rfind(".") else "."
            group_mark = "." if decimal_mark == "," else ","
            text = text.replace(group_mark, "").replace(decimal_mark, ".")
        elif "," in text:
            parts = text.split(",")
            if len(parts) > 2 or (len(parts) == 2 and len(parts[-1]) == 3):
                text = text.replace(",", "")
            else:
                text = text.replace(",", ".")
        elif "." in text:
            parts = text.split(".")
            if len(parts) > 2 or (len(parts) == 2 and len(parts[-1]) == 3):
                text = text.replace(".", "")
        try:
            amount = Decimal(text)
        except InvalidOperation as exc:
            raise PriceUnavailable("Price format is invalid") from exc
    if not amount.is_finite() or amount <= 0:
        raise PriceUnavailable("Price must be a positive finite number")
    return amount.quantize(Decimal("0.0001"))


def money(amount: Decimal, currency: str) -> str:
    return f"{currency} {amount:,.2f}"
