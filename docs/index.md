# TGJU Data Collector

**Real-time market data scraper for [TGJU.org](https://www.tgju.org) (Tehran Gold and Jewelry Union)**

TGJU Data Collector automatically discovers and collects OHLCV (Open/High/Low/Close/Volume) market data from Iran's primary financial data source, with automated persistence to SQL Server and intelligent historical backfill capabilities.

---

## Features

### Comprehensive Market Coverage

Discover and track **385+ symbols** across 10 market categories:

| Category | Examples | Count |
|----------|----------|-------|
| **Currency** | USD/IRR, EUR/IRR, GBP/IRR | 98 |
| **Energy** | WTI Crude, Brent, Natural Gas | 126 |
| **Gold** | Ounce Gold, 18K Gold, Silver | 16 |
| **Coin** | Bahar Azadi, Imami | 13 |
| **Metal** | Copper, Aluminum, Zinc | 11 |
| **Commodity** | Wheat, Cotton, Soybeans | 24 |
| **Crypto** | Bitcoin, Ethereum, Ripple | 12 |
| **Index** | Dow Jones, S&P 500, CAC 40 | 47 |
| **Fund** | Gold ETFs | 4 |
| **Other** | Parsian Coins, Cross Rates | 34 |

### Intelligent Collection

- **Smart Symbol Discovery** — Automatically finds all symbols from TGJU pages
- **Multi-Resolution OHLCV** — 1-minute to monthly data
- **Resilient HTTP** — Retry logic with exponential backoff
- **Rate Limiting** — Polite delays between requests

### Data Integrity

- **Persian Date Support** — Automatic Jalali/Gregorian conversion
- **Gap Detection** — Identifies missing dates in historical data
- **Incremental Loading** — Only inserts new records, avoids duplicates
- **Data Validation** — Validates structure, consistency, and completeness

### Production Ready

- **SQL Server Integration** — Seamless persistence with SQLAlchemy
- **Secure Configuration** — Environment-based credentials (SonarQube S2115 compliant)
- **Comprehensive Logging** — Dual output (file + console) with rotation
- **CLI Interface** — Clean subcommands for all operations

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/alisadeghiaghili/tgju-data-collector.git
cd tgju-data-collector
pip install -r requirements.txt

# Configure database
cp .env.example .env
# Edit .env with your credentials

# Discover all symbols
python main.py discover

# Collect daily data
python main.py collect

# Backfill historical gaps
python main.py backfill
```

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│              CLI Entry Point (main.py)          │
│         collect | discover | backfill | status  │
└────────────────────┬────────────────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌─────────┐   ┌───────────┐   ┌──────────┐
│Discovery │   │ Collector │   │ Backfill │
│ Registry │   │  (OHLCV)  │   │  Engine  │
└────┬─────┘   └─────┬─────┘   └────┬─────┘
     │               │              │
     ▼               ▼              ▼
┌─────────────────────────────────────────────┐
│              TGJU.org API                   │
│     Symbol Discovery → OHLCV History        │
└────────────────────┬────────────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │  SQL Server    │
            │  (TgjuAssets)  │
            └────────────────┘
```

---

## Learn More

<div class="grid cards" markdown>

-   :material-rocket-launch-outline:{ .lg .middle } __Getting Started__

    ---

    Installation, configuration, and your first data collection

    [:octicons-arrow-right-24: Installation](getting-started/installation.md)

-   :material-puzzle-outline:{ .lg .middle } __Architecture__

    ---

    How the system is designed and how data flows through it

    [:octicons-arrow-right-24: Overview](architecture/overview.md)

-   :material-book-open-variant:{ .lg .middle } __Core Modules__

    ---

    Deep dive into each component of the system

    [:octicons-arrow-right-24: Discovery](modules/discovery.md)

-   :material-database:{ .lg .middle } __Data Reference__

    ---

    Database schema, symbol categories, and API documentation

    [:octicons-arrow-right-24: Schema](reference/schema.md)

</div>

---

## Author

**Ali Sadeghi Aghili**

[GitHub](https://github.com/alisadeghiaghili) · [LinkedIn](https://linktr.ee/aliaghili) · [IME](https://www.ime.co.ir)
