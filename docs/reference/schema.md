# Database Schema

## TgjuAssets (Legacy Table)

The primary table for daily OHLCV data, preserving compatibility with the original scraper.

```sql
CREATE TABLE TgjuAssets (
    PersianDate      CHAR(10),        -- 'YYYY-MM-DD' (Jalali)
    EnglishDate      DATETIME,        -- Gregorian datetime
    Weekday          VARCHAR(20),     -- 'Monday', 'Tuesday', etc.
    Open             DECIMAL(18, 5),  -- Opening price
    High             DECIMAL(18, 5),  -- Highest price
    Low              DECIMAL(18, 5),  -- Lowest price
    Close            DECIMAL(18, 5),  -- Closing price
    Name             NVARCHAR(100),   -- Persian symbol name
    Symbol_En        VARCHAR(100),    -- English symbol identifier
    ScrapeDate       CHAR(10),        -- Collection date
    ScrapeTime       CHAR(8),         -- Collection time
    ScrapeDateTime   DATETIME         -- Full collection timestamp
)
```

### Example Data

| PersianDate | EnglishDate | Weekday | Open | High | Low | Close | Name | Symbol_En |
|------------|-------------|---------|------|------|-----|-------|------|-----------|
| 1405-04-31 | 2026-07-21 | Tuesday | 4008.29 | 4166.00 | 4008.29 | 4137.09 | انس طلا | ons |
| 1405-04-31 | 2026-07-21 | Tuesday | 1900850 | 1926200 | 1900800 | 1924050 | دلار | price_dollar_rl |

---

## Symbols

Registry of all discovered symbols from TGJU.

```sql
CREATE TABLE Symbols (
    SymbolCode    VARCHAR(50) PRIMARY KEY,
    SymbolFa      NVARCHAR(100) NOT NULL,
    SymbolEn      VARCHAR(100) NOT NULL,
    SourcePage    VARCHAR(50) NOT NULL,
    Category      VARCHAR(50),
    IsActive      BOOLEAN DEFAULT TRUE,
    DiscoveredAt  DATETIME,
    LastUpdated   DATETIME
)
```

---

## DailyOHLCV

Enhanced OHLCV table with volume support (future use).

```sql
CREATE TABLE DailyOHLCV (
    SymbolCode    VARCHAR(50),
    Date          DATE,
    Open          DECIMAL(18, 5),
    High          DECIMAL(18, 5),
    Low           DECIMAL(18, 5),
    Close         DECIMAL(18, 5),
    Volume        BIGINT,
    PersianDate   CHAR(10),
    Weekday       VARCHAR(20),
    ScrapeDateTime DATETIME,
    PRIMARY KEY (SymbolCode, Date)
)
```

---

## IntradayData

Multi-resolution intraday price data.

```sql
CREATE TABLE IntradayData (
    SymbolCode  VARCHAR(50),
    Timestamp   DATETIME,
    Resolution  VARCHAR(5),
    Open        DECIMAL(18, 5),
    High        DECIMAL(18, 5),
    Low         DECIMAL(18, 5),
    Close       DECIMAL(18, 5),
    Volume      BIGINT,
    PRIMARY KEY (SymbolCode, Timestamp, Resolution)
)
```

---

## SymbolProfile

Rich metadata per symbol including technical indicators.

```sql
CREATE TABLE SymbolProfile (
    SymbolCode      VARCHAR(50) PRIMARY KEY,
    BidPrice        DECIMAL(18, 5),
    AskPrice        DECIMAL(18, 5),
    Spread          DECIMAL(18, 5),
    DailyVolume     BIGINT,
    DailyTurnover   DECIMAL(18, 2),
    High52w         DECIMAL(18, 5),
    Low52w          DECIMAL(18, 5),
    EMA_5           DECIMAL(18, 5),
    EMA_10          DECIMAL(18, 5),
    EMA_20          DECIMAL(18, 5),
    EMA_50          DECIMAL(18, 5),
    EMA_200         DECIMAL(18, 5),
    SMA_5           DECIMAL(18, 5),
    SMA_10          DECIMAL(18, 5),
    SMA_20          DECIMAL(18, 5),
    SMA_50          DECIMAL(18, 5),
    SMA_200         DECIMAL(18, 5),
    Support1        DECIMAL(18, 5),
    Resistance1     DECIMAL(18, 5),
    Performance1d   DECIMAL(10, 4),
    Performance1w   DECIMAL(10, 4),
    Performance1m   DECIMAL(10, 4),
    Performance3m   DECIMAL(10, 4),
    Performance1y   DECIMAL(10, 4),
    LastUpdated     DATETIME
)
```

---

## EconomicIndicator

Economic indicators for Iran and global countries.

```sql
CREATE TABLE EconomicIndicators (
    IndicatorCode  VARCHAR(50),
    Country        VARCHAR(50),
    Period         DATE,
    Value          DECIMAL(18, 4),
    Unit           VARCHAR(20),
    Previous       DECIMAL(18, 4),
    Change         DECIMAL(18, 4),
    LastUpdated    DATETIME,
    PRIMARY KEY (IndicatorCode, Country, Period)
)
```

---

## News

Market news articles from TGJU.

```sql
CREATE TABLE News (
    ArticleId    VARCHAR(100) PRIMARY KEY,
    Title        NVARCHAR(500) NOT NULL,
    Summary      TEXT,
    Content      TEXT,
    Url          VARCHAR(500),
    Category     VARCHAR(50),
    PublishedAt  DATETIME,
    Symbols      NVARCHAR(200),
    ScrapedAt    DATETIME
)
```

---

## CollectionLog

Log of data collection runs for monitoring.

```sql
CREATE TABLE CollectionLog (
    Id            INT PRIMARY KEY AUTO_INCREMENT,
    RunId         VARCHAR(36),
    SourcePage    VARCHAR(50),
    SymbolCode    VARCHAR(50),
    DataType      VARCHAR(50),
    Status        VARCHAR(20),
    RecordCount   INT DEFAULT 0,
    ErrorMessage  NVARCHAR(500),
    StartedAt     DATETIME,
    CompletedAt   DATETIME
)
```
