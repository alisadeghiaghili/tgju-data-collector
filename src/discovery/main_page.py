# -*- coding: utf-8 -*-
"""Symbol discovery from TGJU main page navigation menu."""

from typing import List

from .base import BaseDiscovery, Symbol


class MainPageDiscovery(BaseDiscovery):
    """Discover symbols from the main TGJU navigation menu."""

    url = 'https://www.tgju.org'
    source_name = 'main'
    category = 'mixed'

    def _parse(self, response) -> List[Symbol]:
        xpath_mappings = {
            'href': '//div[@class = "nav-links"]/div[2]/ul/li/div/div/ul/li/ul/li/a/@href',
            'name_fa': '//div[@class = "nav-links"]/div[2]/ul/li/div/div/ul/li/ul/li/a//text()'
        }

        extracted = self._extract_xpaths(response, xpath_mappings)

        if not extracted.get('href') or not extracted.get('name_fa'):
            return []

        symbols = []
        seen_fa = set()

        for href, name_fa in zip(extracted['href'], extracted['name_fa']):
            name_fa = name_fa.strip()
            if not name_fa or name_fa in seen_fa:
                continue

            # Validate URL structure: must have exactly one 'profile' segment
            if href.count('profile') != 1:
                continue

            # Extract English code from URL
            code = href.split('/')[-1]

            # Special case for second-hand gold
            if name_fa == 'طلای دست دوم':
                code = 'gold_mini_size'

            seen_fa.add(name_fa)
            symbols.append(Symbol(
                code=code,
                name_fa=name_fa,
                name_en=code,
                source_page=self.source_name,
                category=self._categorize(code)
            ))

        return symbols

    def _categorize(self, code: str) -> str:
        """Infer category from symbol code."""
        if any(x in code for x in ['gold', 'ons', 'mesghal', 'silver', 'platinum', 'palladium']):
            return 'gold'
        if any(x in code for x in ['seke', 'coin', 'nim', 'rob', 'gerami', 'blubber']):
            return 'coin'
        if any(x in code for x in ['price_', 'dollar', 'eur', 'gbp', 'aed', 'chf', 'cny']):
            return 'currency'
        if 'crypto' in code:
            return 'crypto'
        if any(x in code for x in ['energy', 'oil', 'brent']):
            return 'energy'
        if any(x in code for x in ['commodities', 'wheat', 'corn', 'cotton']):
            return 'commodity'
        if any(x in code for x in ['basemetal', 'copper', 'aluminum', 'zinc']):
            return 'metal'
        if any(x in code for x in ['gc', 'go', 'ime_fund']):
            return 'fund'
        return 'other'
