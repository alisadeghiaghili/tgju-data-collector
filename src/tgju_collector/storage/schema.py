# -*- coding: utf-8 -*-
"""SQLAlchemy schema for the collector database.

Uses SQLAlchemy Core metadata so the same DDL works on SQLite and SQL Server.

Examples:
    >>> from sqlalchemy import create_engine
    >>> engine = create_engine("sqlite:///:memory:")
    >>> create_all(engine)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)

metadata = MetaData()

symbols = Table(
    "symbols",
    metadata,
    Column("symbol", String(128), primary_key=True),
    Column("label_fa", String(255), nullable=False, default=""),
    Column("label_en", String(255), nullable=False, default=""),
    Column("product_section", String(32), nullable=False, default="other"),
    Column("source", String(16), nullable=False, default="api"),
    Column("meta_json", String(4000), nullable=True),
    Column("first_seen_at", DateTime, nullable=False, default=datetime.utcnow),
    Column(
        "last_seen_at",
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    ),
)

price_bars = Table(
    "price_bars",
    metadata,
    Column("symbol", String(128), primary_key=True),
    Column("trade_date", String(10), primary_key=True),
    Column("open", Float, nullable=False),
    Column("high", Float, nullable=False),
    Column("low", Float, nullable=False),
    Column("close", Float, nullable=False),
    Column("volume", Float, nullable=True),
    Column("timeframe", String(8), primary_key=True, default="1D"),
    Column("scraped_at", DateTime, nullable=False, default=datetime.utcnow),
)

live_snapshots = Table(
    "live_snapshots",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("symbol", String(128), nullable=False),
    Column("captured_at", DateTime, nullable=False),
    Column("price", Float, nullable=True),
    Column("change_pct", Float, nullable=True),
    Column("open", Float, nullable=True),
    Column("high", Float, nullable=True),
    Column("low", Float, nullable=True),
    Column("raw_json", String(4000), nullable=True),
    UniqueConstraint("symbol", "captured_at", name="uq_live_symbol_captured"),
)

news_items = Table(
    "news_items",
    metadata,
    Column("news_id", String(64), primary_key=True),
    Column("title", String(500), nullable=False),
    Column("category", String(128), nullable=True),
    Column("url", String(1000), nullable=True),
    Column("published_at", DateTime, nullable=True),
    Column("body_excerpt", String(2000), nullable=True),
    Column("scraped_at", DateTime, nullable=False, default=datetime.utcnow),
)


def create_all(engine) -> None:
    """Create all tables on the given engine.

    Args:
        engine: SQLAlchemy engine.
    """
    metadata.create_all(engine)


__all__ = [
    "metadata",
    "symbols",
    "price_bars",
    "live_snapshots",
    "news_items",
    "create_all",
]
