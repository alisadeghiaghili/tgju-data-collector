# Initial Setup

This guide walks you through setting up TGJU Data Collector from scratch.

## Step 1: Clone and Install

```bash
git clone https://github.com/alisadeghiaghili/tgju-data-collector.git
cd tgju-data-collector
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Step 2: Configure Database

```bash
cp .env.example .env
```

Edit `.env` with your SQL Server credentials:

```env
TGJU_DB_SERVER=localhost
TGJU_DB_NAME=tgju
TGJU_DB_USER=sa
TGJU_DB_PASSWORD=YourPassword123!
TGJU_DB_DRIVER=ODBC Driver 17 for SQL Server
TGJU_DB_PORT=1433
TGJU_DB_TABLE_NAME=TgjuAssets
```

## Step 3: Verify Configuration

```bash
python config.py
```

Expected output:

```
Connection string built successfully (length: 156 characters)
```

## Step 4: Create Database Tables

```bash
python -c "
from src.config import load_config, get_connection_string
from src.models import create_all_tables
from sqlalchemy import create_engine

load_config()
engine = create_engine(get_connection_string())
create_all_tables(engine)
print('Tables created successfully')
"
```

## Step 5: Discover Symbols

```bash
python main.py discover --save-db
```

This discovers all 385+ symbols and saves them to the `Symbols` table.

## Step 6: Initial Data Collection

```bash
python main.py collect
```

This fetches the latest data for all symbols.

## Step 7: Backfill Historical Data

```bash
python main.py backfill
```

This fills in historical gaps (may take 5-15 minutes on first run).

## Step 8: Verify Setup

```bash
python main.py status
```

Check that:

- `.env` file: Found
- Database connection: Works
- `TgjuAssets` table: exists

---

## Next Steps

- Set up [daily scheduling](daily-workflow.md#scheduling)
- Review [troubleshooting](../troubleshooting.md) if issues arise
- Explore the [architecture](../architecture/overview.md) to understand the system
