# -*- coding: utf-8 -*-
"""Tests for domain models."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from tgju_collector.models import (
    LiveSnapshot,
    NewsItem,
    PriceBar,
    ProductSection,
    Symbol,
    SymbolSource,
)


class TestSymbol:
    def test_valid_symbol(self) -> None:
        symbol = Symbol(symbol="sekee", label_fa="سکه", product_section=ProductSection.GOLD_COIN)
        assert symbol.symbol == "sekee"
        assert symbol.product_section is ProductSection.GOLD_COIN

    def test_empty_symbol_rejected(self) -> None:
        with pytest.raises(ValueError):
            Symbol(symbol="  ")

    def test_to_record(self) -> None:
        symbol = Symbol(symbol="usd", source=SymbolSource.HTML)
        record = symbol.to_record()
        assert record["symbol"] == "usd"
        assert record["source"] == "html"


class TestPriceBar:
    def test_valid_bar(self) -> None:
        bar = PriceBar(
            symbol="sekee",
            trade_date=date(2026, 2, 10),
            open=1.0,
            high=2.0,
            low=0.5,
            close=1.5,
        )
        assert bar.key == ("sekee", "2026-02-10", "1D")

    def test_low_above_high_rejected(self) -> None:
        with pytest.raises(ValueError):
            PriceBar(
                symbol="sekee",
                trade_date=date(2026, 2, 10),
                open=1.0,
                high=0.5,
                low=2.0,
                close=1.0,
            )

    def test_to_record_has_iso_date(self) -> None:
        bar = PriceBar(
            symbol="sekee",
            trade_date=date(2026, 2, 10),
            open=1.0,
            high=2.0,
            low=0.5,
            close=1.5,
            scraped_at=datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc),
        )
        record = bar.to_record()
        assert record["trade_date"] == "2026-02-10"


class TestLiveSnapshot:
    def test_requires_symbol(self) -> None:
        with pytest.raises(ValueError):
            LiveSnapshot(symbol="", captured_at=datetime.now(tz=timezone.utc))


class TestNewsItem:
    def test_requires_id_and_title(self) -> None:
        with pytest.raises(ValueError):
            NewsItem(news_id="", title="x")
        with pytest.raises(ValueError):
            NewsItem(news_id="1", title="")
