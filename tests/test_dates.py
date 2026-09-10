# -*- coding: utf-8 -*-
"""Tests for date helpers."""

from __future__ import annotations

from datetime import date, datetime, timezone

from tgju_collector.dates import (
    date_range,
    persian_date,
    to_unix,
    trade_date_from_unix,
    utc_now,
)


def test_trade_date_from_unix_tehran() -> None:
    # 2026-02-10 20:30 UTC == 2026-02-11 00:00 Tehran (UTC+3:30)
    ts = datetime(2026, 2, 10, 20, 30, tzinfo=timezone.utc).timestamp()
    assert trade_date_from_unix(ts) == date(2026, 2, 11)


def test_trade_date_same_day_morning() -> None:
    ts = datetime(2026, 2, 10, 8, 0, tzinfo=timezone.utc).timestamp()
    assert trade_date_from_unix(ts) == date(2026, 2, 10)


def test_persian_date_nowruz() -> None:
    assert persian_date(date(2026, 3, 21)) == "1405-01-01"


def test_date_range_inclusive() -> None:
    days = date_range(date(2026, 2, 1), date(2026, 2, 3))
    assert days == [date(2026, 2, 1), date(2026, 2, 2), date(2026, 2, 3)]


def test_date_range_empty_when_inverted() -> None:
    assert date_range(date(2026, 2, 3), date(2026, 2, 1)) == []


def test_to_unix_roundtrip() -> None:
    d = date(2026, 2, 10)
    ts = to_unix(d)
    assert trade_date_from_unix(ts) == d


def test_utc_now_is_aware() -> None:
    now = utc_now()
    assert now.tzinfo is not None
