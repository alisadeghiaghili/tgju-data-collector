# -*- coding: utf-8 -*-
"""SQL Server connection helpers and documentation.

SQL Server support is optional. Install the extra first:

    pip install -e ".[mssql]"

Connection string examples (see also ``.env.example``):

    # SQL authentication
    mssql+pyodbc://user:pass@host:1433/dbname?driver=ODBC+Driver+17+for+SQL+Server

    # Windows authentication
    mssql+pyodbc://host/dbname?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes

These helpers validate URL shape and surface missing optional drivers with
actionable error messages. They do not open a connection unless asked.

Examples:
    >>> is_mssql_url("mssql+pyodbc://u:p@h/db?driver=ODBC+Driver+17")
    True
    >>> is_mssql_url("sqlite:///local.db")
    False
"""

from __future__ import annotations

from urllib.parse import urlparse

MSSQL_SCHEMES = frozenset({"mssql+pyodbc", "mssql+pytds", "mssql+pymssql"})


def is_mssql_url(database_url: str) -> bool:
    """Return True when the SQLAlchemy URL targets SQL Server.

    Args:
        database_url: SQLAlchemy database URL.

    Returns:
        bool: True for mssql+pyodbc / pytds / pymssql schemes.
    """
    if not database_url:
        return False
    scheme = urlparse(database_url).scheme
    return scheme in MSSQL_SCHEMES


def require_pyodbc() -> None:
    """Ensure the optional ``pyodbc`` dependency is importable.

    Raises:
        ImportError: With install instructions when pyodbc is missing.
    """
    try:
        import pyodbc  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "SQL Server support requires pyodbc.\n"
            "Install with: pip install -e \".[mssql]\"\n"
            "Also ensure an ODBC Driver for SQL Server is installed on the host."
        ) from exc


def engine_kwargs_for_url(database_url: str) -> dict:
    """Return recommended SQLAlchemy engine kwargs for a URL.

    Args:
        database_url: SQLAlchemy database URL.

    Returns:
        dict: Engine kwargs (e.g. ``future=True``, pool pre-ping for MSSQL).
    """
    kwargs: dict = {"future": True}
    if is_mssql_url(database_url):
        kwargs["pool_pre_ping"] = True
        kwargs["fast_executemany"] = True
    return kwargs
