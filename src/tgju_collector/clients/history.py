# -*- coding: utf-8 -*-
"""TGJU chart/history API client.

Wraps ``platform.tgju.org`` TradingView-compatible endpoints.

Examples:
    >>> from tgju_collector.clients.history import HistoryClient
    >>> # client = HistoryClient(http)
    >>> # bars = client.fetch_daily("sekee", days=7)  # doctest: +SKIP
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from ..dates import to_unix, trade_date_from_unix, utc_now
from ..models import PriceBar

logger = logging.getLogger("tgju_collector.clients.history")

DEFAULT_HISTORY_URL = "https://platform.tgju.org/fa/tvdata/history"


class HistoryClient:
    """Fetch OHLCV history from the TGJU platform API.

    Args:
        http: HTTP client exposing ``get_json``.
        base_url: History endpoint URL.
    """

    def __init__(self, http: Any, *, base_url: str = DEFAULT_HISTORY_URL) -> None:
        self.http = http
        self.base_url = base_url

    def fetch_daily(
        self,
        symbol: str,
        *,
        start: date | None = None,
        end: date | None = None,
        days: int = 7,
    ) -> list[PriceBar]:
        """Fetch daily bars for a symbol.

        The window defaults to the last ``days`` calendar days ending today
        (market timezone). A multi-day window is intentional: a 24h window
        around ``resolution=1D`` can miss the last complete bar.

        Args:
            symbol: Market symbol id (uppercase as required by the API).
            start: Optional inclusive start date.
            end: Optional inclusive end date.
            days: Lookback window when start/end are omitted.

        Returns:
            list[PriceBar]: Bars sorted by trade date ascending.
        """
        if not symbol:
            raise ValueError("symbol is required")

        if end is None:
            end = date.today()
        if start is None:
            from datetime import timedelta

            start = end - timedelta(days=max(days, 1))

        payload = self.http.get_json(
            self.base_url,
            params={
                "symbol": symbol.upper(),
                "resolution": "1D",
                "from": to_unix(start),
                "to": to_unix(end, end_of_day=True),
            },
        )
        return parse_history_payload(symbol=symbol, payload=payload, scraped_at=utc_now())


def parse_history_payload(
    *,
    symbol: str,
    payload: dict[str, Any],
    scraped_at: datetime | None = None,
) -> list[PriceBar]:
    """Parse a TradingView-style history payload into ``PriceBar`` objects.

    Args:
        symbol: Symbol id to stamp on each bar.
        payload: JSON object with keys ``t``/``o``/``h``/``l``/``c``/``v``.
        scraped_at: Optional collection timestamp.

    Returns:
        list[PriceBar]: Parsed bars sorted by date.

    Raises:
        ValueError: If series lengths are inconsistent.
    """
    if not isinstance(payload, dict):
        return []
    if payload.get("s") == "no_data":
        return []

    times = payload.get("t") or []
    opens = payload.get("o") or []
    highs = payload.get("h") or []
    lows = payload.get("l") or []
    closes = payload.get("c") or []
    volumes = payload.get("v") or []

    if not times:
        return []

    n = len(times)
    for name, series in (
        ("o", opens),
        ("h", highs),
        ("l", lows),
        ("c", closes),
    ):
        if series and len(series) != n:
            raise ValueError(
                f"Inconsistent series length for {symbol}: t={n} {name}={len(series)}"
            )

    bars: list[PriceBar] = []
    for i, ts in enumerate(times):
        trade_date = trade_date_from_unix(ts)
        open_ = float(opens[i]) if opens else float(closes[i])
        high = float(highs[i]) if highs else open_
        low = float(lows[i]) if lows else open_
        close = float(closes[i])
        volume = float(volumes[i]) if volumes and i < len(volumes) else None
        bars.append(
            PriceBar(
                symbol=symbol,
                trade_date=trade_date,
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=volume,
                scraped_at=scraped_at,
            )
        )
    bars.sort(key=lambda b: b.trade_date)
    return bars
