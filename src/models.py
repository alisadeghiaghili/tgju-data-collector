# -*- coding: utf-8 -*-
"""
SQLAlchemy models for TGJU Data Collector.

Defines all database tables. New tables are additive — existing TgjuAssets is preserved.
"""

from datetime import datetime

from sqlalchemy import (
    Column, String, NVARCHAR, CHAR, VARCHAR, DECIMAL, DATETIME, DATE,
    Integer, BigInteger, Boolean, Text, Index,
    create_engine
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TgjuAssets(Base):
    """Legacy daily OHLC table (preserved for backwards compatibility)."""
    __tablename__ = 'TgjuAssets'

    PersianDate = Column(CHAR(10), primary_key=True)
    EnglishDate = Column(DATETIME)
    Weekday = Column(VARCHAR(20))
    Open = Column(DECIMAL(18, 5))
    High = Column(DECIMAL(18, 5))
    Low = Column(DECIMAL(18, 5))
    Close = Column(DECIMAL(18, 5))
    Name = Column(NVARCHAR(100))
    Symbol_En = Column(VARCHAR(100))
    ScrapeDate = Column(CHAR(10))
    ScrapeTime = Column(CHAR(8))
    ScrapeDateTime = Column(DATETIME)


class Symbol(Base):
    """Symbol registry — all discovered symbols from TGJU."""
    __tablename__ = 'Symbols'

    SymbolCode = Column(VARCHAR(50), primary_key=True)
    SymbolFa = Column(NVARCHAR(100), nullable=False)
    SymbolEn = Column(VARCHAR(100), nullable=False)
    SourcePage = Column(VARCHAR(50), nullable=False)
    Category = Column(VARCHAR(50))
    IsActive = Column(Boolean, default=True)
    DiscoveredAt = Column(DATETIME, default=datetime.utcnow)
    LastUpdated = Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow)


class DailyOHLCV(Base):
    """Enhanced daily OHLCV data (adds Volume to existing OHLC)."""
    __tablename__ = 'DailyOHLCV'

    SymbolCode = Column(VARCHAR(50), primary_key=True)
    Date = Column(DATE, primary_key=True)
    Open = Column(DECIMAL(18, 5))
    High = Column(DECIMAL(18, 5))
    Low = Column(DECIMAL(18, 5))
    Close = Column(DECIMAL(18, 5))
    Volume = Column(BigInteger)
    PersianDate = Column(CHAR(10))
    Weekday = Column(VARCHAR(20))
    ScrapeDateTime = Column(DATETIME, default=datetime.utcnow)


class IntradayData(Base):
    """Multi-resolution intraday price data."""
    __tablename__ = 'IntradayData'

    SymbolCode = Column(VARCHAR(50), primary_key=True)
    Timestamp = Column(DATETIME, primary_key=True)
    Resolution = Column(VARCHAR(5), primary_key=True)
    Open = Column(DECIMAL(18, 5))
    High = Column(DECIMAL(18, 5))
    Low = Column(DECIMAL(18, 5))
    Close = Column(DECIMAL(18, 5))
    Volume = Column(BigInteger)


class SymbolProfile(Base):
    """Rich metadata per symbol: technical indicators, S/R, performance."""
    __tablename__ = 'SymbolProfile'

    SymbolCode = Column(VARCHAR(50), primary_key=True)
    BidPrice = Column(DECIMAL(18, 5))
    AskPrice = Column(DECIMAL(18, 5))
    Spread = Column(DECIMAL(18, 5))
    DailyVolume = Column(BigInteger)
    DailyTurnover = Column(DECIMAL(18, 2))
    High52w = Column(DECIMAL(18, 5))
    Low52w = Column(DECIMAL(18, 5))
    EMA_5 = Column(DECIMAL(18, 5))
    EMA_10 = Column(DECIMAL(18, 5))
    EMA_20 = Column(DECIMAL(18, 5))
    EMA_50 = Column(DECIMAL(18, 5))
    EMA_200 = Column(DECIMAL(18, 5))
    SMA_5 = Column(DECIMAL(18, 5))
    SMA_10 = Column(DECIMAL(18, 5))
    SMA_20 = Column(DECIMAL(18, 5))
    SMA_50 = Column(DECIMAL(18, 5))
    SMA_200 = Column(DECIMAL(18, 5))
    Support1 = Column(DECIMAL(18, 5))
    Resistance1 = Column(DECIMAL(18, 5))
    Performance1d = Column(DECIMAL(10, 4))
    Performance1w = Column(DECIMAL(10, 4))
    Performance1m = Column(DECIMAL(10, 4))
    Performance3m = Column(DECIMAL(10, 4))
    Performance1y = Column(DECIMAL(10, 4))
    LastUpdated = Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow)


class EconomicIndicator(Base):
    """Economic indicators for Iran and global countries."""
    __tablename__ = 'EconomicIndicators'

    IndicatorCode = Column(VARCHAR(50), primary_key=True)
    Country = Column(VARCHAR(50), primary_key=True)
    Period = Column(DATE, primary_key=True)
    Value = Column(DECIMAL(18, 4))
    Unit = Column(VARCHAR(20))
    Previous = Column(DECIMAL(18, 4))
    Change = Column(DECIMAL(18, 4))
    LastUpdated = Column(DATETIME, default=datetime.utcnow)


class News(Base):
    """Market news articles from TGJU."""
    __tablename__ = 'News'

    ArticleId = Column(VARCHAR(100), primary_key=True)
    Title = Column(NVARCHAR(500), nullable=False)
    Summary = Column(Text)
    Content = Column(Text)
    Url = Column(VARCHAR(500))
    Category = Column(VARCHAR(50))
    PublishedAt = Column(DATETIME)
    Symbols = Column(NVARCHAR(200))
    ScrapedAt = Column(DATETIME, default=datetime.utcnow)


class CollectionLog(Base):
    """Log of data collection runs for monitoring."""
    __tablename__ = 'CollectionLog'

    Id = Column(Integer, primary_key=True, autoincrement=True)
    RunId = Column(String(36))
    SourcePage = Column(VARCHAR(50))
    SymbolCode = Column(VARCHAR(50))
    DataType = Column(VARCHAR(50))
    Status = Column(VARCHAR(20))
    RecordCount = Column(Integer, default=0)
    ErrorMessage = Column(NVARCHAR(500))
    StartedAt = Column(DATETIME)
    CompletedAt = Column(DATETIME)


def create_all_tables(engine):
    """Create all tables if they don't exist."""
    Base.metadata.create_all(engine)
