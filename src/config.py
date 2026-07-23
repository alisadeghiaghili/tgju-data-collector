# -*- coding: utf-8 -*-
"""
Unified configuration module for TGJU Data Collector.

Reads from .env file and environment variables.
"""

import os
import logging
from typing import Optional
from urllib.parse import quote_plus

from dotenv import load_dotenv

logger = logging.getLogger('tgju')


def load_config(env_path: str = '.env') -> None:
    """Load configuration from .env file."""
    load_dotenv(env_path)
    logger.debug("Configuration loaded")


def get_connection_string(prefix: str = 'TGJU_DB',
                          connection_string_var: Optional[str] = None) -> str:
    """
    Build SQL Server connection string from environment variables.

    Priority:
        1. Explicit connection_string_var
        2. {prefix}_CONNECTION_STRING
        3. Individual components: {prefix}_SERVER, {prefix}_NAME, etc.
    """
    if connection_string_var:
        return connection_string_var

    conn_str = os.getenv(f'{prefix}_CONNECTION_STRING')
    if conn_str:
        return conn_str

    server = os.getenv(f'{prefix}_SERVER')
    database = os.getenv(f'{prefix}_NAME')
    user = os.getenv(f'{prefix}_USER')
    password = os.getenv(f'{prefix}_PASSWORD')
    driver = os.getenv(f'{prefix}_DRIVER', 'ODBC Driver 17 for SQL Server')
    port = os.getenv(f'{prefix}_PORT', '1433')

    missing = [v for v, val in [
        ('SERVER', server), ('NAME', database),
        ('USER', user), ('PASSWORD', password)
    ] if not val]

    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(f'{prefix}_{m}' for m in missing)}\n"
            f"See .env.example for template."
        )

    user_enc = quote_plus(user)
    pass_enc = quote_plus(password)
    driver_enc = quote_plus(driver)

    return f"mssql+pyodbc://{user_enc}:{pass_enc}@{server}:{port}/{database}?driver={driver_enc}"


def get_table_name(prefix: str = 'TGJU_DB', default: str = 'TgjuAssets') -> str:
    """Get database table name from environment or use default."""
    return os.getenv(f'{prefix}_TABLE_NAME', default)
