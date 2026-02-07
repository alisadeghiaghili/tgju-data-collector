# -*- coding: utf-8 -*-
"""
Secure Configuration Module for TGJU ETL Pipeline.

Provides secure credential management using environment variables.
Compliant with SonarQube security rule python:S2115.

NO credentials should ever be hardcoded in this file.

Usage:
    from config import get_connection_string, get_table_name, load_env_file

    load_env_file()  # Load from .env
    conn_str = get_connection_string(prefix='TGJU_DB')
    table = get_table_name(prefix='TGJU_DB')
"""

import os
import logging
from typing import Optional
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


def load_env_file(env_path: str = '.env') -> None:
    """
    Load environment variables from .env file.

    Simple implementation that doesn't require python-dotenv.
    For production, consider using python-dotenv library.

    Args:
        env_path: Path to .env file (default: '.env')
    """
    if not os.path.exists(env_path):
        logger.debug(f"No {env_path} file found - using system environment variables")
        return

    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse KEY=VALUE
                if '=' not in line:
                    continue

                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]

                # Only set if not already in environment (env vars have priority)
                if key not in os.environ:
                    os.environ[key] = value

        logger.info(f"Loaded environment variables from {env_path}")
    except Exception as e:
        logger.warning(f"Failed to load {env_path}: {e}")


def validate_no_placeholders(value: str, var_name: str) -> None:
    """
    Validate that environment variable doesn't contain placeholder values.

    Args:
        value: Variable value to check
        var_name: Variable name for error message

    Raises:
        ValueError: If placeholder detected
    """
    placeholders = ['your_', 'example', 'placeholder', 'changeme', 'CHANGE_ME']

    if any(ph in value.lower() for ph in placeholders):
        raise ValueError(
            f"⚠️  Environment variable {var_name} contains placeholder value: '{value}'\n"
            f"Please update your .env file with actual credentials.\n"
            f"See .env.example for template."
        )


