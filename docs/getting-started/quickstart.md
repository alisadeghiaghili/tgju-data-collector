# Quick Start

This guide walks you through your first data collection in under 5 minutes.

## Step 1: Verify Setup

```bash
python main.py status
```

Ensure `.env` is configured and the database connection works.

## Step 2: Discover Symbols

Find all available market symbols on TGJU:

```bash
python main.py discover
```

Output:

```
============================================================
Discovery Complete: 385 unique symbols
============================================================

CURRENCY (98 symbols):
  price_dollar_rl                 دلار
  price_eur                       یورو
  price_gbp                       پوند
  ...

GOLD (16 symbols):
  ons                             انس طلا
  gold_melted_wholesale           آبشده بنکداری
  gold_740k                       طلای 18 عیار
  ...
```

### Save Symbols to Database

```bash
python main.py discover --save-db
```

## Step 3: Collect Daily Data

Fetch the latest OHLCV data for all discovered symbols:

```bash
python main.py collect
```

Output:

```
============================================================
TGJU Daily OHLCV Collection
============================================================
INFO: Discovered 385 symbols
INFO: Fetching 385 symbols...
INFO: [1/385] ons - OK
INFO: [2/385] gold_melted_wholesale - OK
...
INFO: Collection complete: 380 records saved
```

## Step 4: Backfill Historical Data

Fill gaps in historical data (first run may take a while):

```bash
python main.py backfill
```

### Backfill Specific Symbols

```bash
python main.py backfill --symbols ons price_dollar_rl sekee
```

### Limit Backfill Window

```bash
python main.py backfill --max-days 365
```

---

## Typical Daily Workflow

```bash
# Morning: collect fresh data
python main.py collect

# Weekly: fill any gaps
python main.py backfill

# Check status
python main.py status
```

---

## Next Steps

- [Architecture Overview](../architecture/overview.md) — Understand how the system works
- [Symbol Discovery](../modules/discovery.md) — Learn about the 10 discovery sources
- [Database Schema](../reference/schema.md) — See the data model
