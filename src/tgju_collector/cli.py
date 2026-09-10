# -*- coding: utf-8 -*-
"""Command-line interface for the TGJU collector.

Examples:
    tgju --help
    tgju sync-catalog
    tgju sync-live --pages home,crypto
    tgju sync-history --symbol sekee --days 14
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from . import __version__
from .config import Settings
from .http import HttpClient
from .logging_setup import setup_logging


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level argument parser.

    Returns:
        argparse.ArgumentParser: Configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="tgju",
        description="Section-aware TGJU market data collector",
    )
    parser.add_argument("--version", action="version", version=f"tgju-collector {__version__}")
    parser.add_argument(
        "--log-level",
        default=None,
        help="Override log level (DEBUG, INFO, WARNING, ERROR)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_catalog = sub.add_parser("sync-catalog", help="Discover symbols and persist catalog")
    p_catalog.add_argument("--dry-run", action="store_true", help="Print summary only")

    p_live = sub.add_parser("sync-live", help="Capture live snapshots from section pages")
    p_live.add_argument(
        "--pages",
        default="",
        help="Comma-separated page names (default: all known pages)",
    )

    p_hist = sub.add_parser("sync-history", help="Fetch daily OHLCV bars")
    p_hist.add_argument("--symbol", action="append", default=[], help="Symbol id (repeatable)")
    p_hist.add_argument("--days", type=int, default=7, help="Lookback window in days")
    p_hist.add_argument(
        "--from-catalog",
        action="store_true",
        help="Use all stored symbols when --symbol is omitted",
    )

    p_status = sub.add_parser("status", help="Show row counts from the database")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argument vector (defaults to ``sys.argv[1:]``).

    Returns:
        int: Process exit code (0 on success).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    log_level = args.log_level or settings.log_level
    logger = setup_logging(log_level)

    if args.command == "status":
        return _cmd_status(settings, logger)

    with HttpClient(
        timeout=settings.http_timeout,
        max_retries=settings.http_max_retries,
        delay_min=settings.request_delay_min,
        delay_max=settings.request_delay_max,
        user_agent=settings.user_agent,
    ) as http:
        if args.command == "sync-catalog":
            return _cmd_sync_catalog(settings, http, logger, dry_run=args.dry_run)
        if args.command == "sync-live":
            pages = [p.strip() for p in args.pages.split(",") if p.strip()] or None
            return _cmd_sync_live(settings, http, logger, pages=pages)
        if args.command == "sync-history":
            return _cmd_sync_history(
                settings,
                http,
                logger,
                symbols=args.symbol,
                days=args.days,
                from_catalog=args.from_catalog,
            )

    parser.error(f"Unknown command: {args.command}")
    return 2


def _engine(settings: Settings):
    from sqlalchemy import create_engine

    from .storage import create_all

    engine = create_engine(settings.database_url, future=True)
    create_all(engine)
    return engine


def _cmd_sync_catalog(settings: Settings, http: HttpClient, logger, *, dry_run: bool) -> int:
    from .discovery import CatalogBuilder
    from .storage import Repository

    builder = CatalogBuilder(http)
    catalog = builder.build()
    logger.info("Discovered %s symbols", len(catalog))

    by_section: dict[str, int] = {}
    for item in catalog:
        by_section[str(item.product_section)] = by_section.get(str(item.product_section), 0) + 1
    for section, count in sorted(by_section.items(), key=lambda kv: -kv[1]):
        logger.info("  %-12s %s", section, count)

    if dry_run:
        return 0

    engine = _engine(settings)
    repo = Repository(engine)
    written = repo.upsert_symbols(catalog)
    logger.info("Persisted %s symbols", written)
    return 0


def _cmd_sync_live(settings: Settings, http: HttpClient, logger, *, pages: list[str] | None) -> int:
    from .collectors import LiveCollector
    from .storage import Repository

    collector = LiveCollector(http)
    snapshots = collector.collect(page_names=pages)
    logger.info("Captured %s live snapshots", len(snapshots))

    engine = _engine(settings)
    repo = Repository(engine)
    inserted = repo.insert_live_snapshots(snapshots)
    logger.info("Inserted %s new live snapshots", inserted)
    return 0


def _cmd_sync_history(
    settings: Settings,
    http: HttpClient,
    logger,
    *,
    symbols: list[str],
    days: int,
    from_catalog: bool,
) -> int:
    from .clients import HistoryClient
    from .storage import Repository

    engine = _engine(settings)
    repo = Repository(engine)

    targets = list(symbols)
    if not targets and from_catalog:
        targets = [row["symbol"] for row in repo.list_symbols()]
    if not targets:
        logger.error("Provide --symbol or --from-catalog")
        return 2

    client = HistoryClient(http)
    total = 0
    for symbol in targets:
        try:
            bars = client.fetch_daily(symbol, days=days)
        except Exception as exc:
            logger.warning("History fetch failed for %s: %s", symbol, exc)
            continue
        total += repo.upsert_price_bars(bars)
        logger.info("%s: %s bars", symbol, len(bars))
    logger.info("Total bars upserted: %s", total)
    return 0


def _cmd_status(settings: Settings, logger) -> int:
    from sqlalchemy import func, select

    from .storage import schema

    engine = _engine(settings)
    with engine.connect() as conn:
        for table, label in (
            (schema.symbols, "symbols"),
            (schema.price_bars, "price_bars"),
            (schema.live_snapshots, "live_snapshots"),
            (schema.news_items, "news_items"),
        ):
            count = conn.execute(select(func.count()).select_from(table)).scalar_one()
            logger.info("%-16s %s", label, count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