def get_connection_string(
    prefix: str = 'TGJU_DB',
    connection_string_var: Optional[str] = None
) -> str:
    """
    Build secure SQL Server connection string from environment variables.

    Priority:
        1. Explicit connection_string_var if provided
        2. {prefix}_CONNECTION_STRING environment variable  
        3. Individual components: {prefix}_SERVER, {prefix}_NAME, etc.

    Args:
        prefix: Environment variable prefix (e.g., 'TGJU_DB')
        connection_string_var: Optional pre-built connection string

    Returns:
        SQLAlchemy connection string

    Raises:
        ValueError: If required configuration is missing or contains placeholders

    Environment Variables:
        {PREFIX}_CONNECTION_STRING: Complete connection string (highest priority)
        {PREFIX}_SERVER: Database server hostname
        {PREFIX}_NAME: Database name
        {PREFIX}_USER: Database username
        {PREFIX}_PASSWORD: Database password
        {PREFIX}_DRIVER: ODBC driver (default: 'ODBC Driver 17 for SQL Server')
        {PREFIX}_PORT: Database port (default: 1433)

    Examples:
        >>> os.environ['TGJU_DB_SERVER'] = 'localhost'
        >>> os.environ['TGJU_DB_NAME'] = 'mydb'
        >>> os.environ['TGJU_DB_USER'] = 'sa'
        >>> os.environ['TGJU_DB_PASSWORD'] = 'SecurePass123!'
        >>> conn = get_connection_string()
    """
    # Check for explicit connection string parameter
    if connection_string_var:
        validate_no_placeholders(connection_string_var, 'connection_string')
        logger.debug("Using provided connection string parameter")
        return connection_string_var

    # Check for full connection string in environment
    conn_str_env = os.getenv(f'{prefix}_CONNECTION_STRING')
    if conn_str_env:
        validate_no_placeholders(conn_str_env, f'{prefix}_CONNECTION_STRING')
        logger.debug(f"Using {prefix}_CONNECTION_STRING from environment")
        return conn_str_env

    # Build from individual components
    server = os.getenv(f'{prefix}_SERVER')
    database = os.getenv(f'{prefix}_NAME')
    user = os.getenv(f'{prefix}_USER')
    password = os.getenv(f'{prefix}_PASSWORD')
    driver = os.getenv(f'{prefix}_DRIVER', 'ODBC Driver 17 for SQL Server')
    port = os.getenv(f'{prefix}_PORT', '1433')

    missing = []
    if not server:
        missing.append(f'{prefix}_SERVER')
    if not database:
        missing.append(f'{prefix}_NAME')
    if not user:
        missing.append(f'{prefix}_USER')
    if not password:
        missing.append(f'{prefix}_PASSWORD')

    if missing:
        raise ValueError(
            f"❌ Missing required environment variables: {', '.join(missing)}\n"
            f"\n"
            f"Please set them in .env file or environment.\n"
            f"See .env.example for template.\n"
            f"\n"
            f"Example .env content:\n"
            f"{prefix}_SERVER=localhost\n"
            f"{prefix}_NAME=mydatabase\n"
            f"{prefix}_USER=myuser\n"
            f"{prefix}_PASSWORD=SecurePassword123!\n"
        )

    # Validate no placeholders
    for var_name, value in [
        (f'{prefix}_SERVER', server),
        (f'{prefix}_NAME', database),
        (f'{prefix}_USER', user),
    ]:
        validate_no_placeholders(value, var_name)

    # Warn about empty password (might be intentional for Windows Auth)
    if not password:
        logger.warning(
            f"⚠️  {prefix}_PASSWORD is empty. "
            f"If using Windows Authentication, this is expected. "
            f"Otherwise, please set a password."
        )

    # URL-encode username and password to handle special characters
    user_encoded = quote_plus(user)
    password_encoded = quote_plus(password)
    driver_encoded = quote_plus(driver)

    # Build connection string
    conn_str = (
        f"mssql+pyodbc://{user_encoded}:{password_encoded}"
        f"@{server}:{port}/{database}"
        f"?driver={driver_encoded}"
    )

    logger.debug(f"Built connection string from {prefix}_* environment variables")
    return conn_str


def get_table_name(prefix: str = 'TGJU_DB', default: str = 'TgjuAssets') -> str:
    """
    Get database table name from environment or use default.

    Args:
        prefix: Environment variable prefix
        default: Default table name

    Returns:
        Table name
    """
    return os.getenv(f'{prefix}_TABLE_NAME', default)


def print_config_status() -> None:
    """
    Print configuration status (with passwords masked) for debugging.

    Useful for troubleshooting configuration issues.
    """
    print("\n" + "="*60)
    print("TGJU Configuration Status")
    print("="*60)

    # Check .env file
    env_exists = os.path.exists('.env')
    print(f"\n.env file: {'✓ Found' if env_exists else '✗ Not found'}")

    if not env_exists:
        print("  → Copy .env.example to .env and configure")

    # Check DB config
    print("\nDatabase Configuration:")
    db_vars = ['TGJU_DB_SERVER', 'TGJU_DB_NAME', 'TGJU_DB_USER', 'TGJU_DB_PASSWORD']
    for var in db_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var:
                print(f"  {var}: {'*' * min(len(value), 8)}")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: ✗ Not set")

    # Check table config
    table_name = get_table_name()
    print(f"\nTable Name: {table_name}")

    print("\n" + "="*60 + "\n")


# Auto-load .env file when module is imported
load_env_file()


if __name__ == '__main__':
    # Test configuration when run directly
    print("Testing TGJU configuration...\n")

    try:
        print_config_status()

        # Try to build connection string
        conn_str = get_connection_string()
        print("✓ Connection string built successfully")
        print(f"  (length: {len(conn_str)} characters)\n")

    except ValueError as e:
        print(f"\n❌ Configuration Error:\n{e}\n")
        exit(1)
