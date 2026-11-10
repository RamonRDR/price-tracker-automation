"""Controlled Playwright tests: redirects and third-party resources never reach other origins."""

from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from price_tracker.errors import SourceError
from price_tracker.extractors import fetch_css, source_is_approved
from price_tracker.schemas import ProductInput


def test_remote_url_requires_approved_https_origin(settings, store):
    product = store.add(
        ProductInput(
            url="https://allowed.example.org/item",
            adapter="css",
            name_selector="h1",
            price_selector=".price",
            currency="USD",
        )
    )
    settings.require_https = True
    settings.allowed_hosts = frozenset({"allowed.example.org"})
    assert source_is_approved(product.url, product, settings)
    assert not source_is_approved("http://allowed.example.org/item", product, settings)
    assert not source_is_approved("https://allowed.example.org:8443/item", product, settings)
    assert not source_is_approved("https://evil.example.org/item", product, settings)
    assert not source_is_approved("https://allowed.example.org@evil.example.org", product, settings)


@pytest.fixture
def guarded_servers() -> Iterator[tuple[str, list[str]]]:
    forbidden_hits: list[str] = []

    class ForbiddenHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            forbidden_hits.append(self.path)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Unexpected access")

        def log_message(self, *_args):
            pass

    forbidden = ThreadingHTTPServer(("127.0.0.1", 0), ForbiddenHandler)
    foreign_url = f"http://127.0.0.1:{forbidden.server_port}/blocked"

    class OriginalHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", foreign_url)
                self.end_headers()
                return
            body = (
                "<!doctype html><html><body>"
                '<h1 id="name">Safe demo</h1><div id="price">20.00</div>'
                f'<script>fetch("{foreign_url}").catch(() => {{}});</script>'
                "</body></html>"
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            pass

    original = ThreadingHTTPServer(("127.0.0.1", 0), OriginalHandler)
    threads = [
        Thread(target=forbidden.serve_forever, daemon=True),
        Thread(target=original.serve_forever, daemon=True),
    ]
    for thread in threads:
        thread.start()
    try:
        yield f"http://127.0.0.1:{original.server_port}", forbidden_hits
    finally:
        for server in (original, forbidden):
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(timeout=3)


@pytest.mark.browser
def test_cross_origin_redirect_blocked_before_any_http_request(
    store, settings, guarded_servers
):
    url, forbidden_hits = guarded_servers
    product = store.add(
        ProductInput(
            url=f"{url}/redirect",
            adapter="css",
            name_selector="#name",
            price_selector="#price",
            currency="USD",
        )
    )
    with pytest.raises(SourceError, match="Playwright extraction failed"):
        fetch_css(product, settings)
    assert forbidden_hits == []


@pytest.mark.browser
def test_external_subresource_aborted_before_fetch(store, settings, guarded_servers):
    url, forbidden_hits = guarded_servers
    product = store.add(
        ProductInput(
            url=f"{url}/product",
            adapter="css",
            name_selector="#name",
            price_selector="#price",
            currency="USD",
        )
    )
    quote = fetch_css(product, settings)
    assert quote.name == "Safe demo"
    assert forbidden_hits == []
