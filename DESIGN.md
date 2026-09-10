# TGJU Data Collector — Design Document

## 1. Problem

The previous implementation collected a partial symbol list (nav menu + energy page)
into a single table with no uniqueness constraint, no multi-section taxonomy, and
no tests. Production claims in the README were not backed by the code.

Goal: a precise, section-aware collector that gathers **all public market data
surface of TGJU** (symbols, live snapshots, OHLCV history, news) with clean
architecture, full type hints, and a TDD-backed core.

## 2. Source Surface (verified 2026-02)

| Surface | URL / pattern | Content | Reliability |
|---------|---------------|---------|-------------|
| Homepage market tables | `https://www.tgju.org/` | ~200+ live rows via `data-market-row` | High |
| Section pages | `/coin`, `/currency`, `/crypto`, `/energy`, `/global-market` | Section-scoped live tables | High |
| Chart history API | `https://platform.tgju.org/fa/tvdata/history?symbol=&resolution=&from=&to=` | OHLCV bars | High |
| Symbol search API | `https://platform.tgju.org/fa/tvdata/search?query=` | Symbol metadata (`type`, `description`) | High |
| Structured market lists | `https://api.tgju.org/v1/newsearch?module=&batch=` | Catalog by batch (crypto, bonds, commodities…) | Medium |
| News | `https://api.tgju.org/v1/news/list` | News items + categories | Medium |

HTML XPath scraping of deep nav menus is **not** the primary catalog source.
Catalog is built from market-row IDs + search API + newsearch batches.

## 3. Product Sections

| Code | Label (fa) | Examples |
|------|------------|----------|
| `gold_coin` | طلا و سکه | sekee, geram18, mesghal, gold_melted, ime_fund_* |
| `currency` | ارز | price_dollar_rl, price_euro_rl, nima_*, sana_* |
| `crypto` | ارز دیجیتال | crypto-bitcoin, crypto-tether-irr |
| `metal` | فلزات | ons, silver, platinum, palladium |
| `energy` | انرژی | oil_brent, oil_opec, energy_natural_gas |
| `commodity` | کالا | commodities-* |
| `bourse` | بورس | gc30, stock symbols, funds |
| `economics` | شاخص‌های اقتصادی | economic indicators |
| `news` | اخبار | news items (separate store) |
| `other` | سایر | unmapped / numeric table IDs |

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI (cli.py)                        │
│   sync-catalog | sync-live | sync-history | backfill | status│
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    Pipelines (use-cases)                    │
│         sync_catalog · sync_live · sync_history · backfill  │
└───────┬─────────────────────┬───────────────────┬───────────┘
        │                     │                   │
┌───────▼───────┐   ┌─────────▼────────┐  ┌───────▼────────┐
│  Discovery    │   │   Collectors     │  │   Storage      │
│  catalog      │   │   live / history │  │   repository   │
│  parsers      │   │   news           │  │   schema       │
└───────┬───────┘   └─────────┬────────┘  └───────┬────────┘
        │                     │                   │
┌───────▼─────────────────────▼────────┐  ┌───────▼────────┐
│  HTTP client (session, retry, rate)  │  │  Adapters      │
│  + TGJU API clients                  │  │  sqlite / mssql│
└──────────────────────────────────────┘  └────────────────┘
```

**Rules**

- Domain models (`models.py`) have no I/O.
- Pipelines orchestrate; they do not parse HTML or build SQL by hand.
- Storage is behind a repository protocol; sqlite is default for tests/dev,
  SQL Server for production.
- Timezone is always `Asia/Tehran` for market dates.
- Unique key on prices: `(symbol, trade_date)`.

## 5. Data Model

### 5.1 `symbols`

| Column | Type | Notes |
|--------|------|-------|
| symbol | TEXT PK | market-row / API symbol id |
| label_fa | TEXT | Persian display name |
| label_en | TEXT NULL | English name if available |
| product_section | TEXT | one of section codes |
| source | TEXT | html / api / both |
| meta_json | TEXT NULL | raw extras |
| first_seen_at | TIMESTAMP | |
| last_seen_at | TIMESTAMP | |

### 5.2 `price_bars`

| Column | Type | Notes |
|--------|------|-------|
| symbol | TEXT | FK → symbols |
| trade_date | DATE | Asia/Tehran calendar date (ISO) |
| open / high / low / close | REAL | |
| volume | REAL NULL | |
| timeframe | TEXT | `1D` (future: intraday) |
| scraped_at | TIMESTAMP | |
| PK | (symbol, trade_date, timeframe) | upsert on conflict |

### 5.3 `live_snapshots`

| Column | Type | Notes |
|--------|------|-------|
| symbol | TEXT | |
| captured_at | TIMESTAMP | |
| price | REAL NULL | last |
| change_pct | REAL NULL | |
| open / high / low | REAL NULL | |
| raw_json | TEXT NULL | |
| PK | (symbol, captured_at) | |

### 5.4 `news_items`

| Column | Type | Notes |
|--------|------|-------|
| news_id | TEXT PK | provider id |
| title | TEXT | |
| category | TEXT NULL | |
| url | TEXT NULL | |
| published_at | TIMESTAMP NULL | |
| body_excerpt | TEXT NULL | |
| scraped_at | TIMESTAMP | |

## 6. HTTP Policy

- Shared `requests.Session` per process.
- Timeout default **30s** (not 100000).
- Retries: 3 attempts, exponential backoff `0.5 * 2**n` + jitter, cap 8s.
- Distinguish `ConnectTimeout` by exception type, not message substring.
- Polite delay 0.3–0.8s between page/API hits.
- User-Agent identifies a research collector, not a fake browser claim.

## 7. Roadmap / Versions

| Version | Scope | PR |
|---------|-------|----|
| **v0.1.0** | Package layout, config, HTTP, models, sqlite schema, catalog discovery, live snapshot, history client, tests, CLI skeleton | PR#1 |
| **v0.2.0** | Full multi-section catalog sync, news collector, backfill gap detection (market-day aware), MSSQL adapter | PR#2 |
| **v0.3.0** | Scheduler examples, data quality checks, export tools, production README | PR#3 |

## 8. TDD Policy

- Tests run offline with fixtures / mocks (no live network in CI).
- Write failing test → implement → green → commit.
- Coverage target for core modules ≥ 85%.

## 9. Naming & Style

- Python: PEP 8, snake_case modules/functions, PascalCase classes.
- Package name: `tgju_collector`.
- Commits: Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`, `ci:`).
- No hardcoded credentials. No AI co-author trailers.
