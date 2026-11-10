<div align="center">

# Price Tracker Automation 🏷️

**Track prices responsibly. Follow every change. Get alerts with confidence.**

[🇺🇸 English](README.md) · [🇧🇷 Português](README.pt-BR.md) · [🇪🇸 Español](README.es.md)

[![CI](https://github.com/RamonRDR/price-tracker-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/RamonRDR/price-tracker-automation/actions/workflows/ci.yml)
[![Python 3.14](https://img.shields.io/badge/Python-3.14-blue)](https://www.python.org/)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063)](https://docs.pydantic.dev/latest/)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-2EAD33)](https://playwright.dev/python/)
[![httpx](https://img.shields.io/badge/httpx-HTTP-4C78A8)](https://www.python-httpx.org/)
[![SQLite](https://img.shields.io/badge/SQLite-history-003B57)](https://www.sqlite.org/)
[![SQLAlchemy 2](https://img.shields.io/badge/SQLAlchemy-2-D71F00)](https://www.sqlalchemy.org/)
[![Typer](https://img.shields.io/badge/Typer-CLI-007C6C)](https://typer.tiangolo.com/)
[![Rich](https://img.shields.io/badge/Rich-terminal-6C63FF)](https://rich.readthedocs.io/en/stable/)
[![hatchling](https://img.shields.io/badge/hatchling-packaging-663399)](https://hatch.pypa.io/latest/)

[![pytest](https://img.shields.io/badge/pytest-62%20passing-0A9EDC)](https://github.com/RamonRDR/price-tracker-automation/actions/runs/42732629484)
[![Chromium tests](https://img.shields.io/badge/Chromium-5%20passing-4A90E2)](https://github.com/RamonRDR/price-tracker-automation/actions/runs/42732629484)
[![Ruff](https://img.shields.io/badge/Ruff-lint%20%26%20format-D7FF64)](https://docs.astral.sh/ruff/)
[![Build](https://img.shields.io/badge/Build-wheel%20%2B%20sdist-passing-555555)](https://github.com/RamonRDR/price-tracker-automation/actions/runs/42732629484)

</div>

> **Project status:** Core MVP integrated into `main` after the resolved Codex review in [PR #1](https://github.com/RamonRDR/price-tracker-automation/pull/1). The CI run used for the test badge passed **57 unit/local HTTP tests + 5 controlled Chromium tests = 62 passing**. External scheduled monitoring remains disabled; optional SMTP delivery is not validated against a live mail server by CI.

A responsible, testable price-tracking CLI built with Python 3.14, Playwright, HTTP adapters, and SQLite. Designed as a practical portfolio project for **Python, Backend, Automation, and QA Automation** roles.

> **Responsible use:** Monitor only public demonstration pages or sources that explicitly allow automated access. This project does not bypass authentication, CAPTCHAs, rate limits, or access restrictions. The examples below use fictional URLs or a local test fixture.

## 1. What it does

Price Tracker Automation registers a product URL, extracts its name and current price, stores timestamped observations, compares consecutive prices, and creates alerts when a configured threshold is met.

**Highlights**

- Two configurable extraction adapters: **JSON-LD over httpx** and **CSS selectors through Playwright Chromium**.
- Persistent **SQLite / SQLAlchemy** product, price-history, and alert records.
- Monetary operations with **Decimal**, including increases and decreases.
- Target-price alerts and percentage-drop alerts, with transition-based deduplication.
- Multi-product monitoring with bounded retries, delays, and optional SMTP alerts.
- Typer CLI with Rich tables, history inspection, pause/resume, and CSV export.
- GitHub Actions quality checks on hosted runners; no live scraping in PR tests.
- A separate, explicitly opt-in manual monitoring workflow with private durable storage.

## 2. Technology stack

| Area | Tools |
| --- | --- |
| Runtime and validation | Python 3.14, Pydantic |
| Extraction | httpx, Playwright (Chromium), HTML JSON-LD |
| Persistence | SQLite, SQLAlchemy 2 |
| Interface and output | Typer, Rich, CSV |
| Notifications | Python SMTP with STARTTLS (optional) |
| Testing and quality | pytest, pytest-playwright, Ruff |
| Packaging and CI | hatchling, Python build, GitHub Actions |

**Version accuracy:** Python 3.14 is used by CI; Pydantic is declared as `>=2.12,<3` and SQLAlchemy as `>=2.0.40,<3`, so the badges identify their **major versions**, not an invented exact installation. Other dependencies are constrained by ranges in `pyproject.toml`.

## 3. Architecture

~~~text
User → Typer CLI → Monitoring service → Extraction adapter
                   │                      ├── JSON-LD / httpx
                   │                      └── CSS / Playwright
                   ├── Pydantic quote validation
                   ├── SQLAlchemy → SQLite
                   │               ├── products
                   │               ├── price_observations
                   │               └── alert_events
                   └── Alert handling → console / optional SMTP
~~~

| File | Responsibility |
| --- | --- |
| `config.py`, `schemas.py` | Environment settings, URLs, product and quote validation |
| `extractors.py` | HTTP JSON-LD and browser CSS extraction |
| `models.py`, `storage.py` | SQLite entities, queries, transactions, alert creation |
| `money.py` | Decimal monetary parsing and formatting |
| `monitor.py` | Bounded retries, comparisons, monitoring results |
| `notifications.py` | Optional SMTP digest for new alerts |
| `cli.py`, `exporter.py` | CLI commands, tables, safe CSV output |
| `github_runner.py` | Approved Actions monitoring with a private state repository |

Each successful check records an observation and creates any new alert events in the same database transaction. Design rationale: [ADR-0001](docs/adr/0001-controlled-monitoring.md).

## 4. Installation

**Requirements:** Python **3.14**, Git, and Chromium installed through Playwright for the CSS adapter. SQLite requires no separate server.

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

The application code is already on `main` ([PR #1](https://github.com/RamonRDR/price-tracker-automation/pull/1)); no feature branch checkout is needed.

## 5. Quick start: an actual, controlled local demo

The repository includes fictional product HTML in `tests/fixtures/product.html`. You can verify the complete JSON-LD → database → CLI path without accessing a commercial website.

**Terminal A** (start the local fixture server):

~~~bash
python -m http.server 8765 --bind 127.0.0.1 --directory tests/fixtures
~~~

**Terminal B** (with the environment activated):

~~~bash
price-tracker add "http://127.0.0.1:8765/product.html" --target 1300 --drop-percent 10
price-tracker check 1
price-tracker products
price-tracker history 1
price-tracker alerts --product-id 1
price-tracker export --output price-history.csv
~~~

The fixture contains a fictional **Demo Widget** priced at **USD 1,234.56**. The first successful check stores an observation and meets the sample USD 1,300 target. To reset the example, use a separate database via `--db ./demo-prices.db` with each command. This local demo is distinct from the GitHub Actions tests and never targets a real retailer.

## 6. CLI reference

| Command | Purpose |
| --- | --- |
| `price-tracker add URL` | Register an HTTP(S) product URL; no fetch on registration |
| `price-tracker products` | List tracked products and their settings |
| `price-tracker check [ID]` | Check one product or all active products |
| `price-tracker monitor` | Perform one or more bounded monitoring passes |
| `price-tracker history ID` | View stored observations |
| `price-tracker alerts` | Review recorded alert events |
| `price-tracker target ID AMOUNT` | Set a target-price threshold |
| `price-tracker drop-alert ID PERCENT` | Set a percentage-drop threshold |
| `price-tracker pause ID` / `resume ID` | Disable / enable a product |
| `price-tracker export --output FILE` | Export recorded price history to CSV |

For a permitted page with explicit selectors:

~~~bash
price-tracker add "https://demo.example.org/item" \
  --adapter css \
  --name-selector "h1.product-name" \
  --price-selector ".current-price" \
  --currency USD
price-tracker check 2
~~~

`demo.example.org` is an **illustrative, fictional source**, not an endorsed website or a working retailer. Consult `price-tracker --help` and each command's `--help` for options.

## 7. Configuration and security

Configuration is read from environment variables. See [`.env.example`](.env.example); local `.env` files are not loaded automatically and must not be committed.

| Variable | Default | Use |
| --- | --- | --- |
| `PRICE_TRACKER_DB` | `~/.local/share/price-tracker/prices.db` | SQLite database location, or pass `--db` |
| `PRICE_TRACKER_TIMEOUT` | `15` | HTTP / browser timeout (seconds) |
| `PRICE_TRACKER_RETRIES` | `2` | Additional source attempts; max 4 |
| `PRICE_TRACKER_RETRY_DELAY` | `0.5` | Initial retry backoff (seconds) |
| `PRICE_TRACKER_DELAY` | `1` | Gap between checked products (seconds) |
| `PRICE_TRACKER_MAX_PRODUCTS` | `50` | Maximum active products checked per pass |
| `PRICE_TRACKER_SMTP_HOST` | Unset | Optional SMTP hostname |
| `PRICE_TRACKER_SMTP_PORT` | `587` if used | STARTTLS SMTP port |
| `PRICE_TRACKER_SMTP_FROM` / `_TO` | Unset | Sender and recipient |
| `PRICE_TRACKER_SMTP_USERNAME` / `_PASSWORD` | Unset | Optional credentials via environment only |

The CLI stores database state locally. The repository ignores private databases and environment files. Do not store credentials or personal product data in commits, logs, or public artifacts.

## 8. Monitoring and scheduling

~~~bash
# One pass over active products
price-tracker monitor

# Three passes separated by 60 minutes, then exit
price-tracker monitor --every-minutes 60 --runs 3

# One pass with optional SMTP delivery for newly recorded alerts
price-tracker check --notify
~~~

Monitoring is bounded, not an infinite loop: default one pass, maximum 100 passes. Source errors are reported and other products can still be checked. Use sensible frequencies and follow each site's stated automation policy.

## 9. Price history, comparisons, and alerts

Every successful check stores a timestamped price observation. `history` displays the newest records, and `export` writes a CSV with `product_id`, `name`, `price`, `currency`, and `checked_at`. Product names are escaped to reduce spreadsheet-formula injection risk.

- **Target price:** fires when the first observation is at/below the target, or a later observation crosses from above to at/below it. Repeated below-target checks do not generate repeated target alerts.
- **Percentage drop:** fires when the new price falls by at least the configured percentage relative to the **immediately previous** successful observation. This can trigger on separate qualifying drops.
- **Price increase:** visible as a positive percent change; it is not an independent alert type.
- **Currency change:** comparisons are rejected rather than comparing unrelated currencies.
- **Email:** only attempted with `--notify` and working SMTP settings. Alerts are committed before email delivery, and failed deliveries are **not automatically resent**.

## 10. Tests and code quality

**Verified test results:** [GitHub Actions run #42732629484](https://github.com/RamonRDR/price-tracker-automation/actions/runs/42732629484) reported **57 passed, 5 deselected** for `pytest -m "not browser"` and **5 passed, 57 deselected** for `pytest -m browser`. Across both non-overlapping suites, **62 passed, 0 failed, 0 skipped**; the deselections are tests handled in the other job, not skipped tests. Ruff lint/format and wheel/sdist builds also passed.

**Badge maintenance:** the `pytest | 62 passing` badge is a **static snapshot of that successful run**, not a live test counter. When tests change, check both CI jobs on the new commit and update the badge count only after a new green run. No workflow auto-commits badge changes to `main`.

~~~bash
python -m pytest -q -m "not browser"
python -m playwright install chromium
python -m pytest -q -m browser
ruff check .
ruff format --check .
python -m build
~~~

Tests use mocks and a loopback HTTP server with controlled HTML. They cover URL validation, extraction and layout changes, formats and unavailable prices, failures/timeouts, SQLite persistence, target and drop alerts, deduplication, CSV, and CLI behavior. No live retailer is required.

## 11. GitHub Actions

- **`.github/workflows/ci.yml`:** Ruff lint and format, Python 3.14 unit/local HTTP tests, controlled Playwright Chromium integration, and wheel/sdist build.
- **`.github/workflows/manual-monitor.yml`:** manual dispatch only, guarded by a repository variable and an explicit approval checkbox. **No scheduled trigger is enabled.**

Hosted runners are temporary. To retain price history **after separate owner approval**, manual monitoring requires an owner-created **private state repository** with branch `monitor-state` and a fine-grained token with Contents read/write only for that repository. Configure repository variables `TRACKER_MONITOR_APPROVED`, `TRACKER_STATE_REPO`, `TRACKER_STATE_BRANCH`, `TRACKER_ALLOWED_HOSTS`, plus encrypted secrets `TRACKER_STATE_TOKEN` and `TRACKER_PRODUCTS_JSON` (a JSON array of approved HTTPS sources). Optional SMTP secrets are independent.

The runner synchronizes the currently approved product list before checking any URL, deactivating previously stored sources that are no longer authorized. Playwright blocks unapproved subresources and redirects **before** following them; even redirects to an otherwise allowed URL are deliberately not followed. Chromium and its OS dependencies are installed in the monitoring job.

For durable state, the runner retrieves the complete SQLite file through GitHub's **Git Blob API** rather than inline Contents data (which can be absent above 1 MB), verifies its size and integrity, and rejects invalid or oversized databases (32 MiB limit) without overwriting history. It commits the new state **before** attempting SMTP delivery, preventing duplicate notifications if the upload fails. Failed SMTP messages are not automatically retried.

The runner refuses public state repositories and unapproved hosts, uses one bounded pass, and writes SQLite to the private repository rather than to this public project's `main` or public artifacts. This design requires owner setup; **external monitoring and recurring schedules are not activated by this repository**.

## 12. Known limitations

- Generic adapters depend on compatible JSON-LD or stable selectors on allowed pages. Browser redirects are intentionally blocked, including redirects to approved destinations.
- Ambiguous currency formatting may require a source-specific adapter.
- SQLite is suitable for small, serial monitoring, not distributed high-frequency scraping.
- Percentage drops use adjacent observations rather than the all-time high.
- Changing a target while an item is already below that target does not immediately generate a new target alert.
- SMTP is best-effort, without guaranteed delivery or an outbox.
- Persistent GitHub Actions monitoring requires a separately provisioned private state repository and explicit authorization.
- This project never provides CAPTCHA bypass, authentication handling, stealth automation, or workarounds for blocked sources.

## 13. Repository structure

~~~text
price-tracker-automation/
├── .github/workflows/        # CI and approval-gated manual monitoring
├── docs/adr/                 # Monitoring and permissions decision
├── examples/                 # Fictional product configuration
├── src/price_tracker/        # CLI, adapters, database, alerts, runner
├── tests/                    # Unit, loopback HTTP, Chromium integration
├── .env.example              # Environment variable examples
├── pyproject.toml            # Python dependencies and build configuration
├── README.md                 # Primary English guide
├── README.pt-BR.md           # Brazilian Portuguese guide
├── README.es.md              # Spanish guide
└── LICENSE                   # MIT
~~~

## 14. Contributing

To propose a change, work on a feature branch and open a pull request. Run the tests and Ruff checks in [section 10](#10-tests-and-code-quality) before submitting. Keep fixtures fictional or local, never commit credentials or personal price data, and do not enable automated external monitoring without the source owner's explicit approval.

## 15. License

Licensed under the [MIT License](LICENSE). Example sources and products are fictional unless explicitly identified as local fixtures.
