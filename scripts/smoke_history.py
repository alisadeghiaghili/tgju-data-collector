# -*- coding: utf-8 -*-
"""Direct history API probe for smoke testing."""
from __future__ import annotations

import sys
import time
from datetime import date, timedelta

sys.path.insert(0, "src")

from tgju_collector.clients.history import HistoryClient
from tgju_collector.http import HttpClient

end = date.today()
start = end - timedelta(days=10)

with HttpClient(timeout=15, max_retries=2, delay_min=0.2, delay_max=0.4) as http:
    client = HistoryClient(http)
    for symbol in ("SEKEE", "PRICE_DOLLAR_RL", "OIL_BRENT"):
        t0 = time.time()
        try:
            bars = client.fetch_daily(symbol, start=start, end=end)
            print(f"{symbol}: {len(bars)} bars in {time.time()-t0:.1f}s")
            if bars:
                print(f"  last: {bars[-1].trade_date} close={bars[-1].close}")
        except Exception as exc:
            print(f"{symbol}: FAIL {type(exc).__name__}: {exc}")
