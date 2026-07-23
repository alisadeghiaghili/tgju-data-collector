# Architecture Overview

TGJU Data Collector follows a modular, layered architecture designed for reliability, maintainability, and extensibility.

## Design Principles

1. **Separation of Concerns** — Each module handles one responsibility
2. **Resilience First** — Retry logic, rate limiting, graceful degradation
3. **Configuration over Code** — Environment-based settings, no hardcoded values
4. **Backwards Compatibility** — Legacy table schema preserved, old scripts still work

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Layer (main.py)                     │
│            collect │ discover │ backfill │ status           │
└───────────────────────────┬─────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
┌─────────────────┐ ┌───────────────┐ ┌────────────────┐
│ SymbolRegistry  │ │ OHLCVCollector│ │  TGJUBackfill  │
│                 │ │               │ │                │
│ • MainPage      │ │ • collect_    │ │ • detect_gaps  │
│ • Energy        │ │   latest()    │ │ • fill_gaps    │
│ • Sana          │ │ • collect_    │ │ • run()        │
│ • Bank          │ │   range()     │ │                │
│ • GlobalMarket  │ │ • collect_    │ │                │
│ • GoldGlobal    │ │   batch()     │ │                │
│ • Crypto        │ │               │ │                │
│ • Commodities   │ └───────┬───────┘ └───────┬────────┘
│ • Coin          │         │                 │
│ • ParsianCoin   │         │                 │
└────────┬────────┘         │                 │
         │                  │                 │
         ▼                  ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    HTTP Client Layer                        │
│         requests + retry + rate limiting + UA spoofing      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      TGJU.org                               │
│    Main Page │ Energy │ Sana │ Bank │ Global │ Crypto │ ... │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Storage Layer                             │
│              SQLAlchemy → SQL Server                        │
│         TgjuAssets │ Symbols │ DailyOHLCV │ ...            │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Responsibilities

| Module | Responsibility | Key Classes |
|--------|---------------|-------------|
| **CLI** | User interface, argument parsing | `main.py` functions |
| **Discovery** | Find symbols from TGJU pages | `SymbolRegistry`, `BaseDiscovery` subclasses |
| **Collection** | Fetch OHLCV price data | `OHLCVCollector` |
| **Backfill** | Detect and fill historical gaps | `TGJUBackfill` |
| **HTTP** | Resilient network requests | `HttpClient` |
| **Storage** | Database persistence | `SQLServerStorage` |
| **Config** | Environment management | `load_config()`, `get_connection_string()` |
| **Utils** | Date conversion, logging | `to_persian_date()`, `setup_logging()` |

---

## Data Flow

### Daily Collection Flow

```
1. CLI parses args → cmd_collect()
2. SymbolRegistry.discover_all()
   → Iterates 11 discovery classes
   → Each fetches a TGJU page → parses HTML → extracts symbols
   → Deduplicates by symbol code
3. OHLCVCollector.collect_batch()
   → For each symbol: HTTP GET to TGJU API
   → Parses JSON response → builds DataFrame
   → Adds Persian dates and metadata
4. SQLServerStorage.save_daily_ohlcv()
   → Writes to TgjuAssets table
   → Appends new records (no overwrite)
```

### Backfill Flow

```
1. CLI parses args → cmd_backfill()
2. TGJUBackfill.get_symbols_from_db()
   → Queries existing symbols from TgjuAssets
3. For each symbol: detect_gaps()
   → Gets all existing Persian dates
   → Converts to Gregorian
   → Finds gaps (before first, between records, after last)
4. For each gap: OHLCVCollector.collect_range()
   → Fetches historical data from TGJU API
5. SQLServerStorage.save_daily_ohlcv()
   → Inserts new records (avoids duplicates)
```

---

## Error Handling Strategy

| Error Type | Strategy |
|------------|----------|
| Network timeout | Retry 3x with exponential backoff (2-3s delay) |
| HTTP errors | Retry with jitter delay |
| Invalid JSON | Log and skip symbol |
| Empty API response | Skip symbol, continue batch |
| Database error | Log error, return 0 inserted |
| Missing env vars | Raise `ValueError` with clear message |

---

## Thread Safety

The current implementation is **single-threaded** by design:

- TGJU.org may rate-limit concurrent requests
- Database writes are sequential to avoid lock contention
- Simpler error handling and debugging

Future versions may add parallel collection with configurable concurrency.
