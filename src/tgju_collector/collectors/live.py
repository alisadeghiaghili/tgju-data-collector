# -*- coding: utf-8 -*-
"""Live snapshot collectors from TGJU HTML market tables."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ..dates import utc_now
from ..discovery.parsers import parse_market_rows
from ..models import LiveSnapshot
from ..sections import SECTION_PAGE_URLS

logger = logging.getLogger("tgju_collector.collectors.live")

# Many TGJU cells embed Persian digits and thousands separators.
_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_number(text: str | None) -> float | None:
    """Parse a human-formatted price cell into a float.

    Handles Persian digits, thousands separators, and percent signs.

    Args:
        text: Raw cell text.

    Returns:
        float | None: Parsed number or None when not numeric.

    Examples:
        >>> normalize_number("۱٬۲۳۴٫۵")
        1234.5
        >>> normalize_number("n/a") is None
        True
    """
    if text is None:
        return None
    cleaned = (
        str(text)
        .translate(_PERSIAN_DIGITS)
        .replace(",", "")
        .replace("٬", "")
        .replace("٫", ".")
        .replace("%", "")
        .replace("٪", "")
        .strip()
    )
    if not cleaned or cleaned in {"-", "—", "null", "None"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def snapshots_from_html(html_text: str, *, captured_at: datetime | None = None) -> list[LiveSnapshot]:
    """Build live snapshots from a TGJU page HTML body.

    Args:
        html_text: Raw HTML containing market tables.
        captured_at: Capture timestamp; defaults to now (UTC).

    Returns:
        list[LiveSnapshot]: Snapshots for rows that expose a symbol id.
    """
    moment = captured_at or utc_now()
    rows = parse_market_rows(html_text)
    snapshots: list[LiveSnapshot] = []
    for row in rows:
        cells = row.get("cells") or []
        # Typical layout: label | last | change% | open | high | low | time
        price = normalize_number(cells[1]) if len(cells) > 1 else None
        change_pct = normalize_number(cells[2]) if len(cells) > 2 else None
        open_ = normalize_number(cells[3]) if len(cells) > 3 else None
        high = normalize_number(cells[4]) if len(cells) > 4 else None
        low = normalize_number(cells[5]) if len(cells) > 5 else None
        snapshots.append(
            LiveSnapshot(
                symbol=row["symbol"],
                captured_at=moment,
                price=price,
                change_pct=change_pct,
                open=open_,
                high=high,
                low=low,
                raw={"label": row.get("label", ""), "cells": cells},
            )
        )
    return snapshots


class LiveCollector:
    """Collect live snapshots from one or more section pages.

    Args:
        http: HTTP client exposing ``get_text``.
        pages: Mapping of page name → URL.
    """

    def __init__(
        self,
        http: Any,
        *,
        pages: dict[str, str] | None = None,
    ) -> None:
        self.http = http
        self.pages = dict(pages or SECTION_PAGE_URLS)

    def collect(self, *, page_names: list[str] | None = None) -> list[LiveSnapshot]:
        """Fetch selected pages and parse live snapshots.

        Args:
            page_names: Optional subset of page keys. Defaults to all.

        Returns:
            list[LiveSnapshot]: Combined snapshots (may include duplicates
            across pages; repository upserts handle persistence).
        """
        selected = page_names or list(self.pages)
        collected: list[LiveSnapshot] = []
        for name in selected:
            url = self.pages.get(name)
            if not url:
                logger.warning("Unknown page name: %s", name)
                continue
            try:
                html_text = self.http.get_text(url)
            except Exception as exc:
                logger.warning("Live collect failed for %s: %s", name, exc)
                continue
            page_snapshots = snapshots_from_html(html_text)
            logger.info("Collected %s live snapshots from %s", len(page_snapshots), name)
            collected.extend(page_snapshots)
        return collected
