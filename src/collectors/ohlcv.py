# -*- coding: utf-8 -*-
"""
Daily OHLCV collector — fetches price data from TGJU API.

Enhanced version of the original scraper with volume support and parameterized resolution.
"""

import time
import logging
from datetime import datetime
from typing import List

import pandas as pd

from ..http_client import HttpClient
from ..utils.dates import to_persian_date, to_weekday

logger = logging.getLogger('tgju')

TGJU_API_URL = 'https://platform.tgju.org/fa/tvdata/history'
SECONDS_PER_DAY = 86400

# Supported resolutions
RESOLUTIONS = {
    '1m': '1', '5m': '5', '15m': '15', '30m': '30',
    '1h': '60', '1d': '1D', '1w': 'W', '1M': 'M'
}


class OHLCVCollector:
    """
    Collects OHLCV (Open/High/Low/Close/Volume) data from the TGJU API.

    Supports multiple resolutions from 1-minute to monthly.
    """

    def __init__(self, http_client: HttpClient):
        self.http = http_client

    def collect_latest(self, symbol_code: str, resolution: str = '1D',
                       lookback_seconds: int = SECONDS_PER_DAY) -> pd.DataFrame | None:
        """
        Fetch the latest price data for a symbol.

        Args:
            symbol_code: API symbol code (e.g., 'price_dollar_rl')
            resolution: Price resolution ('1D', '1w', '1M', etc.)
            lookback_seconds: How far back to look

        Returns:
            DataFrame with latest record, or None if failed.
        """
        now = int(time.time())
        from_ts = now - lookback_seconds

        return self._fetch(symbol_code, resolution, from_ts, now, latest_only=True)

    def collect_range(self, symbol_code: str, resolution: str,
                      from_date: datetime, to_date: datetime) -> pd.DataFrame | None:
        """
        Fetch historical data for a symbol within a date range.

        Args:
            symbol_code: API symbol code
            resolution: Price resolution
            from_date: Start date
            to_date: End date

        Returns:
            DataFrame with all records in range, or None if failed.
        """
        from_ts = int(from_date.timestamp())
        to_ts = int(to_date.timestamp())

        return self._fetch(symbol_code, resolution, from_ts, to_ts, latest_only=False)

    def _fetch(self, symbol_code: str, resolution: str,
               from_ts: int, to_ts: int, latest_only: bool = False) -> pd.DataFrame | None:
        """Internal fetch method."""
        url = (
            f"{TGJU_API_URL}?"
            f"symbol={symbol_code}&"
            f"resolution={resolution}&"
            f"from={from_ts}&"
            f"to={to_ts}"
        )

        response = self.http.get(url)
        if response is None:
            return None

        try:
            api_data = response.json()
        except ValueError:
            logger.error(f"Invalid JSON for {symbol_code}")
            return None

        if not api_data or 't' not in api_data or not api_data['t']:
            return None

        # Build DataFrame — pad shorter arrays to match time axis
        n = len(api_data['t'])
        df = pd.DataFrame({
            'Date': api_data['t'],
            'Open': (api_data.get('o') or [0]*n)[:n],
            'High': (api_data.get('h') or [0]*n)[:n],
            'Low': (api_data.get('l') or [0]*n)[:n],
            'Close': (api_data.get('c') or [0]*n)[:n],
            'Volume': (api_data.get('v') or [0]*n)[:n],
        })

        if df.empty:
            return None

        # Convert timestamps
        df['Date'] = df['Date'].apply(lambda ts: datetime.fromtimestamp(ts))
        df['PersianDate'] = df['Date'].apply(to_persian_date)
        df['Weekday'] = df['Date'].apply(to_weekday)

        if latest_only:
            df = df.iloc[[-1]]

        return df

    def collect_batch(self, symbols: List[dict], resolution: str = '1D',
                      lookback_seconds: int = SECONDS_PER_DAY) -> pd.DataFrame:
        """
        Collect latest data for multiple symbols.

        Args:
            symbols: List of dicts with 'symbol_Fa', 'SYMBOL', 'symbol_En' keys
            resolution: Price resolution
            lookback_seconds: How far back to look

        Returns:
            Combined DataFrame with all collected data.
        """
        results = []
        successful = 0
        failed = 0

        for i, sym in enumerate(symbols, 1):
            symbol_code = sym['SYMBOL']
            symbol_fa = sym['symbol_Fa']
            symbol_en = sym['symbol_En']

            logger.debug(f"[{i}/{len(symbols)}] Fetching {symbol_fa} ({symbol_code})")

            df = self.collect_latest(symbol_code, resolution, lookback_seconds)

            if df is not None and not df.empty:
                df['Name'] = symbol_fa
                df['Symbol_En'] = symbol_en
                results.append(df)
                successful += 1
            else:
                failed += 1

            self.http.sleep_between_requests()

        logger.info(f"Batch collection: {successful} succeeded, {failed} failed")

        if not results:
            return pd.DataFrame()

        combined = pd.concat(results, ignore_index=True)

        # Add scrape metadata
        now = datetime.now()
        combined['ScrapeDate'] = now.strftime('%Y-%m-%d')
        combined['ScrapeTime'] = now.strftime('%H:%M:%S')
        combined['ScrapeDateTime'] = now.strftime('%Y-%m-%d %H:%M:%S')

        return combined
