# Data Flow

This page describes how data moves through the system, from TGJU.org to your database.

## Collection Pipeline

### 1. Symbol Discovery

```
TGJU.org Pages
    │
    ├─ Main Page ──────────┐
    ├─ /energy ────────────┤
    ├─ Sana Exchange ──────┤
    ├─ Bank Rates ─────────┤
    ├─ Global Market ──────┤
    ├─ Global Gold ────────┤  Each discoverer:
    ├─ Crypto ─────────────┤  1. Fetches HTML page
    ├─ Commodities ────────┤  2. Parses with BeautifulSoup + lxml
    ├─ Base Metals ────────┤  3. Extracts symbols via XPath
    ├─ Coin Market ────────┤  4. Returns List[Symbol]
    └─ Parsian Coin ───────┘
                │
                ▼
        SymbolRegistry
        (deduplicates by code)
                │
                ▼
        385 unique symbols
```

### 2. OHLCV Collection

```
Symbol Code (e.g., "ons")
    │
    ▼
TGJU API Request
GET https://platform.tgju.org/fa/tvdata/history
    ?symbol=ons
    &resolution=1D
    &from=<unix_timestamp>
    &to=<unix_timestamp>
    │
    ▼
JSON Response
{
  "t": [1719878400, ...],    # timestamps
  "o": [4008.29, ...],       # open
  "h": [4166.00, ...],       # high
  "l": [4008.29, ...],       # low
  "c": [4137.09, ...],       # close
  "v": [],                    # volume (often empty)
  "s": "ok"
}
    │
    ▼
pandas DataFrame
┌────────────┬────────┬────────┬────────┬─────────┬────────┬────────────┐
│ Date       │ Open   │ High   │ Low    │ Close   │ Volume │ PersianDate│
├────────────┼────────┼────────┼────────┼─────────┼────────┼────────────┤
│ 2026-07-01 │ 4008.29│ 4166.00│ 4008.29│ 4137.09 │ 0      │ 1405-04-10 │
└────────────┴────────┴────────┴────────┴─────────┴────────┴────────────┘
```

### 3. Database Persistence

```
DataFrame
    │
    ▼
SQLServerStorage.save_daily_ohlcv()
    │
    ├─ Maps column types:
    │   PersianDate → CHAR(10)
    │   Open/High/Low/Close → DECIMAL(18,5)
    │   Name → NVARCHAR(100)
    │   ...
    │
    ├─ Filters to existing columns
    │
    ▼
SQL INSERT (via SQLAlchemy)
    │
    ▼
TgjuAssets Table
```

---

## Backfill Pipeline

```
1. Get symbols from DB
   SELECT DISTINCT Symbol_En, Name FROM TgjuAssets
    │
    ▼
2. For each symbol, detect gaps
   ├── Get all existing PersianDate values
   ├── Convert to Gregorian dates
   ├── Sort chronologically
   └── Find gaps:
       ├── Before first record (up to 2 years back)
       ├── Between consecutive records (>1 day gap)
       └── After last record (up to today)
    │
    ▼
3. For each gap, fetch historical data
   TGJU API → OHLCVCollector.collect_range()
    │
    ▼
4. Insert new records
   SQLServerStorage.save_daily_ohlcv()
   (appends, avoids duplicates via date+symbol)
```

---

## Date Conversion Flow

```
Gregorian Date (Python datetime)
    │
    ▼
jdatetime.date.fromgregorian()
    │
    ▼
Persian Date String ("1405-04-31")
    │
    ▼
Stored in TgjuAssets.PersianDate (CHAR(10))
```

---

## Error Recovery Flow

```
Request Fails
    │
    ├─ Timeout/Connection Error
    │   └─ Retry up to 3x with exponential backoff
    │       ├── Attempt 1: immediate
    │       ├── Attempt 2: +2s
    │       └─ Attempt 3: +3s
    │
    ├─ HTTP Error (4xx/5xx)
    │   └─ Retry with jitter delay (0.5-1s)
    │
    ├─ Invalid JSON
    │   └─ Log error, skip symbol, continue batch
    │
    └─ Empty Response
        └─ Skip symbol, continue batch
```
