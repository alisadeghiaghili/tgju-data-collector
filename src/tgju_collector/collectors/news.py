# -*- coding: utf-8 -*-
"""News collector client for the TGJU news API."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ..discovery.parsers import parse_news_payload
from ..models import NewsItem

logger = logging.getLogger("tgju_collector.collectors.news")

DEFAULT_NEWS_URL = "https://api.tgju.org/v1/news/list"


def _parse_timestamp(value: Any) -> datetime | None:
    """Best-effort parse of a news timestamp field.

    Args:
        value: Raw timestamp (ISO string, epoch, or None).

    Returns:
        datetime | None: Parsed datetime or None.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value))
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M", "%Y/%m/%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
    return None


class NewsCollector:
    """Fetch and normalize TGJU news items.

    Args:
        http: HTTP client exposing ``get_json``.
        base_url: News list endpoint URL.
    """

    def __init__(self, http: Any, *, base_url: str = DEFAULT_NEWS_URL) -> None:
        self.http = http
        self.base_url = base_url

    def fetch(self, *, count: int = 50, category_id: str | int | None = None) -> list[NewsItem]:
        """Fetch recent news items.

        Args:
            count: Maximum number of items requested from the API.
            category_id: Optional category filter when supported by the API.

        Returns:
            list[NewsItem]: Normalized news items.
        """
        params: dict[str, Any] = {"count": str(count)}
        if category_id is not None:
            params["category_id"] = str(category_id)

        payload = self.http.get_json(self.base_url, params=params)
        records = parse_news_payload(payload if isinstance(payload, dict) else {})
        items: list[NewsItem] = []
        for record in records:
            items.append(
                NewsItem(
                    news_id=record["news_id"],
                    title=record["title"],
                    category=record.get("category") or "",
                    url=record.get("url") or "",
                    published_at=_parse_timestamp(record.get("published_at")),
                    body_excerpt=record.get("body_excerpt") or "",
                )
            )
        logger.info("Fetched %s news items", len(items))
        return items
