# -*- coding: utf-8 -*-
"""Tests for catalog builder with a fake HTTP client."""

from __future__ import annotations

from tgju_collector.discovery.catalog import CatalogBuilder
from tgju_collector.models import ProductSection, SymbolSource


class FakeClient:
    def __init__(self, html_pages: dict[str, str], search_results: dict[str, list]) -> None:
        self.html_pages = html_pages
        self.search_results = search_results

    def get_text(self, url: str, *, params: dict | None = None) -> str:
        return self.html_pages[url]

    def get_json(self, url: str, *, params: dict | None = None):
        query = (params or {}).get("query", "")
        return self.search_results.get(query, [])


def test_catalog_merges_html_and_api(sample_home_html: str) -> None:
    client = FakeClient(
        html_pages={"https://www.tgju.org/": sample_home_html},
        search_results={
            "price_": [
                {
                    "symbol": "price_euro_rl",
                    "full_name": "price_euro_rl",
                    "description": "یورو",
                    "type": "ارز",
                }
            ],
            "gold_": [],
            "geram": [],
            "mesghal": [],
            "sekee": [
                {
                    "symbol": "sekee",
                    "full_name": "sekee",
                    "description": "سکه امامی",
                    "type": "طلا و سکه",
                }
            ],
            "crypto-": [],
            "oil_": [],
            "silver": [],
            "nima": [],
            "sana": [],
            "commodities": [],
            "ons": [],
            "platinum": [],
            "palladium": [],
        },
    )
    builder = CatalogBuilder(
        client,
        section_pages={"home": "https://www.tgju.org/"},
    )
    catalog = builder.build()
    symbols = {s.symbol: s for s in catalog}

    assert "sekee" in symbols
    assert "price_dollar_rl" in symbols
    assert "price_euro_rl" in symbols
    assert symbols["sekee"].source is SymbolSource.BOTH
    assert symbols["sekee"].product_section is ProductSection.GOLD_COIN
    assert symbols["price_euro_rl"].product_section is ProductSection.CURRENCY
    assert symbols["crypto-bitcoin"].product_section is ProductSection.CRYPTO


def test_catalog_handles_page_failure(sample_home_html: str) -> None:
    client = FakeClient(
        html_pages={"https://www.tgju.org/": sample_home_html},
        search_results={},
    )
    builder = CatalogBuilder(
        client,
        section_pages={
            "home": "https://www.tgju.org/",
            "missing": "https://www.tgju.org/does-not-exist",
        },
        search_queries=(),
    )
    catalog = builder.build()
    assert len(catalog) == 4
