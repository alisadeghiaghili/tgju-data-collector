# -*- coding: utf-8 -*-
"""Build a multi-section symbol catalog from TGJU sources.

The catalog combines:
1. Live market tables on section pages (``data-market-row``).
2. Symbol search API metadata.
3. Optional structured ``newsearch`` batches.

Examples:
    >>> builder = CatalogBuilder(client=FakeClient())
    >>> # builder.build()  # doctest: +SKIP
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from ..models import ProductSection, Symbol, SymbolSource
from ..sections import SECTION_PAGE_URLS, classify_symbol
from .parsers import parse_market_rows

logger = logging.getLogger("tgju_collector.discovery")

SEARCH_API_URL = "https://platform.tgju.org/fa/tvdata/search"
NEWSEARCH_API_URL = "https://api.tgju.org/v1/newsearch"

# Queries used to expand coverage beyond section-page tables.
DEFAULT_SEARCH_QUERIES: tuple[str, ...] = (
    "price_",
    "gold_",
    "geram",
    "mesghal",
    "sekee",
    "crypto-",
    "oil_",
    "silver",
    "nima",
    "sana",
    "commodities",
    "ons",
    "platinum",
    "palladium",
)


class SupportsHttpGet(Protocol):
    """Minimal HTTP surface required by the catalog builder."""

    def get_text(self, url: str, *, params: dict[str, Any] | None = None) -> str: ...

    def get_json(self, url: str, *, params: dict[str, Any] | None = None) -> Any: ...


class CatalogBuilder:
    """Assemble symbols from HTML section pages and search APIs.

    Args:
        client: Object implementing ``get_text`` / ``get_json``.
        section_pages: Mapping of page name → URL. Defaults to known pages.
        search_queries: Queries passed to the symbol search API.
    """

    def __init__(
        self,
        client: SupportsHttpGet,
        *,
        section_pages: dict[str, str] | None = None,
        search_queries: tuple[str, ...] = DEFAULT_SEARCH_QUERIES,
    ) -> None:
        self.client = client
        self.section_pages = dict(section_pages or SECTION_PAGE_URLS)
        self.search_queries = search_queries

    def build(self) -> list[Symbol]:
        """Build the combined catalog.

        Returns:
            list[Symbol]: Deduplicated symbols with product sections assigned.
        """
        merged: dict[str, Symbol] = {}

        for page_name, url in self.section_pages.items():
            try:
                html_text = self.client.get_text(url)
            except Exception as exc:
                logger.warning("Failed to fetch section page %s (%s): %s", page_name, url, exc)
                continue
            for row in parse_market_rows(html_text):
                symbol_id = row["symbol"]
                label = row["label"]
                existing = merged.get(symbol_id)
                if existing is None:
                    merged[symbol_id] = Symbol(
                        symbol=symbol_id,
                        label_fa=label,
                        product_section=classify_symbol(symbol_id, labels=[label]),
                        source=SymbolSource.HTML,
                        meta={"pages": [page_name]},
                    )
                else:
                    pages = existing.meta.get("pages", [])
                    if page_name not in pages:
                        pages.append(page_name)
                    label_fa = existing.label_fa or label
                    merged[symbol_id] = Symbol(
                        symbol=existing.symbol,
                        label_fa=label_fa,
                        label_en=existing.label_en,
                        product_section=existing.product_section,
                        source=SymbolSource.BOTH
                        if existing.source != SymbolSource.HTML
                        else SymbolSource.HTML,
                        meta={**existing.meta, "pages": pages},
                    )

        for query in self.search_queries:
            try:
                payload = self.client.get_json(
                    SEARCH_API_URL,
                    params={"query": query, "exchange": "", "type": ""},
                )
            except Exception as exc:
                logger.warning("Search query %r failed: %s", query, exc)
                continue
            for item in payload if isinstance(payload, list) else []:
                if not isinstance(item, dict):
                    continue
                symbol_id = str(item.get("symbol") or "").strip()
                if not symbol_id:
                    continue
                description = str(item.get("description") or "").strip()
                api_type = str(item.get("type") or "").strip()
                existing = merged.get(symbol_id)
                section = classify_symbol(
                    symbol_id,
                    labels=[description],
                    api_type=api_type or None,
                )
                if existing is None:
                    merged[symbol_id] = Symbol(
                        symbol=symbol_id,
                        label_fa=description,
                        label_en=str(item.get("full_name") or ""),
                        product_section=section,
                        source=SymbolSource.API,
                        meta={"api_type": api_type},
                    )
                else:
                    label_fa = existing.label_fa or description
                    source = (
                        SymbolSource.BOTH
                        if existing.source == SymbolSource.HTML
                        else existing.source
                    )
                    merged[symbol_id] = Symbol(
                        symbol=existing.symbol,
                        label_fa=label_fa,
                        label_en=existing.label_en or str(item.get("full_name") or ""),
                        product_section=existing.product_section
                        if existing.product_section != ProductSection.OTHER
                        else section,
                        source=source,
                        meta={**existing.meta, "api_type": api_type},
                    )

        catalog = sorted(merged.values(), key=lambda s: (s.product_section.value, s.symbol))
        logger.info("Catalog built with %s symbols", len(catalog))
        return catalog
