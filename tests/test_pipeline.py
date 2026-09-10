# -*- coding: utf-8 -*-
"""Tests for gap detection and backfill helpers."""

from __future__ import annotations

from datetime import date, datetime

from tgju_collector.models import PriceBar
from tgju_collector.pipelines.sync import missing_dates_for_symbol
from tgju_collector.storage.repository import Repository


def test_missing_dates_detects_gaps(memory_engine) -> None:
    repo = Repository(memory_engine)
    repo.upsert_price_bars(
        [
            PriceBar(
                symbol="sekee",
                trade_date=date(2026, 2, 1),
                open=1,
                high=2,
                low=1,
                close=1,
                scraped_at=datetime(2026, 2, 1),
            ),
            PriceBar(
                symbol="sekee",
                trade_date=date(2026, 2, 4),
                open=1,
                high=2,
                low=1,
                close=1,
                scraped_at=datetime(2026, 2, 4),
            ),
        ]
    )
    missing = missing_dates_for_symbol(
        memory_engine,
        "sekee",
        start=date(2026, 2, 1),
        end=date(2026, 2, 5),
    )
    assert missing == [date(2026, 2, 2), date(2026, 2, 3), date(2026, 2, 5)]


def test_missing_dates_none_when_complete(memory_engine) -> None:
    repo = Repository(memory_engine)
    repo.upsert_price_bars(
        [
            PriceBar(
                symbol="usd",
                trade_date=d,
                open=1,
                high=2,
                low=1,
                close=1,
                scraped_at=datetime(2026, 2, d.day),
            )
            for d in (date(2026, 2, 1), date(2026, 2, 2))
        ]
    )
    assert missing_dates_for_symbol(
        memory_engine, "usd", start=date(2026, 2, 1), end=date(2026, 2, 2)
    ) == []
