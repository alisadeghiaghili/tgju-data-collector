# -*- coding: utf-8 -*-
"""Deep-probe TGJU JSON APIs that returned 200."""

from __future__ import annotations

import json
from pathlib import Path

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fa,en;q=0.9",
    "Referer": "https://www.tgju.org/",
}


def probe(url: str, params: dict | None = None) -> dict:
    print(f"\n{'='*70}\nGET {url}  params={params}")
    resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
    print(f"status={resp.status_code} content-type={resp.headers.get('content-type')}")
    try:
        data = resp.json()
    except Exception:
        print("not json:", resp.text[:300])
        return {}
    return data


def summarize(label: str, data, out_dir: Path) -> None:
    path = out_dir / f"{label}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved -> {path}")

    if isinstance(data, list):
        print(f"  list len={len(data)}")
        if data:
            print(f"  sample[0] keys={list(data[0]) if isinstance(data[0], dict) else data[0]}")
            print(f"  sample[0]={json.dumps(data[0], ensure_ascii=False)[:400]}")
            if len(data) > 1:
                print(f"  sample[1]={json.dumps(data[1], ensure_ascii=False)[:400]}")
    elif isinstance(data, dict):
        print(f"  dict keys={list(data)}")
        for k, v in list(data.items())[:8]:
            preview = json.dumps(v, ensure_ascii=False)[:300] if not isinstance(v, str) else v[:300]
            print(f"  {k}: {type(v).__name__} -> {preview}")


def main() -> None:
    out = Path("scripts/api_samples")
    out.mkdir(parents=True, exist_ok=True)

    # 1. categories
    cats = probe("https://api.tgju.org/v1/market/categories")
    summarize("market_categories", cats, out)

    # 2. news
    news = probe("https://api.tgju.org/v1/news/list", {"count": "5"})
    summarize("news_list", news, out)

    # 3. platform symbols (maybe huge — sample)
    print(f"\n{'='*70}\nGET platform symbols (may be large)")
    resp = requests.get(
        "https://platform.tgju.org/fa/tvdata/symbols",
        headers=HEADERS,
        timeout=30,
    )
    print(f"status={resp.status_code} bytes={len(resp.content)}")
    try:
        syms = resp.json()
        print(f"type={type(syms).__name__}")
        if isinstance(syms, list):
            print(f"len={len(syms)}")
            (out / "tvdata_symbols_sample.json").write_text(
                json.dumps(syms[:20], ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"saved first 20 of {len(syms)}")
            print("sample:", json.dumps(syms[0], ensure_ascii=False)[:400])
            # unique types
            types = sorted({s.get("type", "?") for s in syms if isinstance(s, dict)})
            print("types:", types)
            # unique exchange
            exchanges = sorted({s.get("exchange", "?") for s in syms if isinstance(s, dict)})
            print("exchanges:", exchanges[:40])
        else:
            summarize("tvdata_symbols", syms, out)
    except Exception as exc:
        print("symbols parse fail:", exc)

    # 4. search with query
    for q in ["gold", "dollar", "bitcoin", "sekee", "oil"]:
        data = probe("https://platform.tgju.org/fa/tvdata/search", {"query": q, "exchange": "", "type": ""})
        summarize(f"search_{q}", data, out)

    # 5. newsearch modules discovered earlier
    for batch in [
        "exchange_crypto_internal",
        "exchange_currency_internal",
        "exchange_global",
        "global_base_metals",
        "global_bonds",
        "global_commodity",
        "crypto",
    ]:
        module = "markets.global" if batch.startswith("global") or batch == "crypto" else "exchange"
        if batch == "crypto":
            module = "markets.global"
        data = probe(
            "https://api.tgju.org/v1/newsearch",
            {"module": module, "batch": batch},
        )
        summarize(f"newsearch_{batch}", data, out)

    # 6. probe call.tgju.org (live prices)
    for url in [
        "https://call.tgju.org/v1/market/data",
        "https://call.tgju.org/v1/page/index",
        "https://call.tgju.org/",
    ]:
        try:
            data = probe(url)
            if data:
                summarize(f"call_{url.rstrip('/').split('/')[-1]}", data, out)
        except Exception as exc:
            print(f"call fail {url}: {exc}")

    # 7. common page APIs used by TGJU frontend
    for url in [
        "https://api.tgju.org/v1/page/index/market",
        "https://api.tgju.org/v1/market/index",
        "https://api.tgju.org/v1/market/index/latest",
        "https://api.tgju.org/v1/market/index/overview",
        "https://api.tgju.org/v1/page/index",
        "https://api.tgju.org/v1/market/data/latest",
        "https://api.tgju.org/v1/market/latest/all",
        "https://api.tgju.org/v1/page/market/latest",
        "https://api.tgju.org/v1/market/last/data",
        "https://api.tgju.org/v1/market/get",
        "https://api.tgju.org/v1/market/price/latest",
        "https://api.tgju.org/v1/page/crypto",
        "https://api.tgju.org/v1/page/global-market",
        "https://api.tgju.org/v1/page/energy",
        "https://api.tgju.org/v1/page/gold",
        "https://api.tgju.org/v1/page/currency",
        "https://api.tgju.org/v1/page/coin",
        "https://api.tgju.org/v1/page/stock",
        "https://api.tgju.org/v1/page/fund",
        "https://api.tgju.org/v1/page/bond",
        "https://api.tgju.org/v1/page/index-indicators",
        "https://api.tgju.org/v1/page/economics",
    ]:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            ctype = resp.headers.get("content-type", "")
            is_json = "json" in ctype or (resp.text[:1] in "{[" and resp.status_code == 200)
            print(f"  {resp.status_code} {'JSON' if is_json else 'html':4s} {url}")
            if resp.status_code == 200 and is_json:
                data = resp.json()
                (out / f"page_{url.rstrip('/').split('/')[-1].replace('?','_')}.json").write_text(
                    json.dumps(data, ensure_ascii=False)[:50000], encoding="utf-8"
                )
                keys = list(data)[:15] if isinstance(data, dict) else f"list[{len(data)}]"
                print(f"       keys={keys}")
        except Exception as exc:
            print(f"  ERR {url}: {exc}")


if __name__ == "__main__":
    main()
