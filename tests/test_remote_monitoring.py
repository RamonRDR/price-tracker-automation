"""Regression tests for all Codex P1/P2 findings; no real GitHub or SMTP calls."""

import base64
import hashlib
import os
import sqlite3
from decimal import Decimal

import httpx
import pytest

from price_tracker import github_runner
from price_tracker.monitor import check_one
from price_tracker.schemas import PriceQuote, ProductInput
from price_tracker.storage import Store


def _blob_sha(content: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\x00" + content,
        usedforsecurity=False,
    ).hexdigest()


class FakeGitHubClient:
    """In-memory GitHub Contents + Git Blob API; inline state is intentionally absent."""

    def __init__(self, state: bytes | None = None, fail_put: bool = False):
        self.state = state
        self.fail_put = fail_put
        self.calls: list[str] = []
        self.saved: bytes | None = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        path = url.split("https://api.github.com", 1)[-1]
        request = httpx.Request(method, url)
        self.calls.append(f"{method} {path}")
        if method == "GET" and path == "/repos/owner/private":
            return httpx.Response(200, json={"private": True}, request=request)
        if method == "GET" and path == "/repos/owner/private/branches/monitor-state":
            return httpx.Response(200, json={"name": "monitor-state"}, request=request)
        contents = "/repos/owner/private/contents/state/price-tracker.sqlite3"
        if method == "GET" and path == contents:
            if self.state is None:
                return httpx.Response(404, json={"message": "Not Found"}, request=request)
            return httpx.Response(
                200,
                json={
                    "type": "file",
                    "sha": _blob_sha(self.state),
                    "size": len(self.state),
                    "content": "",
                    "encoding": "none",
                },
                request=request,
            )
        if method == "GET" and path.startswith("/repos/owner/private/git/blobs/"):
            if self.state is None:
                return httpx.Response(404, request=request)
            encoded = base64.b64encode(self.state).decode("ascii")
            # GitHub blob payloads can be line-wrapped: decoding must accept this.
            wrapped = "\n".join(encoded[i : i + 76] for i in range(0, len(encoded), 76))
            return httpx.Response(
                200,
                json={
                    "sha": _blob_sha(self.state),
                    "size": len(self.state),
                    "encoding": "base64",
                    "content": wrapped,
                },
                request=request,
            )
        if method == "PUT" and path == contents:
            if self.fail_put:
                return httpx.Response(409, json={"message": "Conflict"}, request=request)
            payload = kwargs["json"]
            if self.state is not None:
                assert payload["sha"] == _blob_sha(self.state)
            self.saved = base64.b64decode(payload["content"])
            self.state = self.saved
            return httpx.Response(
                200, json={"content": {"sha": _blob_sha(self.saved)}}, request=request
            )
        raise AssertionError(f"Unexpected simulated GitHub request: {method} {path}")

    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.request("GET", url, **kwargs)


def _approve_env(monkeypatch, sources: list[dict]) -> None:
    import json

    monkeypatch.setenv("TRACKER_MONITOR_APPROVED", "true")
    monkeypatch.setenv("TRACKER_STATE_REPO", "owner/private")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/public")
    monkeypatch.setenv("TRACKER_STATE_TOKEN", "simulated-private-token")
    monkeypatch.setenv("TRACKER_STATE_BRANCH", "monitor-state")
    monkeypatch.setenv("TRACKER_ALLOWED_HOSTS", "allowed.example.org")
    monkeypatch.setenv("TRACKER_PRODUCTS_JSON", json.dumps(sources))
    monkeypatch.setenv("PRICE_TRACKER_DELAY", "0")
    monkeypatch.setenv("PRICE_TRACKER_RETRIES", "0")


def _seed_state(tmp_path, *, large: bool = False) -> bytes:
    path = tmp_path / "state.sqlite3"
    store = Store(path)
    try:
        keep = store.add(
            ProductInput(url="https://allowed.example.org/keep", target=Decimal("100"))
        )
        revoke = store.add(ProductInput(url="https://revoked.example.org/old"))
        store.save_check(revoke.id, PriceQuote(name="Old observation", price=150, currency="USD"))
        assert keep.id != revoke.id
    finally:
        store.close()
    if large:
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE large_history (value BLOB NOT NULL)")
            connection.execute(
                "INSERT INTO large_history(value) VALUES (?)",
                (os.urandom(1_200_000),),
            )
            connection.commit()
    return path.read_bytes()


