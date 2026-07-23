# Installation

## Prerequisites

- **Python 3.8+**
- **SQL Server** (or MSSQL-compatible database)
- **ODBC Driver 17 for SQL Server**

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/alisadeghiaghili/tgju-data-collector.git
cd tgju-data-collector
```

### 2. Create Virtual Environment

=== "Windows"

    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

=== "macOS / Linux"

    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:

| Package | Purpose |
|---------|---------|
| `requests` | HTTP client with retry logic |
| `pandas` | Data manipulation and analysis |
| `jdatetime` | Persian (Jalali) date conversion |
| `beautifulsoup4` | HTML parsing for symbol discovery |
| `lxml` | Fast XML/HTML parser |
| `SQLAlchemy` | Database ORM and connection |
| `pyodbc` | SQL Server ODBC driver |
| `python-dotenv` | Environment variable management |

### 4. Configure Database

```bash
cp .env.example .env
```

Edit `.env` with your database credentials (see [Configuration](configuration.md)).

### 5. Verify Installation

```bash
python main.py status
```

Expected output:

```
============================================================
TGJU Data Collector - Status
============================================================

.env file: Found
  TGJU_DB_SERVER: localhost
  TGJU_DB_NAME: tgju
  TGJU_DB_USER: sa

  TgjuAssets table: exists

============================================================
```

---

## Troubleshooting

### ODBC Driver Not Found

If you see `ODBC Driver 17 for SQL Server` not found:

1. Download from [Microsoft's official site](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
2. Install the driver
3. Verify with `odbcad32.exe` (Windows) or `odbcinst -j` (Linux)

### Permission Errors on Install

If `pip install` fails with permission errors:

```bash
pip install --user -r requirements.txt
```

### SSL Certificate Errors

If you encounter SSL errors behind a corporate proxy:

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```
