"""Human-friendly command line interface for monitored, consented sources."""

import logging
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from price_tracker.config import Settings
from price_tracker.errors import InvalidProduct, TrackerError
from price_tracker.exporter import export_csv
from price_tracker.logging_config import setup_logging
from price_tracker.money import money
from price_tracker.monitor import CheckResult, check_many
from price_tracker.schemas import ProductInput
from price_tracker.storage import Store

app = typer.Typer(
    help="Monitor permitted product pages; compare price history and trigger local/SMTP alerts.",
    no_args_is_help=True,
)
console = Console()
err_console = Console(stderr=True)
DbOption = Annotated[Path | None, typer.Option("--db", help="Override local SQLite database path.")]


def _db(path: Path | None) -> tuple[Store, Settings]:
    settings = Settings.from_env()
    if path is not None:
        settings.database_path = path.expanduser().absolute()
    return Store(settings.database_path), settings


def _decimal_input(raw: str, *, max_value: Decimal | None = None) -> Decimal:
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise InvalidProduct("Invalid decimal number") from exc
    if not value.is_finite() or value <= 0 or (max_value is not None and value > max_value):
        raise InvalidProduct("Value must be positive and within range")
    return value


def _fail(exc: Exception) -> None:
    err_console.print(f"[red]Error:[/red] {exc}")
    raise typer.Exit(code=2) from exc


def _render_results(results: list[CheckResult]) -> None:
    table = Table(title="Price checks")
    for column in ("ID", "Status", "Current price", "Change", "New alerts", "Note"):
        table.add_column(column)
    for result in results:
        quote = result.current
        delta = result.change_percent
        table.add_row(
            str(result.product_id),
            result.status,
            money(quote.price, quote.currency) if quote else "-",
            f"{delta:+.2f}%" if delta is not None else "-",
            str(len(result.alerts)),
            result.error or "",
        )
    console.print(table)
    console.print(
        f"Checked: {len(results)} | Success: {sum(r.status == 'ok' for r in results)} "
        f"| Failed: {sum(r.status in ('error', 'unavailable') for r in results)} "
        f"| Alerts: {sum(len(r.alerts) for r in results)}"
    )


@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", help="Enable diagnostic JSON logs.")) -> None:
    setup_logging(logging.DEBUG if verbose else logging.WARNING)


@app.command()
def add(
    url: str = typer.Argument(..., help="HTTP(S) URL of a publicly accessible, permitted page."),
    adapter: str = typer.Option("jsonld", help="jsonld (HTTP) or css (Playwright)."),
    name_selector: str | None = typer.Option(None, help="CSS selector for product name."),
    price_selector: str | None = typer.Option(None, help="CSS selector for price."),
    currency: str | None = typer.Option(None, help="Three-letter ISO currency."),
    target: str | None = typer.Option(None, help="Alert at or below target price."),
    drop_percent: str | None = typer.Option(None, help="Alert on per-check percentage drop."),
    db: DbOption = None,
) -> None:
    """Register a product without automatically fetching the page."""
    try:
        product_data = ProductInput(
            url=url,
            adapter=adapter,
            name_selector=name_selector,
            price_selector=price_selector,
            currency=currency,
            target=target,
            drop_percent=drop_percent,
        )
        store, _ = _db(db)
        try:
            product = store.add(product_data)
        finally:
            store.close()
        console.print(f"[green]Added[/green] product #{product.id}. Run 'check {product.id}'.")
    except (ValidationError, TrackerError, OSError) as exc:
        _fail(exc)


@app.command("products")
def products(db: DbOption = None) -> None:
    """Show all registered products, including inactive entries."""
    try:
        store, _ = _db(db)
        try:
            rows = store.list_products()
        finally:
            store.close()
        table = Table(title="Tracked products")
        for column in ("ID", "Name", "Adapter", "Currency", "Target", "Drop %", "Active"):
            table.add_column(column)
        for item in rows:
            table.add_row(
                str(item.id), item.name, item.adapter, item.currency or "-",
                str(item.target) if item.target is not None else "-",
                str(item.drop_percent) if item.drop_percent is not None else "-",
                "yes" if item.active else "no",
            )
        console.print(table)
    except (TrackerError, OSError) as exc:
        _fail(exc)


@app.command()
def check(
    product_id: int | None = typer.Argument(None, help="ID (omit to check active products)."),
    notify: bool = typer.Option(False, help="Also send SMTP notifications if configured."),
    db: DbOption = None,
) -> None:
    """Run one bounded monitoring pass; no background loop."""
    try:
        store, settings = _db(db)
        try:
            results = check_many(store, settings, product_id=product_id, notify=notify)
        finally:
            store.close()
        _render_results(results)
        if any(r.status in ("error", "unavailable") for r in results):
            raise typer.Exit(code=1)
    except (TrackerError, OSError, ValidationError) as exc:
        _fail(exc)


