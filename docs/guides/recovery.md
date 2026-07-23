# Recovery from Downtime

This guide covers recovering from extended periods where the collector was not running.

## Scenario: Server Was Down for a Week

### Step 1: Run Daily Collection First

```bash
python main.py collect
```

This gets the latest data and ensures the database is current.

### Step 2: Backfill the Gap

```bash
python main.py backfill
```

The backfill engine will:

1. Query all existing dates for each symbol
2. Detect the gap (missing dates during downtime)
3. Fetch historical data from TGJU API
4. Insert missing records

### Step 3: Verify Recovery

Check that data is now continuous:

```sql
-- Find the gap dates
SELECT PersianDate, Symbol_En
FROM TgjuAssets
WHERE Symbol_En = 'ons'
AND PersianDate BETWEEN '1405-04-20' AND '1405-04-30'
ORDER BY PersianDate
```

---

## Scenario: Database Was Reset

### Step 1: Collect Latest Data

```bash
python main.py collect
```

### Step 2: Full Backfill

```bash
python main.py backfill
```

This will backfill up to 2 years of historical data.

### Step 3: Save Symbol Registry

```bash
python main.py discover --save-db
```

---

## Scenario: Specific Symbols Have Gaps

### Backfill Specific Symbols

```bash
python main.py backfill --symbols ons price_dollar_rl sekee
```

### Check Gaps in Database

```sql
-- Find symbols with few records (potential gaps)
SELECT Symbol_En, Name, COUNT(*) as records
FROM TgjuAssets
GROUP BY Symbol_En, Name
HAVING COUNT(*) < 30
ORDER BY records
```

---

## Scenario: TGJU Website Changed

If symbol discovery fails after a website update:

### Step 1: Test Discovery

```bash
python main.py discover
```

### Step 2: Check XPath Expressions

If no symbols are found, the XPath expressions in the discovery modules may need updating.

Inspect the TGJU website HTML and update the XPath in the relevant discovery module:

- `src/discovery/main_page.py` — Main navigation
- `src/discovery/energy.py` — Energy page
- etc.

### Step 3: Test with Known Symbol

```bash
python -c "
from src.http_client import HttpClient
from src.collectors.ohlcv import OHLCVCollector

http = HttpClient()
collector = OHLCVCollector(http)

df = collector.collect_latest('ons', '1D')
print(df)
http.close()
"
```

---

## Scenario: API Rate Limited

If TGJU.org starts blocking requests:

1. **Increase delay** between requests in `src/http_client.py`:

```python
REQUEST_DELAY_MIN = 1.0  # Was 0.5
REQUEST_DELAY_JITTER = 1.0  # Was 0.5
```

2. **Reduce batch size** — Process fewer symbols at once

3. **Use VPN/Proxy** — If IP-based blocking

---

## Recovery Checklist

- [ ] Database connection verified
- [ ] `.env` configuration correct
- [ ] ODBC driver installed
- [ ] TGJU.org accessible
- [ ] Latest data collected
- [ ] Historical gaps backfilled
- [ ] Symbol registry up to date
- [ ] No errors in logs
