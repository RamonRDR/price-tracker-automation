"""Configurable, permission-respecting JSON-LD and Playwright CSS adapters."""

import json
import logging
from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

import httpx
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright
from pydantic import ValidationError

from price_tracker.config import Settings
from price_tracker.errors import PriceUnavailable, SourceError
from price_tracker.models import Product
from price_tracker.schemas import PriceQuote

logger = logging.getLogger("price_tracker.extractors")


class _StructuredDataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_jsonld = False
        self.chunks: list[str] = []
        self.documents: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if (
            tag.lower() == "script"
            and (attributes.get("type") or "").lower().split(";")[0].strip()
            == "application/ld+json"
        ):
            self.in_jsonld = True
            self.chunks = []

    def handle_data(self, data: str) -> None:
        if self.in_jsonld:
            self.chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self.in_jsonld:
            self.documents.append("".join(self.chunks))
            self.in_jsonld = False


def _walk_json(node: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(node, list):
        for item in node:
            found.extend(_walk_json(item))
    if isinstance(node, dict):
        if node.get("@type") == "Product" or (
            isinstance(node.get("@type"), list) and "Product" in node["@type"]
        ):
            found.append(node)
        for value in node.values():
            if isinstance(value, (dict, list)):
                found.extend(_walk_json(value))
    return found


def extract_jsonld_html(html: str, *, fallback_currency: str | None = None) -> PriceQuote:
    """Extract Product > Offer from public JSON-LD, including @graph / arrays."""
    parser = _StructuredDataParser()
    parser.feed(html)
    for raw in parser.documents:
        try:
            document = json.loads(raw)
        except TypeError, json.JSONDecodeError:
            continue
        for product in _walk_json(document):
            offers = product.get("offers")
            if isinstance(offers, dict):
                offers = [offers]
            if not isinstance(offers, list):
                continue
            for offer in offers:
                if not isinstance(offer, dict):
                    continue
                if str(offer.get("availability", "")).endswith("/OutOfStock"):
                    continue
                price_spec = offer.get("priceSpecification")
                price = offer.get("price")
                if price is None and isinstance(price_spec, dict):
                    price = price_spec.get("price")
                currency = (
                    offer.get("priceCurrency")
                    or (price_spec.get("priceCurrency") if isinstance(price_spec, dict) else None)
                    or fallback_currency
                )
                if price is not None and currency and product.get("name"):
                    try:
                        return PriceQuote(
                            name=str(product["name"]),
                            price=price,
                            currency=str(currency).upper(),
                            checked_at=datetime.now(UTC),
                        )
                    except PriceUnavailable, ValueError:
                        continue
    raise PriceUnavailable("No supported, available Product/Offer price in JSON-LD")


def source_is_approved(url: str, product: Product, settings: Settings) -> bool:
    """Allow only the registered origin, or approved HTTPS hosts in remote mode."""
    try:
        parsed = urlparse(url)
        original = urlparse(product.url)
        if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
            return False
        if not parsed.hostname:
            return False
        if settings.require_https and (parsed.scheme != "https" or parsed.port not in (None, 443)):
            return False
        if settings.allowed_hosts is not None:
            return parsed.scheme == "https" and parsed.hostname in settings.allowed_hosts
        return (
            parsed.scheme == original.scheme
            and parsed.hostname == original.hostname
            and parsed.port == original.port
        )
    except ValueError:
        return False


def fetch_jsonld(product: Product, settings: Settings) -> PriceQuote:
    if not source_is_approved(product.url, product, settings):
        raise PriceUnavailable("Source is not approved for access")
    try:
        with httpx.Client(
            timeout=settings.timeout_seconds,
            follow_redirects=False,
            max_redirects=3,
            headers={"User-Agent": "PriceTrackerAutomation/0.1 (responsible monitoring)"},
        ) as client:
            response = client.get(product.url)
            if response.status_code in (401, 403, 429):
                raise PriceUnavailable("Source denied automated access")
            response.raise_for_status()
            if "html" not in response.headers.get("content-type", "").lower():
                raise PriceUnavailable("Source did not return HTML")
            return extract_jsonld_html(response.text, fallback_currency=product.currency)
    except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as exc:
        raise SourceError(f"HTTP request failed: {type(exc).__name__}") from exc


def fetch_css(product: Product, settings: Settings) -> PriceQuote:
    if not product.name_selector or not product.price_selector or not product.currency:
        raise PriceUnavailable("CSS selectors and currency are not configured")
    if not source_is_approved(product.url, product, settings):
        raise PriceUnavailable("Source is not approved for access")
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                # Route interception is installed BEFORE navigation. It covers redirects
                # and subresources; service workers and WebSockets are disabled.
                context = browser.new_context(service_workers="block")

                def guard(route) -> None:
                    if not source_is_approved(route.request.url, product, settings):
                        logger.warning("Blocked browser request outside approved origins")
                        route.abort("blockedbyclient")
                        return
                    try:
                        # route.continue_() can follow redirects without re-interception.
                        # fetch(max_redirects=0) stops at the FIRST response instead.
                        upstream = route.fetch(
                            max_redirects=0, timeout=int(settings.timeout_seconds * 1000)
                        )
                        if 300 <= upstream.status < 400:
                            logger.warning("Blocked browser redirect before next destination")
                            route.abort("blockedbyclient")
                        else:
                            route.fulfill(response=upstream)
                    except PlaywrightError:
                        route.abort("failed")

                context.route("**/*", guard)
                context.route_web_socket("**/*", lambda websocket: websocket.close())
                page = context.new_page()
                response = page.goto(
                    product.url,
                    wait_until="domcontentloaded",
                    timeout=int(settings.timeout_seconds * 1000),
                )
                if response and response.status in (401, 403, 429):
                    raise PriceUnavailable("Source denied automated access")
                if response and response.status >= 400:
                    raise SourceError(f"Browser returned HTTP {response.status}")
                if not source_is_approved(page.url, product, settings):
                    raise SourceError("Browser navigated outside approved origins")
                name = (
                    page.locator(product.name_selector)
                    .first.inner_text(timeout=int(settings.timeout_seconds * 1000))
                    .strip()
                )
                price = page.locator(product.price_selector).first.inner_text(
                    timeout=int(settings.timeout_seconds * 1000)
                )
                try:
                    return PriceQuote(name=name, price=price, currency=product.currency)
                except ValidationError as exc:
                    raise PriceUnavailable("CSS source returned an invalid quote") from exc
            finally:
                browser.close()
    except (PlaywrightTimeout, PlaywrightError) as exc:
        raise SourceError(f"Playwright extraction failed: {type(exc).__name__}") from exc


def extract(product: Product, settings: Settings) -> PriceQuote:
    logger.info("Extracting price for product_id=%s adapter=%s", product.id, product.adapter)
    if product.adapter == "jsonld":
        return fetch_jsonld(product, settings)
    if product.adapter == "css":
        return fetch_css(product, settings)
    raise PriceUnavailable("Unknown extractor adapter")
