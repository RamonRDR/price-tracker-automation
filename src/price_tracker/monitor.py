"""Bounded monitoring orchestration with persisted price comparisons."""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal

from price_tracker.config import Settings
from price_tracker.errors import PriceUnavailable, SourceError, TrackerError
from price_tracker.extractors import extract
from price_tracker.models import AlertEvent, PriceObservation, Product
from price_tracker.notifications import send_email
from price_tracker.schemas import PriceQuote
from price_tracker.storage import Store

logger = logging.getLogger("price_tracker.monitor")

Extractor = Callable[[Product, Settings], PriceQuote]


@dataclass
class CheckResult:
    product_id: int
    status: str
    current: PriceObservation | None = None
    previous: PriceObservation | None = None
    alerts: list[AlertEvent] = field(default_factory=list)
    error: str | None = None

    @property
    def change_percent(self) -> Decimal | None:
        if self.current is None or self.previous is None:
            return None
        return (self.current.price - self.previous.price) / self.previous.price * 100


def check_one(
    store: Store,
    product: Product,
    settings: Settings,
    *,
    extractor: Extractor = extract,
    notify: bool = False,
    sleep: Callable[[float], None] = time.sleep,
) -> CheckResult:
    if not product.active:
        return CheckResult(product_id=product.id, status="inactive")
    quote: PriceQuote | None = None
    for attempt in range(settings.max_retries + 1):
        try:
            quote = extractor(product, settings)
            break
        except PriceUnavailable as exc:
            logger.warning("Price unavailable for product_id=%s: %s", product.id, exc)
            return CheckResult(product_id=product.id, status="unavailable", error=str(exc))
        except SourceError as exc:
            if attempt == settings.max_retries:
                logger.error(
                    "Source failed for product_id=%s attempts=%s: %s",
                    product.id,
                    attempt + 1,
                    exc,
                )
                return CheckResult(product_id=product.id, status="error", error=str(exc))
            sleep(settings.retry_delay_seconds * (2**attempt))
    if quote is None:
        return CheckResult(product_id=product.id, status="error", error="No quote")
    try:
        current, previous, alerts = store.save_check(product.id, quote)
    except TrackerError as exc:
        return CheckResult(product_id=product.id, status="error", error=str(exc))
    result = CheckResult(
        product_id=product.id, status="ok", current=current, previous=previous, alerts=alerts
    )
    logger.info(
        "Price stored product_id=%s price=%s currency=%s alerts=%s",
        product.id,
        current.price,
        current.currency,
        len(alerts),
    )
    if notify and alerts:
        try:
            send_email(alerts)
        except (OSError, ValueError, ConnectionError) as exc:
            logger.error(
                "Email delivery failed for product_id=%s: %s", product.id, type(exc).__name__
            )
            result.error = "SMTP delivery failed; alerts remain stored locally"
    return result


def check_many(
    store: Store,
    settings: Settings,
    *,
    product_id: int | None = None,
    notify: bool = False,
    extractor: Extractor = extract,
    sleep: Callable[[float], None] = time.sleep,
) -> list[CheckResult]:
    products = (
        [store.get(product_id)]
        if product_id is not None
        else store.list_products(active_only=True, limit=settings.max_products_per_run)
    )
    results: list[CheckResult] = []
    for index, product in enumerate(products):
        if index:
            sleep(settings.between_products_seconds)
        results.append(
            check_one(store, product, settings, extractor=extractor, notify=notify, sleep=sleep)
        )
    return results
