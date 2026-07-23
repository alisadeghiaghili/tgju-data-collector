# -*- coding: utf-8 -*-
"""Abstract base class for symbol discovery from TGJU pages."""

from dataclasses import dataclass
from typing import List

from bs4 import BeautifulSoup
from lxml import etree

from ..http_client import HttpClient


@dataclass
class Symbol:
    """Discovered symbol from TGJU."""
    code: str          # English symbol code (e.g., 'price_dollar_rl')
    name_fa: str       # Persian name
    name_en: str       # English name (same as code for most)
    source_page: str   # Source page identifier
    category: str      # Category (gold, currency, crypto, etc.)


class BaseDiscovery:
    """Abstract base for symbol discovery from a TGJU page."""

    url: str = ''
    source_name: str = ''
    category: str = ''

    def __init__(self, http_client: HttpClient):
        self.http = http_client

    def discover(self) -> List[Symbol]:
        """Fetch page, parse DOM, extract symbols."""
        response = self.http.get(self.url)
        if response is None:
            return []
        symbols = self._parse(response)
        return symbols

    def _parse(self, response) -> List[Symbol]:
        raise NotImplementedError

    def _extract_xpaths(self, response, xpath_queries: dict) -> dict:
        """Parse HTML and extract data using XPath expressions."""
        try:
            soup = BeautifulSoup(response.content, "html.parser")
            dom = etree.HTML(str(soup))

            extracted = {}
            for key, xpath_expr in xpath_queries.items():
                extracted[key] = dom.xpath(xpath_expr)
            return extracted
        except Exception as e:
            return {}
