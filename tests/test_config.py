# -*- coding: utf-8 -*-
"""Tests for configuration loading."""

from __future__ import annotations

import os
from pathlib import Path

from tgju_collector.config import Settings, _load_dotenv


def test_defaults(monkeypatch) -> None:
    for key in list(os.environ):
        if key.startswith("TGJU_"):
            monkeypatch.delenv(key, raising=False)
    settings = Settings.from_env(load_dotenv=False)
    assert settings.http_timeout == 30.0
    assert settings.http_max_retries == 3
    assert settings.request_delay_min >= 1.0
    assert "Mozilla" in settings.user_agent
    assert "tgju-collector" not in settings.user_agent
    assert settings.market_timezone == "Asia/Tehran"
    assert settings.database_url.startswith("sqlite")


def test_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("TGJU_HTTP_TIMEOUT", "12.5")
    monkeypatch.setenv("TGJU_DB_URL", "sqlite:///custom.db")
    monkeypatch.setenv("TGJU_LOG_LEVEL", "debug")
    settings = Settings.from_env(load_dotenv=False)
    assert settings.http_timeout == 12.5
    assert settings.database_url == "sqlite:///custom.db"
    assert settings.log_level == "DEBUG"


def test_load_dotenv(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("TGJU_TEST_ONLY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment\nTGJU_TEST_ONLY=hello\nTGJU_QUOTED='world'\n",
        encoding="utf-8",
    )
    _load_dotenv(env_file)
    assert os.environ["TGJU_TEST_ONLY"] == "hello"
    assert os.environ["TGJU_QUOTED"] == "world"


def test_load_dotenv_missing_file(tmp_path: Path) -> None:
    _load_dotenv(tmp_path / "nope.env")  # should not raise
