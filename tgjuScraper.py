# -*- coding: utf-8 -*-
"""
TGJU Market Data Scraper with Database Integration

This module provides functionality to scrape real-time market data from TGJU.org
(Tehran Gold and Jewelry Union) and store it in SQL Server. It handles symbol
retrieval, HTTP requests with retry logic, and database operations.

Environment Variables Required:
    See .env.example for complete list of required variables.
    
    Quick setup:
    1. Copy .env.example to .env
    2. Fill in your database credentials
    3. Run: python tgjuScraper.py

Created: 2025-08-31
Author: sadeghi.a
"""

import sys
import logging
import logging.handlers
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

# Import secure configuration module
from config import get_connection_string, get_table_name, load_env_file

warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)

# ===== LOGGING CONFIGURATION =====

def setup_logging():
    """
    Configure logging with both file and console handlers.
    
    Creates 'tgju_scraper.log' file and outputs to console with timestamps
    and consistent formatting for all log levels.
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_filename = 'tgju_scraper.log'
    
    # Create logger
    logger = logging.getLogger('tgju_scraper')
    logger.setLevel(logging.DEBUG)
    
    # File handler - logs everything
    file_handler = logging.handlers.RotatingFileHandler(
        log_filename,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler - logs INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)-8s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logging()

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
            logger.debug(f"Attempting request to {url} (attempt {attempt+1}/{max_retries})")
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            logger.debug(f"Successfully fetched {url}")
            return response
            
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as conn_error:
            error_message = str(conn_error)
            logger.warning(f"Connection error for {url} attempt {attempt+1}/{max_retries}: {conn_error}")
            
            # Distinguish connection timeout from other connection errors
            if "Connection to" in error_message and "timed out" in error_message:
                if attempt < max_retries - 1:
                    wait_minutes = CONNECTION_TIMEOUT_WAIT // 60
                    logger.info(f"Connection timeout detected. Waiting {wait_minutes} minutes before retry...")
                    time.sleep(CONNECTION_TIMEOUT_WAIT)
                else:
                    logger.error(f"Max retries reached for {url} after connection timeouts.")
                    return None
            else:
                # Other connection errors use shorter delay with jitter
                if attempt < max_retries - 1:
                    delay = SHORT_RETRY_DELAY_MIN + random.random() * SHORT_RETRY_DELAY_JITTER
                    logger.debug(f"Waiting {delay:.2f}s before retry...")
                    time.sleep(delay)
                    
        except (requests.exceptions.HTTPError,
                requests.exceptions.RequestException) as http_error:
            logger.warning(f"HTTP error for {url} attempt {attempt+1}/{max_retries}: {http_error}")
            if attempt < max_retries - 1:
                delay = SHORT_RETRY_DELAY_MIN + random.random() * SHORT_RETRY_DELAY_JITTER
                logger.debug(f"Waiting {delay:.2f}s before retry...")
                time.sleep(delay)
    
    logger.error(f"Failed to fetch {url} after {max_retries} retries.")
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
        logger.debug("Parsing HTML response with BeautifulSoup and lxml")
        soup = BeautifulSoup(response.content, "html.parser")
        dom = etree.HTML(str(soup))
        
        extracted = {}
        for key, xpath_expr in xpath_queries.items():
            result = dom.xpath(xpath_expr)
            extracted[key] = result
            logger.debug(f"XPath '{key}' extracted {len(result)} items")
        
        return extracted
    except Exception as parse_error:
        logger.error(f"Failed to parse HTML: {parse_error}", exc_info=True)
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
    logger.info("Fetching main symbols from TGJU website...")
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    response = safe_request(TGJU_MAIN_URL, headers=headers)
    
    if response is None:
        logger.error("Could not fetch main symbols page")
        return pd.DataFrame()
    
    xpath_mappings = {
        'href': '//div[@class = "nav-links"]/div[2]/ul/li/div/div/ul/li/ul/li/a/@href',
        'symbol_Fa': '//div[@class = "nav-links"]/div[2]/ul/li/div/div/ul/li/ul/li/a//text()'
    }
    
    extracted = _extract_xpaths_safely(response, xpath_mappings)
    
    if not extracted.get('href') or not extracted.get('symbol_Fa'):
        logger.error("Could not extract symbols from main page")
        return pd.DataFrame()
    
    # Create DataFrame and validate structure
    df = pd.DataFrame({'href': extracted['href'], 
                       'symbol_Fa': extracted['symbol_Fa']})
    logger.debug(f"Extracted {len(df)} initial symbol entries")
    
    # Count 'profile' occurrences in URL to filter correct structure
    df['_profile_count'] = df['href'].apply(lambda x: x.count('profile'))
    df = df.drop_duplicates(subset='symbol_Fa')
    df = df[df['_profile_count'] == 1].drop('_profile_count', axis=1)
    logger.debug(f"Filtered to {len(df)} valid entries after URL validation")
    
    # Extract English symbol from URL
    df = df.set_index('symbol_Fa')
    df['symbol_En'] = df['href'].apply(lambda x: x.split('/')[-1])
    
    # Handle special case for second-hand gold
    if 'طلای دست دوم' in df.index:
        df.loc['طلای دست دوم', 'symbol_En'] = 'gold_mini_size'
        logger.debug("Applied special case mapping for second-hand gold")
    
    df = df.reset_index()
    df['SYMBOL'] = df['symbol_En'].apply(lambda x: x.upper())
    df = df.drop('href', axis=1).drop_duplicates()
    
    logger.info(f"Successfully extracted {len(df)} main symbols")
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
    logger.info("Fetching energy symbols from TGJU energy section...")
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    response = safe_request(TGJU_ENERGY_URL, headers=headers)
    
    if response is None:
        logger.error("Could not fetch energy symbols page")
        return pd.DataFrame()
    
    xpath_mappings = {
        'symbol_Fa': '//table[contains(@class,"market-table")]/tbody/tr/th/span/following-sibling::text()',
        'href': '//table[contains(@class,"market-table")]/tbody/tr/@onclick'
    }
    
    extracted = _extract_xpaths_safely(response, xpath_mappings)
    
    if not extracted.get('symbol_Fa') or not extracted.get('href'):
        logger.error("Could not extract symbols from energy page")
        return pd.DataFrame()
    
    df = pd.DataFrame({'symbol_Fa': extracted['symbol_Fa'], 
                       'href': extracted['href']})
    logger.debug(f"Extracted {len(df)} initial energy symbol entries")
    
    # Extract English symbol from onclick attribute, removing trailing bracket
    df['symbol_En'] = df['href'].apply(lambda x: x.split('/')[-1][:-1])
    df['SYMBOL'] = df['symbol_En'].apply(lambda x: x.upper())
    
    df = df.drop_duplicates().drop('href', axis=1)
    logger.info(f"Successfully extracted {len(df)} energy symbols")
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
    logger.info("Starting symbol aggregation...")
    df_main = get_main_symbols()
    df_energy = get_energy_symbols()
    
    # Combine available dataframes
    df_list = [df for df in [df_main, df_energy] if not df.empty]
    
    if not df_list:
        error_msg = "No symbols could be fetched from any source!"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
    
    df = pd.concat(df_list, axis=0, ignore_index=True)
    logger.debug(f"Combined {len(df)} symbols from all sources")
    
    # Validation: symbol_En should match SYMBOL when uppercased
    df['_is_valid'] = df.apply(
        lambda row: row['symbol_En'].upper() == row['SYMBOL'],
        axis=1
    )
    
    # Keep only valid entries
    invalid_count = (~df['_is_valid']).sum()
    df = df[df['_is_valid']].drop('_is_valid', axis=1)
    if invalid_count > 0:
        logger.warning(f"Filtered out {invalid_count} invalid symbol entries")
    
    df = df.drop_duplicates().reset_index(drop=True)
    logger.info(f"Final symbol list prepared with {len(df)} symbols")
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
            logger.debug(f"Symbol '{symbol}' not found in symbol list")
            return None
        
        # Look up symbol identifiers
        symbol_row = df_of_symbols[df_of_symbols['symbol_Fa'] == symbol]
        symbol_code = symbol_row['SYMBOL'].values[0]
        symbol_en = symbol_row['symbol_En'].values[0]
        logger.debug(f"Looking up data for symbol: {symbol} (EN: {symbol_en}, CODE: {symbol_code})")
        
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
            logger.warning(f"Failed to fetch data for symbol: {symbol}")
            return None
        
        # Parse JSON response
        try:
            api_response = response.json()
            logger.debug(f"Successfully parsed JSON response for {symbol}")
        except ValueError as json_error:
            logger.error(f"Invalid JSON response for {symbol}: {json_error}")
            return None
        
        # Validate response structure and data availability
        if not api_response or "t" not in api_response:
            logger.debug(f"No valid data structure for {symbol}")
            return None
        
        if not api_response["t"] or len(api_response["t"]) == 0:
            logger.debug(f"No time data received for {symbol}")
            return None
        
        # Create DataFrame from API response
        df_data = pd.DataFrame({
            'Date': api_response['t'],
            'Open': api_response.get('o', []),
            'High': api_response.get('h', []),
            'Low': api_response.get('l', []),
            'Close': api_response.get('c', [])
        })
        logger.debug(f"Created DataFrame with {len(df_data)} records for {symbol}")
        
        # Verify data integrity
        date_length = len(df_data['Date'])
        if not all(len(df_data[col]) == date_length for col in df_data.columns):
            logger.error(f"Inconsistent data lengths for {symbol}")
            return None
        
        # Extract latest record
        if len(df_data) == 0:
            logger.debug(f"No data records available for {symbol}")
            return None
        
        df_data = df_data.iloc[[-1]]  # Get last row only
        logger.debug(f"Extracted latest record for {symbol}")
        
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
        
        result = df_data[output_columns]
        logger.info(f"Successfully scraped data for {symbol} on {result['PersianDate'].values[0]}")
        return result
        
    except Exception as error:
        logger.error(f"Unexpected error processing {symbol}: {error}", exc_info=True)
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
    logger.info("="*60)
    logger.info("TGJU Data Collector started")
    logger.info("="*60)
    
    try:
        # Phase 1: Symbol Discovery
        logger.info("Phase 1: Symbol Discovery - Starting symbol collection...")
        symbols = get_df_of_symbols()
        
        if symbols.empty:
            error_msg = "No symbols available for scraping!"
            logger.critical(error_msg)
            raise RuntimeError(error_msg)
        
        # Phase 2: Data Collection
        logger.info(f"Phase 2: Data Collection - Starting scraping for {len(symbols)} symbols...")
        results = []
        successful_count = 0
        failed_count = 0
        
        for index, symbol in enumerate(symbols['symbol_Fa'], 1):
            logger.debug(f"Processing {index}/{len(symbols)}: {symbol}")
            
            try:
                df = get_tgju_data(symbol, symbols)
                
                if df is not None and not df.empty:
                    results.append(df)
                    successful_count += 1
                else:
                    failed_count += 1
                    logger.debug(f"Could not get data for {symbol}")
                    
            except Exception as symbol_error:
                failed_count += 1
                logger.error(f"Exception occurred for {symbol}: {symbol_error}", exc_info=True)
                continue
            
            # Rate limiting: polite delay between requests
            delay = REQUEST_DELAY_MIN + random.random() * REQUEST_DELAY_JITTER
            time.sleep(delay)
        
        # Phase 3: Results Aggregation
        logger.info(f"Phase 3: Results Aggregation")
        logger.info(f"Scraping completed - Successful: {successful_count}, Failed: {failed_count}")
        
        if not results:
            error_msg = "No data scraped successfully!"
            logger.critical(error_msg)
            sys.exit(1)
        
        # Combine all results
        final_data = pd.concat(results, ignore_index=True)
        logger.info(f"Combined results: {len(final_data)} records")
        
        # Add collection metadata
        now = datetime.now()
        final_data['ScrapeDate'] = now.strftime('%Y-%m-%d')
        final_data['ScrapeTime'] = now.strftime('%H:%M:%S')
        final_data['ScrapeDateTime'] = now.strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"Final dataset contains {len(final_data)} records with metadata")
        return final_data
        
    except Exception as fatal_error:
        logger.critical(f"Script failed: {fatal_error}", exc_info=True)
        sys.exit(1)


# ===== DATABASE PERSISTENCE MODULE =====

def save_to_database(data):
    """
    Persist scraped data to SQL Server database.
    
    Connects to MSSQL database and appends records using SQLAlchemy.
    Uses secure configuration from config module.
    Specifies exact data types for each column to ensure proper storage:
    - CHAR for fixed-length strings (dates, time)
    - VARCHAR for variable-length strings (symbols, names)
    - NVARCHAR for Unicode text (Persian names)
    - DECIMAL for numerical prices
    - DATETIME for timestamp fields
    
    Args:
        data (pd.DataFrame): DataFrame with scraped data to persist
        
    Raises:
        ValueError: If database configuration is missing or invalid
        Exception: If database insertion fails
    """
    logger.info("Phase 4: Database Persistence - Starting database insertion...")
    
    # Define column data types for SQL Server (EXACT same as before)
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
    
    try:
        # Load environment variables from .env file
        logger.info("Loading database configuration...")
        load_env_file()
        
        # Get secure connection string from config module
        connection_string = get_connection_string(prefix='TGJU_DB')
        logger.debug("Database connection string loaded successfully")
        
        # Get table name from config (defaults to 'TgjuAssets')
        table_name = get_table_name(prefix='TGJU_DB', default='TgjuAssets')
        
        # Create database engine
        logger.info(f"Connecting to database...")
        engine = create_engine(connection_string)
        
        # Insert data into database
        logger.info(f"Inserting {len(data)} rows into {table_name} table...")
        data.to_sql(
            name=table_name,
            con=engine,
            if_exists='append',
            index=False,
            dtype=column_types
        )
        
        logger.info(f"Successfully inserted {len(data)} rows into {table_name} table.")
        
    except ValueError as config_error:
        logger.critical(f"Configuration error: {config_error}")
        logger.info("\nPlease ensure:")
        logger.info("1. .env file exists (copy from .env.example)")
        logger.info("2. All required variables are set (TGJU_DB_SERVER, TGJU_DB_NAME, etc.)")
        logger.info("3. No placeholder values remain in .env file")
        sys.exit(1)
        
    except Exception as db_error:
        error_msg = f"Failed to insert data into database: {db_error}"
        logger.critical(error_msg, exc_info=True)
        sys.exit(1)


# ===== ENTRY POINT =====

if __name__ == "__main__":
    try:
        # Execute main workflow
        final_dataset = main()
        
        # Persist to database
        save_to_database(final_dataset)
        
        logger.info("="*60)
        logger.info("Script execution completed successfully!")
        logger.info("="*60)
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
