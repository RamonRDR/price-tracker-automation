from decimal import Decimal

from price_tracker.errors import PriceUnavailable, SourceError
from price_tracker.monitor import check_many, check_one
from price_tracker.schemas import PriceQuote, ProductInput


def test_price_increase_drop_and_target_dedup(store, settings) -> None:
    product = store.add(
        ProductInput(
            url="https://example.test/item",
            target=Decimal("80"),
            drop_percent=Decimal("10"),
        )
    )
    prices = iter((100, 78, 78, 85, 79, 110))
    def extractor(product, settings):
        return PriceQuote(name="Widget", price=next(prices), currency="USD")
    results = [check_one(store, product, settings, extractor=extractor) for _ in range(6)]
    assert results[0].change_percent is None
    assert results[1].change_percent == Decimal("-22")
    assert {event.kind for event in results[1].alerts} == {"target", "drop"}
    assert results[2].alerts == []
    assert results[3].change_percent > 0
    assert [event.kind for event in results[4].alerts] == ["target"]
    assert len(store.alerts(product.id)) == 3


def test_unavailable_does_not_persist_or_retry(store, settings) -> None:
    product = store.add(ProductInput(url="https://example.test/other"))
    attempts = []

    def extractor(*_args):
        attempts.append(1)
        raise PriceUnavailable("Product not available")

    result = check_one(store, product, settings, extractor=extractor)
    assert result.status == "unavailable"
    assert len(attempts) == 1
    assert store.history(product.id) == []


def test_retry_limit_then_failure(store, settings) -> None:
    product = store.add(ProductInput(url="https://example.test/other"))
    attempts = []

    def extractor(*_args):
        attempts.append(1)
        raise SourceError("Timeout")

    result = check_one(store, product, settings, extractor=extractor, sleep=lambda _: None)
    assert result.status == "error"
    assert len(attempts) == settings.max_retries + 1
    assert store.history(product.id) == []


def test_retry_then_success(store, settings) -> None:
    product = store.add(ProductInput(url="https://example.test/retry"))
    attempts = []

    def extractor(*_args):
        attempts.append(1)
        if len(attempts) < 2:
            raise SourceError("Connection refused")
        return PriceQuote(name="Recovered", price=Decimal("42"), currency="USD")

    result = check_one(store, product, settings, extractor=extractor, sleep=lambda _: None)
    assert result.status == "ok"
    assert len(attempts) == 2


def test_multiple_products_and_pause(store, settings) -> None:
    one = store.add(ProductInput(url="https://example.test/one"))
    two = store.add(ProductInput(url="https://example.test/two"))
    store.set_active(two.id, active=False)
    results = check_many(
        store, settings,
        extractor=lambda product, _: PriceQuote(
            name=f"Product {product.id}", price=Decimal("10"), currency="USD"
        ),
        sleep=lambda _: None,
    )
    assert [result.product_id for result in results] == [one.id]
    assert len(store.history()) == 1
