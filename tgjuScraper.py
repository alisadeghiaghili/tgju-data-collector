# -*- coding: utf-8 -*-
"""
TGJU Market Data Scraper with Database Integration

This module provides functionality to scrape real-time market data from TGJU.org
(Tehran Gold and Jewelry Union) and store it in SQL Server. It handles symbol
retrieval, HTTP requests with retry logic, and database operations.

Created: 2025-08-31
Author: sadeghi.a
"""

import sys
import requests
import pandas as pd
import calendar
import jdatetime
from bs4 import BeautifulSoup
from lxml import etree
from datetime import datetime
from sqlalchemy import create_engine, CHAR, VARCHAR, NVARCHAR, DATETIME, DECIMAL
import warnings
import time
import random
import os

warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)

# ===== CONFIGURATION CONSTANTS =====

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
CONNECTION_TIMEOUT_WAIT = 600  # 10 minutes in seconds
SHORT_RETRY_DELAY_MIN = 2
SHORT_RETRY_DELAY_JITTER = 1
REQUEST_DELAY_MIN = 0.5
REQUEST_DELAY_JITTER = 0.5
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 100000

TGJU_MAIN_URL = 'https://www.tgju.org'
TGJU_ENERGY_URL = 'https://www.tgju.org/energy'
TGJU_API_URL = 'https://platform.tgju.org/fa/tvdata/history'

SECONDS_PER_DAY = 86400


# ===== SAFE HTTP REQUEST MODULE =====

