"""Validated transport and application payloads."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator, model_validator

from price_tracker.errors import InvalidProduct
from price_tracker.money import parse_price


class ProductInput(BaseModel):
    url: AnyHttpUrl
    adapter: Literal["jsonld", "css"] = "jsonld"
    name_selector: str | None = None
    price_selector: str | None = None
    currency: str | None = None
    target: Decimal | None = Field(default=None, gt=0)
    drop_percent: Decimal | None = Field(default=None, gt=0, le=100)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, currency: str | None) -> str | None:
        if currency is None:
            return None
        value = currency.upper().strip()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("currency must be a 3-letter ISO code")
        return value

    @model_validator(mode="after")
    def validate_css(self) -> "ProductInput":
        if self.adapter == "css" and not (
            self.name_selector and self.price_selector and self.currency
        ):
            raise ValueError("CSS adapter requires name-selector, price-selector and currency")
        return self


class PriceQuote(BaseModel):
    name: str = Field(min_length=1)
    price: Decimal = Field(gt=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("price", mode="before")
    @classmethod
    def price_from_source(cls, value: object) -> Decimal:
        return parse_price(value)  # type: ignore[arg-type]

    @field_validator("checked_at")
    @classmethod
    def aware_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("checked_at must contain timezone")
        return value


def checked_product_id(product_id: int) -> int:
    if product_id <= 0:
        raise InvalidProduct("Product ID must be greater than zero")
    return product_id
