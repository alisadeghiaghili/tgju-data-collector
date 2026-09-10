# -*- coding: utf-8 -*-
"""Tests for None / dirty OHLC ticks from the history API."""

from __future__ import annotations

from datetime import date

from tgju_collector.clients.history import parse_history_payload


def test_skips_bar_when_close_is_none() -> None:
    payload = {
        "s": "ok",
        "t": [1770585600, 1770672000],
        "o": [1.0, 2.0],
        "h": [2.0, 3.0],
        "l": [0.5, 1.0],
        "c": [None, 2.5],
    }
    bars = parse_history_payload(symbol="x", payload=payload)
    assert len(bars) == 1
    assert bars[0].close == 2.5


def test_none_open_falls_back_to_close() -> None:
    payload = {
        "s": "ok",
        "t": [1770585600],
        "o": [None],
        "h": [None],
        "l": [None],
        "c": [10.0],
    }
    bars = parse_history_payload(symbol="x", payload=payload)
    assert len(bars) == 1
    assert bars[0].open == 10.0
    assert bars[0].high == 10.0
    assert bars[0].low == 10.0
    assert bars[0].close == 10.0


def test_clamps_open_close_into_range_after_swap() -> None:
    payload = {
        "s": "ok",
        "t": [1770585600],
        "o": [50.0],
        "h": [40.0],  # inverted
        "l": [60.0],
        "c": [55.0],
    }
    bars = parse_history_payload(symbol="x", payload=payload)
    assert len(bars) == 1
    bar = bars[0]
    assert bar.low <= bar.open <= bar.high
    assert bar.low <= bar.close <= bar.high
