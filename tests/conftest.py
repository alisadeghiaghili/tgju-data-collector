# -*- coding: utf-8 -*-
"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from tgju_collector.storage.schema import create_all

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def fixtures_dir() -> Path:
    """Directory containing HTML/JSON fixtures."""
    return FIXTURES


@pytest.fixture()
def memory_engine():
    """In-memory SQLite engine with schema created."""
    engine = create_engine("sqlite:///:memory:", future=True)
    create_all(engine)
    return engine


@pytest.fixture()
def sample_home_html() -> str:
    """Minimal homepage-like HTML with market rows."""
    return """
    <html><body>
    <table class="market-table">
      <tr data-market-row="sekee">
        <th>سکه امامی</th>
        <td>2,410,100,000</td>
        <td>1.25%</td>
        <td>2,400,000,000</td>
        <td>2,420,000,000</td>
        <td>2,390,000,000</td>
        <td>12:00:00</td>
      </tr>
      <tr data-market-row="price_dollar_rl">
        <th>دلار</th>
        <td>72,350</td>
        <td>-0.5%</td>
        <td>72,500</td>
        <td>72,600</td>
        <td>72,200</td>
        <td>12:00:00</td>
      </tr>
      <tr data-market-row="crypto-bitcoin">
        <th>بیت کوین</th>
        <td>77,026.63</td>
        <td>2.1%</td>
        <td>75,000</td>
        <td>78,000</td>
        <td>74,500</td>
        <td>12:00:00</td>
      </tr>
      <tr data-market-row="oil_brent">
        <th>نفت برنت</th>
        <td>104.761</td>
        <td>3.88%</td>
        <td>100.291</td>
        <td>105.741</td>
        <td>100.0</td>
        <td>12:00:00</td>
      </tr>
    </table>
    </body></html>
    """


@pytest.fixture()
def sample_history_payload() -> dict:
    """TradingView-style daily history payload."""
    # 2026-02-08, 2026-02-09, 2026-02-10 in UTC-ish unix seconds
    return {
        "s": "ok",
        "t": [1770585600, 1770672000, 1770758400],
        "o": [100.0, 101.0, 102.0],
        "h": [110.0, 111.0, 112.0],
        "l": [95.0, 96.0, 97.0],
        "c": [108.0, 109.0, 110.0],
        "v": [1.0, 2.0, 3.0],
    }


@pytest.fixture()
def fixed_now() -> datetime:
    """Fixed UTC timestamp for deterministic assertions."""
    return datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def sample_date() -> date:
    """Fixed calendar date."""
    return date(2026, 2, 10)
