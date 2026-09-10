# -*- coding: utf-8 -*-
"""Tests for the Iranian trading calendar."""

from __future__ import annotations

from datetime import date

from tgju_collector.calendar.trading import MarketCalendar


def test_friday_is_closed() -> None:
    cal = MarketCalendar()
    # 2026-02-13 is a Friday
    assert date(2026, 2, 13).weekday() == 4
    assert cal.is_friday(date(2026, 2, 13))
    assert not cal.is_trading_day(date(2026, 2, 13))


def test_weekday_is_open() -> None:
    cal = MarketCalendar()
    # 2026-02-10 Tuesday, 2026-02-12 Thursday — not holidays
    assert cal.is_trading_day(date(2026, 2, 10))
    assert cal.is_trading_day(date(2026, 2, 12))


def test_norouz_holiday() -> None:
    cal = MarketCalendar()
    assert cal.is_holiday(date(2026, 3, 21))
    assert not cal.is_trading_day(date(2026, 3, 21))


def test_bahman_22_is_holiday() -> None:
    cal = MarketCalendar()
    assert cal.is_holiday(date(2026, 2, 11))
    assert not cal.is_trading_day(date(2026, 2, 11))


def test_trading_days_skips_friday_and_holiday() -> None:
    cal = MarketCalendar()
    # Tue 10 open, Wed 11 holiday, Thu 12 open, Fri 13 closed, Sat 14 open
    days = cal.trading_days(date(2026, 2, 10), date(2026, 2, 14))
    assert days == [date(2026, 2, 10), date(2026, 2, 12), date(2026, 2, 14)]


def test_missing_trading_days() -> None:
    cal = MarketCalendar()
    existing = ["2026-02-10"]
    missing = cal.missing_trading_days(date(2026, 2, 10), date(2026, 2, 14), existing)
    assert missing == [date(2026, 2, 12), date(2026, 2, 14)]


def test_extra_closed_dates() -> None:
    cal = MarketCalendar(extra_closed=[date(2026, 2, 12)])
    assert not cal.is_trading_day(date(2026, 2, 12))
