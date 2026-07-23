# Backfill Engine

The Backfill Engine detects and fills gaps in historical data, replacing the legacy `AutoTrowel_TGJU.py` script.

## How It Works

```
1. Load symbols from database
         │
         ▼
2. For each symbol, detect gaps
   ├── Get all existing PersianDate values
   ├── Convert to Gregorian
   └── Find missing date ranges:
       ├── Before first record (up to 2 years)
       ├── Between records (>1 day gap)
       └── After last record (up to today)
         │
         ▼
3. For each gap, fetch historical data
   TGJU API → OHLCVCollector.collect_range()
         │
         ▼
4. Insert new records
   SQLServerStorage.save_daily_ohlcv()
```

---

## Usage

### CLI

```bash
# Backfill all symbols in database
python main.py backfill

# Backfill specific symbols
python main.py backfill --symbols ons price_dollar_rl sekee

# Limit backfill window (default: 730 days = 2 years)
python main.py backfill --max-days 365
```

### Programmatic

```python
from src.backfill import TGJUBackfill

backfill = TGJUBackfill()

# Backfill all symbols
backfill.run()

# Backfill specific symbols with custom window
backfill.run(max_days=365, symbols=['ons', 'price_dollar_rl'])
```

---

## Gap Detection Algorithm

### Input

For each symbol, the backfill engine queries:

```sql
SELECT DISTINCT PersianDate
FROM TgjuAssets
WHERE Symbol_En = :symbol
ORDER BY PersianDate
```

### Processing

1. **Convert** Persian dates to Gregorian
2. **Sort** chronologically
3. **Find gaps**:

```
Existing dates: [2026-01-01, 2026-01-02, 2026-01-05, 2026-01-06]

Gap before first:  [2024-07-01, 2025-12-31]  (2 years back)
Gap between:       [2026-01-03, 2026-01-04]  (2 missing days)
Gap after last:    [2026-01-07, 2026-07-01]  (up to today)
```

### Output

List of `(start_date, end_date)` tuples representing gaps to fill.

---

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_BACKFILL_DAYS` | 730 | Maximum days to look back (2 years) |
| Rate limit delay | 0.5-1s | Delay between API requests |

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| No symbols in DB | Log warning, return |
| Symbol has no existing dates | Backfill entire window (2 years) |
| API returns empty data | Skip gap, continue |
| Network error | Retry 3x with backoff |
| Database error | Log error, continue with next symbol |

---

## Performance

| Metric | Value |
|--------|-------|
| Speed | ~1-2 symbols/second (depends on gaps) |
| API calls | 1 per gap per symbol |
| Rate limiting | 0.5-1s delay between requests |

For a full backfill of 85 symbols with 2 years of data, expect 5-15 minutes depending on network conditions.
