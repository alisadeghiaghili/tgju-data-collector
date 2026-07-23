# Changelog

## v2.1.0 (2026-07-21)

### Added

- **Modular Architecture**: Refactored monolithic scripts into `src/` package
- **CLI Entry Point**: `main.py` with subcommands (`collect`, `discover`, `backfill`, `status`)
- **Symbol Discovery**: 11 discovery sources covering 385+ symbols across 10 categories
- **OHLCV Collector**: Multi-resolution data collection (1m to monthly)
- **Backfill Engine**: Automatic gap detection and historical data fill
- **Configuration Module**: Unified `.env` support with validation
- **HTTP Client**: Shared client with retry, rate limiting, and error handling
- **SQLAlchemy Models**: Complete ORM for all database tables
- **Documentation**: Comprehensive MkDocs documentation site

### Fixed

- **Volume Array Handling**: Pad empty volume arrays to prevent DataFrame construction errors
- **Date Conversion**: Improved Persian/Gregorian date handling

### Changed

- **Config Wrapper**: Root `config.py` now delegates to `src.config` for backwards compatibility
- **Dependencies**: Added `python-dotenv` to requirements

### Removed

- **tgju_scraper.py**: Replaced by modular `src/` architecture
- **AutoTrowel_TGJU.py**: Replaced by `src/backfill.py`

---

## v2.0.0 (2026-02-07)

### Added

- **AutoTrowel_TGJU.py**: Intelligent backfill for historical data gaps
- **Gap Detection**: Automatic identification of missing dates
- **Incremental Loading**: Only inserts new records, avoids duplicates
- **Progress Tracking**: Real-time progress for large backfill operations
- **Configurable Backfill Window**: Default 2 years, adjustable

### Security

- **SonarQube S2115 Compliant**: Passes security rule checks
- **Placeholder Validation**: Rejects placeholder values (e.g., `your_password`)
- **Connection String Encoding**: Special characters URL-encoded

### Documentation

- **Comprehensive README**: Detailed setup, usage, and troubleshooting guides
- **Architecture Diagram**: Visual representation of system design
- **Performance Metrics**: Benchmarks for collection and backfill operations

---

## v1.0.0 (2026-02-07)

### Added

- **Daily Data Scraper**: Collects latest OHLCV data for all TGJU symbols
- **Symbol Discovery**: Automatically finds symbols from main and energy pages
- **Resilient HTTP Requests**: Retry logic with exponential backoff
- **Data Validation**: Validates structure, consistency, and completeness
- **Persian Date Support**: Converts Gregorian to Persian calendar automatically
- **Database Integration**: SQL Server persistence with proper type mapping
- **Secure Configuration**: Environment-based credentials management
- **Comprehensive Error Handling**: Detailed logging and graceful degradation
- **User Agent Spoofing**: Avoids blocking by appearing as regular browser
- **Rate Limiting**: 0.5-1s delays between requests
- **Dual Logging**: File + console output with rotation

---

## Roadmap

### v2.2.0 (Planned)

- **Parallel Collection**: Multi-threaded symbol processing
- **Redis Caching**: Cache API responses to reduce server load
- **Web Dashboard**: Real-time monitoring interface
- **Alert System**: Email/Telegram notifications for failures
- **Docker Support**: Containerized deployment
- **CI/CD Pipeline**: Automated testing and deployment

### v3.0.0 (Future)

- **Real-time Streaming**: WebSocket-based live data
- **Machine Learning**: Price prediction models
- **Portfolio Tracking**: Personal investment portfolio management
- **API Server**: RESTful API for external integrations
- **Multi-database Support**: PostgreSQL, MySQL, SQLite
