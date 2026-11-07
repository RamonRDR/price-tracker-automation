import csv
from decimal import Decimal

from typer.testing import CliRunner

from price_tracker.cli import app
from price_tracker.exporter import export_csv
from price_tracker.schemas import PriceQuote, ProductInput

runner = CliRunner()


def test_cli_registration_list_target_pause_resume_and_export(tmp_path) -> None:
    database = tmp_path / "prices.db"
    opts = ["--db", str(database)]
    result = runner.invoke(app, ["add", "https://example.test/item", *opts])
    assert result.exit_code == 0, result.output
    assert "Added" in result.output
    assert runner.invoke(app, ["products", *opts]).exit_code == 0
    assert runner.invoke(app, ["target", "1", "90", *opts]).exit_code == 0
    assert runner.invoke(app, ["drop-alert", "1", "10", *opts]).exit_code == 0
    assert runner.invoke(app, ["pause", "1", *opts]).exit_code == 0
    assert runner.invoke(app, ["resume", "1", *opts]).exit_code == 0
    output = tmp_path / "history.csv"
    assert runner.invoke(app, ["export", "-o", str(output), *opts]).exit_code == 0
    assert output.read_text().startswith("product_id,name,price")
    assert runner.invoke(app, ["history", "1", *opts]).exit_code == 0
    assert runner.invoke(app, ["alerts", *opts]).exit_code == 0


def test_cli_invalid_product_url(tmp_path) -> None:
    result = runner.invoke(app, ["add", "javascript:alert(1)", "--db", str(tmp_path / "prices.db")])
    assert result.exit_code == 2


def test_csv_history_and_formula_safety(store, tmp_path) -> None:
    product = store.add(ProductInput(url="https://example.test/item"))
    store.save_check(
        product.id,
        PriceQuote(name="=HYPERLINK(1)", price=Decimal("15.75"), currency="USD"),
    )
    output = tmp_path / "folder" / "history.csv"
    assert export_csv(store, output) == 1
    with output.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 1
    assert rows[0]["name"] == "'=HYPERLINK(1)"
    assert rows[0]["price"] == "15.7500"
