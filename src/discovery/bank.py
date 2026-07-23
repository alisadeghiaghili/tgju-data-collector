# -*- coding: utf-8 -*-
"""Symbol discovery from TGJU bank rates page."""

from typing import List

from .base import BaseDiscovery, Symbol


class BankDiscovery(BaseDiscovery):
    """Discover symbols from the TGJU bank rates page."""

    url = 'https://www.tgju.org/bank'
    source_name = 'bank'
    category = 'currency'

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
