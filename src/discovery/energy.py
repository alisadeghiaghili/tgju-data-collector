# -*- coding: utf-8 -*-
"""Symbol discovery from TGJU energy page."""

from typing import List

from .base import BaseDiscovery, Symbol


class EnergyDiscovery(BaseDiscovery):
    """Discover symbols from the TGJU energy market table."""

    url = 'https://www.tgju.org/energy'
    source_name = 'energy'
    category = 'energy'

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

            # Extract code from onclick attribute (e.g., "location.href='/profile/oil_brent'")
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
