# TGJU Data Collector

> بهینه شده و تمیز شده برای production | Optimized for production use

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-green.svg)
![Code Quality](https://img.shields.io/badge/Code%20Quality-Sonar%20Verified-brightgreen.svg)

Real-time market data scraper for TGJU.org (Tehran Gold and Jewelry Union) with automated database persistence to SQL Server.

## Features ✨

- **Smart Symbol Discovery**: Automatically fetches commodity symbols from main and energy sections
- **Resilient HTTP Requests**: Implements retry logic with exponential backoff for network failures
- **Comprehensive Error Handling**: Detailed logging and graceful degradation
- **Data Validation**: Validates structure, consistency, and completeness of scraped data
- **Persian Date Support**: Converts Gregorian to Persian calendar automatically
- **Database Integration**: Seamless SQL Server persistence with proper type mapping
- **Configuration Management**: Uses environment variables for sensitive credentials
- **Production-Ready**: Passes Sonar Code Quality checks, cognitive complexity optimized

## Architecture 🏗️

```
TGJU Website → Symbol Discovery → Data Scraping → Date Conversion → SQL Server
               (Main + Energy)                                        ↓
                                                              TgjuAssets Table
```

## Installation 🚀

### Prerequisites
- Python 3.8+
- SQL Server (or MSSQL-compatible database)
- ODBC Driver 17 for SQL Server

### Setup

```bash
# Clone repository
git clone https://github.com/alisadeghiaghili/tgju-data-collector.git
cd tgju-data-collector

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Set database connection environment variable:

```bash
# Linux/macOS
export TGJU_DB_CONNECTION="mssql+pyodbc://username:password@server/database?driver=ODBC+Driver+17+for+SQL+Server"

# Windows (PowerShell)
$env:TGJU_DB_CONNECTION="mssql+pyodbc://username:password@server/database?driver=ODBC+Driver+17+for+SQL+Server"

# Or use trusted connection (Windows)
export TGJU_DB_CONNECTION="mssql+pyodbc://username@server/database?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
```

## Usage 📖

### Basic Execution

```bash
python tgjuScraper.py
```

### Output Example

```
[INFO] Starting symbol collection...
[INFO] Fetching main symbols...
[INFO] Fetching energy symbols...
[INFO] Found 85 symbols to scrape
[INFO] Starting latest data scraping for 85 symbols...
[INFO] Processing 1/85: طلای آب شده
[SUCCESS] Got latest record for طلای آب شده
[INFO] Processing 2/85: طلای سکه امامی
[SUCCESS] Got latest record for طلای سکه امامی
...
[SUMMARY] Latest data scraping complete!
[SUMMARY] Successful: 82
[SUMMARY] Failed: 3
[INFO] Final dataset contains 82 latest records
[SUCCESS] Inserted 82 rows into TgjuAssets table.
[INFO] Script execution completed successfully!
```

## Code Structure 📁

```python
# Configuration Module
DEFAULT_USER_AGENT, TGJU_MAIN_URL, CONNECTION_TIMEOUT_WAIT, etc.

# HTTP Request Module
safe_request()  # Resilient HTTP GET with retry logic

# Symbol Scraping Module
_extract_xpaths_safely()  # XPath extraction helper
get_main_symbols()        # Main page symbols
get_energy_symbols()      # Energy page symbols
get_df_of_symbols()       # Combined and validated symbols

# Data Scraping Module
get_tgju_data()  # Fetch latest price for symbol

# Main Execution
main()  # Orchestrator

# Database Persistence
save_to_database()  # SQL Server integration
```

## Data Flow 🔄

1. **Symbol Discovery**: Extracts commodity symbols from TGJU navigation menu and energy section
2. **Validation**: Deduplicates and validates symbol format consistency
3. **Data Retrieval**: Fetches 24-hour historical data via API for each symbol
4. **Transformation**:
   - Unix timestamp → DateTime
   - Gregorian → Persian calendar
   - Extract weekday
5. **Persistence**: Appends records to SQL Server with proper type mapping

## Database Schema 📊

```sql
CREATE TABLE TgjuAssets (
    PersianDate CHAR(10),              -- YYYY-MM-DD
    EnglishDate DATETIME,              -- ISO format
    Weekday VARCHAR(20),               -- Monday, Tuesday, etc.
    Open DECIMAL(18, 5),               -- Price (5 decimal places)
    High DECIMAL(18, 5),
    Low DECIMAL(18, 5),
    Close DECIMAL(18, 5),
    Name NVARCHAR(100),                -- Persian symbol name
    Symbol_En VARCHAR(100),            -- English symbol
    ScrapeDate CHAR(10),               -- Collection date
    ScrapeTime CHAR(8),                -- Collection time
    ScrapeDateTime DATETIME            -- Exact timestamp
)
```

## Error Handling & Resilience 🛡️

### Network Failures
- **Connection Timeout**: Waits 10 minutes before retrying (configurable)
- **HTTP Errors**: Retries with exponential backoff (2-3 seconds)
- **JSON Parsing**: Logs and skips on invalid responses

### Data Validation
- Validates XPath extraction results
- Checks data consistency (column length matching)
- Ensures symbol format correctness
- Rate-limits requests (0.5-1s delays)

## Performance Metrics ⚡

- **Code Quality**: Passes Sonar verification
- **Cognitive Complexity**: 15 (reduced from 22)
- **Execution Time**: ~2-3 minutes for 80+ symbols
- **Success Rate**: Typically 95%+ with error recovery

## Logging 📝

Logging uses standardized prefixes:

```
[INFO]    - General information
[RETRY]   - Retry attempt
[WAIT]    - Waiting for timeout
[SUCCESS] - Successful operation
[SKIP]    - Skipped (not critical)
[ERROR]   - Error condition
[FAILED]  - Failed operation
[SUMMARY] - Summary statistics
```

## Security 🔐

- **Credentials**: Never hardcoded—uses environment variables
- **User Agent**: Spoofed to avoid blocking
- **Rate Limiting**: Built-in delays to avoid DOS
- **Data Validation**: Sanitizes inputs before database insertion

## Troubleshooting 🔧

### Connection Timeout
```
[WAIT] Connection timeout detected. Waiting 10 minutes before retry...
```
**Solution**: Check network connectivity and firewall rules

### No Symbols Found
```
[ERROR] Could not extract symbols from main page
[FATAL ERROR] Script failed: No symbols could be fetched from any source!
```
**Solution**: TGJU website structure may have changed—check XPath expressions

### Database Connection Failed
```
[DB ERROR] Failed to insert data: ...
```
**Solution**: Verify `TGJU_DB_CONNECTION` environment variable and SQL Server accessibility

## Development 🛠️

### Testing

```python
# Test safe_request
response = safe_request('https://www.tgju.org')
assert response is not None

# Test symbol extraction
symbols = get_df_of_symbols()
assert not symbols.empty
assert 'symbol_Fa' in symbols.columns
```

### Code Style
- PEP 8 compliant
- Comprehensive docstrings with examples
- Type hints in docstrings
- Clear variable names and comments

## Dependencies 📦

See `requirements.txt` for full list:

- `requests`: HTTP client
- `pandas`: Data manipulation
- `jdatetime`: Persian date conversion
- `BeautifulSoup4`: HTML parsing
- `lxml`: XPath support
- `SQLAlchemy`: Database ORM
- `pyodbc`: MSSQL driver

## Contributing 🤝

1. Fork repository
2. Create feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add feature'`)
4. Push branch (`git push origin feature/improvement`)
5. Open Pull Request

## License 📄

MIT License - See LICENSE file for details

## Changelog 📋

### v1.0.0 (2026-02-07)
- ✨ Initial release
- 🔄 Refactored for Sonar compliance
- 📚 Comprehensive documentation
- 🛡️ Robust error handling
- 🚀 Production-ready code

## Support 💬

For issues or questions:
1. Check Troubleshooting section
2. Review TGJU website for changes
3. Open GitHub issue with detailed logs

---

**Made with ❤️ by Ali Sadeghi Aghili**

[GitHub](https://github.com/alisadeghiaghili) | [LinkedIn](https://linktr.ee/aliaghili)