def safe_request(url, headers=None, max_retries=DEFAULT_MAX_RETRIES, 
                 timeout=DEFAULT_TIMEOUT):
    """
    Execute HTTP GET request with automatic retry logic and error handling.
    
    Implements resilience patterns for network failures:
    - Handles timeout errors with extended wait periods (10 min)
    - Manages connection errors with exponential backoff
    - Validates HTTP response status codes
    
    Args:
        url (str): Target URL for the GET request
        headers (dict, optional): HTTP headers dictionary. Defaults to None
        max_retries (int): Number of retry attempts. Defaults to 3
        timeout (int): Request timeout in seconds. Defaults to 100000
        
    Returns:
        requests.Response: HTTP response object if successful, None otherwise
        
    Example:
        >>> response = safe_request('https://www.tgju.org')
        >>> if response:
        ...     data = response.json()
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
            
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as conn_error:
            error_message = str(conn_error)
            print(f"[RETRY] {url} attempt {attempt+1}/{max_retries} failed: {conn_error}")
            
            # Distinguish connection timeout from other connection errors
            if "Connection to" in error_message and "timed out" in error_message:
                if attempt < max_retries - 1:
                    print(f"[WAIT] Connection timeout detected. "
                          f"Waiting {CONNECTION_TIMEOUT_WAIT // 60} minutes before retry...")
                    time.sleep(CONNECTION_TIMEOUT_WAIT)
                else:
                    print(f"[SKIP] Max retries reached for {url} "
                          f"after connection timeouts.")
                    return None
            else:
                # Other connection errors use shorter delay with jitter
                if attempt < max_retries - 1:
                    delay = SHORT_RETRY_DELAY_MIN + random.random() * SHORT_RETRY_DELAY_JITTER
                    time.sleep(delay)
                    
        except (requests.exceptions.HTTPError,
                requests.exceptions.RequestException) as http_error:
            print(f"[RETRY] {url} attempt {attempt+1}/{max_retries} failed: {http_error}")
            if attempt < max_retries - 1:
                delay = SHORT_RETRY_DELAY_MIN + random.random() * SHORT_RETRY_DELAY_JITTER
                time.sleep(delay)
    
    print(f"[SKIP] Failed to fetch {url} after {max_retries} retries.")
    return None


# ===== SYMBOL SCRAPING MODULE =====

def _extract_xpaths_safely(response, xpath_queries):
    """
    Safely parse HTML and extract data using XPath expressions.
    
    Helper function to reduce code duplication when parsing HTML responses
    and applying multiple XPath queries.
    
    Args:
        response (requests.Response): HTTP response object
        xpath_queries (dict): Mapping of result keys to XPath expression strings
        
    Returns:
        dict: Dictionary with extracted data, or empty dict if parsing fails
        
    Example:
        >>> paths = {'href': '//a/@href', 'text': '//a//text()'}
        >>> data = _extract_xpaths_safely(response, paths)
    """
    try:
        soup = BeautifulSoup(response.content, "html.parser")
        dom = etree.HTML(str(soup))
        
        extracted = {}
        for key, xpath_expr in xpath_queries.items():
            extracted[key] = dom.xpath(xpath_expr)
        
        return extracted
    except Exception as parse_error:
        print(f"[ERROR] Failed to parse HTML: {parse_error}")
        return {}


def get_main_symbols():
    """
    Retrieve commodity symbols from main TGJU navigation menu.
    
    Scrapes the main TGJU website to extract commodity symbols and their
    corresponding URLs. Performs validation to ensure data quality:
    - Removes duplicate symbols
    - Filters entries with incorrect URL structure
    - Normalizes symbol format
    
    Returns:
        pd.DataFrame: DataFrame with columns [symbol_Fa, symbol_En, SYMBOL]
                      Returns empty DataFrame if fetch/parse fails
    """
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    response = safe_request(TGJU_MAIN_URL, headers=headers)
    
    if response is None:
        print("[ERROR] Could not fetch main symbols page")
        return pd.DataFrame()
    
    xpath_mappings = {
        'href': '//div[@class = "nav-links"]/div[2]/ul/li/div/div/ul/li/ul/li/a/@href',
        'symbol_Fa': '//div[@class = "nav-links"]/div[2]/ul/li/div/div/ul/li/ul/li/a//text()'
    }
    
    extracted = _extract_xpaths_safely(response, xpath_mappings)
    
    if not extracted.get('href') or not extracted.get('symbol_Fa'):
        print("[ERROR] Could not extract symbols from main page")
        return pd.DataFrame()
    
    # Create DataFrame and validate structure
    df = pd.DataFrame({'href': extracted['href'], 
                       'symbol_Fa': extracted['symbol_Fa']})
    
    # Count 'profile' occurrences in URL to filter correct structure
    df['_profile_count'] = df['href'].apply(lambda x: x.count('profile'))
    df = df.drop_duplicates(subset='symbol_Fa')
    df = df[df['_profile_count'] == 1].drop('_profile_count', axis=1)
    
    # Extract English symbol from URL
    df = df.set_index('symbol_Fa')
    df['symbol_En'] = df['href'].apply(lambda x: x.split('/')[-1])
    
    # Handle special case for second-hand gold
    if 'طلای دست دوم' in df.index:
        df.loc['طلای دست دوم', 'symbol_En'] = 'gold_mini_size'
    
    df = df.reset_index()
    df['SYMBOL'] = df['symbol_En'].apply(lambda x: x.upper())
    df = df.drop('href', axis=1).drop_duplicates()
    
    return df


def get_energy_symbols():
    """
    Retrieve energy commodity symbols from TGJU energy section.
    
    Scrapes the dedicated energy page to extract oil and gas commodity symbols.
    Uses table-based parsing for structured data extraction.
    
    Returns:
        pd.DataFrame: DataFrame with columns [symbol_Fa, symbol_En, SYMBOL]
                      Returns empty DataFrame if fetch/parse fails
    """
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    response = safe_request(TGJU_ENERGY_URL, headers=headers)
    
    if response is None:
        print("[ERROR] Could not fetch energy symbols page")
        return pd.DataFrame()
    
    xpath_mappings = {
        'symbol_Fa': '//table[contains(@class,"market-table")]/tbody/tr/th/span/following-sibling::text()',
        'href': '//table[contains(@class,"market-table")]/tbody/tr/@onclick'
    }
    
    extracted = _extract_xpaths_safely(response, xpath_mappings)
    
    if not extracted.get('symbol_Fa') or not extracted.get('href'):
        print("[ERROR] Could not extract symbols from energy page")
        return pd.DataFrame()
    
    df = pd.DataFrame({'symbol_Fa': extracted['symbol_Fa'], 
                       'href': extracted['href']})
    
    # Extract English symbol from onclick attribute, removing trailing bracket
    df['symbol_En'] = df['href'].apply(lambda x: x.split('/')[-1][:-1])
    df['SYMBOL'] = df['symbol_En'].apply(lambda x: x.upper())
    
    df = df.drop_duplicates().drop('href', axis=1)
    return df


def get_df_of_symbols():
    """
    Aggregate symbols from all available sources.
    
    Combines symbols from both main and energy pages, removes duplicates,
    and validates data consistency. Ensures that symbol_En matches SYMBOL
    (uppercase conversion).
    
    Returns:
        pd.DataFrame: Clean, deduplicated symbol list ready for scraping
        
    Raises:
        RuntimeError: If no symbols could be fetched from any source
    """
    print("[INFO] Fetching main symbols...")
    df_main = get_main_symbols()
    
    print("[INFO] Fetching energy symbols...")
    df_energy = get_energy_symbols()
    
    # Combine available dataframes
    df_list = [df for df in [df_main, df_energy] if not df.empty]
    
    if not df_list:
        raise RuntimeError("No symbols could be fetched from any source!")
    
    df = pd.concat(df_list, axis=0, ignore_index=True)
    
    # Validation: symbol_En should match SYMBOL when uppercased
    df['_is_valid'] = df.apply(
        lambda row: row['symbol_En'].upper() == row['SYMBOL'],
        axis=1
    )
    
    # Keep only valid entries
    df = df[df['_is_valid']].drop('_is_valid', axis=1)
    df = df.drop_duplicates().reset_index(drop=True)
    
    print(f"[INFO] Found {len(df)} symbols to scrape")
    return df


# ===== DATA SCRAPING MODULE =====

def get_tgju_data(symbol, df_of_symbols, max_retries=DEFAULT_MAX_RETRIES):
    """
    Fetch latest price data for a specific commodity symbol.
    
    Retrieves 24-hour historical data for a symbol and extracts the most
    recent price record. Performs comprehensive validation:
    - Verifies symbol exists in lookup table
    - Checks JSON response structure
    - Validates data consistency (same row lengths)
    - Converts timestamps and date formats
    
    Args:
        symbol (str): Persian symbol name
        df_of_symbols (pd.DataFrame): Symbol lookup reference table
        max_retries (int): Retry attempts for API request. Defaults to 3
        
    Returns:
        pd.DataFrame: Single row with latest price data, or None if failed
        
    Note:
        Price data includes: Open, High, Low, Close, Persian date, English date,
        and weekday information.
    """
    try:
        # Validate symbol exists
        if symbol not in df_of_symbols['symbol_Fa'].values:
            print(f"[SKIP] Symbol {symbol} not found in symbol list.")
            return None
        
        # Look up symbol identifiers
        symbol_row = df_of_symbols[df_of_symbols['symbol_Fa'] == symbol]
        symbol_code = symbol_row['SYMBOL'].values[0]
        symbol_en = symbol_row['symbol_En'].values[0]
        
        # Prepare API request
        headers = {"User-Agent": DEFAULT_USER_AGENT}
        current_timestamp = int(time.time())
        from_timestamp = current_timestamp - SECONDS_PER_DAY
        
        url = (f"{TGJU_API_URL}?"
               f"symbol={symbol_code}&"
               f"resolution=1D&"
               f"from={from_timestamp}&"
               f"to={current_timestamp}")
        
        # Execute request with retry logic
        response = safe_request(url, headers=headers, max_retries=max_retries)
        if response is None:
            return None
        
        # Parse JSON response
        try:
            api_response = response.json()
        except ValueError as json_error:
            print(f"[ERROR] Invalid JSON response for {symbol}: {json_error}")
            return None
        
        # Validate response structure and data availability
        if not api_response or "t" not in api_response:
            print(f"[SKIP] No valid data structure for {symbol}.")
            return None
        
        if not api_response["t"] or len(api_response["t"]) == 0:
            print(f"[SKIP] No time data for {symbol}.")
            return None
        
        # Create DataFrame from API response
        df_data = pd.DataFrame({
            'Date': api_response['t'],
            'Open': api_response.get('o', []),
            'High': api_response.get('h', []),
            'Low': api_response.get('l', []),
            'Close': api_response.get('c', [])
        })
        
        # Verify data integrity
        date_length = len(df_data['Date'])
        if not all(len(df_data[col]) == date_length for col in df_data.columns):
            print(f"[ERROR] Inconsistent data lengths for {symbol}")
            return None
        
        # Extract latest record
        if len(df_data) == 0:
            print(f"[SKIP] No data records for {symbol}.")
            return None
        
        df_data = df_data.iloc[[-1]]  # Get last row only
        
        # Convert Unix timestamp to datetime
        df_data['Date'] = df_data['Date'].apply(
            lambda timestamp: datetime.fromtimestamp(timestamp)
        )
        df_data['EnglishDate'] = pd.to_datetime(df_data['Date'])
        
        # Extract date components
        df_data['Weekday'] = df_data['EnglishDate'].dt.weekday.apply(
            lambda day_num: calendar.day_name[day_num]
        )
        
        # Convert to Persian calendar
        df_data['PersianDate'] = df_data['EnglishDate'].apply(
            lambda eng_date: str(jdatetime.date.fromgregorian(
                date=eng_date.date()
            ))
        )
        
        # Add symbol identifiers
        df_data['Name'] = symbol
        df_data['Symbol_En'] = symbol_en
        
        # Select and reorder output columns
        output_columns = ['PersianDate', 'EnglishDate', 'Weekday',
                         'Open', 'High', 'Low', 'Close', 'Name', 'Symbol_En']
        
        return df_data[output_columns]
        
    except Exception as error:
        print(f"[ERROR] Unexpected error for {symbol}: {error}")
        return None


# ===== MAIN EXECUTION MODULE =====

def main():
    """
    Main execution orchestrator for symbol discovery and data collection.
    
    Workflow:
    1. Retrieve all available symbols
    2. Iterate through symbols and scrape latest price data
    3. Combine results and add metadata timestamps
    4. Validate that at least some data was collected
    5. Save to database
    
    Includes comprehensive logging and error handling.
    """
    try:
        # Phase 1: Symbol Discovery
        print("[INFO] Starting symbol collection...")
        symbols = get_df_of_symbols()
        
        if symbols.empty:
            raise RuntimeError("No symbols available for scraping!")
        
        # Phase 2: Data Collection
        print(f"[INFO] Starting latest data scraping for {len(symbols)} symbols...")
        results = []
        successful_count = 0
        failed_count = 0
        
        for index, symbol in enumerate(symbols['symbol_Fa'], 1):
            print(f"[INFO] Processing {index}/{len(symbols)}: {symbol}")
            
            try:
                df = get_tgju_data(symbol, symbols)
                
                if df is not None and not df.empty:
                    results.append(df)
                    successful_count += 1
                    print(f"[SUCCESS] Got latest record for {symbol}")
                else:
                    failed_count += 1
                    print(f"[FAILED] Could not get data for {symbol}")
                    
            except Exception as symbol_error:
                failed_count += 1
                print(f"[ERROR] Exception occurred for {symbol}: {symbol_error}")
                print("[SKIP] Continuing with next symbol...")
                continue
            
            # Rate limiting: polite delay between requests
            delay = REQUEST_DELAY_MIN + random.random() * REQUEST_DELAY_JITTER
            time.sleep(delay)
        
        # Phase 3: Results Aggregation
        print(f"\n[SUMMARY] Latest data scraping complete!")
        print(f"[SUMMARY] Successful: {successful_count}")
        print(f"[SUMMARY] Failed: {failed_count}")
        
        if not results:
            print("[WARNING] No data scraped successfully!")
            sys.exit(1)
        
        # Combine all results
        final_data = pd.concat(results, ignore_index=True)
        
        # Add collection metadata
        now = datetime.now()
        final_data['ScrapeDate'] = now.strftime('%Y-%m-%d')
        final_data['ScrapeTime'] = now.strftime('%H:%M:%S')
        final_data['ScrapeDateTime'] = now.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"[INFO] Final dataset contains {len(final_data)} latest records")
        
        return final_data
        
    except Exception as fatal_error:
        print(f"[FATAL ERROR] Script failed: {fatal_error}")
        sys.exit(1)


# ===== DATABASE PERSISTENCE MODULE =====

def save_to_database(data):
    """
    Persist scraped data to SQL Server database.
    
    Connects to MSSQL database and appends records using SQLAlchemy.
    Specifies data types for each column to ensure proper storage:
    - CHAR for fixed-length strings (dates, time)
    - VARCHAR for variable-length strings (symbols, names)
    - NVARCHAR for Unicode text (Persian names)
    - DECIMAL for numerical prices
    - DATETIME for timestamp fields
    
    Args:
        data (pd.DataFrame): DataFrame with scraped data to persist
        
    Note:
        Database connection string should use environment variables or
        configuration file instead of hardcoding credentials.
    """
    # Define column data types for SQL Server
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
    
    # Get database connection from environment or use default
    # IMPORTANT: Use environment variables for credentials, never hardcode!
    connection_string = os.getenv(
        'TGJU_DB_CONNECTION',
        'mssql+pyodbc://sadeghi.a@SADEGHI/scrape?'
        'driver=ODBC+Driver+17+for+SQL+Server&'
        'trusted_connection=yes'
    )
    
    try:
        engine = create_engine(connection_string)
        
        data.to_sql(
            name='TgjuAssets',
            con=engine,
            if_exists='append',
            index=False,
            dtype=column_types
        )
        
        print(f"[SUCCESS] Inserted {len(data)} rows into TgjuAssets table.")
        
    except Exception as db_error:
        print(f"[DB ERROR] Failed to insert data: {db_error}")
        sys.exit(1)


# ===== ENTRY POINT =====

if __name__ == "__main__":
    # Execute main workflow
    final_dataset = main()
    
    # Persist to database
    save_to_database(final_dataset)
    
    print("[INFO] Script execution completed successfully!")
