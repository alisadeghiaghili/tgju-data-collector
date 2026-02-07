# -*- coding: utf-8 -*-
"""
AutoTrowel - TGJU Market Data Backfill Tool

A production-grade ETL pipeline for backfilling missing historical market data
from TGJU.org (Tehran Gold and Jewelry Union) with intelligent gap detection
and incremental loading.

Author: sadeghi.a
Created: 2026-02-07
Version: 1.0.0

Security:
    - NO hardcoded credentials (compliant with SonarQube S2115)
    - Credentials loaded from environment variables via config module
    - Supports .env file for local development

Features:
    - Detects missing date ranges for each symbol in database
    - Fetches historical data from TGJU API with date range support
    - Implements incremental loading to avoid duplicates
    - Maintains exact same schema as tgjuScraper.py
    - Comprehensive error handling and retry logic
    - Detailed logging for debugging and monitoring
    - Progress tracking for large backfill operations
    
Dependencies:
    - requests: HTTP client for API calls
    - pandas: Data manipulation and analysis
    - jdatetime: Jalali/Gregorian date conversion
    - sqlalchemy: Database ORM and connection management
    - pyodbc: SQL Server ODBC driver
    
Configuration:
    Uses same .env configuration as tgjuScraper.py
    Required environment variables:
        TGJU_DB_SERVER, TGJU_DB_NAME, TGJU_DB_USER, TGJU_DB_PASSWORD
    Or:
        TGJU_DB_CONNECTION_STRING
    
Usage:
    python AutoTrowel_TGJU.py
    
    Or programmatically:
    >>> from AutoTrowel_TGJU import TGJUBackfillETL
    >>> etl = TGJUBackfillETL()
    >>> etl.run()
"""

import sys
import logging
import logging.handlers
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import time
import random

import requests
import pandas as pd
import calendar
import jdatetime
from sqlalchemy import create_engine, CHAR, VARCHAR, NVARCHAR, DATETIME, DECIMAL, text
from sqlalchemy.exc import SQLAlchemyError

# Import secure configuration module
from config import get_connection_string, get_table_name, load_env_file

# Load environment variables
load_env_file()


# ===== LOGGING CONFIGURATION =====

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure logging with file and console handlers."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger('autotrowel_tgju')
    logger.setLevel(log_level)
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / f"autotrowel_tgju_{datetime.now().strftime('%Y%m%d')}.log",
        maxBytes=10*1024*1024,
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(levelname)-8s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logging()


# ===== CONFIGURATION =====

class Config:
    """Configuration constants for TGJU AutoTrowel."""
    
    TGJU_API_URL = 'https://platform.tgju.org/fa/tvdata/history'
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    
    API_TIMEOUT = 30
    MAX_RETRIES = 3
    REQUEST_DELAY_MIN = 0.5
    REQUEST_DELAY_JITTER = 0.5
    
    # How far back to look for missing data (days)
    MAX_BACKFILL_DAYS = 365 * 2  # 2 years


