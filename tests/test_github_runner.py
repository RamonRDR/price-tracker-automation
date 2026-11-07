"""Approval and host guards fail closed without any network access."""

import json

import pytest

from price_tracker.errors import InvalidProduct
from price_tracker.github_runner import execute


def test_remote_monitoring_is_off_by_default(monkeypatch) -> None:
    monkeypatch.delenv("TRACKER_MONITOR_APPROVED", raising=False)
    assert execute() == 0


def test_public_repository_cannot_be_state_store(monkeypatch) -> None:
    monkeypatch.setenv("TRACKER_MONITOR_APPROVED", "true")
    monkeypatch.setenv("TRACKER_STATE_REPO", "owner/public")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/public")
    monkeypatch.setenv("TRACKER_STATE_TOKEN", "fake-value")
    monkeypatch.setenv("TRACKER_ALLOWED_HOSTS", "demo.example.org")
    monkeypatch.setenv("TRACKER_PRODUCTS_JSON", "[]")
    with pytest.raises(ValueError, match="public source repository"):
        execute()


def test_unapproved_hosts_fail_before_any_request(monkeypatch) -> None:
    monkeypatch.setenv("TRACKER_MONITOR_APPROVED", "true")
    monkeypatch.setenv("TRACKER_STATE_REPO", "owner/private")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/public")
    monkeypatch.setenv("TRACKER_STATE_TOKEN", "fake-value")
    monkeypatch.setenv("TRACKER_ALLOWED_HOSTS", "demo.example.org")
    monkeypatch.setenv(
        "TRACKER_PRODUCTS_JSON",
        json.dumps([{"url": "https://other.example.net/item", "adapter": "jsonld"}]),
    )
    with pytest.raises(InvalidProduct, match="approved HTTPS hosts"):
        execute()


def test_plain_http_is_not_approved_for_actions(monkeypatch) -> None:
    monkeypatch.setenv("TRACKER_MONITOR_APPROVED", "true")
    monkeypatch.setenv("TRACKER_STATE_REPO", "owner/private")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/public")
    monkeypatch.setenv("TRACKER_STATE_TOKEN", "fake-value")
    monkeypatch.setenv("TRACKER_ALLOWED_HOSTS", "demo.example.org")
    monkeypatch.setenv(
        "TRACKER_PRODUCTS_JSON",
        json.dumps([{"url": "http://demo.example.org/item", "adapter": "jsonld"}]),
    )
    with pytest.raises(InvalidProduct, match="approved HTTPS hosts"):
        execute()
