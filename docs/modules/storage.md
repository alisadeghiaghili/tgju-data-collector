# Storage Layer

The Storage Layer handles all database operations using SQLAlchemy.

## Architecture

```
SQLServerStorage
    │
    ├── save_daily_ohlcv()    → TgjuAssets table
    ├── save_symbols()        → Symbols table
    └── table_exists()        → Check table existence
              │
              ▼
        SQLAlchemy Engine
              │
              ▼
        SQL Server (via pyodbc)
```

---

## Usage

### Save OHLCV Data

```python
from src.storage.sqlserver import SQLServerStorage
import pandas as pd

storage = SQLServerStorage()

# DataFrame with OHLCV data
data = pd.DataFrame({
    'PersianDate': ['1405-04-10'],
    'EnglishDate': ['2026-07-01'],
    'Weekday': ['Wednesday'],
    'Open': [4008.29],
    'High': [4166.00],
    'Low': [4008.29],
    'Close': [4137.09],
    'Name': ['انس طلا'],
    'Symbol_En': ['ons'],
    'ScrapeDate': ['2026-07-01'],
    'ScrapeTime': ['10:30:00'],
    'ScrapeDateTime': ['2026-07-01 10:30:00']
})

rows_saved = storage.save_daily_ohlcv(data)
print(f"Saved {rows_saved} rows")
```

### Save Symbols

```python
registry = SymbolRegistry(http)
registry.discover_all()
df = registry.to_dataframe()

storage = SQLServerStorage()
storage.save_symbols(df)
```

### Check Table Exists

```python
if storage.table_exists('TgjuAssets'):
    print("Table found")
```

---

## Column Type Mapping

The storage layer maps pandas dtypes to SQL Server types:

| Column | SQL Type | Description |
|--------|----------|-------------|
| `PersianDate` | `CHAR(10)` | Jalali date (`YYYY-MM-DD`) |
| `EnglishDate` | `DATETIME` | Gregorian datetime |
| `Weekday` | `VARCHAR(20)` | Day name |
| `Open` | `DECIMAL(18, 5)` | Opening price |
| `High` | `DECIMAL(18, 5)` | Highest price |
| `Low` | `DECIMAL(18, 5)` | Lowest price |
| `Close` | `DECIMAL(18, 5)` | Closing price |
| `Name` | `NVARCHAR(100)` | Persian symbol name |
| `Symbol_En` | `VARCHAR(100)` | English symbol code |
| `ScrapeDate` | `CHAR(10)` | Collection date |
| `ScrapeTime` | `CHAR(8)` | Collection time |
| `ScrapeDateTime` | `DATETIME` | Full timestamp |

---

## Connection Management

The storage layer uses SQLAlchemy's connection pooling:

```python
class SQLServerStorage:
    def __init__(self, connection_string=None, table_name=None):
        self.connection_string = connection_string or get_connection_string()
        self.table_name = table_name or get_table_name()
        self._engine = None

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(self.connection_string)
        return self._engine
```

!!! note "Lazy Initialization"
    The database engine is created on first use, not at import time. This allows the module to be imported even if the database is unavailable.

---

## Error Handling

| Error | Handling |
|-------|----------|
| `SQLAlchemyError` | Log error, return 0 rows saved |
| Connection failure | Raised by SQLAlchemy, caught by caller |
| Missing columns | Filtered to only include existing columns |

---

## Creating Tables

To create all tables defined in `src/models.py`:

```python
from sqlalchemy import create_engine
from src.config import get_connection_string
from src.models import create_all_tables

engine = create_engine(get_connection_string())
create_all_tables(engine)
```

This creates:

- `TgjuAssets` — Legacy OHLC table
- `Symbols` — Symbol registry
- `DailyOHLCV` — Enhanced OHLCV with volume
- `IntradayData` — Multi-resolution intraday data
- `SymbolProfile` — Rich metadata per symbol
- `EconomicIndicator` — Economic indicators
- `News` — Market news articles
- `CollectionLog` — Data collection run logs
