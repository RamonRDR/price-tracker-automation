"""Locale-tolerant price parsing without binary floating-point arithmetic."""

import re
from decimal import Decimal, InvalidOperation

from price_tracker.errors import PriceUnavailable

_NUMBER_TOKEN = re.compile(r"\d+(?:[.,]\d+|[ \u00a0\u202f]\d{3}(?!\d))*")
_CURRENCY_AFFIX = re.compile(r"(?:[A-Za-z]{3}|[A-Za-z]{1,3}[$€£¥₹₽₩₫]|[$€£¥₹₽₩₫])")
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
        source = str(raw).strip()
        matches = list(_NUMBER_TOKEN.finditer(source))
        if len(matches) != 1:
            raise PriceUnavailable("Price must contain exactly one monetary amount")
        token = matches[0]
        prefix = source[: token.start()].strip()
        suffix = source[token.end() :].strip()
        if (
            (prefix and suffix)
            or (prefix and not _CURRENCY_AFFIX.fullmatch(prefix))
            or (suffix and not _CURRENCY_AFFIX.fullmatch(suffix))
        ):
            raise PriceUnavailable("Price contains unsupported or ambiguous text")
        text = _SPACES.sub("", token.group(0))
        if (
            text.count(".") > 1
            and "," not in text
            and not re.fullmatch(r"\d{1,3}(?:\.\d{3})+", text)
        ):
            raise PriceUnavailable("Invalid thousands grouping")
        if (
            text.count(",") > 1
            and "." not in text
            and not re.fullmatch(r"\d{1,3}(?:,\d{3})+", text)
        ):
            raise PriceUnavailable("Invalid thousands grouping")
        if "." in text and "," in text:
            decimal_mark = "," if text.rfind(",") > text.rfind(".") else "."
            group_mark = "." if decimal_mark == "," else ","
            integer_part, decimal_part = text.rsplit(decimal_mark, 1)
            grouped = integer_part.split(group_mark)
            if (
                not (1 <= len(decimal_part) <= 4)
                or not decimal_part.isdigit()
                or any(len(part) != 3 for part in grouped[1:])
                or not (1 <= len(grouped[0]) <= 3 and grouped[0].isdigit())
            ):
                raise PriceUnavailable("Invalid grouped monetary value")
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
