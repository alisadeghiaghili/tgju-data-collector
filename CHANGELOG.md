# Changelog

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
