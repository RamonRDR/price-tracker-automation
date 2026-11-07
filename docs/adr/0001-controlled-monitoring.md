# ADR-0001: Minimal adapters and controlled automation

**Status:** Accepted (2026-11-07)

## Context

A public portfolio project must demonstrate price automation without depending on a commercial page layout, scraping disallowed sources, exposing tracked URLs, or losing SQLite history between temporary GitHub runners.

## Decision

1. Use a small CLI with distinct extraction, validation, persistence, monitoring and notification layers.
2. Provide two explicit adapters: JSON-LD/httpx and CSS/Playwright. Do not circumvent CAPTCHA, authentication, rate limits or restrictions.
3. Use Decimal and SQLAlchemy Numeric for historical monetary values.
4. Record an alert only on a qualifying threshold crossing or adjacent-observation drop. Commit alerts and observations together with a deduplication key.
5. Bound retries, delays, total products and monitoring passes. CI uses local fixtures and never commercial sites.
6. Keep remote monitoring manual-only and approval-gated. No scheduled cron before owner authorization.
7. If approved, a **separate private GitHub state repository** and `monitor-state` branch store the durable SQLite bytes using a fine-grained token and GitHub Contents SHA conflict checks. Public source `main` and artifacts must not contain private data.

## Consequences

The design is small and interview-ready but does not provide high-scale parallel scraping or guaranteed SMTP delivery. It requires private-repository provisioning before remote monitoring. The repository owner controls sources, cadence, future Codex review and all merges.
