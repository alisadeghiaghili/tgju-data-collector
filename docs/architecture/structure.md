# Project Structure

## Directory Layout

```
tgju-data-collector/
├── main.py                     # CLI entry point
├── config.py                   # Backwards-compatible config wrapper
├── requirements.txt            # Python dependencies
├── .env.example                # Configuration template
├── .env                        # Your credentials (gitignored)
├── .gitignore                  # Git ignore rules
├── README.md                   # Project documentation
├── mkdocs.yml                  # Documentation site config
├── docs/                       # Documentation source (MkDocs)
│   ├── index.md
│   ├── getting-started/
│   ├── architecture/
│   ├── modules/
│   ├── reference/
│   └── guides/
├── src/                        # Core package
│   ├── __init__.py
│   ├── config.py               # Unified configuration module
│   ├── http_client.py          # Shared HTTP client
│   ├── models.py               # SQLAlchemy models
│   ├── backfill.py             # Historical backfill engine
│   ├── collectors/
│   │   ├── __init__.py
│   │   └── ohlcv.py            # OHLCV data collection
│   ├── discovery/
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract base class
│   │   ├── registry.py         # Unified symbol registry
│   │   ├── main_page.py        # Main page discovery
│   │   ├── energy.py           # Energy market discovery
│   │   ├── sana.py             # Sana exchange discovery
│   │   ├── bank.py             # Bank rates discovery
│   │   ├── global_market.py    # Global market discovery
│   │   ├── gold_global.py      # Global gold discovery
│   │   ├── crypto.py           # Cryptocurrency discovery
│   │   ├── commodities.py      # Commodities discovery
│   │   └── coin.py             # Coin market discovery
│   ├── storage/
│   │   ├── __init__.py
│   │   └── sqlserver.py        # SQL Server backend
│   └── utils/
│       ├── __init__.py
│       ├── dates.py            # Persian/Gregorian conversion
│       └── logging.py          # Logging configuration
└── logs/                       # Log files (auto-created)
    └── tgju_YYYYMMDD.log
```

---

## Module Map

### Entry Points

| File | Purpose |
|------|---------|
| `main.py` | CLI entry point with subcommands |
| `config.py` | Backwards-compatible wrapper (delegates to `src.config`) |

### Core Package (`src/`)

#### Configuration

| File | Description |
|------|-------------|
| `src/config.py` | Loads `.env`, builds connection strings, validates config |

#### Network

| File | Description |
|------|-------------|
| `src/http_client.py` | `HttpClient` class with retry, timeout, rate limiting |

#### Discovery (`src/discovery/`)

| File | Class | Source |
|------|-------|--------|
| `base.py` | `BaseDiscovery` | Abstract base class |
| `registry.py` | `SymbolRegistry` | Aggregates all discoverers |
| `main_page.py` | `MainPageDiscovery` | TGJU main navigation |
| `energy.py` | `EnergyDiscovery` | `/energy` page |
| `sana.py` | `SanaDiscovery` | Sana exchange rates |
| `bank.py` | `BankDiscovery` | Bank rates |
| `global_market.py` | `GlobalMarketDiscovery` | Global indices/forex |
| `gold_global.py` | `GoldGlobalDiscovery` | Global gold prices |
| `crypto.py` | `CryptoDiscovery` | Cryptocurrency prices |
| `commodities.py` | `CommoditiesDiscovery`, `BaseMetalDiscovery` | Commodities + metals |
| `coin.py` | `CoinDiscovery`, `ParsianCoinDiscovery` | Iranian coins |

#### Collection (`src/collectors/`)

| File | Class | Description |
|------|-------|-------------|
| `ohlcv.py` | `OHLCVCollector` | Fetches OHLCV data from TGJU API |

#### Storage (`src/storage/`)

| File | Class | Description |
|------|-------|-------------|
| `sqlserver.py` | `SQLServerStorage` | SQL Server persistence via SQLAlchemy |

#### Models

| File | Description |
|------|-------------|
| `src/models.py` | SQLAlchemy ORM models for all tables |

#### Utilities (`src/utils/`)

| File | Functions | Description |
|------|-----------|-------------|
| `dates.py` | `to_persian_date()`, `to_weekday()`, `persian_to_gregorian()` | Calendar conversion |
| `logging.py` | `setup_logging()` | Dual-output logging with rotation |

---

## Dependency Graph

```
main.py
├── src.config
├── src.http_client
├── src.discovery.registry
│   ├── src.discovery.main_page
│   ├── src.discovery.energy
│   ├── src.discovery.sana
│   ├── src.discovery.bank
│   ├── src.discovery.global_market
│   ├── src.discovery.gold_global
│   ├── src.discovery.crypto
│   ├── src.discovery.commodities
│   └── src.discovery.coin
├── src.collectors.ohlcv
│   └── src.utils.dates
├── src.storage.sqlserver
│   └── src.config
└── src.backfill
    ├── src.config
    ├── src.http_client
    ├── src.collectors.ohlcv
    └── src.storage.sqlserver
```
