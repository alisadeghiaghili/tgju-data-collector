# -*- coding: utf-8 -*-
"""
Unified symbol registry — discovers and deduplicates symbols from all TGJU pages.
"""

import logging
from typing import List

from ..http_client import HttpClient
from .base import Symbol
from .main_page import MainPageDiscovery
from .energy import EnergyDiscovery
from .sana import SanaDiscovery
from .bank import BankDiscovery
from .global_market import GlobalMarketDiscovery
from .gold_global import GoldGlobalDiscovery
from .crypto import CryptoDiscovery
from .commodities import CommoditiesDiscovery, BaseMetalDiscovery
from .coin import CoinDiscovery, ParsianCoinDiscovery

logger = logging.getLogger('tgju')

# All discovery classes to run
ALL_DISCOVERERS = [
    MainPageDiscovery,
    EnergyDiscovery,
    SanaDiscovery,
    BankDiscovery,
    GlobalMarketDiscovery,
    GoldGlobalDiscovery,
    CryptoDiscovery,
    CommoditiesDiscovery,
    BaseMetalDiscovery,
    CoinDiscovery,
    ParsianCoinDiscovery,
]


class SymbolRegistry:
    """
    Discovers symbols from all TGJU pages and maintains a deduplicated registry.

    Usage:
        registry = SymbolRegistry(http_client)
        registry.discover_all()
        symbols = registry.get_all()
    """

    def __init__(self, http_client: HttpClient):
        self.http = http_client
        self._symbols: dict[str, Symbol] = {}  # code -> Symbol

    def discover_all(self) -> int:
        """
        Run all discovery classes and aggregate results.

        Returns:
            Total number of unique symbols discovered.
        """
        total = 0
        for discoverer_cls in ALL_DISCOVERERS:
            discoverer = discoverer_cls(self.http)
            try:
                symbols = discoverer.discover()
                new_count = 0
                for sym in symbols:
                    if sym.code not in self._symbols:
                        self._symbols[sym.code] = sym
                        new_count += 1
                logger.info(f"{discoverer.source_name}: found {len(symbols)} symbols ({new_count} new)")
                total += new_count
            except Exception as e:
                logger.error(f"Discovery failed for {discoverer.source_name}: {e}")

        logger.info(f"Total unique symbols discovered: {len(self._symbols)}")
        return len(self._symbols)

    def get_all(self) -> List[Symbol]:
        """Return all discovered symbols."""
        return list(self._symbols.values())

    def get_by_category(self, category: str) -> List[Symbol]:
        """Return symbols filtered by category."""
        return [s for s in self._symbols.values() if s.category == category]

    def get_by_source(self, source: str) -> List[Symbol]:
        """Return symbols filtered by source page."""
        return [s for s in self._symbols.values() if s.source_page == source]

    def to_dataframe(self):
        """Convert registry to a pandas DataFrame."""
        import pandas as pd
        data = [{
            'symbol_Fa': s.name_fa,
            'symbol_En': s.name_en,
            'SYMBOL': s.code.upper(),
            'SourcePage': s.source_page,
            'Category': s.category
        } for s in self._symbols.values()]
        return pd.DataFrame(data)
