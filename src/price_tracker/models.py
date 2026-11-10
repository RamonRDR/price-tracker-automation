"""SQLite schema, including immutable observations and alert deduplication."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    adapter: Mapped[str] = mapped_column(String(16), default="jsonld")
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_selector: Mapped[str | None] = mapped_column(Text)
    price_selector: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str | None] = mapped_column(String(3))
    target: Mapped[Decimal | None] = mapped_column(Numeric(18, 4, asdecimal=True))
    drop_percent: Mapped[Decimal | None] = mapped_column(Numeric(7, 3, asdecimal=True))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    observations: Mapped[list[PriceObservation]] = relationship(back_populates="product")


class PriceObservation(Base):
    __tablename__ = "price_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    name: Mapped[str] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4, asdecimal=True))
    currency: Mapped[str] = mapped_column(String(3))
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    product: Mapped[Product] = relationship(back_populates="observations")


class AlertEvent(Base):
    __tablename__ = "alert_events"
    __table_args__ = (UniqueConstraint("dedupe_key", name="uq_alert_dedupe"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    observation_id: Mapped[int] = mapped_column(ForeignKey("price_observations.id"))
    kind: Mapped[str] = mapped_column(String(16))
    dedupe_key: Mapped[str] = mapped_column(String(120))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
