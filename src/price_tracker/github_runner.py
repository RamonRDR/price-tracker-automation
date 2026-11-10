"""Approval-gated GitHub Actions monitoring with durable state in a private repository."""

import base64
import hashlib
import json
import logging
import os
import smtplib
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import httpx
from pydantic import ValidationError

from price_tracker.config import Settings
from price_tracker.errors import InvalidProduct
from price_tracker.logging_config import setup_logging
from price_tracker.monitor import check_many
from price_tracker.notifications import send_email
from price_tracker.schemas import ProductInput
from price_tracker.storage import Store

logger = logging.getLogger("price_tracker.github_runner")
STATE_PATH = "state/price-tracker.sqlite3"
MAX_STATE_BYTES = 32 * 1024 * 1024


def _required(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


def _api(client: httpx.Client, method: str, path: str, **kwargs: object) -> httpx.Response:
    response = client.request(method, "https://api.github.com" + path, **kwargs)
    response.raise_for_status()
    return response


def _read_state(
    client: httpx.Client, repository: str, branch: str
) -> tuple[str | None, bytes | None]:
    """Fetch binary data through the Git Blob API; never trust inline Contents encoding."""
    content_path = f"/repos/{repository}/contents/{STATE_PATH}"
    response = client.get("https://api.github.com" + content_path, params={"ref": branch})
    if response.status_code == 404:
        return None, None
    response.raise_for_status()
    metadata = response.json()
    sha = metadata["sha"]
    if metadata.get("type") != "file":
        raise ValueError("Persisted state is not a file")
    if not 0 < metadata["size"] <= MAX_STATE_BYTES:
        raise ValueError("Persisted state exceeds allowed size or is empty")

    # Contents JSON omits inline Base64 after 1 MB. Git Blobs serves the full content.
    blob = _api(client, "GET", f"/repos/{repository}/git/blobs/{sha}").json()
    if blob.get("encoding") != "base64" or not blob.get("content"):
        raise ValueError("Git Blob response does not contain complete encoded state")
    # GitHub wraps Base64 content at line boundaries in the Git Blob API.
    data = base64.b64decode("".join(blob["content"].split()), validate=True)
    if len(data) != metadata["size"] or len(data) != blob.get("size"):
        raise ValueError("Persisted state size does not match Git metadata")
    if not data.startswith(b"SQLite format 3\x00"):
        raise ValueError("Persisted state is not a valid SQLite database")
    # GitHub repositories with 40-character object IDs use Git SHA-1.
    if len(sha) == 40:
        digest = hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\x00" + data,
            usedforsecurity=False,
        ).hexdigest()
        if digest != sha or blob.get("sha") != sha:
            raise ValueError("Persisted state Git object hash mismatch")
    return sha, data


def _approved_products(allowed_hosts: set[str]) -> list[ProductInput]:
    raw = json.loads(_required("TRACKER_PRODUCTS_JSON"))
    if not isinstance(raw, list) or not raw:
        raise ValueError("TRACKER_PRODUCTS_JSON must be a non-empty array")
    if len(raw) > 50:
        raise ValueError("Maximum 50 approved products per run")
    approved = []
    for entry in raw:
        product = ProductInput.model_validate(entry)
        parsed = urlparse(str(product.url))
        if (
            parsed.scheme != "https"
            or parsed.port not in (None, 443)
            or parsed.hostname not in allowed_hosts
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise InvalidProduct("All scheduled sources must use approved HTTPS hosts")
        approved.append(product)
    return approved


def execute() -> int:
    """One approved monitoring pass, with state committed before any outbound alert."""
    if os.environ.get("TRACKER_MONITOR_APPROVED") != "true":
        logger.info("Remote monitoring disabled; no HTTP requests were made")
        return 0

    repository = _required("TRACKER_STATE_REPO")
    source_repository = _required("GITHUB_REPOSITORY")
    token = _required("TRACKER_STATE_TOKEN")
    allowed_hosts = {
        host.strip().lower()
        for host in _required("TRACKER_ALLOWED_HOSTS").split(",")
        if host.strip()
    }
    if not allowed_hosts:
        raise ValueError("TRACKER_ALLOWED_HOSTS must not be empty")
    if repository.casefold() == source_repository.casefold():
        raise ValueError("State repository must not be the public source repository")
    if repository.count("/") != 1:
        raise ValueError("TRACKER_STATE_REPO must have form owner/repository")
    branch = os.environ.get("TRACKER_STATE_BRANCH") or "monitor-state"
    if not branch.replace("-", "").replace("_", "").isalnum():
        raise ValueError("Unsafe state branch name")
    products = _approved_products(allowed_hosts)

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    with httpx.Client(timeout=30, headers=headers) as client:
        metadata = _api(client, "GET", f"/repos/{repository}").json()
        if not metadata.get("private"):
            raise ValueError("Durable state repository must be private")
        _api(client, "GET", f"/repos/{repository}/branches/{branch}")
        previous_sha, database_bytes = _read_state(client, repository, branch)

        with tempfile.TemporaryDirectory(prefix="price-tracker-") as folder:
            database = Path(folder) / "state.sqlite3"
            if database_bytes is not None:
                database.write_bytes(database_bytes)
            settings = Settings.from_env()
            settings.database_path = database
            settings.allowed_hosts = frozenset(allowed_hosts)
            settings.require_https = True
            settings.max_products_per_run = len(products)
            store = Store(database)
            try:
                # Revocation and configuration changes take effect on every run.
                store.sync_approved_products(products)
                results = check_many(store, settings, notify=False)
                failed = sum(result.status != "ok" for result in results)
                new_alerts = [alert for result in results for alert in result.alerts]
                logger.info(
                    "Checked=%s failed=%s new_alerts=%s",
                    len(results),
                    failed,
                    len(new_alerts),
                )
            finally:
                store.close()

            state_bytes = database.read_bytes()
            if len(state_bytes) > MAX_STATE_BYTES:
                raise ValueError("SQLite state exceeds maximum supported size")
            payload: dict[str, str] = {
                "message": "chore(state): persist monitored prices",
                "content": base64.b64encode(state_bytes).decode("ascii"),
                "branch": branch,
            }
            if previous_sha:
                payload["sha"] = previous_sha
            # A failed PUT (including conflict) MUST prevent outgoing SMTP alerts.
            _api(client, "PUT", f"/repos/{repository}/contents/{STATE_PATH}", json=payload)
            logger.info("SQLite state committed to the separate private repository")

            # State and alert deduplication records are durable before SMTP starts.
            if new_alerts:
                try:
                    send_email(new_alerts)
                except (OSError, ValueError, smtplib.SMTPException) as exc:
                    logger.error("SMTP delivery failed after state commit: %s", type(exc).__name__)
                    return 1
            return 1 if failed else 0


def main() -> None:
    setup_logging()
    try:
        raise SystemExit(execute())
    except (httpx.HTTPError, ValueError, ValidationError, InvalidProduct) as exc:
        logger.error("Controlled monitoring aborted: %s", type(exc).__name__)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
