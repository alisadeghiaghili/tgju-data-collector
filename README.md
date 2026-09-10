# TGJU Data Collector

Section-aware market data collector for [TGJU.org](https://www.tgju.org)
(gold, currency, crypto, energy, metals, commodities, bourse, news).

**Current version: v0.6.0**

## What it collects

| Domain | Source | Storage |
|--------|--------|---------|
| Symbol catalog | Section pages + search API | `symbols` |
| Live snapshots | Homepage / section market tables | `live_snapshots` |
| Daily OHLCV | `platform.tgju.org` history API | `price_bars` |
| News | `api.tgju.org` news list | `news_items` |

Product sections: `gold_coin`, `currency`, `crypto`, `metal`, `energy`,
`commodity`, `bourse`, `economics`, `news`, `other`.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e ".[dev]"
```

## Configure

```bash
cp .env.example .env
# edit TGJU_DB_URL if needed (defaults to SQLite)
```

## Usage

```bash
# Discover all symbols across sections
tgju sync-catalog
tgju sync-catalog --dry-run

# Capture live prices from section pages
tgju sync-live
tgju sync-live --pages home,crypto

# Fetch daily history (7-day window by default)
tgju sync-history --symbol sekee --days 14
tgju sync-history --from-catalog --days 30

# News
tgju sync-news --count 30

# Backfill gaps (skips Fridays and Iranian holidays)
tgju backfill --symbol sekee --max-days 365
tgju backfill --from-catalog

# Full gap backfill across history-capable symbols (trowel)
tgju trowel --max-days 365
tgju trowel --symbol sekee --all

# Data quality (exit code 1 if issues found)
tgju quality

# Export
tgju export --table price_bars --output out/bars.csv --symbol sekee
tgju export --table symbols --output out/catalog.json

# Database status
tgju status
```

Without installing the package:

```bash
set PYTHONPATH=src
python -m tgju_collector.cli --help
```

## Architecture

See [DESIGN.md](DESIGN.md) for source surface map, data model, HTTP policy,
and version roadmap.

```
src/tgju_collector/
  config.py          # env-driven settings
  http.py            # session, retries, rate limit
  models.py          # Symbol, PriceBar, LiveSnapshot, NewsItem
  sections.py        # product-section taxonomy
  dates.py           # Asia/Tehran date helpers
  calendar/          # Iranian trading calendar (Fridays + holidays)
  discovery/         # catalog + HTML parsers
  clients/           # history API
  collectors/        # live snapshots + news
  quality/           # OHLC / coverage checks
  storage/           # schema, repository, MSSQL helpers
  pipelines/         # sync + backfill orchestration
  export.py          # CSV/Parquet/JSON export
  cli.py             # argparse entry point
ops/
  daily_job.bat      # Task Scheduler entrypoint
  README.md          # rate profile + ops notes
```

## Testing

```bash
pytest
```

Tests are offline (fixtures + fakes). No live network required.

## Migration from v1 scripts

If you previously ran `tgjuScraper.py` / `AutoTrowel_TGJU.py`:

1. Point `TGJU_DB_URL` at the same SQL Server database
   (`mssql+pyodbc://...`).
2. The new schema uses `symbols` / `price_bars` / `live_snapshots` /
   `news_items` with unique keys. The old `TgjuAssets` table is left
   untouched — export or copy it yourself if you still need it.
3. Run `tgju sync-catalog` then `tgju backfill --from-catalog`.

## License

MIT
