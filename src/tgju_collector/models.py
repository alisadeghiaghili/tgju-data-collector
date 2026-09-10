# -*- coding: utf-8 -*-
"""Domain models for TGJU market data.

Pure data structures. No I/O, no network, no SQL.

Examples:
    >>> bar = PriceBar(
    ...     symbol="sekee",
    ...     trade_date=date(2026, 2, 10),
    ...     open=100.0,
    ...     high=110.0,
    ...     low=95.0,
    ...     close=108.0,
    ... )
    >>> bar.symbol
    'sekee'
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any


class ProductSection(StrEnum):
    """High-level market section codes used for taxonomy and storage."""

    GOLD_COIN = "gold_coin"
    CURRENCY = "currency"
    CRYPTO = "crypto"
    METAL = "metal"
    ENERGY = "energy"
    COMMODITY = "commodity"
    BOURSE = "bourse"
    ECONOMICS = "economics"
    NEWS = "news"
    OTHER = "other"


class SymbolSource(StrEnum):
    """Where a symbol was discovered."""

    HTML = "html"
    API = "api"
    BOTH = "both"


@dataclass(frozen=True, slots=True)
class Symbol:
    """A tradable / trackable TGJU market symbol.

    Attributes:
        symbol: Stable identifier used by TGJU APIs and HTML market rows.
        label_fa: Persian display name when known.
        label_en: English display name when known.
        product_section: Mapped product section.
        source: Discovery channel.
        meta: Optional raw extras from the source payload.
    """

    symbol: str
    label_fa: str = ""
    label_en: str = ""
    product_section: ProductSection = ProductSection.OTHER
    source: SymbolSource = SymbolSource.API
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise ValueError("symbol must be a non-empty string")

    def to_record(self) -> dict[str, Any]:
        """Return a flat dict suitable for repository inserts.

        Returns:
            dict[str, Any]: Mapping with symbol metadata columns.
        """
        data = asdict(self)
        data["product_section"] = str(self.product_section)
        data["source"] = str(self.source)
        return data


@dataclass(frozen=True, slots=True)
class PriceBar:
    """OHLCV bar for one symbol on one trade date.

    Attributes:
        symbol: Market symbol id.
        trade_date: Calendar date in Asia/Tehran.
        open: Opening price.
        high: Highest price.
        low: Lowest price.
        close: Closing / last price.
        volume: Optional volume.
        timeframe: Bar resolution, default ``1D``.
        scraped_at: Collection timestamp (UTC).
    """

    symbol: str
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    timeframe: str = "1D"
    scraped_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("symbol is required")
        if self.low > self.high:
            raise ValueError(f"low ({self.low}) cannot exceed high ({self.high}) for {self.symbol}")

    @property
    def key(self) -> tuple[str, str, str]:
        """Primary key tuple used by the repository.

        Returns:
            tuple[str, str, str]: ``(symbol, iso_date, timeframe)``.
        """
        return (self.symbol, self.trade_date.isoformat(), self.timeframe)

    def to_record(self) -> dict[str, Any]:
        """Return a flat dict suitable for repository upserts.

        Returns:
            dict[str, Any]: Mapping with price bar columns.
        """
        return {
            "symbol": self.symbol,
            "trade_date": self.trade_date.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "timeframe": self.timeframe,
            "scraped_at": (self.scraped_at or datetime.utcnow()).isoformat(sep=" ", timespec="seconds"),
        }


@dataclass(frozen=True, slots=True)
class LiveSnapshot:
    """Point-in-time quote captured from a live market table.

    Attributes:
        symbol: Market symbol id.
        captured_at: Capture timestamp (UTC).
        price: Last / current price when available.
        change_pct: Percent change when available.
        open: Session open when available.
        high: Session high when available.
        low: Session low when available.
        raw: Optional raw payload fragment.
    """

    symbol: str
    captured_at: datetime
    price: float | None = None
    change_pct: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("symbol is required")


@dataclass(frozen=True, slots=True)
class NewsItem:
    """A single news entry from TGJU.

    Attributes:
        news_id: Provider-assigned identifier.
        title: Headline text.
        category: Category label when available.
        url: Canonical URL when available.
        published_at: Publication timestamp if known.
        body_excerpt: Short excerpt or summary.
    """

    news_id: str
    title: str
    category: str = ""
    url: str = ""
    published_at: datetime | None = None
    body_excerpt: str = ""

    def __post_init__(self) -> None:
        if not self.news_id:
            raise ValueError("news_id is required")
        if not self.title:
            raise ValueError("title is required")
