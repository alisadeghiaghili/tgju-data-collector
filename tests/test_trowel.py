# -*- coding: utf-8 -*-
"""Tests for the trowel full-backfill pipeline."""

from __future__ import annotations

from datetime import date, datetime, timezone

from tgju_collector.models import PriceBar, Symbol
from tgju_collector.pipelines.sync import run_trowel
from tgju_collector.storage.repository import Repository


class FakeHistoryHttp:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_json(self, url, *, params=None):
        self.calls.append((params or {}).get("symbol", ""))
        # Return a small OHLCV payload covering a few days
        return {
            "s": "ok",
            "t": [
                int(datetime(2026, 9, 8, 12).timestamp()),
                int(datetime(2026, 9, 9, 12).timestamp()),
            ],
            "o": [1.0, 1.1],
            "h": [2.0, 2.1],
            "l": [0.5, 0.6],
            "c": [1.5, 1.6],
        }


def test_trowel_uses_catalog_and_skips_numeric(memory_engine) -> None:
    repo = Repository(memory_engine)
    repo.upsert_symbols(
        [
            Symbol(symbol="sekee"),
            Symbol(symbol="131398"),  # HTML row id → not history capable
        ]
    )
    http = FakeHistoryHttp()
    result = run_trowel(http, memory_engine, max_days=30, only_gaps=True)
    assert "SEKEE" in http.calls or "sekee" in {c.lower() for c in http.calls}
    assert "131398" not in http.calls
    assert result.bars >= 1


def test_trowel_only_gaps_skips_complete_symbol(memory_engine) -> None:
    repo = Repository(memory_engine)
    repo.upsert_symbols([Symbol(symbol="sekee")])
    # Pre-fill today so there is no gap in a 0-day window… use small window
    # and store a recent trading day.
    repo.upsert_price_bars(
        [
            PriceBar(
                symbol="sekee",
                trade_date=date.today(),
                open=1,
                high=2,
                low=0.5,
                close=1.5,
                scraped_at=datetime.now(timezone.utc),
            )
        ]
    )
    http = FakeHistoryHttp()
    result = run_trowel(http, memory_engine, max_days=0, only_gaps=True)
    # max_days=0 → start=end=today → already stored → no gap → no fetch
    assert http.calls == []
    assert result.bars == 0
