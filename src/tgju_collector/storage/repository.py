# -*- coding: utf-8 -*-
"""Repository for persisting collector domain objects.

Uses SQLAlchemy 2.0 connection API. Upserts are implemented with portable
``INSERT ... ON CONFLICT`` for SQLite and fall back to merge semantics.

Examples:
    >>> from sqlalchemy import create_engine
    >>> from tgju_collector.storage.schema import create_all
    >>> from tgju_collector.storage.repository import Repository
    >>> engine = create_engine("sqlite:///:memory:")
    >>> create_all(engine)
    >>> repo = Repository(engine)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.engine import Engine

from ..dates import utc_now
from ..models import LiveSnapshot, NewsItem, PriceBar, Symbol
from . import schema

logger = logging.getLogger("tgju_collector.storage")


class Repository:
    """Persistence gateway for symbols, prices, snapshots, and news.

    Args:
        engine: Configured SQLAlchemy engine.
    """

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    # ----- symbols -----

    def upsert_symbols(self, symbols: Sequence[Symbol]) -> int:
        """Insert or update symbol metadata.

        Args:
            symbols: Symbols to persist.

        Returns:
            int: Number of symbols processed.
        """
        if not symbols:
            return 0
        now = utc_now().replace(tzinfo=None)
        rows = []
        for item in symbols:
            rows.append(
                {
                    "symbol": item.symbol,
                    "label_fa": item.label_fa or "",
                    "label_en": item.label_en or "",
                    "product_section": str(item.product_section),
                    "source": str(item.source),
                    "meta_json": json.dumps(item.meta, ensure_ascii=False)[:4000],
                    "first_seen_at": now,
                    "last_seen_at": now,
                }
            )

        with self.engine.begin() as conn:
            existing = {
                row.symbol
                for row in conn.execute(select(schema.symbols.c.symbol)).all()
            }
            for row in rows:
                if row["symbol"] in existing:
                    conn.execute(
                        schema.symbols.update()
                        .where(schema.symbols.c.symbol == row["symbol"])
                        .values(
                            label_fa=row["label_fa"],
                            label_en=row["label_en"],
                            product_section=row["product_section"],
                            source=row["source"],
                            meta_json=row["meta_json"],
                            last_seen_at=row["last_seen_at"],
                        )
                    )
                else:
                    conn.execute(schema.symbols.insert().values(**row))
        return len(rows)

    def list_symbols(self, *, section: str | None = None) -> list[dict[str, Any]]:
        """Return stored symbols, optionally filtered by product section.

        Args:
            section: Optional product section code.

        Returns:
            list[dict[str, Any]]: Symbol rows.
        """
        stmt = select(schema.symbols)
        if section:
            stmt = stmt.where(schema.symbols.c.product_section == section)
        with self.engine.connect() as conn:
            return [dict(row._mapping) for row in conn.execute(stmt).all()]

    # ----- price bars -----

    def upsert_price_bars(self, bars: Sequence[PriceBar]) -> int:
        """Upsert OHLCV bars keyed by ``(symbol, trade_date, timeframe)``.

        Args:
            bars: Bars to persist.

        Returns:
            int: Number of bars written.
        """
        if not bars:
            return 0

        # Last write wins when the API maps multiple timestamps to one trade date.
        deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
        for bar in bars:
            record = bar.to_record()
            if isinstance(record["scraped_at"], str):
                record["scraped_at"] = datetime.fromisoformat(record["scraped_at"])
            key = (record["symbol"], record["trade_date"], record["timeframe"])
            deduped[key] = record

        records = list(deduped.values())
        symbols_in_batch = {record["symbol"] for record in records}

        with self.engine.begin() as conn:
            existing_keys = {
                (row.symbol, row.trade_date, row.timeframe)
                for row in conn.execute(
                    select(
                        schema.price_bars.c.symbol,
                        schema.price_bars.c.trade_date,
                        schema.price_bars.c.timeframe,
                    ).where(schema.price_bars.c.symbol.in_(symbols_in_batch))
                ).all()
            }

            to_insert: list[dict[str, Any]] = []
            to_update: list[dict[str, Any]] = []
            for record in records:
                key = (record["symbol"], record["trade_date"], record["timeframe"])
                if key in existing_keys:
                    to_update.append(record)
                else:
                    to_insert.append(record)
                    existing_keys.add(key)

            if to_insert:
                conn.execute(schema.price_bars.insert(), to_insert)

            for record in to_update:
                conn.execute(
                    schema.price_bars.update()
                    .where(
                        (schema.price_bars.c.symbol == record["symbol"])
                        & (schema.price_bars.c.trade_date == record["trade_date"])
                        & (schema.price_bars.c.timeframe == record["timeframe"])
                    )
                    .values(
                        open=record["open"],
                        high=record["high"],
                        low=record["low"],
                        close=record["close"],
                        volume=record["volume"],
                        scraped_at=record["scraped_at"],
                    )
                )
        return len(records)

    def existing_trade_dates(self, symbol: str) -> set[str]:
        """Return ISO trade dates already stored for a symbol.

        Args:
            symbol: Market symbol id.

        Returns:
            set[str]: ISO date strings present in ``price_bars``.
        """
        stmt = select(schema.price_bars.c.trade_date).where(
            schema.price_bars.c.symbol == symbol
        )
        with self.engine.connect() as conn:
            return {row[0] for row in conn.execute(stmt).all()}

    # ----- live snapshots -----

    def insert_live_snapshots(self, snapshots: Sequence[LiveSnapshot]) -> int:
        """Insert live snapshots, skipping exact ``(symbol, captured_at)`` dupes.

        Args:
            snapshots: Snapshots to persist.

        Returns:
            int: Number of rows inserted.
        """
        if not snapshots:
            return 0
        inserted = 0
        with self.engine.begin() as conn:
            for snap in snapshots:
                captured = snap.captured_at.replace(tzinfo=None)
                exists = conn.execute(
                    select(schema.live_snapshots.c.id).where(
                        (schema.live_snapshots.c.symbol == snap.symbol)
                        & (schema.live_snapshots.c.captured_at == captured)
                    )
                ).first()
                if exists:
                    continue
                conn.execute(
                    schema.live_snapshots.insert().values(
                        symbol=snap.symbol,
                        captured_at=captured,
                        price=snap.price,
                        change_pct=snap.change_pct,
                        open=snap.open,
                        high=snap.high,
                        low=snap.low,
                        raw_json=json.dumps(snap.raw, ensure_ascii=False)[:4000],
                    )
                )
                inserted += 1
        return inserted

    # ----- news -----

    def upsert_news(self, items: Iterable[NewsItem]) -> int:
        """Insert or update news items keyed by ``news_id``.

        Args:
            items: News items to persist.

        Returns:
            int: Number of items processed.
        """
        count = 0
        with self.engine.begin() as conn:
            for item in items:
                exists = conn.execute(
                    select(schema.news_items.c.news_id).where(
                        schema.news_items.c.news_id == item.news_id
                    )
                ).first()
                values = {
                    "title": item.title,
                    "category": item.category,
                    "url": item.url,
                    "published_at": item.published_at,
                    "body_excerpt": item.body_excerpt[:2000],
                    "scraped_at": utc_now().replace(tzinfo=None),
                }
                if exists:
                    conn.execute(
                        schema.news_items.update()
                        .where(schema.news_items.c.news_id == item.news_id)
                        .values(**values)
                    )
                else:
                    conn.execute(
                        schema.news_items.insert().values(news_id=item.news_id, **values)
                    )
                count += 1
        return count
