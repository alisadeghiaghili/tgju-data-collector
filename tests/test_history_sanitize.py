# -*- coding: utf-8 -*-
"""Tests for inverted OHLC sanitization in history parsing."""

from __future__ import annotations

from tgju_collector.clients.history import parse_history_payload


def test_swaps_inverted_low_high() -> None:
    payload = {
        "s": "ok",
        "t": [1770585600],
        "o": [100.0],
        "h": [90.0],  # inverted
        "l": [110.0],
        "c": [105.0],
    }
    bars = parse_history_payload(symbol="sekee", payload=payload)
    assert len(bars) == 1
    assert bars[0].low == 90.0
    assert bars[0].high == 110.0
