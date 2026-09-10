# -*- coding: utf-8 -*-
"""Build a full symbol catalog from TGJU section pages + search API."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests
from lxml import html as lxml_html

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "fa,en;q=0.9",
}

SECTION_PAGES = {
    "home": "https://www.tgju.org/",
    "gold_hallmarks": "https://www.tgju.org/gold-hallmarks",
    "melted_gold": "https://www.tgju.org/melted-gold",
    "coin": "https://www.tgju.org/coin",
    "currency": "https://www.tgju.org/currency",
    "crypto": "https://www.tgju.org/crypto",
    "energy": "https://www.tgju.org/energy",
    "global_market": "https://www.tgju.org/global-market",
    "bourse": "https://www.tgju.org/bourse",
    "stock": "https://www.tgju.org/stock",
    "fund": "https://www.tgju.org/fund",
    "bond": "https://www.tgju.org/bond",
    "metal": "https://www.tgju.org/metals",
    "commodity": "https://www.tgju.org/commodity",
    "economics": "https://www.tgju.org/economics",
    "retail": "https://www.tgju.org/retail",
    "sekee": "https://www.tgju.org/sekee",
    "nim": "https://www.tgju.org/nim",
    "rob": "https://www.tgju.org/rob",
    "gerami": "https://www.tgju.org/gerami",
    "world_market": "https://www.tgju.org/world-market",
}

# Common symbol prefixes / queries used by TGJU market-row IDs
SEARCH_QUERIES = [
    "price_", "gold_", "geram", "mesghal", "sekee", "sekeb", "nim", "rob",
    "crypto-", "oil_", "silver", "platinum", "palladium", "ons",
    "ime_", "bourse", "gc", "tedpix", "dollar", "euro", "pound",
    "yen", "yuan", "lira", "dirham", "rial", "nima", "sana",
    "bitcoin", "ethereum", "tether", "bnb", "xrp", "solana",
    "retail_", "coin_", "fund_", "bond_", "index_", "metal",
    "basemetal", "commodities", "energy", "natgas", "gas_",
    "stock", "شاخص", "طلا", "سکه", "دلار", "یورو", "نفت",
]


def fetch(url: str, timeout: int = 25) -> requests.Response | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            return resp
        print(f"  {resp.status_code} {url}")
    except Exception as exc:
        print(f"  ERR {url}: {exc}")
    return None


def extract_market_rows(content: bytes) -> list[dict]:
    if not content or not content.strip():
        return []
    try:
        root = lxml_html.fromstring(content)
    except Exception:
        return []
    rows: list[dict] = []
    for tr in root.xpath('//tr[@data-market-row]'):
        rid = tr.get("data-market-row") or ""
        cells = [" ".join(t.strip() for t in td.xpath(".//text()") if t.strip())
                 for td in tr.xpath("./th|./td")]
        onclick = tr.get("onclick") or ""
        href = ""
        m = re.search(r"['\"]([^'\"]+)['\"]", onclick)
        if m:
            href = m.group(1)
        a = tr.xpath(".//a[@href]")
        if a:
            href = a[0].get("href") or href
        rows.append({
            "id": rid,
            "cells": cells,
            "href": href,
            "text": " | ".join(c for c in cells if c),
        })
    # also profile links
    for a in root.xpath('//a[contains(@href,"/profile/")]'):
        href = a.get("href") or ""
        text = " ".join(t.strip() for t in a.xpath(".//text()") if t.strip())
        m = re.search(r"/profile/([^/?#]+)", href)
        if m:
            rows.append({"id": m.group(1), "cells": [text], "href": href, "text": text})
    return rows


def search_symbols(query: str) -> list[dict]:
    url = "https://platform.tgju.org/fa/tvdata/search"
    try:
        resp = requests.get(
            url,
            params={"query": query, "exchange": "", "type": ""},
            headers={**HEADERS, "Referer": "https://www.tgju.org/"},
            timeout=15,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        if isinstance(data, list):
            return data
    except Exception:
        return []
    return []


def main() -> None:
    out = Path("scripts/api_samples")
    out.mkdir(parents=True, exist_ok=True)

    catalog: dict[str, dict] = {}

    print("=== Section pages ===")
    for name, url in SECTION_PAGES.items():
        resp = fetch(url)
        if not resp:
            continue
        rows = extract_market_rows(resp.content)
        print(f"  {name:15s} rows={len(rows)}")
        for row in rows:
            rid = row["id"]
            if not rid:
                continue
            entry = catalog.setdefault(rid, {
                "symbol": rid,
                "labels": [],
                "sections": [],
                "hrefs": [],
                "source": "html",
            })
            if row["text"] and row["text"] not in entry["labels"]:
                entry["labels"].append(row["text"][:120])
            if name not in entry["sections"]:
                entry["sections"].append(name)
            if row["href"] and row["href"] not in entry["hrefs"]:
                entry["hrefs"].append(row["href"])
        time.sleep(0.4)

    print(f"\nHTML catalog size: {len(catalog)}")

    print("\n=== Search API ===")
    api_hits = 0
    for q in SEARCH_QUERIES:
        results = search_symbols(q)
        if results:
            print(f"  query={q!r:20s} -> {len(results)}")
        for item in results:
            sym = item.get("symbol") or item.get("full_name") or ""
            if not sym:
                continue
            api_hits += 1
            entry = catalog.setdefault(sym, {
                "symbol": sym,
                "labels": [],
                "sections": [],
                "hrefs": [],
                "source": "api",
            })
            entry["source"] = "both" if entry["source"] == "html" else "api"
            desc = item.get("description") or ""
            typ = item.get("type") or ""
            if desc and desc not in entry["labels"]:
                entry["labels"].append(desc)
            if typ and typ not in entry["sections"]:
                entry["sections"].append(typ)
            if item.get("full_name"):
                entry["full_name"] = item["full_name"]
            if item.get("exchange"):
                entry["exchange"] = item["exchange"]
        time.sleep(0.25)

    print(f"API extra hits: {api_hits}")
    print(f"Combined catalog: {len(catalog)}")

    # Classify into product sections
    def classify(sym: str, sections: list[str], labels: list[str]) -> str:
        s = sym.lower()
        joined = " ".join(sections + labels).lower()
        if s.startswith("crypto-") or "ارز دیجیتال" in joined or "crypto" in joined:
            return "crypto"
        if any(k in s for k in ("oil_", "gas", "brent", "energy")) or "انرژی" in joined or "نفت" in joined:
            return "energy"
        if any(k in s for k in ("silver", "platinum", "palladium", "basemetal", "ons", "metal")) or "فلز" in joined:
            return "metal"
        if any(k in s for k in ("gold", "geram", "mesghal", "sekee", "sekeb", "nim", "rob", "coin_", "blubber", "ayar")) or "طلا" in joined or "سکه" in joined:
            return "gold_coin"
        if any(k in s for k in ("price_", "dollar", "euro", "nima", "sana", "dirham", "pound", "yen", "yuan", "lira")) or "ارز" in joined:
            return "currency"
        if any(k in s for k in ("gc", "bourse", "tedpix", "stock", "fund_", "bond", "index_", "ime_", "retail_")) or "بورس" in joined or "شاخص" in joined:
            return "bourse"
        if "کالا" in joined or "commodit" in joined:
            return "commodity"
        if "شاخص‌های اقتصادی" in joined or "economics" in joined:
            return "economics"
        return "other"

    by_section: dict[str, list[str]] = {}
    for sym, entry in catalog.items():
        sec = classify(sym, entry.get("sections", []), entry.get("labels", []))
        entry["product_section"] = sec
        by_section.setdefault(sec, []).append(sym)

    print("\n=== By product section ===")
    for sec, syms in sorted(by_section.items(), key=lambda x: -len(x[1])):
        print(f"  {sec:15s} {len(syms):4d}")
        for s in sorted(syms)[:8]:
            lab = catalog[s]["labels"][:1]
            print(f"      {s:40s} {lab}")

    (out / "symbol_catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nSaved catalog -> {out / 'symbol_catalog.json'}")


if __name__ == "__main__":
    main()
