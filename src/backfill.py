# -*- coding: utf-8 -*-
"""
Unified backfill module — replaces AutoTrowel_TGJU.py.

Detects missing date ranges and fills historical gaps.
"""

import logging
import time
import random
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from .config import get_connection_string, get_table_name
from .http_client import HttpClient
from .collectors.ohlcv import OHLCVCollector
from .utils.dates import persian_to_gregorian

logger = logging.getLogger('tgju')

MAX_BACKFILL_DAYS = 730  # 2 years


class TGJUBackfill:
    """
    Backfill historical data for symbols in the database.

    Detects gaps in existing data and fetches missing records from the TGJU API.
    """

    def __init__(self, connection_string: str = None, table_name: str = None):
        self.connection_string = connection_string or get_connection_string()
        self.table_name = table_name or get_table_name()
        self.http = HttpClient()
        self.collector = OHLCVCollector(self.http)

    def get_symbols_from_db(self) -> pd.DataFrame:
        """Get all symbols currently in the database."""
        engine = create_engine(self.connection_string)
        query = f"""
            SELECT DISTINCT Symbol_En, Name
            FROM {self.table_name}
            ORDER BY Symbol_En
        """
        df = pd.read_sql(query, engine)
        logger.info(f"Found {len(df)} symbols in database")
        return df

    def get_existing_dates(self, symbol_en: str) -> List[str]:
        """Get all existing Persian dates for a symbol."""
        engine = create_engine(self.connection_string)
        query = text(f"""
            SELECT DISTINCT PersianDate
            FROM {self.table_name}
            WHERE Symbol_En = :symbol
            ORDER BY PersianDate
        """)
        result = engine.execute(query, {'symbol': symbol_en})
        return [row[0] for row in result]

    def detect_gaps(self, symbol_en: str) -> List[Tuple[datetime, datetime]]:
        """Detect missing date ranges for a symbol."""
        existing_dates = self.get_existing_dates(symbol_en)

        if not existing_dates:
            end = datetime.now()
            start = end - timedelta(days=MAX_BACKFILL_DAYS)
            return [(start, end)]

        # Convert Persian dates to Gregorian
        try:
            dates_g = []
            for pd_str in existing_dates:
                dates_g.append(persian_to_gregorian(pd_str))
        except Exception as e:
            logger.error(f"Error converting dates for {symbol_en}: {e}")
            return []

        dates_g.sort()
        gaps = []
        today = datetime.now().date()

        # Gap before first date
        earliest = (datetime.now() - timedelta(days=MAX_BACKFILL_DAYS)).date()
        if dates_g[0] > earliest:
            gaps.append((datetime.combine(earliest, datetime.min.time()),
                         datetime.combine(dates_g[0] - timedelta(days=1), datetime.min.time())))

        # Gaps between dates
        for i in range(len(dates_g) - 1):
            diff = (dates_g[i + 1] - dates_g[i]).days
            if diff > 1:
                gaps.append((datetime.combine(dates_g[i] + timedelta(days=1), datetime.min.time()),
                             datetime.combine(dates_g[i + 1] - timedelta(days=1), datetime.min.time())))

        # Gap after last date
        if dates_g[-1] < today:
            gaps.append((datetime.combine(dates_g[-1] + timedelta(days=1), datetime.min.time()),
                         datetime.combine(today, datetime.min.time())))

        return gaps

    def backfill_symbol(self, symbol_en: str, name: str) -> int:
        """Backfill missing data for a single symbol."""
        symbol_code = symbol_en.upper()
        gaps = self.detect_gaps(symbol_en)

        if not gaps:
            logger.info(f"  {symbol_en}: no gaps")
            return 0

        total_inserted = 0

        for start, end in gaps:
            logger.info(f"  Gap: {start.date()} to {end.date()}")

            df = self.collector.collect_range(symbol_code, '1D', start, end)

            if df is not None and not df.empty:
                df['Name'] = name
                df['Symbol_En'] = symbol_en

                now = datetime.now()
                df['ScrapeDate'] = now.strftime('%Y-%m-%d')
                df['ScrapeTime'] = now.strftime('%H:%M:%S')
                df['ScrapeDateTime'] = now.strftime('%Y-%m-%d %H:%M:%S')

                # Save using the same schema as tgjuScraper
                from .storage.sqlserver import SQLServerStorage
                storage = SQLServerStorage(self.connection_string, self.table_name)
                saved = storage.save_daily_ohlcv(df)
                total_inserted += saved

            self.http.sleep_between_requests()

        return total_inserted

    def run(self, max_days: int = MAX_BACKFILL_DAYS, symbols: list = None):
        """
        Execute the complete backfill pipeline.

        Args:
            max_days: Maximum days to backfill
            symbols: Specific symbols to backfill (None = all in DB)
        """
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("Starting TGJU Backfill Pipeline")
        logger.info("=" * 60)

        try:
            if symbols:
                # Use provided symbols
                symbol_list = [{'Symbol_En': s, 'Name': s} for s in symbols]
            else:
                # Get symbols from database
                db_symbols = self.get_symbols_from_db()
                if db_symbols.empty:
                    logger.warning("No symbols found in database")
                    return
                symbol_list = db_symbols.to_dict('records')

            total_inserted = 0

            for i, sym in enumerate(symbol_list, 1):
                logger.info(f"[{i}/{len(symbol_list)}] {sym['Name']}")
                inserted = self.backfill_symbol(sym['Symbol_En'], sym['Name'])
                total_inserted += inserted

            duration = datetime.now() - start_time
            logger.info(f"\nBackfill complete: {total_inserted} records inserted in {duration.total_seconds():.1f}s")

        except KeyboardInterrupt:
            logger.warning("Backfill interrupted by user")
        except Exception as e:
            logger.error(f"Backfill failed: {e}", exc_info=True)
        finally:
            self.http.close()
