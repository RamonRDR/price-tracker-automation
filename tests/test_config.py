from pathlib import Path

import pytest
from pydantic import ValidationError

from price_tracker.config import Settings


def test_settings_environment(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PRICE_TRACKER_DB", str(tmp_path / "test.db"))
    monkeypatch.setenv("PRICE_TRACKER_RETRIES", "3")
    settings = Settings.from_env()
    assert settings.database_path == tmp_path / "test.db"
    assert settings.max_retries == 3


def test_retry_boundaries() -> None:
    with pytest.raises(ValidationError):
        Settings(max_retries=12)
    with pytest.raises(ValidationError):
        Settings(timeout_seconds=0)
