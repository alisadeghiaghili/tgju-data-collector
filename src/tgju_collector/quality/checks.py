# -*- coding: utf-8 -*-
"""Data quality checks for stored market data.

Checks are pure functions over rows / DataFrames so they can run in CI or
as a CLI subcommand without network access.

Examples:
    >>> rows = [{"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "symbol": "x"}]
    >>> report = check_price_bars(rows)
    >>> report["ohlc_violations"]
    0
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping, Sequence


def check_price_bars(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate OHLC consistency and null rates on price bar rows.

    Args:
        rows: Mapping rows with open/high/low/close/symbol/trade_date keys.

    Returns:
        dict[str, Any]: Report with counts:
            ``total``, ``ohlc_violations``, ``null_close``,
            ``null_rate_close``, ``duplicate_keys``.
    """
    total = len(rows)
    ohlc_violations = 0
    null_close = 0
    keys: list[tuple[Any, ...]] = []

    for row in rows:
        close = row.get("close")
        if close is None:
            null_close += 1
        try:
            open_ = float(row.get("open"))
            high = float(row.get("high"))
            low = float(row.get("low"))
            close_f = float(close) if close is not None else None
        except (TypeError, ValueError):
            ohlc_violations += 1
            continue
        if close_f is None:
            continue
        if low > high or open_ > high or open_ < low or close_f > high or close_f < low:
            ohlc_violations += 1

        keys.append((row.get("symbol"), row.get("trade_date"), row.get("timeframe") or "1D"))

    key_counts = Counter(keys)
    duplicate_keys = sum(1 for _, count in key_counts.items() if count > 1)

    return {
        "total": total,
        "ohlc_violations": ohlc_violations,
        "null_close": null_close,
        "null_rate_close": (null_close / total) if total else 0.0,
        "duplicate_keys": duplicate_keys,
    }


def check_symbol_coverage(
    catalog: Iterable[str],
    stored: Iterable[str],
    *,
    history_capable: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Compare catalog symbols against symbols present in storage.

    Args:
        catalog: Symbol ids discovered from the live catalog.
        stored: Symbol ids that have at least one stored row.
        history_capable: Optional subset expected to have OHLCV history.
            When provided, ``missing_history_capable`` is the actionable gap.

    Returns:
        dict[str, Any]: Report with ``catalog_size``, ``stored_size``,
        ``missing_from_store`` (count), missing history-capable count,
        and capped sample lists.
    """
    catalog_set = set(catalog)
    stored_set = set(stored)
    missing = sorted(catalog_set - stored_set)

    report: dict[str, Any] = {
        "catalog_size": len(catalog_set),
        "stored_size": len(stored_set),
        "missing_from_store": len(missing),
        "missing_sample": missing[:25],
        "orphans_in_store": len(stored_set - catalog_set),
    }

    if history_capable is not None:
        capable = set(history_capable)
        missing_capable = sorted(capable - stored_set)
        report["history_capable_size"] = len(capable)
        report["missing_history_capable"] = len(missing_capable)
        report["missing_history_capable_sample"] = missing_capable[:25]
    return report


def summarize_quality(price_report: Mapping[str, Any], coverage_report: Mapping[str, Any]) -> list[str]:
    """Build human-readable quality notes for CLI output.

    Args:
        price_report: Output of :func:`check_price_bars`.
        coverage_report: Output of :func:`check_symbol_coverage`.

    Returns:
        list[str]: Short issue strings (empty list means healthy).
    """
    issues: list[str] = []
    if price_report.get("ohlc_violations"):
        issues.append(f"OHLC violations: {price_report['ohlc_violations']}")
    if price_report.get("duplicate_keys"):
        issues.append(f"duplicate price keys: {price_report['duplicate_keys']}")
    null_rate = float(price_report.get("null_rate_close") or 0.0)
    if null_rate > 0.01:
        issues.append(f"null close rate {null_rate:.2%}")
    if coverage_report.get("missing_history_capable"):
        issues.append(
            f"{coverage_report['missing_history_capable']} history-capable symbols "
            f"have no stored bars"
        )
    elif coverage_report.get("missing_from_store") and "missing_history_capable" not in coverage_report:
        issues.append(
            f"{coverage_report['missing_from_store']} catalog symbols have no stored rows"
        )
    return issues
