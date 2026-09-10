# -*- coding: utf-8 -*-
"""Export stored tables to CSV or Parquet.

Examples:
    >>> # export_price_bars(engine, "out/bars.csv")  # doctest: +SKIP
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.engine import Engine

from .storage import schema

logger = logging.getLogger("tgju_collector.export")


def _read_rows(engine: Engine, table, *, symbol: str | None = None) -> list[dict]:
    stmt = select(table)
    if symbol and "symbol" in table.c:
        stmt = stmt.where(table.c.symbol == symbol)
    with engine.connect() as conn:
        return [dict(row._mapping) for row in conn.execute(stmt).all()]


def _write_rows(rows: list[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        import csv

        if not rows:
            path.write_text("", encoding="utf-8")
            return path
        fieldnames = list(rows[0].keys())
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path

    if suffix in {".parquet", ".pq"}:
        import pandas as pd

        pd.DataFrame(rows).to_parquet(path, index=False)
        return path

    if suffix == ".json":
        import json

        path.write_text(json.dumps(rows, ensure_ascii=False, default=str, indent=2), encoding="utf-8")
        return path

    raise ValueError(f"Unsupported export format: {suffix} (use .csv, .parquet, or .json)")


def export_price_bars(
    engine: Engine,
    output: str | Path,
    *,
    symbol: str | None = None,
) -> Path:
    """Export ``price_bars`` to CSV/Parquet/JSON.

    Args:
        engine: SQLAlchemy engine.
        output: Destination path ending in ``.csv``, ``.parquet``, or ``.json``.
        symbol: Optional symbol filter (lowercase).

    Returns:
        Path: Written file path.
    """
    rows = _read_rows(engine, schema.price_bars, symbol=symbol)
    path = _write_rows(rows, Path(output))
    logger.info("Exported %s price bars to %s", len(rows), path)
    return path


def export_live_snapshots(
    engine: Engine,
    output: str | Path,
    *,
    symbol: str | None = None,
) -> Path:
    """Export ``live_snapshots`` to CSV/Parquet/JSON.

    Args:
        engine: SQLAlchemy engine.
        output: Destination path.
        symbol: Optional symbol filter.

    Returns:
        Path: Written file path.
    """
    rows = _read_rows(engine, schema.live_snapshots, symbol=symbol)
    path = _write_rows(rows, Path(output))
    logger.info("Exported %s live snapshots to %s", len(rows), path)
    return path


def export_symbols(engine: Engine, output: str | Path, *, section: str | None = None) -> Path:
    """Export the symbol catalog.

    Args:
        engine: SQLAlchemy engine.
        output: Destination path.
        section: Optional product-section filter.

    Returns:
        Path: Written file path.
    """
    stmt = select(schema.symbols)
    if section:
        stmt = stmt.where(schema.symbols.c.product_section == section)
    with engine.connect() as conn:
        rows = [dict(row._mapping) for row in conn.execute(stmt).all()]
    path = _write_rows(rows, Path(output))
    logger.info("Exported %s symbols to %s", len(rows), path)
    return path
