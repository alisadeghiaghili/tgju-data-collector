# TGJU Data Collector

Section-aware market data collector for [TGJU.org](https://www.tgju.org)
(gold, currency, crypto, energy, metals, commodities, bourse, news).

**Current version: v0.1.0**

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
  discovery/         # catalog + HTML parsers
  clients/           # history API
  collectors/        # live snapshots
  storage/           # schema + repository (SQLAlchemy 2.0)
  cli.py             # argparse entry point
```

## Testing

```bash
pytest
```

Tests are offline (fixtures + fakes). No live network required.

## Legacy scripts

`tgjuScraper.py`, `tgju_scraper.py`, and `AutoTrowel_TGJU.py` are the previous
generation scripts. They are superseded by `src/tgju_collector` and kept only
until migration is complete. Prefer the `tgju` CLI.

## License

MIT
