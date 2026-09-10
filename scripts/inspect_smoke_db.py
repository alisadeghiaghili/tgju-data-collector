# -*- coding: utf-8 -*-
"""Inspect smoke_test.db contents."""
import sqlite3
from pathlib import Path

db = Path("smoke_test.db")
if not db.exists():
    print("no db")
    raise SystemExit(1)

conn = sqlite3.connect(str(db), timeout=5)
print("tables:", [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")])
for table in ("symbols", "price_bars", "live_snapshots", "news_items"):
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count}")
    except Exception as exc:
        print(f"{table}: ERR {exc}")

print("\nsection breakdown:")
try:
    for row in conn.execute(
        "SELECT product_section, COUNT(*) FROM symbols GROUP BY product_section ORDER BY 2 DESC"
    ):
        print(f"  {row[0]:12s} {row[1]}")
except Exception as exc:
    print("ERR", exc)

print("\nsample symbols:")
try:
    for row in conn.execute("SELECT symbol, label_fa, product_section FROM symbols LIMIT 8"):
        print(" ", row)
except Exception as exc:
    print("ERR", exc)

print("\nsample prices:")
try:
    for row in conn.execute(
        "SELECT symbol, trade_date, close FROM price_bars ORDER BY trade_date DESC LIMIT 8"
    ):
        print(" ", row)
except Exception as exc:
    print("ERR", exc)
