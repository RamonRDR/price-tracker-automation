"""Permission-denied and redirected local pages are handled without bypass."""

import pytest

from price_tracker.errors import SourceError
from price_tracker.extractors import fetch_jsonld
from price_tracker.schemas import ProductInput


def test_no_redirect_following(store, settings, local_pages) -> None:
    product = store.add(ProductInput(url=f"{local_pages}/redirect"))
    with pytest.raises(SourceError, match="HTTP request failed"):
        fetch_jsonld(product, settings)


@pytest.mark.browser
def test_missing_css_selector_is_controlled_error(store, settings, local_pages) -> None:
    from price_tracker.extractors import fetch_css

    product = store.add(
        ProductInput(
            url=f"{local_pages}/css",
            adapter="css",
            name_selector="#missing-name",
            price_selector='[data-testid="price"]',
            currency="BRL",
        )
    )
    settings.timeout_seconds = 0.5
    with pytest.raises(SourceError, match="Playwright extraction failed"):
        fetch_css(product, settings)
