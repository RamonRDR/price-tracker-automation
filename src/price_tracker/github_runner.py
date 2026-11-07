"""Opt-in GitHub Actions bridge with state in a SEPARATE PRIVATE repository.

Never commit SQLite history, tracked URLs or credentials into this public source repository.
The private state branch and a fine-grained Contents token must be set up by the owner.
"""

import base64
import json
import logging
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import httpx
from pydantic import ValidationError

from price_tracker.config import Settings
from price_tracker.errors import InvalidProduct
from price_tracker.logging_config import setup_logging
from price_tracker.monitor import check_many
from price_tracker.schemas import ProductInput
from price_tracker.storage import Store

logger = logging.getLogger("price_tracker.github_runner")
STATE_PATH = "state/price-tracker.sqlite3"


def _required(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


def _api(client: httpx.Client, method: str, path: str, **kwargs: object) -> httpx.Response:
    response = client.request(method, "https://api.github.com" + path, **kwargs)
    response.raise_for_status()
    return response


def execute() -> int:
    """One pass only; requires explicit opt-in AND private durable state."""
    if os.environ.get("TRACKER_MONITOR_APPROVED") != "true":
        logger.info("Remote monitoring is disabled; no HTTP requests were made.")
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
        raise ValueError("State repository must not be this public source repository")
    if repository.count("/") != 1:
        raise ValueError("TRACKER_STATE_REPO must have form owner/repository")
    branch = os.environ.get("TRACKER_STATE_BRANCH") or "monitor-state"
    if not branch.replace("-", "").replace("_", "").isalnum():
        raise ValueError("Unsafe state branch name")

    raw_products = json.loads(_required("TRACKER_PRODUCTS_JSON"))
    if not isinstance(raw_products, list) or not raw_products:
        raise ValueError("TRACKER_PRODUCTS_JSON must be a non-empty JSON array")
    products: list[ProductInput] = []
    for entry in raw_products:
        product = ProductInput.model_validate(entry)
        parsed = urlparse(str(product.url))
        if (
            parsed.scheme != "https"
            or parsed.hostname not in allowed_hosts
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise InvalidProduct("All scheduled sources must use explicitly approved HTTPS hosts")
        products.append(product)
    if len(products) > 50:
        raise ValueError("Maximum 50 scheduled products per run")

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    with httpx.Client(timeout=30, headers=headers) as client:
        metadata = _api(client, "GET", f"/repos/{repository}").json()
        if not metadata.get("private"):
            raise ValueError("Durable state repository must be private")
        _api(client, "GET", f"/repos/{repository}/branches/{branch}")
        state_url = f"/repos/{repository}/contents/{STATE_PATH}"
        remote = client.get("https://api.github.com" + state_url, params={"ref": branch})
        if remote.status_code == 404:
            previous_sha = None
            database_bytes = None
        else:
            remote.raise_for_status()
            payload = remote.json()
            previous_sha = payload["sha"]
            database_bytes = base64.b64decode(payload["content"])
        with tempfile.TemporaryDirectory(prefix="price-tracker-") as folder:
            db_path = Path(folder) / "state.sqlite3"
            if database_bytes is not None:
                db_path.write_bytes(database_bytes)
            settings = Settings.from_env()
            settings.database_path = db_path
            store = Store(db_path)
            try:
                existing = {item.url for item in store.list_products()}
                for data in products:
                    if str(data.url) not in existing:
                        store.add(data)
                        existing.add(str(data.url))
                results = check_many(store, settings, notify=True)
                failed = sum(result.status != "ok" for result in results)
                logger.info(
                    "Checked=%s failed=%s new_alerts=%s",
                    len(results),
                    failed,
                    sum(len(result.alerts) for result in results),
                )
            finally:
                store.close()
            commit_payload = {
                "message": "chore(state): persist monitored prices",
                "content": base64.b64encode(db_path.read_bytes()).decode("ascii"),
                "branch": branch,
            }
            if previous_sha:
                commit_payload["sha"] = previous_sha
            # The remote content SHA provides optimistic concurrency protection.
            _api(client, "PUT", state_url, json=commit_payload)
            logger.info("State safely persisted in designated private repository")
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
