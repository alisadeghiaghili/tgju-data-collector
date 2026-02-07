# TGJU Data Collector

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
- **Production-Ready Code**: Passes Sonar Code Quality checks, cognitive complexity optimized

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

#### Option 1: Using Environment File (Recommended)

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your database credentials
# NEVER commit .env to version control - it's in .gitignore
```

Example `.env` file:
```env
TGJU_DB_SERVER=localhost
TGJU_DB_NAME=tgju
TGJU_DB_USER=sa
TGJU_DB_PASSWORD=YourSecurePassword123!
TGJU_DB_DRIVER=ODBC Driver 17 for SQL Server
TGJU_DB_PORT=1433

LOG_LEVEL=INFO
LOG_DIR=logs
```

#### Option 2: Direct Environment Variables

```bash
# Linux/macOS
export TGJU_DB_SERVER=localhost
export TGJU_DB_NAME=tgju
export TGJU_DB_USER=sa
export TGJU_DB_PASSWORD="YourSecurePassword123!"

# Windows (PowerShell)
$env:TGJU_DB_SERVER="localhost"
$env:TGJU_DB_NAME="tgju"
$env:TGJU_DB_USER="sa"
$env:TGJU_DB_PASSWORD="YourSecurePassword123!"
```

#### Option 3: Complete Connection String

```bash
# Use this if you prefer a single connection string
export TGJU_DB_CONNECTION_STRING="mssql+pyodbc://username:password@server:1433/database?driver=ODBC+Driver+17+for+SQL+Server"
```

**Priority**: Complete connection string > Individual components

## Usage 📖

### Basic Execution

```bash
python tgju_scraper.py
```

### Output Example

```
2026-02-07 10:35:00,123 - __main__ - INFO - ============================================================
2026-02-07 10:35:00,125 - __main__ - INFO - Starting TGJU Market Data Scraper
2026-02-07 10:35:00,127 - __main__ - INFO - ============================================================
2026-02-07 10:35:00,245 - __main__ - INFO - Starting symbol collection...
2026-02-07 10:35:00,346 - __main__ - INFO - Fetching main TGJU symbols...
2026-02-07 10:35:02,567 - __main__ - INFO - Extracted 75 main symbols
2026-02-07 10:35:02,890 - __main__ - INFO - Fetching TGJU energy symbols...
2026-02-07 10:35:03,234 - __main__ - INFO - Extracted 10 energy symbols
2026-02-07 10:35:03,456 - __main__ - INFO - Symbol collection complete: 85 symbols found
2026-02-07 10:35:03,500 - __main__ - INFO - Starting data scraping for 85 symbols...
2026-02-07 10:35:03,502 - __main__ - INFO - [1/85] Processing: طلای آب شده
2026-02-07 10:35:04,123 - __main__ - DEBUG - Successfully scraped latest data for طلای آب شده
...
2026-02-07 10:42:15,890 - __main__ - INFO - ============================================================
2026-02-07 10:42:15,892 - __main__ - INFO - Data scraping phase complete
2026-02-07 10:42:15,893 - __main__ - INFO - Successful: 82/85
2026-02-07 10:42:15,894 - __main__ - INFO - Failed: 3/85
2026-02-07 10:42:15,896 - __main__ - INFO - ============================================================
2026-02-07 10:42:16,123 - __main__ - INFO - Aggregated 82 latest records
2026-02-07 10:42:16,345 - config - INFO - Loaded environment variables from .env
2026-02-07 10:42:16,456 - config - INFO - Built connection string from TGJU_DB_* environment variables
2026-02-07 10:42:16,567 - __main__ - INFO - Connecting to database...
2026-02-07 10:42:16,890 - __main__ - INFO - Inserting 82 rows into TgjuAssets table...
2026-02-07 10:42:17,234 - __main__ - INFO - Successfully inserted 82 rows into TgjuAssets table
2026-02-07 10:42:17,345 - __main__ - INFO - ============================================================
2026-02-07 10:42:17,347 - __main__ - INFO - Script execution completed successfully!
2026-02-07 10:42:17,349 - __main__ - INFO - ============================================================
```

## Code Structure 📁

```python
# Configuration Module (config.py)
load_env_file()          # Load .env file
get_connection_string()  # Build DB connection string
get_table_name()         # Get table name from env

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

