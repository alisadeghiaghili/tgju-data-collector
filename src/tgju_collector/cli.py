# -*- coding: utf-8 -*-
"""Command-line interface for the TGJU collector.

Examples:
    tgju --help
    tgju sync-catalog
    tgju sync-live --pages home,crypto
    tgju sync-history --symbol sekee --days 14
    tgju sync-news --count 30
    tgju backfill --symbol sekee --max-days 365
    tgju quality
    tgju status
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from sqlalchemy import create_engine

from . import __version__
from .config import Settings
from .http import HttpClient
from .logging_setup import setup_logging
from .storage.mssql import engine_kwargs_for_url, is_mssql_url, require_pyodbc


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

    p_news = sub.add_parser("sync-news", help="Fetch and store recent news items")
    p_news.add_argument("--count", type=int, default=50, help="Number of news items to request")

    p_backfill = sub.add_parser(
        "backfill",
        help="Fill missing trading-day gaps (skips Fridays/holidays)",
    )
    p_backfill.add_argument("--symbol", action="append", default=[], help="Symbol id (repeatable)")
    p_backfill.add_argument(
        "--from-catalog",
        action="store_true",
        help="Use all stored symbols when --symbol is omitted",
    )
    p_backfill.add_argument(
        "--max-days",
        type=int,
        default=730,
        help="Maximum lookback window in calendar days",
    )

    p_export = sub.add_parser("export", help="Export stored tables to CSV/Parquet/JSON")
    p_export.add_argument(
        "--table",
        choices=("price_bars", "live_snapshots", "symbols"),
        default="price_bars",
        help="Table to export",
    )
    p_export.add_argument("--output", required=True, help="Output path (.csv/.parquet/.json)")
    p_export.add_argument("--symbol", default=None, help="Optional symbol filter")
    p_export.add_argument("--section", default=None, help="Optional section filter (symbols only)")

    sub.add_parser("quality", help="Run data-quality checks on stored data")
    sub.add_parser("status", help="Show row counts from the database")

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
    if args.command == "quality":
        return _cmd_quality(settings, logger)
    if args.command == "export":
        return _cmd_export(
            settings,
            logger,
            table=args.table,
            output=args.output,
            symbol=args.symbol,
            section=args.section,
        )

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
        if args.command == "sync-news":
            return _cmd_sync_news(settings, http, logger, count=args.count)
        if args.command == "backfill":
            return _cmd_backfill(
                settings,
                http,
                logger,
                symbols=args.symbol,
                from_catalog=args.from_catalog,
                max_days=args.max_days,
            )

    parser.error(f"Unknown command: {args.command}")
    return 2


def _engine(settings: Settings):
    """Create a SQLAlchemy engine from settings, with MSSQL preflight checks.

    Args:
        settings: Application settings.

    Returns:
        sqlalchemy.engine.Engine: Configured engine with schema created.
    """
    from .storage import create_all

    if is_mssql_url(settings.database_url):
        require_pyodbc()
    engine = create_engine(settings.database_url, **engine_kwargs_for_url(settings.database_url))
    create_all(engine)
    return engine


def _stored_symbols(engine) -> list[str]:
    from sqlalchemy import select

    from .storage import schema

    with engine.connect() as conn:
        return [row[0] for row in conn.execute(select(schema.symbols.c.symbol)).all()]


def _cmd_sync_catalog(settings: Settings, http: HttpClient, logger, *, dry_run: bool) -> int:
    from .pipelines import sync_catalog

    engine = _engine(settings) if not dry_run else None
    # dry_run still needs an engine object for the pipeline signature; skip DB when dry
    if dry_run:
        from sqlalchemy import create_engine as _ce

        engine = _ce("sqlite:///:memory:", future=True)
    result = sync_catalog(http, engine, dry_run=dry_run)
    for message in result.messages:
        logger.info(message)
    logger.info("symbols=%s", result.symbols)
    return 0


def _cmd_sync_live(settings: Settings, http: HttpClient, logger, *, pages: list[str] | None) -> int:
    from .pipelines import sync_live

    engine = _engine(settings)
    result = sync_live(http, engine, pages=pages)
    for message in result.messages:
        logger.info(message)
    logger.info("snapshots=%s", result.snapshots)
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
    from .pipelines import sync_history

    engine = _engine(settings)
    targets = list(symbols)
    if not targets and from_catalog:
        targets = _stored_symbols(engine)
    if not targets:
        logger.error("Provide --symbol or --from-catalog")
        return 2

    result = sync_history(http, engine, symbols=targets, days=days)
    for message in result.messages:
        logger.info(message)
    logger.info("bars=%s", result.bars)
    return 0


def _cmd_sync_news(settings: Settings, http: HttpClient, logger, *, count: int) -> int:
    from .pipelines import sync_news

    engine = _engine(settings)
    result = sync_news(http, engine, count=count)
    for message in result.messages:
        logger.info(message)
    logger.info("news=%s", result.news)
    return 0


def _cmd_backfill(
    settings: Settings,
    http: HttpClient,
    logger,
    *,
    symbols: list[str],
    from_catalog: bool,
    max_days: int,
) -> int:
    from .pipelines import backfill_symbol

    engine = _engine(settings)
    targets = list(symbols)
    if not targets and from_catalog:
        targets = _stored_symbols(engine)
    if not targets:
        logger.error("Provide --symbol or --from-catalog")
        return 2

    total = 0
    for symbol in targets:
        result = backfill_symbol(http, engine, symbol, max_days=max_days)
        for message in result.messages:
            logger.info(message)
        total += result.bars
    logger.info("total_backfilled=%s", total)
    return 0


def _cmd_export(
    settings: Settings,
    logger,
    *,
    table: str,
    output: str,
    symbol: str | None,
    section: str | None,
) -> int:
    from .export import export_live_snapshots, export_price_bars, export_symbols

    engine = _engine(settings)
    if table == "price_bars":
        path = export_price_bars(engine, output, symbol=symbol)
    elif table == "live_snapshots":
        path = export_live_snapshots(engine, output, symbol=symbol)
    else:
        path = export_symbols(engine, output, section=section)
    logger.info("exported %s to %s", table, path)
    return 0


def _cmd_quality(settings: Settings, logger) -> int:
    from .pipelines import run_quality_report

    engine = _engine(settings)
    report = run_quality_report(engine)
    logger.info("price: %s", report["price"])
    logger.info("coverage: %s", report["coverage"])
    if report["issues"]:
        for issue in report["issues"]:
            logger.warning("ISSUE %s", issue)
        return 1
    logger.info("quality: OK")
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
