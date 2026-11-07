"""Deterministic fixtures: tests never call commercial websites."""

from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest

from price_tracker.config import Settings
from price_tracker.storage import Store


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    db = Store(tmp_path / "state" / "prices.db")
    yield db
    db.close()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        database_path=tmp_path / "prices.db",
        max_retries=2,
        retry_delay_seconds=0,
        between_products_seconds=0,
    )


@pytest.fixture
def local_pages() -> Iterator[str]:
    """Loopback server for controlled integration; no internet dependency."""
    folder = Path(__file__).parent / "fixtures"

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "/product")
                self.end_headers()
                return
            if self.path == "/unavailable":
                self.send_response(503)
                self.end_headers()
                return
            page = "css-product.html" if self.path == "/css" else "product.html"
            data = (folder / page).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *_args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
