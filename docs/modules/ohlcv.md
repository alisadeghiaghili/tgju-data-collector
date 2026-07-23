# OHLCV Collection

The OHLCV Collector fetches Open/High/Low/Close/Volume price data from the TGJU API.

## API Endpoint

```
GET https://platform.tgju.org/fa/tvdata/history
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | string | Symbol code (e.g., `ons`, `price_dollar_rl`) |
| `resolution` | string | Time resolution: `1m`, `5m`, `15m`, `30m`, `1h`, `1D`, `1w`, `1M` |
| `from` | int | Start timestamp (Unix seconds) |
| `to` | int | End timestamp (Unix seconds) |

### Response Format

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

| Field | Description |
|-------|-------------|
| `t` | Timestamps (Unix seconds) |
| `o` | Open prices |
| `h` | High prices |
| `l` | Low prices |
| `c` | Close prices |
| `v` | Volumes (often empty) |
| `s` | Status (`ok` or error) |

---

## Usage

### Fetch Latest Data

```python
from src.http_client import HttpClient
from src.collectors.ohlcv import OHLCVCollector

http = HttpClient()
collector = OHLCVCollector(http)

# Get latest daily data for gold ounce
df = collector.collect_latest('ons', resolution='1D', lookback_seconds=86400*3)

print(df)
#    Date        Open     High      Low     Close  Volume PersianDate Weekday
# 0 2026-07-01  4008.29  4166.00  4008.29  4137.09      0  1405-04-10  Wednesday

http.close()
```

### Fetch Historical Range

```python
from datetime import datetime, timedelta

# Get last 30 days of data
end = datetime.now()
start = end - timedelta(days=30)

df = collector.collect_range('ons', '1D', start, end)
```

### Batch Collection

```python
symbols = [
    {'symbol_Fa': 'دلار', 'symbol_En': 'usd', 'SYMBOL': 'price_dollar_rl'},
    {'symbol_Fa': 'یورو', 'symbol_En': 'eur', 'SYMBOL': 'price_eur'},
]

df = collector.collect_batch(symbols, resolution='1D')
```

---

## Supported Resolutions

| Resolution | API Value | Description |
|------------|-----------|-------------|
| 1 minute | `1m` | Intraday 1-min bars |
| 5 minutes | `5m` | Intraday 5-min bars |
| 15 minutes | `15m` | Intraday 15-min bars |
| 30 minutes | `30m` | Intraday 30-min bars |
| 1 hour | `1h` | Hourly bars |
| **1 day** | `1D` | Daily OHLCV (default) |
| 1 week | `1w` | Weekly bars |
| 1 month | `1M` | Monthly bars |

---

## Data Processing

### Volume Array Handling

The TGJU API often returns empty volume arrays. The collector handles this by padding missing arrays with zeros:

```python
n = len(api_data['t'])
df = pd.DataFrame({
    'Date': api_data['t'],
    'Open': (api_data.get('o') or [0]*n)[:n],
    'High': (api_data.get('h') or [0]*n)[:n],
    'Low': (api_data.get('l') or [0]*n)[:n],
    'Close': (api_data.get('c') or [0]*n)[:n],
    'Volume': (api_data.get('v') or [0]*n)[:n],
})
```

### Date Conversion

Timestamps are automatically converted to both Gregorian and Persian dates:

```python
df['Date'] = df['Date'].apply(lambda ts: datetime.fromtimestamp(ts))
df['PersianDate'] = df['Date'].apply(to_persian_date)
df['Weekday'] = df['Date'].apply(to_weekday)
```

---

## Rate Limiting

The collector includes built-in rate limiting:

- **Delay between requests**: 0.5–1.0 seconds (randomized)
- **Retry on failure**: Up to 3 attempts with exponential backoff
- **Polite crawling**: Respects server resources

```python
def sleep_between_requests(self):
    delay = REQUEST_DELAY_MIN + random.random() * REQUEST_DELAY_JITTER
    time.sleep(delay)
```

---

## Batch Collection Metadata

When using `collect_batch()`, the following metadata is added:

| Column | Description |
|--------|-------------|
| `Name` | Persian symbol name |
| `Symbol_En` | English symbol identifier |
| `ScrapeDate` | Collection date (`YYYY-MM-DD`) |
| `ScrapeTime` | Collection time (`HH:MM:SS`) |
| `ScrapeDateTime` | Full collection timestamp |
