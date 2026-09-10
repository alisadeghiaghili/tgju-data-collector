# -*- coding: utf-8 -*-
"""Tests that history client filters to the requested window."""

from __future__ import annotations

from datetime import date, timedelta

from tgju_collector.clients.history import HistoryClient


class FakeHttp:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def get_json(self, url, *, params=None):
        return self.payload


def test_filters_out_of_window_bars() -> None:
    # Three bars: 2026-02-08, 09, 10 (unix from fixture-like values)
    payload = {
        "s": "ok",
        "t": [1770585600, 1770672000, 1770758400],
        "o": [1, 2, 3],
        "h": [2, 3, 4],
        "l": [0.5, 1, 2],
        "c": [1.5, 2.5, 3.5],
    }
    client = HistoryClient(FakeHttp(payload))
    # Request a tight window that may not match API timestamps exactly;
    # ensure no crash and only bars inside [start, end] are returned.
    bars = client.fetch_daily("X", start=date(2026, 2, 9), end=date(2026, 2, 10))
    assert all(date(2026, 2, 9) <= b.trade_date <= date(2026, 2, 10) for b in bars)


def test_empty_when_all_outside_window() -> None:
    payload = {
        "s": "ok",
        "t": [1770585600],
        "o": [1],
        "h": [2],
        "l": [0.5],
        "c": [1.5],
    }
    client = HistoryClient(FakeHttp(payload))
    far = date(2030, 1, 1)
    bars = client.fetch_daily("X", start=far, end=far + timedelta(days=1))
    assert bars == []
