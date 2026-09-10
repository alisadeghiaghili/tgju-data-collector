# -*- coding: utf-8 -*-
"""Tests for HTML parsers."""

from __future__ import annotations

from tgju_collector.discovery.parsers import (
    parse_market_rows,
    parse_news_payload,
    parse_profile_links,
)


def test_parse_market_rows(sample_home_html: str) -> None:
    rows = parse_market_rows(sample_home_html)
    assert len(rows) == 4
    symbols = [r["symbol"] for r in rows]
    assert "sekee" in symbols
    assert "price_dollar_rl" in symbols
    assert rows[0]["label"] == "سکه امامی"


def test_parse_market_rows_empty() -> None:
    assert parse_market_rows("") == []
    assert parse_market_rows("   ") == []


def test_parse_market_rows_invalid_html() -> None:
    # lxml is tolerant; ensure no exception and empty-ish result
    rows = parse_market_rows("<html")
    assert isinstance(rows, list)


def test_parse_profile_links() -> None:
    html = """
    <a href="/profile/sekee">x</a>
    <a href="https://www.tgju.org/profile/price_dollar_rl">y</a>
    <a href="/profile/sekee">dup</a>
    """
    assert parse_profile_links(html) == ["price_dollar_rl", "sekee"]


def test_parse_news_payload() -> None:
    payload = {
        "response": {
            "news": [
                {"id": 10, "title": "خبر اول", "category": "قیمت‌ها", "url": "https://x", "lead": "خلاصه"},
                {"id": 11, "title": "خبر دوم"},
                {"id": 12},  # missing title → skipped
            ]
        }
    }
    items = parse_news_payload(payload)
    assert len(items) == 2
    assert items[0]["news_id"] == "10"
    assert items[0]["title"] == "خبر اول"


def test_parse_news_payload_empty() -> None:
    assert parse_news_payload({"response": {"news": []}}) == []
    assert parse_news_payload({}) == []
