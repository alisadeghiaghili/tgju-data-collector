# -*- coding: utf-8 -*-
"""Date and timezone helpers for Iranian market data.

All market dates are interpreted in ``Asia/Tehran`` unless overridden.

Examples:
    >>> from datetime import datetime, timezone
    >>> ts = datetime(2026, 2, 10, 20, 30, tzinfo=timezone.utc).timestamp()
    >>> trade_date_from_unix(ts).isoformat()
    '2026-02-10'
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

DEFAULT_MARKET_TZ = "Asia/Tehran"


def market_tz(name: str = DEFAULT_MARKET_TZ) -> ZoneInfo:
    """Return a ZoneInfo for the market timezone.

    Args:
        name: IANA timezone name.

    Returns:
        ZoneInfo: Timezone object.
    """
    return ZoneInfo(name)


def trade_date_from_unix(
    timestamp: float | int,
    *,
    tz_name: str = DEFAULT_MARKET_TZ,
) -> date:
    """Convert a Unix timestamp to a market-local calendar date.

    Args:
        timestamp: Seconds since Unix epoch.
        tz_name: IANA timezone used for the conversion.

    Returns:
        date: Calendar date in the market timezone.
    """
    moment = datetime.fromtimestamp(float(timestamp), tz=market_tz(tz_name))
    return moment.date()


def persian_date(gregorian: date) -> str:
    """Convert a Gregorian date to Jalali ``YYYY-MM-DD`` string.

    Args:
        gregorian: Gregorian calendar date.

    Returns:
        str: Persian calendar date, zero-padded.

    Examples:
        >>> from datetime import date
        >>> persian_date(date(2026, 3, 21))
        '1405-01-01'
    """
    import jdatetime

    return jdatetime.date.fromgregorian(date=gregorian).strftime("%Y-%m-%d")


def date_range(start: date, end: date) -> list[date]:
    """Inclusive list of calendar dates from ``start`` to ``end``.

    Args:
        start: First date.
        end: Last date (inclusive). If before ``start``, returns empty list.

    Returns:
        list[date]: Ordered calendar dates.
    """
    if end < start:
        return []
    days = (end - start).days
    return [start + timedelta(days=i) for i in range(days + 1)]


def utc_now() -> datetime:
    """Return timezone-aware current UTC time.

    Returns:
        datetime: Current UTC datetime.
    """
    return datetime.now(tz=timezone.utc)


def to_unix(date_obj: date, *, end_of_day: bool = False, tz_name: str = DEFAULT_MARKET_TZ) -> int:
    """Convert a market-local calendar date to a Unix timestamp.

    Args:
        date_obj: Calendar date in market timezone.
        end_of_day: When True, use 23:59:59; otherwise 00:00:00.
        tz_name: IANA timezone name.

    Returns:
        int: Unix timestamp in seconds.
    """
    hour, minute, second = (23, 59, 59) if end_of_day else (0, 0, 0)
    moment = datetime(
        date_obj.year,
        date_obj.month,
        date_obj.day,
        hour,
        minute,
        second,
        tzinfo=market_tz(tz_name),
    )
    return int(moment.timestamp())
