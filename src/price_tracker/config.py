"""Validated environment configuration; credentials are never committed."""

import os
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    database_path: Path = Field(
        default_factory=lambda: Path.home() / ".local" / "share" / "price-tracker" / "prices.db"
    )
    timeout_seconds: float = Field(default=15, gt=0, le=120)
    max_retries: int = Field(default=2, ge=0, le=4)
    retry_delay_seconds: float = Field(default=0.5, ge=0, le=30)
    between_products_seconds: float = Field(default=1, ge=0, le=60)
    max_products_per_run: int = Field(default=50, ge=1, le=500)

    @field_validator("database_path")
    @classmethod
    def normalize_path(cls, value: Path) -> Path:
        return value.expanduser().absolute()

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_path=os.environ.get(
                "PRICE_TRACKER_DB", str(Path.home() / ".local/share/price-tracker/prices.db")
            ),
            timeout_seconds=os.environ.get("PRICE_TRACKER_TIMEOUT", "15"),
            max_retries=os.environ.get("PRICE_TRACKER_RETRIES", "2"),
            retry_delay_seconds=os.environ.get("PRICE_TRACKER_RETRY_DELAY", "0.5"),
            between_products_seconds=os.environ.get("PRICE_TRACKER_DELAY", "1"),
            max_products_per_run=os.environ.get("PRICE_TRACKER_MAX_PRODUCTS", "50"),
        )
