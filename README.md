# Price Tracker Automation

[![CI](https://github.com/RamonRDR/price-tracker-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/RamonRDR/price-tracker-automation/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.14-blue) ![License](https://img.shields.io/badge/License-MIT-green)

A responsible, adapter-based price-monitoring CLI. Demonstrates Python automation, Playwright browser testing, HTTP extraction, SQLite persistence, typed validation and GitHub Actions.

**Documentation:** English (main) | [Português](README.pt-BR.md) | [Español](README.es.md)

## 1. Goal

Track prices on public demonstration pages or sites **explicitly allowing automated access**. Compare past and current prices, and report meaningful changes. The tool never bypasses CAPTCHA, logins, rate limits or access controls. Verify permission before monitoring any URL.

## 2. Implemented features

- Register products by HTTP(S) URL with target and drop-percentage settings.
- JSON-LD / httpx adapter and configurable CSS / Playwright Chromium adapter.
- SQLAlchemy/SQLite products, immutable price observations and deduplicated alert events.
- Decimal money, increases/decreases, local console summary and CSV export.
- Bounded multi-product monitoring, limited retries and configurable frequency.
- Optional STARTTLS SMTP notifications; pause/resume commands.
- Python 3.14 quality gates, deterministic local HTTP and browser integration tests.
- An approval-gated manual Action with a separate private repository for durable state.

## 3. Technologies

Python 3.14, Playwright, httpx, SQLite, SQLAlchemy, Pydantic, Typer, Rich, pytest, pytest-playwright, Ruff, hatchling and GitHub Actions.

## 4. Architecture

| Module | Responsibility |
| --- | --- |
| `schemas.py`, `config.py` | Product/quote validation and settings |
| `extractors.py` | JSON-LD/httpx and Playwright/CSS adapters |
| `models.py`, `storage.py` | Products, historical observations and alert events |
| `monitor.py` | Bounded orchestrator, comparisons and retries |
| `notifications.py` | Optional SMTP alert digest |
| `exporter.py`, `cli.py` | CSV and Typer/Rich interface |
| `github_runner.py` | Approved remote monitoring with private durable state |

A successful check validates a quote, stores an observation, compares it with the previous one and records alerts within one transaction. See [ADR-0001](docs/adr/0001-controlled-monitoring.md).

## 5. Installation

Requires Python **3.14**.

~~~bash
git clone https://github.com/RamonRDR/price-tracker-automation.git
cd price-tracker-automation
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m playwright install chromium
price-tracker --help
~~~

No database service is required. Local SQLite defaults to `~/.local/share/price-tracker/prices.db`.

## 6. Command examples

**Fictional example URLs, not real commercial websites:**

~~~bash
price-tracker add "https://demo.example.org/widget" --target 80 --drop-percent 10
price-tracker products
price-tracker check 1
price-tracker history 1 --limit 20
price-tracker alerts --product-id 1
price-tracker target 1 75
price-tracker drop-alert 1 15
price-tracker export --output history.csv
price-tracker pause 1
price-tracker resume 1
~~~

For an authorized page requiring selectors:

~~~bash
price-tracker add "https://demo.example.org/item" \
  --adapter css --name-selector "h1.product-name" \
  --price-selector ".current-price" --currency USD
price-tracker check 2
~~~

Registration is offline; only `check` or `monitor` fetches pages.

## 7. Configuration

See [`.env.example`](.env.example). The app reads exported environment variables, but does not load `.env` automatically.

| Variable | Default | Meaning |
| --- | --- | --- |
| `PRICE_TRACKER_DB` | user data directory | SQLite file (or use `--db`) |
| `PRICE_TRACKER_TIMEOUT` | 15 | Request/browser timeout, seconds |
| `PRICE_TRACKER_RETRIES` | 2 | Additional attempts (max 4) |
| `PRICE_TRACKER_RETRY_DELAY` | 0.5 | Initial exponential backoff |
| `PRICE_TRACKER_DELAY` | 1 | Seconds between products |
| `PRICE_TRACKER_MAX_PRODUCTS` | 50 | Maximum products per pass |
| `PRICE_TRACKER_SMTP_*` | unset | Optional SMTP/STARTTLS configuration |

Passwords and tokens must only be supplied via environment or Actions secrets.

## 8. Monitoring example and frequency

~~~bash
price-tracker monitor
price-tracker monitor --every-minutes 60 --runs 3
price-tracker check --notify
~~~

The default is one pass. Even repeated monitoring has an explicit finite run limit. Product errors do not stop checking other products; the process returns nonzero when a check fails. Sources must permit automation and be polled at a reasonable rate.

## 9. History and alerts

`history` shows UTC timestamps, currency and Decimal amounts; `alerts` lists stored alert events; `export` creates CSV. Target alerts fire at the first price **at or below** the target and after a subsequent crossing from above. Percentage drops compare **adjacent observations**. Unchanged prices produce no repeat alerts. Alerts are committed before optional email delivery. SMTP failures are logged but email is **not automatically retried**.

## 10. Tests and packaging

~~~bash
python -m pytest -q -m "not browser"
python -m playwright install chromium
python -m pytest -q -m browser
ruff check .
ruff format --check .
python -m build
~~~

Tests use fake prices, mocks and a controlled loopback HTML server. No external commercial site is called by CI. Tests cover validation, HTTP failures/timeouts, layout changes, money, SQLite, change detection, alert deduplication, CSV and CLI.

## 11. GitHub Actions / durable state

`ci.yml` runs Ruff, Python 3.14 tests, Chromium tests on **local HTML only**, and wheel/sdist build. `manual-monitor.yml` is **manual-only and disabled unless explicitly approved**; there is **no active cron**. To enable later, the owner must:

1. Approve the sources and create a separate **private** GitHub repository with branch `monitor-state`.
2. Create a fine-grained token with Contents read/write **only** in that private state repository.
3. Set repository variables `TRACKER_MONITOR_APPROVED=true`, `TRACKER_STATE_REPO`, `TRACKER_STATE_BRANCH`, `TRACKER_ALLOWED_HOSTS`.
4. Set Actions secrets `TRACKER_STATE_TOKEN` and `TRACKER_PRODUCTS_JSON`, with approved HTTPS URLs. Optional SMTP secrets are separate.
5. Approve the checkbox when manually dispatching a run. Adding a `schedule` trigger requires **another explicit authorization**.

Example secret (fictional): `[{"url":"https://demo.example.org/widget","adapter":"jsonld"}]`. The runner checks that the state repository is private and distinct from this public one, downloads SQLite, runs one bounded pass and stores the updated SQLite via GitHub's Contents API and blob SHA conflict protection. No public artifact, no state commit on public `main`.

## 12. Known limitations

- Generic JSON-LD and CSS adapters require compatible metadata or selectors.
- Ambiguous number formats may require source-specific normalization.
- SQLite is designed for small/serial monitoring, not parallel distributed ingestion.
- Drop percentages compare the previous check, not the all-time peak.
- Changing a target while already below it does not immediately trigger an alert.
- SMTP delivery is best-effort; no transactional email outbox.
- Remote scheduling requires private-state setup and separate approval.
- No authentication, CAPTCHA bypass or avoidance of website restrictions.

## 13. License

[MIT](LICENSE). All examples are fictional. Use only with sites that allow your automation.
