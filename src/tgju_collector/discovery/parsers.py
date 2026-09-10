# -*- coding: utf-8 -*-
"""HTML parsers for TGJU market tables.

Parsers are pure functions over HTML text so they can be unit-tested from
fixture files without network access.

Examples:
    >>> html = '''<table><tr data-market-row="sekee">
    ...   <th>سکه</th><td>1000</td></tr></table>'''
    >>> rows = parse_market_rows(html)
    >>> rows[0]["symbol"]
    'sekee'
"""

from __future__ import annotations

import re
from typing import Any

from lxml import html as lxml_html

_MARKET_ROW_XPATH = "//tr[@data-market-row]"
_PROFILE_HREF_RE = re.compile(r"/profile/([^/?#]+)")


def _clean_text(nodes: list[str]) -> str:
    return " ".join(part.strip() for part in nodes if part and part.strip())


def parse_market_rows(html_text: str) -> list[dict[str, Any]]:
    """Parse ``data-market-row`` table rows from a TGJU page.

    Args:
        html_text: Raw HTML document text.

    Returns:
        list[dict[str, Any]]: One dict per row with keys:
            ``symbol``, ``label``, ``href``, ``cells``.

    Examples:
        >>> parse_market_rows("")
        []
    """
    if not html_text or not html_text.strip():
        return []

    try:
        root = lxml_html.fromstring(html_text)
    except Exception:
        return []

    rows: list[dict[str, Any]] = []
    for tr in root.xpath(_MARKET_ROW_XPATH):
        symbol = (tr.get("data-market-row") or "").strip()
        if not symbol:
            continue

        cells = [
            _clean_text(td.xpath(".//text()"))
            for td in tr.xpath("./th|./td")
        ]
        label = cells[0] if cells else ""

        href = ""
        anchors = tr.xpath(".//a[@href]")
        if anchors:
            href = anchors[0].get("href") or ""

        rows.append(
            {
                "symbol": symbol,
                "label": label,
                "href": href,
                "cells": cells,
            }
        )
    return rows


def parse_profile_links(html_text: str) -> list[str]:
    """Extract unique ``/profile/<symbol>`` identifiers from HTML.

    Args:
        html_text: Raw HTML document text.

    Returns:
        list[str]: Sorted unique symbol ids found in profile links.
    """
    if not html_text or not html_text.strip():
        return []
    try:
        root = lxml_html.fromstring(html_text)
    except Exception:
        return []

    found: set[str] = set()
    for anchor in root.xpath("//a[@href]"):
        href = anchor.get("href") or ""
        match = _PROFILE_HREF_RE.search(href)
        if match:
            found.add(match.group(1))
    return sorted(found)


def parse_news_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize a TGJU news API payload into plain dicts.

    Args:
        payload: JSON body from ``/v1/news/list``.

    Returns:
        list[dict[str, Any]]: Normalized news records.

    Examples:
        >>> parse_news_payload({"response": {"items": {"data": []}}})
        []
    """
    response = payload.get("response") if isinstance(payload, dict) else None
    if not isinstance(response, dict):
        return []

    items = response.get("items")
    # Live API shape: response.items.data = [...]
    if isinstance(items, dict):
        items = items.get("data") or items.get("news") or []
    if items is None:
        items = response.get("news") or response.get("list") or []
    if not isinstance(items, list):
        return []

    normalized: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        news_id = str(item.get("id") or item.get("news_id") or item.get("mid") or "")
        title = str(item.get("title") or item.get("name") or "").strip()
        if not news_id or not title:
            continue
        summary = str(item.get("summary") or item.get("lead") or item.get("desc") or item.get("body") or "")
        normalized.append(
            {
                "news_id": news_id,
                "title": title,
                "category": str(item.get("category") or item.get("category_title") or ""),
                "url": str(item.get("url") or item.get("link") or ""),
                "published_at": item.get("publish_at") or item.get("date") or item.get("created_at"),
                "body_excerpt": summary[:500],
            }
        )
    return normalized
