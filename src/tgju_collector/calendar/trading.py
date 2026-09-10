# -*- coding: utf-8 -*-
"""Iranian market trading calendar.

Tehran markets typically close on Fridays. Official holidays are maintained
as a static set of ISO dates; extend ``DEFAULT_HOLIDAYS`` when new holidays
are announced. The calendar is intentionally simple and offline-friendly so
gap detection never depends on a remote holiday API.

Examples:
    >>> from datetime import date
    >>> cal = MarketCalendar()
    >>> cal.is_trading_day(date(2026, 2, 13))  # Friday
    False
    >>> cal.is_trading_day(date(2026, 2, 11))
    True
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

# Friday is weekday 4 under Python's Monday=0 convention.
FRIDAY_WEEKDAY = 4

# Fixed / well-known Iranian holidays (ISO). Extend as needed.
# Sources: official calendar announcements; subset covering 2025-2027.
DEFAULT_HOLIDAYS: frozenset[date] = frozenset(
    {
        # 2025
        date(2025, 2, 11),  # 22 Bahman
        date(2025, 3, 20),  # Oil Nationalization
        date(2025, 3, 21),  # Norouz
        date(2025, 3, 22),
        date(2025, 3, 23),
        date(2025, 3, 24),
        date(2025, 4, 1),  # Islamic Republic Day
        date(2025, 4, 2),  # Sizdah Bedar
        date(2025, 6, 4),  # Demise of Imam Khomeini
        date(2025, 6, 5),  # Khordad National Uprising
        date(2025, 6, 25),  # Eid Fetr (approx)
        date(2025, 6, 26),
        date(2025, 7, 5),  # Ashura (approx)
        date(2025, 7, 6),
        date(2025, 9, 5),  # Arbaeen (approx)
        date(2025, 9, 14),  # Prophet passing (approx)
        date(2025, 11, 25),  # Martyrdom Imam Reza (approx)
        # 2026
        date(2026, 2, 11),  # 22 Bahman
        date(2026, 3, 20),  # Oil Nationalization
        date(2026, 3, 21),  # Norouz
        date(2026, 3, 22),
        date(2026, 3, 23),
        date(2026, 3, 24),
        date(2026, 4, 1),  # Islamic Republic Day
        date(2026, 4, 2),  # Sizdah Bedar
        date(2026, 6, 4),  # Demise of Imam Khomeini
        date(2026, 6, 5),  # Khordad National Uprising
        date(2026, 6, 15),  # Eid Fetr (approx)
        date(2026, 6, 16),
        date(2026, 6, 24),  # Ashura (approx)
        date(2026, 6, 25),
        date(2026, 8, 26),  # Arbaeen (approx)
        date(2026, 9, 4),  # Prophet passing (approx)
        date(2026, 11, 15),  # Martyrdom Imam Reza (approx)
        # 2027
        date(2027, 2, 11),
        date(2027, 3, 20),
        date(2027, 3, 21),
        date(2027, 3, 22),
        date(2027, 3, 23),
        date(2027, 3, 24),
        date(2027, 4, 1),
        date(2027, 4, 2),
    }
)


class MarketCalendar:
    """Trading-day calendar for Iranian markets.

    Args:
        holidays: Extra non-Friday holidays to treat as closed.
        extra_closed: Additional ad-hoc closed dates (maintenance, etc.).
    """

    def __init__(
        self,
        *,
        holidays: Iterable[date] | None = None,
        extra_closed: Iterable[date] | None = None,
    ) -> None:
        closed = set(DEFAULT_HOLIDAYS)
        if holidays:
            closed.update(holidays)
        if extra_closed:
            closed.update(extra_closed)
        self._closed = closed

    def is_friday(self, day: date) -> bool:
        """Return True when ``day`` falls on a Friday.

        Args:
            day: Calendar date.

        Returns:
            bool: True if Friday.
        """
        return day.weekday() == FRIDAY_WEEKDAY

    def is_holiday(self, day: date) -> bool:
        """Return True when ``day`` is a known official holiday.

        Args:
            day: Calendar date.

        Returns:
            bool: True if in the holiday set.
        """
        return day in self._closed

    def is_trading_day(self, day: date) -> bool:
        """Return True when the market is expected to trade.

        Args:
            day: Calendar date.

        Returns:
            bool: True for trading days (not Friday, not holiday).
        """
        return not self.is_friday(day) and not self.is_holiday(day)

    def trading_days(self, start: date, end: date) -> list[date]:
        """List trading days in ``[start, end]`` inclusive.

        Args:
            start: Inclusive start date.
            end: Inclusive end date.

        Returns:
            list[date]: Ordered trading days.
        """
        if end < start:
            return []
        days: list[date] = []
        current = start
        while current <= end:
            if self.is_trading_day(current):
                days.append(current)
            current += timedelta(days=1)
        return days

    def missing_trading_days(self, start: date, end: date, existing: Iterable[str]) -> list[date]:
        """Return trading days in range that are absent from ``existing``.

        Args:
            start: Inclusive start date.
            end: Inclusive end date.
            existing: ISO date strings already stored.

        Returns:
            list[date]: Missing trading days, ordered ascending.
        """
        present = set(existing)
        return [
            day
            for day in self.trading_days(start, end)
            if day.isoformat() not in present
        ]
