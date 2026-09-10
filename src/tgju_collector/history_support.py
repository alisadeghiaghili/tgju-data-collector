# -*- coding: utf-8 -*-
"""History-capability heuristics for catalog symbols.

Not every ``data-market-row`` id is a platform.tgju.org chart symbol.
Numeric table row ids and some retail HTML ids have live quotes but no
OHLCV history. History sync and backfill should skip those.

Examples:
    >>> is_history_capable("sekee")
    True
    >>> is_history_capable("131398")
    False
"""

from __future__ import annotations

import re
from typing import Any, Mapping

_NUMERIC_ID = re.compile(r"^\d+$")

# Prefixes / fragments that reliably resolve on the history API.
_HISTORY_HINTS = (
    "price_",
    "gold_",
    "geram",
    "mesghal",
    "sekee",
    "sekeb",
    "nim",
    "rob",
    "gerami",
    "crypto-",
    "crypto_",
    "oil_",
    "energy_",
    "silver",
    "platinum",
    "palladium",
    "ons",
    "nima_",
    "sana_",
    "commodit",
    "basemetal",
    "aluminium",
    "aluminum",
    "copper",
    "ime_fund",
    "retail_",
    "coin_",
    "blubber",
)


def is_history_capable(
    symbol: str,
    *,
    meta: Mapping[str, Any] | None = None,
    api_type: str | None = None,
) -> bool:
    """Return True when a symbol is expected to have OHLCV history.

    Args:
        symbol: Market symbol id.
        meta: Optional symbol metadata dict (may contain ``api_type``).
        api_type: Optional search-API type field.

    Returns:
        bool: True if history sync is worth attempting.

    Examples:
        >>> is_history_capable("price_dollar_rl")
        True
        >>> is_history_capable("999999")
        False
    """
    if not symbol:
        return False

    lowered = symbol.lower().strip()

    if _NUMERIC_ID.match(lowered):
        return False

    type_value = api_type
    if type_value is None and meta:
        type_value = meta.get("api_type") or None
    if type_value:
        # Search API already knows this symbol.
        return True

    if any(hint in lowered for hint in _HISTORY_HINTS):
        return True

    # Hyphenated / underscored alphanumeric ids from platform are usually real.
    if "-" in lowered or "_" in lowered:
        return not lowered.replace("-", "").replace("_", "").isdigit()

    return False


def filter_history_capable(symbols: list) -> list:
    """Filter a list of Symbol objects (or mappings with symbol/meta).

    Args:
        symbols: Sequence of ``Symbol`` or dicts with ``symbol`` / ``meta``.

    Returns:
        list: Only history-capable entries, original order preserved.
    """
    kept = []
    for item in symbols:
        if hasattr(item, "symbol"):
            symbol = item.symbol
            meta = getattr(item, "meta", {}) or {}
        else:
            symbol = item.get("symbol") or ""
            meta = item.get("meta") or {}
        if is_history_capable(symbol, meta=meta if isinstance(meta, Mapping) else {}):
            kept.append(item)
    return kept
