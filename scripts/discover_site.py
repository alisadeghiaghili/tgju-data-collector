# -*- coding: utf-8 -*-
"""
Discover TGJU site structure: navigation sections and public API endpoints.

This is a one-shot reconnaissance helper. Not part of the production package.

Usage:
    python scripts/discover_site.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from typing import Any
from urllib.parse import urljoin

import requests
from lxml import html as lxml_html

BASE = "https://www.tgju.org"
API_BASE = "https://api.tgju.org"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "fa,en;q=0.9",
}


def fetch(url: str) -> requests.Response:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp


def discover_nav(root: Any) -> dict[str, list[dict[str, str]]]:
    """Extract header navigation tree: top-level menus and their market links."""
    sections: dict[str, list[dict[str, str]]] = defaultdict(list)

    # Primary header menu items
    for top in root.xpath('//div[@class="nav-links"]//li[contains(@class,"nav-item")]'):
        title_nodes = top.xpath('./a//text() | ./span//text()')
        title = " ".join(t.strip() for t in title_nodes if t.strip())
        if not title:
            continue
        for a in top.xpath('.//a[@href]'):
            href = a.get("href") or ""
            if not href or href.startswith("#") or href.startswith("javascript"):
                continue
            text = " ".join(t.strip() for t in a.xpath('.//text()') if t.strip())
            if not text:
                continue
            full = urljoin(BASE, href)
            if "tgju.org" not in full:
                continue
            sections[title].append({"text": text, "url": full})

    # Also grab data-name attributes used by the site
    for a in root.xpath('//a[@data-name]'):
        name = a.get("data-name")
        href = a.get("href") or ""
        text = " ".join(t.strip() for t in a.xpath('.//text()') if t.strip())
        if name and href:
            sections["__data_name__"].append(
                {"data_name": name, "text": text, "url": urljoin(BASE, href)}
            )

    # Market table rows on homepage (live prices)
    for tr in root.xpath('//table[contains(@class,"market-table")]//tr[@data-market-row]'):
        row_id = tr.get("data-market-row")
        onclick = tr.get("onclick") or ""
        name_nodes = tr.xpath('.//th//text() | .//td[1]//text()')
        name = " ".join(t.strip() for t in name_nodes if t.strip())
        sections["__market_rows__"].append(
            {"id": row_id or "", "name": name, "onclick": onclick}
        )

    return sections


def discover_api_candidates() -> list[str]:
    """Probe known TGJU API path patterns."""
    candidates = [
        f"{API_BASE}/v1/market/data",
        f"{API_BASE}/v1/market/last",
        f"{API_BASE}/v1/market/info",
        f"{API_BASE}/v1/market/overview",
        f"{API_BASE}/v1/market/latest",
        f"{API_BASE}/v1/market/pulse",
        f"{API_BASE}/v1/page/index",
        f"{API_BASE}/v1/page/home",
        f"{API_BASE}/v1/page/market",
        f"{API_BASE}/v1/page/crypto",
        f"{API_BASE}/v1/page/global",
        f"{API_BASE}/v1/page/energy",
        f"{API_BASE}/v1/page/gold",
        f"{API_BASE}/v1/page/currency",
        f"{API_BASE}/v1/page/coin",
        f"{API_BASE}/v1/chart/price-history",
        f"{API_BASE}/v1/chart/history",
        f"{API_BASE}/v1/search",
        f"{API_BASE}/v1/symbol",
        f"{API_BASE}/v1/symbols",
        f"{API_BASE}/v1/market/categories",
        f"{API_BASE}/v1/market/category/gold",
        f"{API_BASE}/v1/market/category/currency",
        f"{API_BASE}/v1/market/category/crypto",
        f"{API_BASE}/v1/market/category/energy",
        f"{API_BASE}/v1/market/category/coin",
        f"{API_BASE}/v1/market/category/metal",
        f"{API_BASE}/v1/market/category/stock",
        f"{API_BASE}/v1/market/category/fund",
        f"{API_BASE}/v1/market/category/bond",
        f"{API_BASE}/v1/market/category/index",
        f"{API_BASE}/v1/market/list",
        f"{API_BASE}/v1/market/tables",
        f"{API_BASE}/v1/market/quotes",
        f"{API_BASE}/v1/market/price",
        f"{API_BASE}/v1/market/prices",
        f"{API_BASE}/v1/market/live",
        f"{API_BASE}/v1/market/summary",
        f"{API_BASE}/v1/market/widgets",
        f"{API_BASE}/v1/market/box",
        f"{API_BASE}/v1/market/header",
        f"{API_BASE}/v1/news/list",
        f"{API_BASE}/v1/news/latest",
        f"{API_BASE}/v1/calendar",
        f"{API_BASE}/v1/calendar/events",
        "https://platform.tgju.org/fa/tvdata/history",
        "https://platform.tgju.org/fa/tvdata/symbols",
        "https://platform.tgju.org/fa/tvdata/search",
    ]
    return candidates


def main() -> int:
    print("=" * 70)
    print("TGJU Site Discovery")
    print("=" * 70)

    print("\n[1] Fetching homepage...")
    try:
        home = fetch(BASE)
        root = lxml_html.fromstring(home.content)
    except Exception as exc:
        print(f"  FAILED: {exc}", file=sys.stderr)
        return 1

    sections = discover_nav(root)

    print("\n[2] Navigation sections:")
    for title, items in sections.items():
        if title.startswith("__"):
            continue
        uniq = {i["url"]: i["text"] for i in items}
        print(f"\n  ## {title} ({len(uniq)} links)")
        for url, text in sorted(uniq.items(), key=lambda x: x[1]):
            print(f"     - {text}: {url}")

    print("\n[3] data-name market anchors:")
    seen = set()
    for item in sections.get("__data_name__", []):
        key = item["data_name"]
        if key in seen:
            continue
        seen.add(key)
        print(f"     {key:40s}  {item['text'][:40]:40s}  {item['url']}")

    print(f"\n[4] Homepage market rows: {len(sections.get('__market_rows__', []))}")
    for item in sections.get("__market_rows__", [])[:40]:
        print(f"     {item['id']:40s}  {item['name'][:50]}")

    # Extract JS config / API base hints
    print("\n[5] Inline JS API hints:")
    text = home.text or ""
    for pattern in [
        r'https://api\.tgju\.org[^"\'\s]*',
        r'https://platform\.tgju\.org[^"\'\s]*',
        r'https://call\.tgju\.org[^"\'\s]*',
        r'["\'](/v1/[^"\']+)["\']',
    ]:
        hits = sorted(set(re.findall(pattern, text)))
        for h in hits[:30]:
            print(f"     {h}")

    print("\n[6] Probing API endpoints...")
    api_hits: list[dict[str, Any]] = []
    for url in discover_api_candidates():
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            ctype = resp.headers.get("content-type", "")
            snippet = resp.text[:120].replace("\n", " ")
            status = resp.status_code
            is_json = "json" in ctype or resp.text.strip()[:1] in "{["
            marker = "JSON" if is_json else ctype[:30]
            print(f"     {status} {marker:8s} {url}")
            if status == 200 and is_json:
                try:
                    data = resp.json()
                    api_hits.append({"url": url, "keys": list(data)[:20] if isinstance(data, dict) else type(data).__name__})
                except Exception:
                    pass
            elif status == 200:
                print(f"            snippet: {snippet}")
        except Exception as exc:
            print(f"     ERR {url}: {exc}")

    print("\n[7] Successful JSON endpoints:")
    for hit in api_hits:
        print(f"     {hit['url']}")
        print(f"       keys/type: {hit['keys']}")

    out_path = "scripts/discover_output.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "sections": {k: v for k, v in sections.items()},
                "api_hits": api_hits,
            },
            fh,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\nSaved raw output to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
