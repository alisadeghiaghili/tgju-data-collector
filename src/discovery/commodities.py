# -*- coding: utf-8 -*-
"""Symbol discovery from TGJU commodities and base metals pages."""

from typing import List

from .base import BaseDiscovery, Symbol


class CommoditiesDiscovery(BaseDiscovery):
    """Discover symbols from the TGJU commodities page."""

    url = 'https://www.tgju.org/commodities'
    source_name = 'commodities'
    category = 'commodity'

    def _parse(self, response) -> List[Symbol]:
        xpath_mappings = {
            'name_fa': '//table[contains(@class,"market-table")]/tbody/tr/th/span/following-sibling::text()',
            'href': '//table[contains(@class,"market-table")]/tbody/tr/@onclick'
        }

        extracted = self._extract_xpaths(response, xpath_mappings)

        if not extracted.get('name_fa') or not extracted.get('href'):
            return []

        symbols = []
        seen = set()

        for name_fa, href in zip(extracted['name_fa'], extracted['href']):
            name_fa = name_fa.strip()
            if not name_fa or name_fa in seen:
                continue

            code = href.split('/')[-1].rstrip(')')
            seen.add(name_fa)

            symbols.append(Symbol(
                code=code,
                name_fa=name_fa,
                name_en=code,
                source_page=self.source_name,
                category=self.category
            ))

        return symbols


class BaseMetalDiscovery(BaseDiscovery):
    """Discover symbols from the TGJU base metals page."""

    url = 'https://www.tgju.org/basemetal'
    source_name = 'basemetal'
    category = 'metal'

    def _parse(self, response) -> List[Symbol]:
        xpath_mappings = {
            'name_fa': '//table[contains(@class,"market-table")]/tbody/tr/th/span/following-sibling::text()',
            'href': '//table[contains(@class,"market-table")]/tbody/tr/@onclick'
        }

        extracted = self._extract_xpaths(response, xpath_mappings)

        if not extracted.get('name_fa') or not extracted.get('href'):
            return []

        symbols = []
        seen = set()

        for name_fa, href in zip(extracted['name_fa'], extracted['href']):
            name_fa = name_fa.strip()
            if not name_fa or name_fa in seen:
                continue

            code = href.split('/')[-1].rstrip(')')
            seen.add(name_fa)

            symbols.append(Symbol(
                code=code,
                name_fa=name_fa,
                name_en=code,
                source_page=self.source_name,
                category=self.category
            ))

        return symbols
