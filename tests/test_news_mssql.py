# -*- coding: utf-8 -*-
"""Tests for news collector and mssql helpers."""

from __future__ import annotations

from datetime import datetime

from tgju_collector.collectors.news import NewsCollector, _parse_timestamp
from tgju_collector.storage.mssql import engine_kwargs_for_url, is_mssql_url


class FakeHttp:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def get_json(self, url: str, *, params: dict | None = None):
        return self.payload


def test_news_collector_parses_items() -> None:
    payload = {
        "response": {
            "news": [
                {"id": 1, "title": "خبر اول", "category": "قیمت", "url": "https://x", "date": "2026-02-10 12:00:00"},
                {"id": 2, "title": "خبر دوم"},
            ]
        }
    }
    items = NewsCollector(FakeHttp(payload)).fetch(count=10)
    assert len(items) == 2
    assert items[0].news_id == "1"
    assert items[0].published_at == datetime(2026, 2, 10, 12, 0, 0)


def test_parse_timestamp_formats() -> None:
    assert _parse_timestamp("2026-02-10") == datetime(2026, 2, 10)
    assert _parse_timestamp(1770758400) is not None
    assert _parse_timestamp(None) is None
    assert _parse_timestamp("not-a-date") is None


def test_is_mssql_url() -> None:
    assert is_mssql_url("mssql+pyodbc://u:p@h/db")
    assert is_mssql_url("mssql+pytds://u:p@h/db")
    assert not is_mssql_url("sqlite:///x.db")
    assert not is_mssql_url("")


def test_engine_kwargs() -> None:
    assert engine_kwargs_for_url("sqlite:///x.db") == {"future": True}
    mssql = engine_kwargs_for_url("mssql+pyodbc://u:p@h/db")
    assert mssql["pool_pre_ping"] is True
    assert mssql["fast_executemany"] is True
