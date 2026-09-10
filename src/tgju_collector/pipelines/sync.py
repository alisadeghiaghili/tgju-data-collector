# -*- coding: utf-8 -*-
"""High-level sync pipelines used by the CLI.

Pipelines orchestrate discovery/collectors/storage. They do not parse HTML
or construct SQL themselves.

Examples:
    >>> from sqlalchemy import create_engine
    >>> from tgju_collector.storage import Repository, create_all
    >>> engine = create_engine("sqlite:///:memory:")
    >>> create_all(engine)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Sequence

from sqlalchemy.engine import Engine

from ..clients.history import HistoryClient
from ..collectors.live import LiveCollector
from ..dates import date_range
from ..discovery.catalog import CatalogBuilder
from ..models import PriceBar
from ..storage.repository import Repository

logger = logging.getLogger("tgju_collector.pipelines")


@dataclass(slots=True)
class SyncResult:
    """Outcome counters for a pipeline run.

    Attributes:
        symbols: Symbols processed or discovered.
        snapshots: Live snapshots written.
        bars: Price bars written.
        messages: Optional human-readable notes.
    """

    symbols: int = 0
    snapshots: int = 0
    bars: int = 0
    messages: list[str] = field(default_factory=list)


def sync_catalog(http: Any, engine: Engine, *, dry_run: bool = False) -> SyncResult:
    """Discover the multi-section symbol catalog and persist it.

    Args:
        http: HTTP client with ``get_text`` / ``get_json``.
        engine: SQLAlchemy engine.
        dry_run: When True, skip persistence.

    Returns:
        SyncResult: Counts of discovered symbols.
    """
    catalog = CatalogBuilder(http).build()
    result = SyncResult(symbols=len(catalog))
    result.messages.append(f"discovered {len(catalog)} symbols")
    if dry_run:
        return result
    repo = Repository(engine)
    repo.upsert_symbols(catalog)
    return result


def sync_live(http: Any, engine: Engine, *, pages: list[str] | None = None) -> SyncResult:
    """Capture live snapshots from section pages and persist them.

    Args:
        http: HTTP client with ``get_text``.
        engine: SQLAlchemy engine.
        pages: Optional page name filter.

    Returns:
        SyncResult: Snapshot counts.
    """
    snapshots = LiveCollector(http).collect(page_names=pages)
    repo = Repository(engine)
    inserted = repo.insert_live_snapshots(snapshots)
    result = SyncResult(snapshots=inserted)
    result.messages.append(f"captured {len(snapshots)}, inserted {inserted}")
    return result


def sync_history(
    http: Any,
    engine: Engine,
    *,
    symbols: Sequence[str],
    days: int = 7,
) -> SyncResult:
    """Fetch and upsert daily OHLCV bars for the given symbols.

    Args:
        http: HTTP client with ``get_json``.
        engine: SQLAlchemy engine.
        symbols: Symbol ids to fetch.
        days: Lookback window in calendar days.

    Returns:
        SyncResult: Bar counts.
    """
    client = HistoryClient(http)
    repo = Repository(engine)
    total = 0
    for symbol in symbols:
        try:
            bars = client.fetch_daily(symbol, days=days)
        except Exception as exc:
            logger.warning("history failed for %s: %s", symbol, exc)
            continue
        total += repo.upsert_price_bars(bars)
    return SyncResult(bars=total, messages=[f"upserted {total} bars"])


def missing_dates_for_symbol(
    engine: Engine,
    symbol: str,
    *,
    start: date,
    end: date,
) -> list[date]:
    """Return calendar dates in ``[start, end]`` not yet stored for a symbol.

    Args:
        engine: SQLAlchemy engine.
        symbol: Market symbol id.
        start: Inclusive range start.
        end: Inclusive range end.

    Returns:
        list[date]: Missing dates, ordered ascending.
    """
    repo = Repository(engine)
    existing = repo.existing_trade_dates(symbol)
    return [d for d in date_range(start, end) if d.isoformat() not in existing]


def backfill_symbol(
    http: Any,
    engine: Engine,
    symbol: str,
    *,
    max_days: int = 730,
) -> SyncResult:
    """Backfill missing daily bars for one symbol over the lookback window.

    Args:
        http: HTTP client with ``get_json``.
        engine: SQLAlchemy engine.
        symbol: Market symbol id.
        max_days: Maximum lookback from today.

    Returns:
        SyncResult: Number of bars written for gaps.
    """
    end = date.today()
    start = end - timedelta(days=max_days)
    missing = missing_dates_for_symbol(engine, symbol, start=start, end=end)
    if not missing:
        return SyncResult(messages=[f"{symbol}: no gaps"])

    # Collapse consecutive missing dates into ranges for fewer API calls.
    ranges: list[tuple[date, date]] = []
    range_start = missing[0]
    prev = missing[0]
    for current in missing[1:]:
        if (current - prev).days == 1:
            prev = current
            continue
        ranges.append((range_start, prev))
        range_start = current
        prev = current
    ranges.append((range_start, prev))

    client = HistoryClient(http)
    repo = Repository(engine)
    written = 0
    for gap_start, gap_end in ranges:
        try:
            bars = client.fetch_daily(symbol, start=gap_start, end=gap_end)
        except Exception as exc:
            logger.warning("backfill failed for %s %s..%s: %s", symbol, gap_start, gap_end, exc)
            continue
        # Keep only bars inside the requested gap window.
        filtered: list[PriceBar] = [
            b for b in bars if gap_start <= b.trade_date <= gap_end
        ]
        written += repo.upsert_price_bars(filtered)
    return SyncResult(bars=written, messages=[f"{symbol}: backfilled {written} bars"])
