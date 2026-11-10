import json
from decimal import Decimal

import pytest

from price_tracker.errors import PriceUnavailable, SourceError
from price_tracker.extractors import extract_jsonld_html, fetch_jsonld


def test_jsonld_nested_graph() -> None:
    document = {
        "@graph": [
            {"@type": "Organization", "name": "Test"},
            {
                "@type": ["Thing", "Product"],
                "name": "Sample",
                "offers": [{"price": "9,95", "priceCurrency": "EUR"}],
            },
        ]
    }
    html = f'<script type="application/ld+json">{json.dumps(document)}</script>'
    result = extract_jsonld_html(html)
    assert result.name == "Sample"
    assert result.currency == "EUR"
    assert result.price == Decimal("9.9500")


def test_missing_or_layout_changed() -> None:
    with pytest.raises(PriceUnavailable):
        extract_jsonld_html("<h1>Product with no structured metadata</h1>")
    with pytest.raises(PriceUnavailable):
        extract_jsonld_html('<script type="application/ld+json">{invalid}</script>')


def test_out_of_stock() -> None:
    raw = (
        '{"@type":"Product","name":"Widget","offers":'
        '{"price":"99","priceCurrency":"USD",'
        '"availability":"https://schema.org/OutOfStock"}}'
    )
    with pytest.raises(PriceUnavailable):
        extract_jsonld_html(f'<script type="application/ld+json">{raw}</script>')


def test_httpx_local_fixture(store, settings, local_pages) -> None:
    from price_tracker.schemas import ProductInput

    product = store.add(ProductInput(url=f"{local_pages}/product"))
    quote = fetch_jsonld(product, settings)
    assert quote.name == "Demo Widget"
    assert quote.price == Decimal("1234.5600")


def test_http_error_from_controlled_server(store, settings, local_pages) -> None:
    from price_tracker.schemas import ProductInput

    product = store.add(ProductInput(url=f"{local_pages}/unavailable"))
    with pytest.raises(SourceError, match="HTTP request failed"):
        fetch_jsonld(product, settings)


@pytest.mark.browser
def test_playwright_css_local_fixture(store, settings, local_pages) -> None:
    from price_tracker.extractors import fetch_css
    from price_tracker.schemas import ProductInput

    product = store.add(
        ProductInput(
            url=f"{local_pages}/css",
            adapter="css",
            name_selector='[data-testid="name"]',
            price_selector='[data-testid="price"]',
            currency="BRL",
        )
    )
    quote = fetch_css(product, settings)
    assert quote.name == "Another Demo Widget"
    assert quote.price == Decimal("1234.5600")


@pytest.mark.parametrize("bad_price", ["N/A", "0", "-1"])
def test_jsonld_skips_bad_offers_and_uses_next_valid_price(bad_price: str) -> None:
    document = {
        "@type": "Product",
        "name": "Two offers",
        "offers": [
            {"price": bad_price, "priceCurrency": "USD"},
            {"price": "19.99", "priceCurrency": "USD"},
        ],
    }
    html = f'<script type="application/ld+json">{json.dumps(document)}</script>'
    quote = extract_jsonld_html(html)
    assert quote.price == Decimal("19.9900")
    assert quote.currency == "USD"
