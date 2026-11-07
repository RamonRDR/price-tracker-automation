"""Consistent CSV export with spreadsheet-formula injection protection."""

import csv
from pathlib import Path

from price_tracker.storage import Store

HEADERS = ["product_id", "name", "price", "currency", "checked_at"]


def _safe_cell(value: str) -> str:
    """Prevent remote product titles from being interpreted as spreadsheet formulas."""
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


def export_csv(
    store: Store, output: Path, *, product_id: int | None = None, limit: int = 100_000
) -> int:
    output = output.expanduser().absolute()
    output.parent.mkdir(parents=True, exist_ok=True)
    observations = store.history(product_id, limit=limit)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS)
        writer.writeheader()
        for entry in reversed(observations):
            writer.writerow(
                {
                    "product_id": entry.product_id,
                    "name": _safe_cell(entry.name),
                    "price": f"{entry.price:.4f}",
                    "currency": entry.currency,
                    "checked_at": entry.checked_at.isoformat(),
                }
            )
    return len(observations)
