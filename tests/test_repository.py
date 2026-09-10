# -*- coding: utf-8 -*-
"""Tests for repository persistence."""

from __future__ import annotations

from datetime import date, datetime, timezone

from tgju_collector.models import (
    LiveSnapshot,
    NewsItem,
    PriceBar,
    ProductSection,
    Symbol,
    SymbolSource,
)
from tgju_collector.storage.repository import Repository


def test_upsert_symbols_and_list(memory_engine) -> None:
    repo = Repository(memory_engine)
    symbols = [
        Symbol(symbol="sekee", label_fa="سکه", product_section=ProductSection.GOLD_COIN),
        Symbol(symbol="price_dollar_rl", label_fa="دلار", product_section=ProductSection.CURRENCY),
    ]
    assert repo.upsert_symbols(symbols) == 2

    all_rows = repo.list_symbols()
    assert len(all_rows) == 2

    gold = repo.list_symbols(section="gold_coin")
    assert len(gold) == 1
    assert gold[0]["symbol"] == "sekee"

    # update label
    symbols[0] = Symbol(
        symbol="sekee",
        label_fa="سکه امامی",
        product_section=ProductSection.GOLD_COIN,
        source=SymbolSource.BOTH,
    )
    repo.upsert_symbols(symbols)
    rows = repo.list_symbols(section="gold_coin")
    assert rows[0]["label_fa"] == "سکه امامی"


def test_upsert_price_bars_idempotent(memory_engine) -> None:
    repo = Repository(memory_engine)
    bar = PriceBar(
        symbol="sekee",
        trade_date=date(2026, 2, 10),
        open=1.0,
        high=2.0,
        low=0.5,
        close=1.5,
        scraped_at=datetime(2026, 2, 10, 12, 0, 0),
    )
    assert repo.upsert_price_bars([bar]) == 1
    # second write updates, does not duplicate
    updated = PriceBar(
        symbol="sekee",
        trade_date=date(2026, 2, 10),
        open=1.0,
        high=3.0,
        low=0.5,
        close=2.5,
        scraped_at=datetime(2026, 2, 10, 13, 0, 0),
    )
    assert repo.upsert_price_bars([updated]) == 1

    dates = repo.existing_trade_dates("sekee")
    assert dates == {"2026-02-10"}

    from sqlalchemy import select

    from tgju_collector.storage import schema

    with memory_engine.connect() as conn:
        rows = list(conn.execute(select(schema.price_bars)).all())
        assert len(rows) == 1
        assert float(rows[0].close) == 2.5


def test_insert_live_snapshots_skips_duplicates(memory_engine) -> None:
    repo = Repository(memory_engine)
    moment = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)
    snap = LiveSnapshot(symbol="sekee", captured_at=moment, price=100.0)
    assert repo.insert_live_snapshots([snap]) == 1
    assert repo.insert_live_snapshots([snap]) == 0


def test_upsert_news(memory_engine) -> None:
    repo = Repository(memory_engine)
    item = NewsItem(news_id="10", title="خبر", category="قیمت")
    assert repo.upsert_news([item]) == 1
    updated = NewsItem(news_id="10", title="خبر به‌روز", category="قیمت")
    assert repo.upsert_news([updated]) == 1

    from sqlalchemy import select

    from tgju_collector.storage import schema

    with memory_engine.connect() as conn:
        rows = list(conn.execute(select(schema.news_items)).all())
        assert len(rows) == 1
        assert rows[0].title == "خبر به‌روز"
