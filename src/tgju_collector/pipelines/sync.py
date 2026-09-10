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

from sqlalchemy import select
from sqlalchemy.engine import Engine

from ..calendar.trading import MarketCalendar
from ..clients.history import HistoryClient
from ..collectors.live import LiveCollector
from ..collectors.news import NewsCollector
from ..discovery.catalog import CatalogBuilder
from ..history_support import is_history_capable
from ..models import PriceBar
from ..quality.checks import check_price_bars, check_symbol_coverage, summarize_quality
from ..storage import schema
from ..storage.repository import Repository

logger = logging.getLogger("tgju_collector.pipelines")


@dataclass(slots=True)
class SyncResult:
    """Outcome counters for a pipeline run.

    Attributes:
        symbols: Symbols processed or discovered.
        snapshots: Live snapshots written.
        bars: Price bars written.
        news: News items written.
        messages: Optional human-readable notes.
    """

    symbols: int = 0
    snapshots: int = 0
    bars: int = 0
    news: int = 0
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
    skipped = 0
    for symbol in symbols:
        if not is_history_capable(symbol):
            skipped += 1
            continue
        try:
            bars = client.fetch_daily(symbol, days=days)
        except Exception as exc:
            logger.warning("history failed for %s: %s", symbol, exc)
            continue
        total += repo.upsert_price_bars(bars)
    messages = [f"upserted {total} bars"]
    if skipped:
        messages.append(f"skipped {skipped} non-history symbols")
    return SyncResult(bars=total, messages=messages)


def sync_news(http: Any, engine: Engine, *, count: int = 50) -> SyncResult:
    """Fetch recent news items and persist them.

    Args:
        http: HTTP client with ``get_json``.
        engine: SQLAlchemy engine.
        count: Number of items to request.

    Returns:
        SyncResult: News write counts.
    """
    items = NewsCollector(http).fetch(count=count)
    repo = Repository(engine)
    written = repo.upsert_news(items)
    return SyncResult(news=written, messages=[f"news upserted {written}"])


def missing_dates_for_symbol(
    engine: Engine,
    symbol: str,
    *,
    start: date,
    end: date,
    calendar: MarketCalendar | None = None,
) -> list[date]:
    """Return market trading days in ``[start, end]`` not yet stored.

    Fridays and known Iranian holidays are excluded so backfill does not
    waste API calls on non-trading days.

    Args:
        engine: SQLAlchemy engine.
        symbol: Market symbol id.
        start: Inclusive range start.
        end: Inclusive range end.
        calendar: Optional trading calendar; defaults to :class:`MarketCalendar`.

    Returns:
        list[date]: Missing trading dates, ordered ascending.
    """
    repo = Repository(engine)
    existing = repo.existing_trade_dates(symbol)
    cal = calendar or MarketCalendar()
    return cal.missing_trading_days(start, end, existing)


def _collapse_ranges(days: Sequence[date]) -> list[tuple[date, date]]:
    """Collapse consecutive dates into inclusive ranges.

    Args:
        days: Ordered unique dates.

    Returns:
        list[tuple[date, date]]: ``(start, end)`` inclusive ranges.
    """
    if not days:
        return []
    ranges: list[tuple[date, date]] = []
    range_start = days[0]
    prev = days[0]
    for current in days[1:]:
        if (current - prev).days == 1:
            prev = current
            continue
        ranges.append((range_start, prev))
        range_start = current
        prev = current
    ranges.append((range_start, prev))
    return ranges


