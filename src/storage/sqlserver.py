# -*- coding: utf-8 -*-
"""SQL Server storage backend for TGJU Data Collector."""

import logging
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, CHAR, VARCHAR, NVARCHAR, DATETIME, DECIMAL, BigInteger
from sqlalchemy.exc import SQLAlchemyError

from ..config import get_connection_string, get_table_name

logger = logging.getLogger('tgju')


class SQLServerStorage:
    """SQL Server storage backend using SQLAlchemy."""

    def __init__(self, connection_string: str = None, table_name: str = None):
        self.connection_string = connection_string or get_connection_string()
        self.table_name = table_name or get_table_name()
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(self.connection_string)
        return self._engine

    def save_daily_ohlcv(self, data: pd.DataFrame) -> int:
        """
        Save daily OHLCV data to the legacy TgjuAssets table.

        Maintains exact same schema as the original tgjuScraper.py.
        """
        if data.empty:
            return 0

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

        # Only include columns that exist in the table
        cols_to_write = [c for c in column_types if c in data.columns]
        df_write = data[cols_to_write]

        try:
            df_write.to_sql(
                name=self.table_name,
                con=self.engine,
                if_exists='append',
                index=False,
                dtype={k: v for k, v in column_types.items() if k in cols_to_write}
            )
            logger.info(f"Saved {len(df_write)} rows to {self.table_name}")
            return len(df_write)
        except SQLAlchemyError as e:
            logger.error(f"Database error saving daily OHLCV: {e}")
            return 0

    def save_symbols(self, symbols_df: pd.DataFrame) -> int:
        """Save discovered symbols to the Symbols table."""
        if symbols_df.empty:
            return 0

        try:
            now = datetime.now()
            symbols_df['IsActive'] = True
            symbols_df['DiscoveredAt'] = now
            symbols_df['LastUpdated'] = now

            # Rename columns to match model
            df = symbols_df.rename(columns={
                'SYMBOL': 'SymbolCode',
                'symbol_Fa': 'SymbolFa',
                'symbol_En': 'SymbolEn',
                'SourcePage': 'SourcePage',
                'Category': 'Category'
            })

            # Select only model columns
            model_cols = ['SymbolCode', 'SymbolFa', 'SymbolEn', 'SourcePage',
                          'Category', 'IsActive', 'DiscoveredAt', 'LastUpdated']
            df = df[[c for c in model_cols if c in df.columns]]

            df.to_sql(
                name='Symbols',
                con=self.engine,
                if_exists='append',
                index=False
            )
            logger.info(f"Saved {len(df)} symbols to Symbols table")
            return len(df)
        except SQLAlchemyError as e:
            logger.error(f"Database error saving symbols: {e}")
            return 0

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        try:
            from sqlalchemy import inspect
            inspector = inspect(self.engine)
            return table_name in inspector.get_table_names()
        except Exception:
            return False