1. **Configuration**: Loads environment variables from `.env` file
2. **Symbol Discovery**: Extracts commodity symbols from TGJU navigation menu and energy section
3. **Validation**: Deduplicates and validates symbol format consistency
4. **Data Retrieval**: Fetches 24-hour historical data via API for each symbol
5. **Transformation**:
   - Unix timestamp → DateTime
   - Gregorian → Persian calendar
   - Extract weekday
6. **Persistence**: Appends records to SQL Server with proper type mapping

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

### Logging Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages (recoverable issues)
- **ERROR**: Error messages (non-fatal failures)
- **CRITICAL**: Critical errors (script termination)

## Performance Metrics ⚡

- **Code Quality**: Passes Sonar verification
- **Cognitive Complexity**: 15 (reduced from 22)
- **Execution Time**: ~2-3 minutes for 80+ symbols
- **Success Rate**: Typically 95%+ with error recovery
- **Log Output**: Both file (`tgju_scraper.log`) and console

## Security 🔐

- **Credentials**: Never hardcoded—uses environment variables exclusively
- **Validation**: Environment variables checked for placeholder values before use
- **User Agent**: Spoofed to avoid blocking
- **Rate Limiting**: Built-in delays to avoid DOS
- **Data Validation**: Sanitizes inputs before database insertion
- **Connection String Encoding**: Special characters URL-encoded for safety

## Troubleshooting 🔧

### Missing Environment Variables
```
ValueError: ❌ Missing required environment variables: TGJU_DB_SERVER, TGJU_DB_NAME, TGJU_DB_USER, TGJU_DB_PASSWORD
```
**Solution**: Copy `.env.example` to `.env` and fill in your database credentials

### Connection Timeout
```
2026-02-07 10:35:00,500 - __main__ - INFO - Connection timeout detected. Waiting 10 minutes before retry...
```
**Solution**: Check network connectivity and firewall rules

### No Symbols Found
```
2026-02-07 10:35:00,500 - __main__ - ERROR - Could not extract symbols from main page
```
**Solution**: TGJU website structure may have changed—verify XPath expressions

### Database Connection Failed
```
2026-02-07 10:42:16,890 - __main__ - ERROR - Database operation failed: ...
```
**Solution**: 
1. Verify ODBC Driver 17 is installed: `odbcad32.exe` (Windows) or test connection
2. Test connection string: `python config.py`
3. Check SQL Server is running and accessible
4. Verify database exists and credentials are correct

## Testing Configuration

```bash
# Test if configuration is correct
python config.py

# Output:
# ============================================================
# Configuration Status
# ============================================================
#
# .env file: ✓ Found
#
# Database Configuration:
#   TGJU_DB_SERVER: localhost
#   TGJU_DB_NAME: tgju
#   TGJU_DB_USER: sa
#   TGJU_DB_PASSWORD: ********
#
# Logging Configuration:
#   level: INFO
#   directory: logs
#
# ============================================================
# ✓ Connection string built successfully
#   (length: 156 characters)
```

## Development 🛠️

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

### v1.1.0 (2026-02-07)
- ✨ Refactored configuration management to `config.py`
- 📊 Enhanced logging with structured output
- 🔐 Improved security: environment variables only, no hardcoded credentials
- 📝 Better documentation and setup guide
- 🛠️ Added configuration testing via `config.py`

### v1.0.0 (2026-02-07)
- ✨ Initial release
- 🔄 Refactored for Sonar compliance
- 📚 Comprehensive documentation
- 🛡️ Robust error handling
- 🚀 Production-ready code

## Support 💬

For issues or questions:
1. Check Troubleshooting section
2. Run `python config.py` to verify configuration
3. Review log output in `tgju_scraper.log`
4. Open GitHub issue with detailed logs

---

**Made with ❤️ by Ali Sadeghi Aghili**

[GitHub](https://github.com/alisadeghiaghili) | [Website](https://linktr.ee/aliaghili)