def backfill_symbol(
    http: Any,
    engine: Engine,
    symbol: str,
    *,
    max_days: int = 730,
    calendar: MarketCalendar | None = None,
) -> SyncResult:
    """Backfill missing daily bars for one symbol over the lookback window.

    Args:
        http: HTTP client with ``get_json``.
        engine: SQLAlchemy engine.
        symbol: Market symbol id.
        max_days: Maximum lookback from today.
        calendar: Optional trading calendar.

    Returns:
        SyncResult: Number of bars written for gaps.
    """
    end = date.today()
    start = end - timedelta(days=max_days)
    missing = missing_dates_for_symbol(
        engine, symbol, start=start, end=end, calendar=calendar
    )
    if not missing:
        return SyncResult(messages=[f"{symbol}: no gaps"])

    client = HistoryClient(http)
    repo = Repository(engine)
    written = 0
    for gap_start, gap_end in _collapse_ranges(missing):
        try:
            bars = client.fetch_daily(symbol, start=gap_start, end=gap_end)
        except Exception as exc:
            logger.warning(
                "backfill failed for %s %s..%s: %s", symbol, gap_start, gap_end, exc
            )
            continue
        filtered: list[PriceBar] = [
            b for b in bars if gap_start <= b.trade_date <= gap_end
        ]
        written += repo.upsert_price_bars(filtered)
    return SyncResult(bars=written, messages=[f"{symbol}: backfilled {written} bars"])


def run_quality_report(engine: Engine) -> dict[str, Any]:
    """Compute data-quality metrics over stored price bars and catalog coverage.

    Coverage is evaluated against history-capable symbols so HTML-only
    numeric row ids do not count as missing OHLCV data.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        dict[str, Any]: Keys ``price``, ``coverage``, ``issues``.
    """
    with engine.connect() as conn:
        bar_rows = [
            dict(row._mapping)
            for row in conn.execute(select(schema.price_bars)).all()
        ]
        stored_symbols = {row["symbol"] for row in bar_rows}
        catalog_rows = [
            dict(row._mapping)
            for row in conn.execute(select(schema.symbols)).all()
        ]

    catalog_symbols = {row["symbol"] for row in catalog_rows}
    capable = {
        row["symbol"] for row in catalog_rows if is_history_capable(row["symbol"])
    }

    price_report = check_price_bars(bar_rows)
    coverage_report = check_symbol_coverage(
        catalog_symbols, stored_symbols, history_capable=capable
    )
    issues = summarize_quality(price_report, coverage_report)
    return {
        "price": price_report,
        "coverage": coverage_report,
        "issues": issues,
        "history_capable_size": len(capable),
    }


def run_trowel(
    http: Any,
    engine: Engine,
    *,
    symbols: Sequence[str] | None = None,
    max_days: int = 730,
    only_gaps: bool = True,
) -> SyncResult:
    """Full backfill pass (AutoTrowel successor) over history-capable symbols.

    For each symbol:
      1. Detect missing trading days in the lookback window.
      2. Collapse gaps into ranges.
      3. Fetch and upsert those ranges only.

    Args:
        http: HTTP client with ``get_json``.
        engine: SQLAlchemy engine.
        symbols: Optional explicit symbol list. Defaults to all catalog
            symbols that pass the history-capable filter.
        max_days: Maximum lookback from today.
        only_gaps: When True (default), skip symbols with no gaps.

    Returns:
        SyncResult: Aggregate bar counts and per-symbol notes.
    """
    from datetime import date, timedelta

    repo = Repository(engine)

    if symbols is None:
        with engine.connect() as conn:
            catalog_rows = [
                dict(row._mapping)
                for row in conn.execute(select(schema.symbols)).all()
            ]
        targets = [
            row["symbol"]
            for row in catalog_rows
            if is_history_capable(row["symbol"])
        ]
    else:
        targets = [s for s in symbols if is_history_capable(s)]

    end = date.today()
    start = end - timedelta(days=max_days)
    cal = MarketCalendar()

    total_bars = 0
    processed = 0
    skipped_no_gap = 0
    notes: list[str] = []

    for symbol in targets:
        missing = missing_dates_for_symbol(
            engine, symbol, start=start, end=end, calendar=cal
        )
        if only_gaps and not missing:
            skipped_no_gap += 1
            continue

        result = backfill_symbol(http, engine, symbol, max_days=max_days, calendar=cal)
        total_bars += result.bars
        processed += 1
        notes.append(f"{symbol}: {result.bars} bars")
        logger.info("trowel %s → %s bars", symbol, result.bars)

    messages = [
        f"trowel targets={len(targets)} processed={processed} "
        f"no_gap={skipped_no_gap} bars={total_bars}"
    ]
    messages.extend(notes[:20])
    if len(notes) > 20:
        messages.append(f"... {len(notes) - 20} more symbols")
    return SyncResult(bars=total_bars, messages=messages)
