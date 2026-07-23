# -*- coding: utf-8 -*-
"""Date conversion utilities for Persian (Jalali) and Gregorian calendars."""

import calendar
from datetime import datetime, date

import jdatetime


def to_persian_date(dt: datetime | date) -> str:
    """
    Convert Gregorian date to Persian (Jalali) date string.

    Args:
        dt: Gregorian date or datetime

    Returns:
        Persian date string in 'YYYY-MM-DD' format
    """
    if isinstance(dt, datetime):
        dt = dt.date()
    return str(jdatetime.date.fromgregorian(date=dt))


def to_weekday(dt: datetime | date) -> str:
    """
    Get English weekday name for a date.

    Args:
        dt: Date or datetime

    Returns:
        Weekday name (e.g., 'Monday', 'Tuesday')
    """
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime.combine(dt, datetime.min.time())
    return calendar.day_name[dt.weekday()]


def persian_to_gregorian(persian_str: str) -> date:
    """
    Convert Persian date string to Gregorian date.

    Args:
        persian_str: Persian date in 'YYYY-MM-DD' format

    Returns:
        Gregorian date object
    """
    parts = persian_str.split('-')
    jd = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
    return jd.togregorian()
