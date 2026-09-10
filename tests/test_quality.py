# -*- coding: utf-8 -*-
"""Tests for data-quality checks."""

from __future__ import annotations

from tgju_collector.quality.checks import (
    check_price_bars,
    check_symbol_coverage,
    summarize_quality,
)


def test_check_price_bars_clean() -> None:
    rows = [
        {"symbol": "a", "trade_date": "2026-02-11", "open": 1, "high": 2, "low": 0.5, "close": 1.5},
        {"symbol": "a", "trade_date": "2026-02-12", "open": 1.5, "high": 2, "low": 1, "close": 1.8},
    ]
    report = check_price_bars(rows)
    assert report["total"] == 2
    assert report["ohlc_violations"] == 0
    assert report["null_close"] == 0
    assert report["duplicate_keys"] == 0


def test_check_price_bars_detects_violations() -> None:
    rows = [
        {"symbol": "a", "trade_date": "2026-02-11", "open": 1, "high": 0.5, "low": 2, "close": 1},
    ]
    report = check_price_bars(rows)
    assert report["ohlc_violations"] == 1


def test_check_price_bars_null_close() -> None:
    rows = [
        {"symbol": "a", "trade_date": "2026-02-11", "open": 1, "high": 2, "low": 1, "close": None},
    ]
    report = check_price_bars(rows)
    assert report["null_close"] == 1
    assert report["null_rate_close"] == 1.0


def test_check_price_bars_duplicates() -> None:
    row = {"symbol": "a", "trade_date": "2026-02-11", "open": 1, "high": 2, "low": 1, "close": 1.5}
    report = check_price_bars([row, dict(row)])
    assert report["duplicate_keys"] == 1


def test_coverage() -> None:
    report = check_symbol_coverage(["a", "b", "c"], ["a", "b", "z"])
    assert report["catalog_size"] == 3
    assert report["stored_size"] == 3
    assert report["missing_from_store"] == 1
    assert report["missing_sample"] == ["c"]
    assert report["orphans_in_store"] == 1


def test_summarize_quality_flags_issues() -> None:
    price = check_price_bars(
        [{"symbol": "a", "trade_date": "d", "open": 1, "high": 0, "low": 2, "close": 1}]
    )
    coverage = check_symbol_coverage(["a", "b"], ["a"])
    issues = summarize_quality(price, coverage)
    assert any("OHLC" in i for i in issues)
    assert any("catalog symbols" in i for i in issues)
