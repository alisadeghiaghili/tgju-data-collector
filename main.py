# -*- coding: utf-8 -*-
"""
TGJU Data Collector - Main Entry Point

Modular CLI for collecting market data from tgju.org.

Usage:
    python main.py collect          # Daily OHLCV collection (all symbols)
    python main.py discover         # Discover symbols only
    python main.py backfill         # Backfill historical gaps
    python main.py status           # Show configuration status
"""

import sys
import argparse
import logging

from src.utils.logging import setup_logging
from src.config import load_config
from src.http_client import HttpClient
from src.discovery.registry import SymbolRegistry
from src.collectors.ohlcv import OHLCVCollector
from src.storage.sqlserver import SQLServerStorage


logger = setup_logging('tgju')


def cmd_collect(args):
    """Run daily OHLCV collection for all symbols."""
    logger.info("=" * 60)
    logger.info("TGJU Daily OHLCV Collection")
    logger.info("=" * 60)

    http = HttpClient()
    registry = SymbolRegistry(http)
    registry.discover_all()

    symbols = registry.get_all()
    if not symbols:
        logger.critical("No symbols discovered!")
        sys.exit(1)

    # Convert to dict format expected by collector
    symbol_dicts = [{
        'symbol_Fa': s.name_fa,
        'symbol_En': s.name_en,
        'SYMBOL': s.code.upper()
    } for s in symbols]

    collector = OHLCVCollector(http)
    data = collector.collect_batch(symbol_dicts, resolution=args.resolution)

    if data.empty:
        logger.critical("No data collected!")
        sys.exit(1)

    storage = SQLServerStorage()
    saved = storage.save_daily_ohlcv(data)

    logger.info(f"Collection complete: {saved} records saved")
    http.close()


def cmd_discover(args):
    """Discover all available symbols from TGJU."""
    logger.info("=" * 60)
    logger.info("TGJU Symbol Discovery")
    logger.info("=" * 60)

    http = HttpClient()
    registry = SymbolRegistry(http)
    total = registry.discover_all()

    symbols = registry.get_all()

    # Print summary by category
    categories = {}
    for s in symbols:
        categories.setdefault(s.category, []).append(s)

    print(f"\n{'='*60}")
    print(f"Discovery Complete: {total} unique symbols")
    print(f"{'='*60}")

    for cat, syms in sorted(categories.items()):
        print(f"\n{cat.upper()} ({len(syms)} symbols):")
        for s in syms[:10]:  # Show first 10 per category
            print(f"  {s.code:30s} {s.name_fa}")
        if len(syms) > 10:
            print(f"  ... and {len(syms) - 10} more")

    # Save to database if requested
    if args.save_db:
        storage = SQLServerStorage()
        df = registry.to_dataframe()
        storage.save_symbols(df)
        logger.info(f"Saved {len(df)} symbols to database")

    http.close()


def cmd_backfill(args):
    """Backfill historical data gaps."""
    logger.info("=" * 60)
    logger.info("TGJU Historical Backfill")
    logger.info("=" * 60)

    # Import backfill module (lazy to avoid circular imports)
    from src.backfill import TGJUBackfill

    backfill = TGJUBackfill()
    backfill.run(
        max_days=args.max_days,
        symbols=args.symbols  # None = all symbols in DB
    )


def cmd_status(args):
    """Show configuration and database status."""
    print("\n" + "=" * 60)
    print("TGJU Data Collector - Status")
    print("=" * 60)

    import os
    env_exists = os.path.exists('.env')
    print(f"\n.env file: {'Found' if env_exists else 'Not found'}")

    if env_exists:
        load_config()
        db_vars = ['TGJU_DB_SERVER', 'TGJU_DB_NAME', 'TGJU_DB_USER']
        for var in db_vars:
            val = os.getenv(var)
            print(f"  {var}: {val or 'Not set'}")

        try:
            storage = SQLServerStorage()
            if storage.table_exists('TgjuAssets'):
                print(f"\n  TgjuAssets table: exists")
            else:
                print(f"\n  TgjuAssets table: not found")
        except Exception as e:
            print(f"\n  Database connection: {e}")

    print("\n" + "=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='TGJU Data Collector - Modular market data scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # collect command
    collect_parser = subparsers.add_parser('collect', help='Collect daily OHLCV data')
    collect_parser.add_argument('--resolution', default='1D',
                                choices=list(OHLCVCollector._fetch.__code__.co_varnames[:5]) or ['1D'],
                                help='Price resolution (default: 1D)')
    collect_parser.set_defaults(func=cmd_collect)

    # discover command
    discover_parser = subparsers.add_parser('discover', help='Discover available symbols')
    discover_parser.add_argument('--save-db', action='store_true',
                                 help='Save discovered symbols to database')
    discover_parser.set_defaults(func=cmd_discover)

    # backfill command
    backfill_parser = subparsers.add_parser('backfill', help='Backfill historical gaps')
    backfill_parser.add_argument('--max-days', type=int, default=730,
                                 help='Maximum days to backfill (default: 730)')
    backfill_parser.add_argument('--symbols', nargs='*',
                                 help='Specific symbols to backfill (default: all in DB)')
    backfill_parser.set_defaults(func=cmd_backfill)

    # status command
    status_parser = subparsers.add_parser('status', help='Show configuration status')
    status_parser.set_defaults(func=cmd_status)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    load_config()
    args.func(args)


if __name__ == '__main__':
    main()