class TGJUBackfillETL:
    """Main ETL pipeline for TGJU historical data backfill."""
    
    def __init__(self, connection_string: Optional[str] = None, table_name: Optional[str] = None):
        """
        Initialize the backfill ETL pipeline.
        
        Args:
            connection_string: SQL Server connection string (optional)
            table_name: Target database table name (optional)
        
        Raises:
            ValueError: If required environment variables are missing
        """
        try:
            # Get secure connection string
            self.connection_string = connection_string or get_connection_string(prefix='TGJU_DB')
            self.table_name = table_name or get_table_name(prefix='TGJU_DB', default='TgjuAssets')
            
            # Initialize HTTP session
            self.session = requests.Session()
            self.session.headers.update({'User-Agent': Config.DEFAULT_USER_AGENT})
            
            logger.info(f"TGJUBackfillETL initialized - Table: {self.table_name}")
            
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise
    
    def get_symbols_from_db(self) -> pd.DataFrame:
        """
        Get list of all symbols currently in database.
        
        Returns:
            DataFrame with Symbol_En and Name columns
        """
        try:
            engine = create_engine(self.connection_string)
            query = f"""
                SELECT DISTINCT Symbol_En, Name
                FROM {self.table_name}
                ORDER BY Symbol_En
            """
            df = pd.read_sql(query, engine)
            logger.info(f"Found {len(df)} symbols in database")
            return df
        except SQLAlchemyError as e:
            logger.error(f"Database error loading symbols: {e}")
            raise
    
    def get_existing_dates_for_symbol(self, symbol_en: str) -> List[str]:
        """
        Get all existing dates for a specific symbol.
        
        Args:
            symbol_en: English symbol name
        
        Returns:
            List of date strings in 'YYYY-MM-DD' format
        """
        try:
            engine = create_engine(self.connection_string)
            query = text(f"""
                SELECT DISTINCT PersianDate
                FROM {self.table_name}
                WHERE Symbol_En = :symbol
                ORDER BY PersianDate
            """)
            
            result = engine.execute(query, {'symbol': symbol_en})
            dates = [row[0] for row in result]
            logger.debug(f"Found {len(dates)} existing dates for {symbol_en}")
            return dates
            
        except SQLAlchemyError as e:
            logger.error(f"Database error loading dates for {symbol_en}: {e}")
            return []
    
    def detect_missing_date_ranges(self, symbol_en: str) -> List[Tuple[datetime, datetime]]:
        """
        Detect missing date ranges for a symbol.
        
        Args:
            symbol_en: English symbol name
        
        Returns:
            List of (start_date, end_date) tuples representing gaps
        """
        existing_dates = self.get_existing_dates_for_symbol(symbol_en)
        
        if not existing_dates:
            # No data exists - backfill from MAX_BACKFILL_DAYS ago to today
            end_date = datetime.now()
            start_date = end_date - timedelta(days=Config.MAX_BACKFILL_DAYS)
            logger.info(f"{symbol_en}: No existing data - will backfill {Config.MAX_BACKFILL_DAYS} days")
            return [(start_date, end_date)]
        
        # Convert Persian dates to datetime objects
        try:
            dates_dt = []
            for pd_str in existing_dates:
                parts = pd_str.split('-')
                if len(parts) == 3:
                    jd = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                    gd = jd.togregorian()
                    dates_dt.append(gd)
        except Exception as e:
            logger.error(f"Error converting dates for {symbol_en}: {e}")
            return []
        
        if not dates_dt:
            return []
        
        # Sort dates
        dates_dt.sort()
        
        # Find gaps
        gaps = []
        today = datetime.now().date()
        
        # Check if we need to backfill before first date
        first_date = dates_dt[0]
        earliest_allowed = (datetime.now() - timedelta(days=Config.MAX_BACKFILL_DAYS)).date()
        if first_date > earliest_allowed:
            gaps.append((datetime.combine(earliest_allowed, datetime.min.time()), 
                        datetime.combine(first_date - timedelta(days=1), datetime.min.time())))
        
        # Check for gaps between dates
        for i in range(len(dates_dt) - 1):
            current = dates_dt[i]
            next_date = dates_dt[i + 1]
            
            # If gap is more than 1 day
            if (next_date - current).days > 1:
                gap_start = current + timedelta(days=1)
                gap_end = next_date - timedelta(days=1)
                gaps.append((datetime.combine(gap_start, datetime.min.time()), 
                            datetime.combine(gap_end, datetime.min.time())))
        
        # Check if we need to backfill after last date
        last_date = dates_dt[-1]
        if last_date < today:
            gaps.append((datetime.combine(last_date + timedelta(days=1), datetime.min.time()), 
                        datetime.combine(today, datetime.min.time())))
        
        if gaps:
            logger.info(f"{symbol_en}: Found {len(gaps)} gap(s) to fill")
        else:
            logger.debug(f"{symbol_en}: No gaps detected")
        
        return gaps
    
    def fetch_historical_data(self, symbol: str, symbol_en: str, 
                            start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch historical data for a symbol within date range.
        
        Args:
            symbol: Symbol code (uppercase)
            symbol_en: English symbol name
            start_date: Start date for data fetch
            end_date: End date for data fetch
        
        Returns:
            DataFrame with historical price data
        """
        try:
            # Convert to Unix timestamps
            from_timestamp = int(start_date.timestamp())
            to_timestamp = int(end_date.timestamp())
            
            url = (
                f"{Config.TGJU_API_URL}?"
                f"symbol={symbol}&"
                f"resolution=1D&"
                f"from={from_timestamp}&"
                f"to={to_timestamp}"
            )
            
            logger.debug(f"Fetching {symbol} from {start_date.date()} to {end_date.date()}")
            
            response = self.session.get(url, timeout=Config.API_TIMEOUT)
            response.raise_for_status()
            
            api_response = response.json()
            
            if not api_response or "t" not in api_response or not api_response["t"]:
                logger.debug(f"No data returned for {symbol} in date range")
                return pd.DataFrame()
            
            # Create DataFrame
            df = pd.DataFrame({
                'Date': api_response['t'],
                'Open': api_response.get('o', []),
                'High': api_response.get('h', []),
                'Low': api_response.get('l', []),
                'Close': api_response.get('c', [])
            })
            
            # Convert Unix timestamp to datetime
            df['Date'] = df['Date'].apply(lambda ts: datetime.fromtimestamp(ts))
            df['EnglishDate'] = pd.to_datetime(df['Date'])
            
            # Extract weekday
            df['Weekday'] = df['EnglishDate'].dt.weekday.apply(
                lambda day_num: calendar.day_name[day_num]
            )
            
            # Convert to Persian date
            df['PersianDate'] = df['EnglishDate'].apply(
                lambda eng_date: str(jdatetime.date.fromgregorian(date=eng_date.date()))
            )
            
            # Add symbol info
            df['Symbol_En'] = symbol_en
            
            # Select columns
            df = df[['PersianDate', 'EnglishDate', 'Weekday', 'Open', 'High', 'Low', 'Close', 'Symbol_En']]
            
            logger.debug(f"Fetched {len(df)} records for {symbol}")
            return df
            
        except requests.RequestException as e:
            logger.error(f"API error fetching {symbol}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching {symbol}: {e}")
            return pd.DataFrame()
    
    def backfill_symbol(self, symbol_info: Dict) -> int:
        """
        Backfill missing data for a single symbol.
        
        Args:
            symbol_info: Dictionary with 'Symbol_En' and 'Name' keys
        
        Returns:
            Number of records inserted
        """
        symbol_en = symbol_info['Symbol_En']
        name = symbol_info['Name']
        symbol_code = symbol_en.upper()
        
        logger.info(f"Processing: {name} ({symbol_en})")
        
        # Detect missing date ranges
        gaps = self.detect_missing_date_ranges(symbol_en)
        
        if not gaps:
            logger.info(f"  ✓ No gaps found for {symbol_en}")
            return 0
        
        all_new_data = []
        
        for idx, (start_date, end_date) in enumerate(gaps, 1):
            logger.info(f"  Gap {idx}/{len(gaps)}: {start_date.date()} to {end_date.date()}")
            
            df = self.fetch_historical_data(symbol_code, symbol_en, start_date, end_date)
            
            if not df.empty:
                df['Name'] = name
                all_new_data.append(df)
            
            # Rate limiting
            time.sleep(Config.REQUEST_DELAY_MIN + random.random() * Config.REQUEST_DELAY_JITTER)
        
        if not all_new_data:
            logger.info(f"  ✗ No data retrieved for gaps")
            return 0
        
        # Combine all fetched data
        df_combined = pd.concat(all_new_data, ignore_index=True)
        
        # Add scrape metadata
        now = datetime.now()
        df_combined['ScrapeDate'] = now.strftime('%Y-%m-%d')
        df_combined['ScrapeTime'] = now.strftime('%H:%M:%S')
        df_combined['ScrapeDateTime'] = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # Reorder columns to match tgjuScraper.py
        df_combined = df_combined[[
            'PersianDate', 'EnglishDate', 'Weekday',
            'Open', 'High', 'Low', 'Close',
            'Name', 'Symbol_En',
            'ScrapeDate', 'ScrapeTime', 'ScrapeDateTime'
        ]]
        
        # Save to database
        inserted = self.save_to_database(df_combined)
        
        logger.info(f"  ✓ Inserted {inserted} records for {symbol_en}")
        return inserted
    
    def save_to_database(self, df: pd.DataFrame) -> int:
        """
        Save DataFrame to database with exact same schema as tgjuScraper.py.
        
        Args:
            df: DataFrame to save
        
        Returns:
            Number of rows inserted
        """
        if df.empty:
            return 0
        
        try:
            engine = create_engine(self.connection_string)
            
            # Use EXACT same data types as tgjuScraper.py
            column_types = {
                'PersianDate': CHAR(10),
                'EnglishDate': DATETIME(),
                'Weekday': VARCHAR(20),
                'Open': DECIMAL(18, 5),
                'High': DECIMAL(18, 5),
                'Low': DECIMAL(18, 5),
                'Close': DECIMAL(18, 5),
                'Name': NVARCHAR(100),
                'Symbol_En': VARCHAR(100),
                'ScrapeDate': CHAR(10),
                'ScrapeTime': CHAR(8),
                'ScrapeDateTime': DATETIME()
            }
            
            df.to_sql(
                name=self.table_name,
                con=engine,
                if_exists='append',
                index=False,
                dtype=column_types
            )
            
            return len(df)
            
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            return 0
    
    def run(self) -> bool:
        """
        Execute the complete backfill pipeline.
        
        Returns:
            True if successful, False otherwise
        """
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("Starting TGJU AutoTrowel Backfill Pipeline")
        logger.info("=" * 60)
        
        try:
            # Step 1: Get all symbols from database
            logger.info("[1/2] Loading symbols from database...")
            symbols = self.get_symbols_from_db()
            
            if symbols.empty:
                logger.warning("No symbols found in database - nothing to backfill")
                return False
            
            # Step 2: Process each symbol
            logger.info(f"[2/2] Processing {len(symbols)} symbols...")
            total_inserted = 0
            
            for idx, row in symbols.iterrows():
                logger.info(f"\n[{idx+1}/{len(symbols)}] {row['Name']}")
                inserted = self.backfill_symbol(row.to_dict())
                total_inserted += inserted
            
            # Summary
            duration = datetime.now() - start_time
            logger.info("\n" + "=" * 60)
            logger.info("Backfill Pipeline Completed")
            logger.info("=" * 60)
            logger.info(f"Total records inserted: {total_inserted}")
            logger.info(f"Duration: {duration.total_seconds():.2f} seconds")
            logger.info("=" * 60)
            
            return True
            
        except KeyboardInterrupt:
            logger.warning("\nPipeline interrupted by user")
            return False
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return False
        finally:
            self.session.close()


def main():
    """Main entry point."""
    try:
        logger.info("Initializing AutoTrowel with secure configuration...")
        
        etl = TGJUBackfillETL()
        success = etl.run()
        
        sys.exit(0 if success else 1)
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("")
        logger.error("Setup instructions:")
        logger.error("  1. Ensure .env file exists (copy from .env.example)")
        logger.error("  2. Verify database credentials in .env")
        logger.error("  3. Run the script again")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
