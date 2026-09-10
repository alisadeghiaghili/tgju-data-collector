# -*- coding: utf-8 -*-
"""Tests for export helpers."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from tgju_collector.export import export_price_bars, export_symbols
from tgju_collector.models import PriceBar, ProductSection, Symbol
from tgju_collector.storage.repository import Repository


def test_export_price_bars_csv(memory_engine, tmp_path) -> None:
    repo = Repository(memory_engine)
    repo.upsert_price_bars(
        [
            PriceBar(
                symbol="sekee",
                trade_date=date(2026, 2, 10),
                open=1,
                high=2,
                low=0.5,
                close=1.5,
                scraped_at=datetime(2026, 2, 10),
            )
        ]
    )
    out = tmp_path / "bars.csv"
    path = export_price_bars(memory_engine, out)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "sekee" in text
    assert "2026-02-10" in text


def test_export_price_bars_json(memory_engine, tmp_path) -> None:
    out = tmp_path / "bars.json"
    path = export_price_bars(memory_engine, out)
    assert path.read_text(encoding="utf-8") == "[]"


def test_export_unsupported_format(memory_engine, tmp_path) -> None:
    with pytest.raises(ValueError):
        export_price_bars(memory_engine, tmp_path / "bars.xlsx")


def test_export_symbols_filter_section(memory_engine, tmp_path) -> None:
    repo = Repository(memory_engine)
    repo.upsert_symbols(
        [
            Symbol(symbol="sekee", product_section=ProductSection.GOLD_COIN),
            Symbol(symbol="usd", product_section=ProductSection.CURRENCY),
        ]
    )
    out = tmp_path / "symbols.csv"
    export_symbols(memory_engine, out, section="gold_coin")
    text = out.read_text(encoding="utf-8")
    assert "sekee" in text
    assert "usd" not in text