@app.command()
def monitor(
    every_minutes: int = typer.Option(60, min=1, max=1440, help="Frequency between passes."),
    runs: int = typer.Option(1, min=1, max=100, help="Bounded passes; default is one."),
    notify: bool = typer.Option(False, help="Use SMTP if configured."),
    db: DbOption = None,
) -> None:
    """Monitor multiple products at a configurable frequency, with a finite run limit."""
    try:
        store, settings = _db(db)
        any_failed = False
        try:
            for round_number in range(runs):
                if round_number:
                    time.sleep(every_minutes * 60)
                console.print(f"[bold]Monitoring pass {round_number + 1}/{runs}[/bold]")
                results = check_many(store, settings, notify=notify)
                _render_results(results)
                any_failed |= any(r.status in ("error", "unavailable") for r in results)
        finally:
            store.close()
        if any_failed:
            raise typer.Exit(code=1)
    except (TrackerError, OSError, ValidationError) as exc:
        _fail(exc)


@app.command()
def history(
    product_id: int = typer.Argument(..., min=1),
    limit: int = typer.Option(25, min=1, max=1000),
    db: DbOption = None,
) -> None:
    """Show newest stored observations for one product."""
    try:
        store, _ = _db(db)
        try:
            store.get(product_id)
            rows = store.history(product_id, limit=limit)
        finally:
            store.close()
        table = Table(title=f"History for product #{product_id}")
        for label in ("Checked at (UTC)", "Name", "Price"):
            table.add_column(label)
        for row in rows:
            table.add_row(row.checked_at.isoformat(), row.name, money(row.price, row.currency))
        console.print(table)
    except (TrackerError, OSError) as exc:
        _fail(exc)


@app.command()
def target(
    product_id: int = typer.Argument(..., min=1),
    amount: str = typer.Argument(...),
    db: DbOption = None,
) -> None:
    """Set a positive target price (same currency as the product)."""
    try:
        store, _ = _db(db)
        try:
            store.set_alerts(product_id, target=_decimal_input(amount))
        finally:
            store.close()
        console.print(f"Target for product #{product_id}: {_decimal_input(amount):.2f}")
    except (TrackerError, OSError) as exc:
        _fail(exc)


@app.command("drop-alert")
def drop_alert(
    product_id: int = typer.Argument(..., min=1),
    percent: str = typer.Argument(...),
    db: DbOption = None,
) -> None:
    """Configure percentage drop alert against the previous check."""
    try:
        store, _ = _db(db)
        try:
            store.set_alerts(product_id, drop_percent=_decimal_input(percent, max_value=Decimal(100)))
        finally:
            store.close()
        console.print(f"Drop alert for product #{product_id}: {percent}%")
    except (TrackerError, OSError) as exc:
        _fail(exc)


@app.command()
def pause(
    product_id: int = typer.Argument(..., min=1),
    db: DbOption = None,
) -> None:
    """Disable automatic checks for one product."""
    _active(product_id, False, db)


@app.command()
def resume(
    product_id: int = typer.Argument(..., min=1),
    db: DbOption = None,
) -> None:
    """Re-enable checks for one product."""
    _active(product_id, True, db)


def _active(product_id: int, active: bool, path: Path | None) -> None:
    try:
        store, _ = _db(path)
        try:
            store.set_active(product_id, active=active)
        finally:
            store.close()
        console.print(f"Product #{product_id}: {'active' if active else 'paused'}")
    except (TrackerError, OSError) as exc:
        _fail(exc)


@app.command("alerts")
def show_alerts(
    product_id: int | None = typer.Option(None, help="Filter by product ID."),
    limit: int = typer.Option(25, min=1, max=1000),
    db: DbOption = None,
) -> None:
    """Show persisted alert events."""
    try:
        store, _ = _db(db)
        try:
            rows = store.alerts(product_id, limit=limit)
        finally:
            store.close()
        table = Table(title="Alert history")
        for label in ("ID", "Product", "Kind", "Message", "Created (UTC)"):
            table.add_column(label)
        for row in rows:
            table.add_row(
                str(row.id), str(row.product_id), row.kind, row.message,
                row.created_at.isoformat(),
            )
        console.print(table)
    except (TrackerError, OSError) as exc:
        _fail(exc)


@app.command("export")
def export(
    output: Path = typer.Option(Path("price-history.csv"), "--output", "-o"),
    product_id: int | None = typer.Option(None, help="Optional product filter."),
    db: DbOption = None,
) -> None:
    """Export the stored historical observations to a CSV file."""
    try:
        store, _ = _db(db)
        try:
            if product_id is not None:
                store.get(product_id)
            count = export_csv(store, output, product_id=product_id)
        finally:
            store.close()
        console.print(f"Exported {count} observations to {output}.")
    except (TrackerError, OSError) as exc:
        _fail(exc)


if __name__ == "__main__":
    app()
