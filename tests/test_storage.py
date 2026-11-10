from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from price_tracker.errors import InvalidProduct
from price_tracker.schemas import PriceQuote, ProductInput
from price_tracker.storage import Store


def test_register_url_validation_and_duplicate(store: Store) -> None:
    with pytest.raises(ValidationError):
        ProductInput(url="file:///etc/passwd")
    with pytest.raises(ValidationError):
        ProductInput(url="https://example.test", adapter="css")
    item = store.add(ProductInput(url="https://example.test/widget"))
    assert item.id == 1
    with pytest.raises(InvalidProduct, match="already"):
        store.add(ProductInput(url="https://example.test/widget"))


def test_sqlite_survives_restart(store: Store) -> None:
    product = store.add(ProductInput(url="https://example.test/product", target=Decimal("50")))
    store.save_check(product.id, PriceQuote(name="First", price=Decimal("45"), currency="USD"))
    path = store.path
    second_store = Store(path)
    try:
        assert len(second_store.history(product.id)) == 1
        assert second_store.get(product.id).name == "First"
        assert second_store.alerts(product.id)[0].kind == "target"
    finally:
        second_store.close()


def test_history_order_and_currency_safety(store: Store) -> None:
    product = store.add(ProductInput(url="https://example.test/product"))
    for value in (Decimal("20"), Decimal("18"), Decimal("21")):
        store.save_check(product.id, PriceQuote(name="Sample", price=value, currency="USD"))
    assert [row.price for row in store.history(product.id)] == [
        Decimal("21"),
        Decimal("18"),
        Decimal("20"),
    ]
    with pytest.raises(InvalidProduct, match="Currency changed"):
        store.save_check(
            product.id,
            PriceQuote(name="Sample", price=Decimal("10"), currency="EUR"),
        )
    assert len(store.history(product.id)) == 3


def test_timestamps_are_explicitly_aware() -> None:
    with pytest.raises(ValidationError):
        PriceQuote(
            name="Invalid",
            price=Decimal("1"),
            currency="USD",
            checked_at=datetime(2026, 1, 1),
        )
    assert PriceQuote(name="Valid", price=1, currency="USD", checked_at=datetime.now(UTC))


def test_update_alerts_and_pause(store: Store) -> None:
    product = store.add(ProductInput(url="https://example.test/one"))
    store.set_alerts(product.id, target=Decimal("100"), drop_percent=Decimal("12"))
    store.set_active(product.id, active=False)
    assert not store.get(product.id).active
    assert store.get(product.id).target == Decimal("100")


def test_configured_currency_is_checked_on_first_quote(store: Store) -> None:
    product = store.add(
        ProductInput(url="https://example.test/currency", currency="USD", target=Decimal("100"))
    )
    with pytest.raises(InvalidProduct, match="configured product currency"):
        store.save_check(product.id, PriceQuote(name="Widget", price=80, currency="EUR"))
    assert store.history(product.id) == []
    assert store.alerts(product.id) == []
    assert store.get(product.id).currency == "USD"

    store.save_check(product.id, PriceQuote(name="Widget", price=90, currency="USD"))
    assert len(store.history(product.id)) == 1
    assert len(store.alerts(product.id)) == 1
