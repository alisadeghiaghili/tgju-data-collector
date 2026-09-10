# Changelog

## v0.6.1 — 2026-09-10

### Fixed
- Exclude table chrome (`cat_title*`) and hyphenated `commodities-*` ids from
  history-capable targets (live tables exist, OHLCV does not).
- Quality coverage no longer treats raw `meta_json` blobs as API types.

## v0.6.0 — 2026-09-10

### Added
- `tgju trowel`: full gap backfill across history-capable catalog symbols
  (successor to AutoTrowel). Skips numeric HTML row ids; optional `--all`.
- History-capability heuristics (`history_support.py`); `sync-history`
  skips symbols that cannot have OHLCV.
- Quality coverage now reports `missing_history_capable` instead of treating
  every catalog row as needing bars.
- `ops/weekly_job.bat` (catalog refresh + trowel + quality).

## v0.5.1 — 2026-09-10

### Fixed
- History parser no longer crashes on `null` OHLC ticks from the API.
- Open/close are clamped into the high–low range after inverted low/high
  swaps, so dirty ticks persist instead of failing the whole symbol.
- Added `ops/audit_integration.py` (catalog-wide consistency audit).

## v0.5.0 — 2026-09-10

### Removed
- Legacy entrypoints: `tgjuScraper.py`, `tgju_scraper.py`, `AutoTrowel_TGJU.py`.
  Use the `tgju` CLI under `src/tgju_collector` instead. See README
  "Migration from v1 scripts".

### Added
- `LICENSE` (MIT).

## v0.4.0 — 2026-09-10

### Changed
- Default HTTP profile is browser-like: desktop Chrome User-Agent (no package
  token), Accept-Language `fa-IR`, Referer `https://www.tgju.org/`.
- Default inter-request delay raised to 1.2–2.8s jittered.
- Catalog search expansion sleeps an extra 0.8s between queries.
- Removed one-off discovery/probe/smoke scripts from the repository.

### Added
- `ops/daily_job.bat` and `ops/README.md` for Task Scheduler + rate guidance.

## v0.3.0 — 2026-09-10

### Added
- Export command: `tgju export --table price_bars|live_snapshots|symbols`
  writing CSV, Parquet, or JSON (optional `--symbol` / `--section` filter).

### Fixed (from live smoke test)
- History API ignores `from`/`to` and can return full history; client now
  filters bars to the requested window before returning.
- TGJU sometimes returns inverted low/high; parser swaps and keeps the bar
  instead of dropping the whole symbol.
- Multiple API timestamps can collapse to one Tehran trade date; repository
  dedupes by `(symbol, trade_date, timeframe)` and bulk-inserts.
- News API payload is `response.items.data`, not `response.news`.
- History symbols normalized to lowercase to match catalog keys.
- `gc*` / `retail_*` coin symbols classified as gold_coin when labels indicate
  coins (previously forced into bourse).

## v0.2.0 — 2026-02-10

### Added
- Iranian trading calendar (`MarketCalendar`): Fridays closed, static holiday
  set for 2025–2027, extra ad-hoc closed dates.
- Gap detection and backfill now skip non-trading days.
- News collector and `sync-news` pipeline/CLI command.
- Data-quality checks (OHLC consistency, null rate, duplicate keys,
  catalog coverage) and `tgju quality` command (exit 1 on issues).
- `tgju backfill` CLI command with `--max-days` and `--from-catalog`.
- SQL Server helpers: `is_mssql_url`, `require_pyodbc`,
  `engine_kwargs_for_url` (pool pre-ping + fast_executemany).
- GitHub Actions CI: ruff + pytest on Python 3.11/3.12.

### Changed
- `missing_dates_for_symbol` is trading-day aware by default.
- CLI engine creation validates optional pyodbc for MSSQL URLs.
- Version bumped to 0.2.0.

## v0.1.0 — 2026-02-10

### Added
- New package layout under `src/tgju_collector` with clean architecture
  (models, http, discovery, clients, collectors, storage, pipelines, CLI).
- Multi-section product taxonomy: gold_coin, currency, crypto, metal, energy,
  commodity, bourse, economics, news, other.
- Catalog discovery from section pages (`data-market-row`) plus the
  TGJU symbol search API.
- Live snapshot collector with Persian-digit / thousands-separator parsing.
- Daily OHLCV history client against `platform.tgju.org` with multi-day windows.
- SQLAlchemy 2.0 schema and repository with upserts and unique keys.
  Price bars are unique on `(symbol, trade_date, timeframe)`.
- Gap detection helper and backfill pipeline skeleton.
- HTTP client with exception-typed timeouts, exponential backoff, and
  polite rate limiting.
- Offline unit test suite with fixtures and fakes.
- CLI: `sync-catalog`, `sync-live`, `sync-history`, `status`.
- `DESIGN.md` architecture and source-surface map.

### Changed
- README rewritten around the new package and honest capability list.
- `.env.example` switched to SQLAlchemy URL + HTTP policy variables.
- `requirements.txt` aligned with `pyproject.toml`.

### Deprecated
- `tgjuScraper.py`, `tgju_scraper.py`, `AutoTrowel_TGJU.py` remain only as
  legacy scripts until migration completes. Prefer the `tgju` CLI.
