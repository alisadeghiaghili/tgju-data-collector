# -*- coding: utf-8 -*-
"""Tests for history payload parsing."""

from __future__ import annotations

from datetime import date

import pytest

from tgju_collector.clients.history import HistoryClient, parse_history_payload


class FakeHttp:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[tuple[str, dict]] = []

    def get_json(self, url: str, *, params: dict | None = None):
        self.calls.append((url, params or {}))
        return self.payload


def test_parse_history_payload(sample_history_payload: dict) -> None:
    bars = parse_history_payload(symbol="sekee", payload=sample_history_payload)
    assert len(bars) == 3
    assert bars[0].open == 100.0
    assert bars[-1].close == 110.0
    assert bars[0].symbol == "sekee"


def test_parse_history_no_data() -> None:
    assert parse_history_payload(symbol="x", payload={"s": "no_data", "t": []}) == []
    assert parse_history_payload(symbol="x", payload={}) == []


def test_parse_history_inconsistent_lengths() -> None:
    payload = {"t": [1, 2], "o": [1], "h": [1, 2], "l": [1, 2], "c": [1, 2]}
    with pytest.raises(ValueError):
        parse_history_payload(symbol="x", payload=payload)


def test_history_client_builds_window(sample_history_payload: dict) -> None:
    http = FakeHttp(sample_history_payload)
    client = HistoryClient(http)
    bars = client.fetch_daily("sekee", start=date(2026, 2, 7), end=date(2026, 2, 12))
    assert len(bars) >= 1
    assert all(date(2026, 2, 7) <= b.trade_date <= date(2026, 2, 12) for b in bars)
    assert http.calls
    url, params = http.calls[0]
    assert "tvdata/history" in url
    assert params["symbol"] == "SEKEE"
    assert params["resolution"] == "1D"
    assert "from" in params and "to" in params


def test_history_client_requires_symbol(sample_history_payload: dict) -> None:
    client = HistoryClient(FakeHttp(sample_history_payload))
    with pytest.raises(ValueError):
        client.fetch_daily("")
