# TGJU Data Collector

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-green.svg)
![Code Quality](https://img.shields.io/badge/Code%20Quality-Sonar%20Verified-brightgreen.svg)
![Security](https://img.shields.io/badge/Security-S2115%20Compliant-success.svg)

Real-time market data scraper for TGJU.org (Tehran Gold and Jewelry Union) with automated database persistence to SQL Server and intelligent backfill capabilities.

## Features ✨

### Core Features
- **Smart Symbol Discovery**: Automatically fetches commodity symbols from main and energy sections
- **Resilient HTTP Requests**: Implements retry logic with exponential backoff for network failures
- **Comprehensive Error Handling**: Detailed logging and graceful degradation
- **Data Validation**: Validates structure, consistency, and completeness of scraped data
- **Persian Date Support**: Converts Gregorian to Persian calendar automatically
- **Database Integration**: Seamless SQL Server persistence with proper type mapping
- **Secure Configuration**: Environment-based credentials management (SonarQube S2115 compliant)
- **Production-Ready Code**: Passes Sonar Code Quality checks, cognitive complexity optimized

### AutoTrowel - Intelligent Backfill 🧱
- **Gap Detection**: Automatically identifies missing dates in database
- **Historical Data Retrieval**: Fetches missing data from TGJU API
- **Incremental Loading**: Only inserts new records, avoids duplicates
- **Progress Tracking**: Real-time progress for large backfill operations
- **Configurable Backfill Window**: Default 2 years, adjustable

## Architecture 🏭️

```
┌────────────────────────────────────┐
│  Daily Scraper (tgjuScraper.py)  │
└───────────────┬────────────────────┘
                │
         TGJU Website → Symbol Discovery → Latest Data → SQL Server
                       (Main + Energy)                           │
                                                                  │
┌────────────────────────────────────────────────────┐
│  AutoTrowel (AutoTrowel_TGJU.py) - Backfill Tool  │
└─────────────┬────────────────────────────────────┘
                │
         DB Query → Gap Detection → Historical API → Fill Gaps
                                                            │
                                                            ↓
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
TGJU_DB_TABLE_NAME=TgjuAssets
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

### 1. Daily Data Collection (tgjuScraper.py)

Collects the **latest** price data for all symbols:

```bash
python tgjuScraper.py
```

**Use Case**: Run daily (e.g., via cron/Task Scheduler) to collect fresh market data.

#### Output Example

```
INFO    : ============================================================
INFO    : TGJU Data Collector started
INFO    : ============================================================
INFO    : Phase 1: Symbol Discovery - Starting symbol collection...
INFO    : Fetching main symbols from TGJU website...
INFO    : Successfully extracted 75 main symbols
INFO    : Fetching energy symbols from TGJU energy section...
INFO    : Successfully extracted 10 energy symbols
INFO    : Final symbol list prepared with 85 symbols
INFO    : Phase 2: Data Collection - Starting scraping for 85 symbols...
INFO    : Successfully scraped data for طلای آب شده on 1405-11-18
INFO    : Successfully scraped data for دلار آمریکا on 1405-11-18
...
INFO    : Phase 3: Results Aggregation
INFO    : Scraping completed - Successful: 82, Failed: 3
INFO    : Combined results: 82 records
INFO    : Final dataset contains 82 records with metadata
INFO    : Phase 4: Database Persistence - Starting database insertion...
INFO    : Successfully inserted 82 rows into TgjuAssets table.
INFO    : ============================================================
INFO    : Script execution completed successfully!
INFO    : ============================================================
```

---

### 2. Backfill Missing Data (AutoTrowel_TGJU.py)

Fills **gaps** in historical data:

```bash
python AutoTrowel_TGJU.py
```

**Use Case**: 
- Initial database population
- Recover from extended downtime
- Fill gaps when daily scraper fails

#### How AutoTrowel Works

1. **Queries Database**: Loads all symbols currently in `TgjuAssets`
2. **Gap Detection**: For each symbol, identifies missing date ranges:
   - Gaps before first record (up to 2 years back)
   - Gaps between existing records
   - Gaps after last record (up to today)
3. **Historical Fetch**: Retrieves missing data from TGJU API
4. **Incremental Insert**: Only inserts new records (avoids duplicates)

#### Output Example

```
INFO    : ============================================================
INFO    : Starting TGJU AutoTrowel Backfill Pipeline
INFO    : ============================================================
INFO    : [1/2] Loading symbols from database...
INFO    : Found 85 symbols in database
INFO    : [2/2] Processing 85 symbols...

INFO    : [1/85] طلای آب شده
INFO    : Processing: طلای آب شده (gold_melted)
INFO    : gold_melted: Found 2 gap(s) to fill
INFO    :   Gap 1/2: 2024-01-15 to 2024-02-10
INFO    :   Gap 2/2: 2025-12-20 to 2026-02-07
INFO    :   ✓ Inserted 45 records for gold_melted

INFO    : [2/85] دلار آمریکا
INFO    : Processing: دلار آمریکا (usd)
INFO    :   ✓ No gaps found for usd

...

INFO    : ============================================================
INFO    : Backfill Pipeline Completed
INFO    : ============================================================
INFO    : Total records inserted: 1,247
INFO    : Duration: 145.67 seconds
INFO    : ============================================================
```

---

## Code Structure 📁

```
tgju-data-collector/
├── config.py                  # Secure configuration management
├── tgjuScraper.py             # Daily data collection script
├── AutoTrowel_TGJU.py         # Historical backfill tool
├── .env.example               # Configuration template
├── .env                       # Your credentials (gitignored)
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── .gitignore                 # Git ignore rules
└── logs/                      # Log files (auto-created)
    ├── tgju_scraper.log
    └── autotrowel_tgju_YYYYMMDD.log
```

### Module Responsibilities

#### `config.py`
```python
load_env_file()          # Load .env file
get_connection_string()  # Build secure DB connection
get_table_name()         # Get table name from env
validate_no_placeholders() # Security validation
```

#### `tgjuScraper.py`
```python
# HTTP Request Module
safe_request()  # Resilient HTTP GET with retry logic

# Symbol Scraping Module
get_main_symbols()        # Main page symbols
get_energy_symbols()      # Energy page symbols
get_df_of_symbols()       # Combined and validated symbols

# Data Scraping Module
get_tgju_data()  # Fetch latest price for symbol

# Database Persistence
save_to_database()  # SQL Server integration
```

#### `AutoTrowel_TGJU.py`
```python
get_symbols_from_db()              # Load existing symbols
get_existing_dates_for_symbol()    # Query DB for dates
detect_missing_date_ranges()       # Gap detection logic
fetch_historical_data()            # API call for date range
backfill_symbol()                  # Process single symbol
save_to_database()                 # Insert with deduplication
```

---

## Database Schema 📊

```sql
CREATE TABLE TgjuAssets (
    PersianDate CHAR(10),              -- YYYY-MM-DD (Jalali)
    EnglishDate DATETIME,              -- Gregorian datetime
    Weekday VARCHAR(20),               -- Monday, Tuesday, etc.
    Open DECIMAL(18, 5),               -- Opening price
    High DECIMAL(18, 5),               -- Highest price
    Low DECIMAL(18, 5),                -- Lowest price
    Close DECIMAL(18, 5),              -- Closing price
    Name NVARCHAR(100),                -- Persian symbol name
    Symbol_En VARCHAR(100),            -- English symbol identifier
    ScrapeDate CHAR(10),               -- Collection date (YYYY-MM-DD)
    ScrapeTime CHAR(8),                -- Collection time (HH:MM:SS)
    ScrapeDateTime DATETIME            -- Exact collection timestamp
)
```

**Note**: Both `tgjuScraper.py` and `AutoTrowel_TGJU.py` use **identical** data types for consistency.

---

## Error Handling & Resilience 🛡️

### Network Failures
- **Connection Timeout**: Waits 10 minutes before retrying (configurable)
- **HTTP Errors**: Retries with exponential backoff (2-3 seconds)
- **JSON Parsing**: Logs and skips on invalid responses
- **Rate Limiting**: 0.5-1s delays between requests

### Data Validation
- Validates XPath extraction results
- Checks data consistency (column length matching)
- Ensures symbol format correctness
- Filters duplicate records before insertion

### Logging
- **Dual Output**: File (`logs/`) + Console
- **Log Rotation**: 10MB files, 5 backups
- **Structured Logs**: Timestamp, level, function, line number
- **Debug Mode**: Enable via environment variable `LOG_LEVEL=DEBUG`

---

## Security 🔐

- **No Hardcoded Credentials**: All credentials from environment variables
- **SonarQube S2115 Compliant**: Passes security rule checks
- **Placeholder Validation**: Rejects placeholder values (e.g., `your_password`)
- **Connection String Encoding**: Special characters URL-encoded
- **User Agent Spoofing**: Avoids blocking by appearing as regular browser
- **.gitignore Protection**: `.env` file never committed to Git

---

## Troubleshooting 🔧

### 1. Configuration Issues

**Problem**: Missing environment variables
```
ValueError: ❌ Missing required environment variables: TGJU_DB_SERVER, TGJU_DB_NAME
```

**Solution**:
```bash
# Verify .env file exists
ls -la .env

# Test configuration
python config.py

# If missing, create from template
cp .env.example .env
# Edit .env with your credentials
```

---

### 2. Database Connection Failed

**Problem**: Cannot connect to SQL Server
```
ERROR   : Database error: (pyodbc.OperationalError) ...
```

**Solution**:
1. **Verify ODBC Driver**:
   ```bash
   # Windows
   odbcad32.exe
   
   # Linux
   odbcinst -j
   ```

2. **Test connection string**:
   ```bash
   python config.py
   ```

3. **Check SQL Server status**:
   - Ensure SQL Server service is running
   - Verify firewall allows connections on port 1433
   - Test credentials manually via SQL Server Management Studio

---

### 3. AutoTrowel - No Symbols Found

**Problem**: AutoTrowel says "No symbols found in database"

**Solution**: Run `tgjuScraper.py` first to populate initial data:
```bash
python tgjuScraper.py  # Populate database with latest data
python AutoTrowel_TGJU.py  # Then backfill historical gaps
```

---

### 4. TGJU Website Structure Changed

**Problem**: "Could not extract symbols from main page"

**Solution**: 
1. Check if TGJU website is accessible:
   ```bash
   curl https://www.tgju.org
   ```

2. Verify XPath expressions in `tgjuScraper.py` (lines for `xpath_mappings`)
3. Inspect HTML structure using browser DevTools
4. Update XPath if website layout changed

---

### 5. AutoTrowel Finds No Gaps (But Data is Missing)

**Problem**: AutoTrowel reports no gaps, but visual inspection shows missing dates

**Solution**:
1. **Check date format** in database:
   ```sql
   SELECT TOP 10 PersianDate, Symbol_En 
   FROM TgjuAssets 
   ORDER BY Symbol_En, PersianDate
   ```

2. **Verify Persian date parsing**:
   - Format should be `YYYY-MM-DD` (e.g., `1405-11-18`)
   - Not `YYYYMMDD` or other formats

3. **Manually trigger backfill** by temporarily deleting test records:
   ```sql
   DELETE FROM TgjuAssets 
   WHERE Symbol_En = 'gold_melted' 
   AND PersianDate BETWEEN '1405-01-01' AND '1405-01-10'
   ```
   Then run AutoTrowel again.

---

## Performance Metrics ⚡

| Metric | tgjuScraper.py | AutoTrowel_TGJU.py |
|--------|----------------|--------------------|
| **Execution Time** | ~2-3 min (85 symbols) | ~2-5 min (depends on gaps) |
| **Success Rate** | 95%+ with retry | 98%+ (historical data more stable) |
| **API Calls** | 1 per symbol | 1 per gap per symbol |
| **Rate Limiting** | 0.5-1s delay | 0.5-1s delay |
| **Log Output** | `tgju_scraper.log` | `autotrowel_tgju_YYYYMMDD.log` |

---

## Testing Configuration

```bash
# Test if configuration is correct
python config.py

# Expected output:
# ============================================================
# TGJU Configuration Status
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
# Table Name: TgjuAssets
#
# ============================================================
# ✓ Connection string built successfully
#   (length: 156 characters)
```

---

## Best Practices 🎯

### Daily Workflow
1. **Schedule `tgjuScraper.py`** to run daily (cron/Task Scheduler)
2. **Monitor logs** for failures
3. **Run `AutoTrowel_TGJU.py`** weekly or after extended downtime

### Initial Setup
1. Configure `.env` with database credentials
2. Run `python config.py` to validate
3. Run `python tgjuScraper.py` to collect latest data
4. Run `python AutoTrowel_TGJU.py` to backfill historical gaps

### Recovery from Downtime
1. Run `tgjuScraper.py` to get latest data
2. Run `AutoTrowel_TGJU.py` to fill gaps from downtime period

---

## Dependencies 📦

See `requirements.txt` for full list:

```
requests>=2.31.0
pandas>=2.0.0
jdatetime>=4.1.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
SQLAlchemy>=2.0.0
pyodbc>=5.0.0
```

Install all:
```bash
pip install -r requirements.txt
```

---

## Contributing 🤝

1. Fork repository
2. Create feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -am 'Add feature'`)
4. Push branch (`git push origin feature/improvement`)
5. Open Pull Request

**Code Standards**:
- PEP 8 compliant
- Comprehensive docstrings
- Type hints in docstrings
- No hardcoded credentials
- SonarQube verified

---

## License 📄

MIT License - See LICENSE file for details

---

## Changelog 📋

### v2.0.0 (2026-02-07)
- ✨ **NEW**: AutoTrowel_TGJU.py for intelligent backfill
- ✨ **NEW**: Gap detection and incremental loading
- 🔐 Enhanced security: SonarQube S2115 compliant
- 📁 Refactored configuration to `config.py` module
- 📊 Better logging with structured output
- 📖 Comprehensive documentation

### v1.0.0 (2026-02-07)
- ✨ Initial release
- 🔄 Daily data scraper
- 🛡️ Robust error handling
- 🚀 Production-ready code

---

## Support 💬

For issues or questions:
1. Check **Troubleshooting** section above
2. Run `python config.py` to verify configuration
3. Review log output in `logs/` directory
4. Open GitHub issue with:
   - Error message
   - Relevant log excerpts
   - Environment details (Python version, OS, SQL Server version)

---

**Made with ❤️ by Ali Sadeghi Aghili**

[GitHub](https://github.com/alisadeghiaghili) | [LinkedIn](https://linktr.ee/aliaghili) | [IME](https://www.ime.co.ir)