def _install_fake_network(monkeypatch, network: FakeGitHubClient, seen: list) -> None:
    monkeypatch.setattr(github_runner.httpx, "Client", lambda **kwargs: network)

    def run_checks(store, settings, *, notify: bool):
        assert notify is False, "SMTP must not occur before state upload"
        assert settings.require_https is True
        assert settings.allowed_hosts == frozenset({"allowed.example.org"})
        selected = store.list_products(active_only=True)
        seen.extend(item.url for item in selected)
        results = []
        for product in selected:
            results.append(
                check_one(
                    store,
                    product,
                    settings,
                    extractor=lambda *_: PriceQuote(
                        name="Approved widget", price=Decimal("50"), currency="USD"
                    ),
                    sleep=lambda _: None,
                )
            )
        return results

    monkeypatch.setattr(github_runner, "check_many", run_checks)


def test_revoked_products_never_checked_and_existing_history_preserved(monkeypatch, tmp_path):
    previous = _seed_state(tmp_path)
    network = FakeGitHubClient(previous)
    checked: list[str] = []
    sent = []
    _approve_env(
        monkeypatch,
        [{"url": "https://allowed.example.org/keep", "adapter": "jsonld", "target": "100"}],
    )
    _install_fake_network(monkeypatch, network, checked)

    def send(events):
        assert any("PUT /repos/owner/private/contents" in call for call in network.calls)
        sent.extend(events)

    monkeypatch.setattr(github_runner, "send_email", send)
    assert github_runner.execute() == 0
    assert checked == ["https://allowed.example.org/keep"]
    assert len(sent) == 1
    assert network.saved is not None
    new_path = tmp_path / "latest.sqlite3"
    new_path.write_bytes(network.saved)
    state = Store(new_path)
    try:
        assert [product.url for product in state.list_products(active_only=True)] == checked
        assert len(state.history()) == 2
        assert state.get(2).active is False
    finally:
        state.close()


def test_git_blob_over_one_megabyte_preserves_history(monkeypatch, tmp_path):
    previous = _seed_state(tmp_path, large=True)
    assert len(previous) > 1_000_000
    network = FakeGitHubClient(previous)
    checked: list[str] = []
    _approve_env(
        monkeypatch,
        [{"url": "https://allowed.example.org/keep", "adapter": "jsonld", "target": "100"}],
    )
    _install_fake_network(monkeypatch, network, checked)
    monkeypatch.setattr(github_runner, "send_email", lambda _: None)
    assert github_runner.execute() == 0
    assert network.saved is not None
    new_path = tmp_path / "new-state.sqlite3"
    new_path.write_bytes(network.saved)
    state = Store(new_path)
    try:
        assert len(state.history()) == 2
        with sqlite3.connect(new_path) as connection:
            length = connection.execute("SELECT length(value) FROM large_history").fetchone()[0]
        assert length == 1_200_000
    finally:
        state.close()
    assert any("/git/blobs/" in call for call in network.calls)


def test_failed_state_commit_never_emails(monkeypatch, tmp_path):
    original = _seed_state(tmp_path)
    network = FakeGitHubClient(original, fail_put=True)
    checked: list[str] = []
    emails = []
    _approve_env(
        monkeypatch,
        [{"url": "https://allowed.example.org/keep", "adapter": "jsonld", "target": "100"}],
    )
    _install_fake_network(monkeypatch, network, checked)
    monkeypatch.setattr(github_runner, "send_email", lambda alerts: emails.extend(alerts))
    with pytest.raises(httpx.HTTPStatusError):
        github_runner.execute()
    assert checked == ["https://allowed.example.org/keep"]
    assert not emails
    assert network.saved is None
    assert network.state == original


def test_invalid_blob_cannot_reset_existing_database(monkeypatch, tmp_path):
    original = _seed_state(tmp_path)
    network = FakeGitHubClient(original)

    def corrupt_blob(method, url, **kwargs):
        response = FakeGitHubClient.request(network, method, url, **kwargs)
        if "/git/blobs/" in url:
            payload = response.json()
            payload["content"] = base64.b64encode(b"not a sqlite database").decode()
            return httpx.Response(200, json=payload, request=httpx.Request(method, url))
        return response

    monkeypatch.setattr(network, "request", corrupt_blob)
    _approve_env(
        monkeypatch,
        [{"url": "https://allowed.example.org/keep", "adapter": "jsonld"}],
    )
    monkeypatch.setattr(github_runner.httpx, "Client", lambda **kwargs: network)
    with pytest.raises(ValueError, match="size does not match"):
        github_runner.execute()
    assert network.saved is None
