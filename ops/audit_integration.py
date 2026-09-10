# -*- coding: utf-8 -*-
"""Integration audit: does the pipeline stay consistent across the full catalog?

Not a unit test — a one-off ops check against the live site + local DB.
"""

from __future__ import annotations

import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, "src")

from sqlalchemy import create_engine, select

from tgju_collector.calendar.trading import MarketCalendar
from tgju_collector.clients.history import HistoryClient
from tgju_collector.discovery.catalog import CatalogBuilder
from tgju_collector.http import HttpClient
from tgju_collector.quality.checks import check_price_bars, check_symbol_coverage
from tgju_collector.sections import classify_symbol
from tgju_collector.storage import create_all, schema
from tgju_collector.storage.repository import Repository

DB = "sqlite:///audit_test.db"


def main() -> int:
    engine = create_engine(DB, future=True)
    create_all(engine)
    repo = Repository(engine)

    print("=== 1. Full catalog (polite) ===")
    with HttpClient(timeout=30, max_retries=2, delay_min=1.2, delay_max=2.0) as http:
        catalog = CatalogBuilder(http, search_pause_sec=1.0).build()
        print(f"catalog size: {len(catalog)}")
        sections = Counter(str(s.product_section) for s in catalog)
        for sec, n in sections.most_common():
            print(f"  {sec:12s} {n}")

        # Re-classify check: any symbol whose stored section differs from
        # a fresh classify_symbol() call?
        mismatched = [
            s
            for s in catalog
            if classify_symbol(s.symbol, labels=[s.label_fa]) != s.product_section
            and s.product_section.value == "other"
        ]
        print(f"still OTHER after classify with labels: {len(mismatched)}")
        for s in mismatched[:10]:
            print(f"  {s.symbol!r} label={s.label_fa!r}")

        repo.upsert_symbols(catalog)

        print("\n=== 2. History sample across every section ===")
        client = HistoryClient(http)
        end = date.today()
        start = end - timedelta(days=14)
        by_section: dict[str, list[str]] = {}
        for s in catalog:
            by_section.setdefault(str(s.product_section), []).append(s.symbol)

        ok = 0
        empty = 0
        fail = 0
        section_stats: dict[str, dict[str, int]] = {}
        for section, symbols in by_section.items():
            sample = symbols[:3]
            stats = {"ok": 0, "empty": 0, "fail": 0}
            for symbol in sample:
                try:
                    bars = client.fetch_daily(symbol, start=start, end=end)
                except Exception as exc:
                    print(f"  FAIL {section:12s} {symbol}: {exc}")
                    stats["fail"] += 1
                    fail += 1
                    continue
                if bars:
                    repo.upsert_price_bars(bars)
                    stats["ok"] += 1
                    ok += 1
                    print(
                        f"  OK   {section:12s} {symbol:30s} "
                        f"{len(bars):3d} bars last={bars[-1].trade_date} close={bars[-1].close}"
                    )
                else:
                    stats["empty"] += 1
                    empty += 1
                    print(f"  EMPTY {section:12s} {symbol}")
            section_stats[section] = stats

        print(f"\nhistory sample totals: ok={ok} empty={empty} fail={fail}")

        print("\n=== 3. Trading calendar vs stored dates ===")
        cal = MarketCalendar()
        stored = set()
        with engine.connect() as conn:
            for row in conn.execute(select(schema.price_bars.c.trade_date)).all():
                stored.add(row[0])
        bad = []
        for iso in stored:
            d = date.fromisoformat(iso)
            if not cal.is_trading_day(d):
                bad.append(iso)
        print(f"stored dates that are non-trading (Fri/holiday): {len(bad)}")
        if bad:
            print("  sample:", sorted(bad)[:10])

        print("\n=== 4. Quality report ===")
        with engine.connect() as conn:
            bar_rows = [dict(r._mapping) for r in conn.execute(select(schema.price_bars)).all()]
            stored_syms = {r["symbol"] for r in bar_rows}
            cat_syms = {r[0] for r in conn.execute(select(schema.symbols.c.symbol)).all()}
        price = check_price_bars(bar_rows)
        coverage = check_symbol_coverage(cat_syms, stored_syms)
        print("price:", price)
        print("coverage catalog/stored/missing:", coverage["catalog_size"], coverage["stored_size"], coverage["missing_from_store"])

        print("\n=== 5. Case consistency ===")
        upper = [s for s in stored_syms if s != s.lower()]
        print(f"stored symbols not lowercase: {len(upper)} {upper[:5]}")

    Path("audit_test.db").unlink(missing_ok=True)
    print("\nAUDIT DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
