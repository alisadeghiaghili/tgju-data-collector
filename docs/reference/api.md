# API Reference

## TGJU API

### OHLCV History Endpoint

```
GET https://platform.tgju.org/fa/tvdata/history
```

#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `symbol` | string | Yes | Symbol code (e.g., `ons`, `price_dollar_rl`) |
| `resolution` | string | Yes | Time resolution: `1m`, `5m`, `15m`, `30m`, `1h`, `1D`, `1w`, `1M` |
| `from` | int | Yes | Start timestamp (Unix seconds) |
| `to` | int | Yes | End timestamp (Unix seconds) |

#### Response

```json
{
  "t": [1719878400, 1719964800],
  "o": [4008.29, 4050.00],
  "h": [4166.00, 4100.00],
  "l": [4008.29, 4020.00],
  "c": [4137.09, 4080.00],
  "v": [],
  "s": "ok"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `t` | int[] | Timestamps (Unix seconds) |
| `o` | float[] | Open prices |
| `h` | float[] | High prices |
| `l` | float[] | Low prices |
| `c` | float[] | Close prices |
| `v` | int[] | Volumes (may be empty) |
| `s` | string | Status (`ok` or error message) |

#### Example Request

```bash
curl "https://platform.tgju.org/fa/tvdata/history?symbol=ons&resolution=1D&from=1719792000&to=1719878400"
```

#### Example Response

```json
{
  "t": [1719792000],
  "o": [3950.00],
  "h": [4000.00],
  "l": [3940.00],
  "c": [3980.50],
  "v": [],
  "s": "ok"
}
```

---

## Python Client API

### HttpClient

```python
from src.http_client import HttpClient

http = HttpClient(
    user_agent="Mozilla/5.0 ...",  # Optional
    timeout=30,                     # Optional
    max_retries=3                   # Optional
)

# Make GET request
response = http.get(url, **kwargs)

# Rate limiting
http.sleep_between_requests()

# Cleanup
http.close()
```

### SymbolRegistry

```python
from src.http_client import HttpClient
from src.discovery.registry import SymbolRegistry

http = HttpClient()
registry = SymbolRegistry(http)

# Discover all symbols
total = registry.discover_all()

# Get symbols
symbols = registry.get_all()                    # All symbols
symbols = registry.get_by_category('gold')      # By category
symbols = registry.get_by_source('energy')      # By source

# Convert to DataFrame
df = registry.to_dataframe()
```

### OHLCVCollector

```python
from src.http_client import HttpClient
from src.collectors.ohlcv import OHLCVCollector

http = HttpClient()
collector = OHLCVCollector(http)

# Latest data
df = collector.collect_latest('ons', '1D', lookback_seconds=86400*3)

# Historical range
from datetime import datetime, timedelta
start = datetime.now() - timedelta(days=30)
end = datetime.now()
df = collector.collect_range('ons', '1D', start, end)

# Batch collection
symbols = [{'SYMBOL': 'ons', 'symbol_Fa': 'انس طلا', 'symbol_En': 'gold_ounce'}]
df = collector.collect_batch(symbols, '1D')
```

### SQLServerStorage

```python
from src.storage.sqlserver import SQLServerStorage

storage = SQLServerStorage(
    connection_string='mssql+pyodbc://...',  # Optional (uses .env)
    table_name='TgjuAssets'                  # Optional
)

# Save data
rows = storage.save_daily_ohlcv(dataframe)
rows = storage.save_symbols(symbols_df)

# Check table
exists = storage.table_exists('TgjuAssets')
```

### TGJUBackfill

```python
from src.backfill import TGJUBackfill

backfill = TGJUBackfill(
    connection_string='...',  # Optional
    table_name='...'          # Optional
)

# Run backfill
backfill.run(max_days=730, symbols=None)

# Detect gaps for a symbol
gaps = backfill.detect_gaps('ons')

# Backfill single symbol
inserted = backfill.backfill_symbol('ons', 'انس طلا')
```
