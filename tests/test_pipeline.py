# -*- coding: utf-8 -*-
"""Tests for gap detection and backfill helpers with trading calendar."""

from __future__ import annotations

from datetime import date, datetime

from tgju_collector.models import PriceBar
from tgju_collector.pipelines.sync import (
    _collapse_ranges,
    missing_dates_for_symbol,
    sync_news,
)
from tgju_collector.storage.repository import Repository


def test_missing_dates_skips_friday_and_holiday(memory_engine) -> None:
    repo = Repository(memory_engine)
    # Store Tue 2026-02-10 only.
    # Expected missing trading days: Thu 12, Sat 14
    # (Wed 11 = 22 Bahman holiday, Fri 13 = weekend)
    repo.upsert_price_bars(
        [
            PriceBar(
                symbol="sekee",
                trade_date=date(2026, 2, 10),
                open=1,
                high=2,
                low=1,
                close=1,
                scraped_at=datetime(2026, 2, 10),
            )
        ]
    )
    missing = missing_dates_for_symbol(
        memory_engine,
        "sekee",
        start=date(2026, 2, 10),
        end=date(2026, 2, 14),
    )
    assert missing == [date(2026, 2, 12), date(2026, 2, 14)]


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
            for d in (date(2026, 2, 10), date(2026, 2, 12))
        ]
    )
    assert (
        missing_dates_for_symbol(
            memory_engine, "usd", start=date(2026, 2, 10), end=date(2026, 2, 12)
        )
        == []
    )


def test_collapse_ranges() -> None:
    days = [
        date(2026, 2, 10),
        date(2026, 2, 12),
        date(2026, 2, 14),
        date(2026, 2, 15),
    ]
    ranges = _collapse_ranges(days)
    assert ranges == [
        (date(2026, 2, 10), date(2026, 2, 10)),
        (date(2026, 2, 12), date(2026, 2, 12)),
        (date(2026, 2, 14), date(2026, 2, 15)),
    ]
    assert _collapse_ranges([]) == []


def test_sync_news_persists(memory_engine) -> None:
    class FakeHttp:
        def get_json(self, url, *, params=None):
            return {
                "response": {
                    "news": [
                        {"id": 9, "title": "قیمت طلا بالا رفت", "category": "طلا"},
                    ]
                }
            }

    result = sync_news(FakeHttp(), memory_engine, count=5)
    assert result.news == 1
    from sqlalchemy import func, select

    from tgju_collector.storage import schema

    with memory_engine.connect() as conn:
        count = conn.execute(select(func.count()).select_from(schema.news_items)).scalar_one()
        assert count == 1
