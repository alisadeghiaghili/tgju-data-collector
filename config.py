# -*- coding: utf-8 -*-
"""
Backwards-compatible config wrapper.

Delegates to src.config for the actual implementation.
This file is kept for backwards compatibility with existing scripts.
"""

from src.config import load_config, get_connection_string, get_table_name

# Auto-load on import (matches original behavior)
load_env_file = load_config

# Re-export for backwards compatibility
__all__ = ['get_connection_string', 'get_table_name', 'load_env_file', 'load_config']


if __name__ == '__main__':
    from src.config import load_config
    load_config()
    try:
        conn = get_connection_string()
        print(f"Connection string built successfully (length: {len(conn)})")
    except ValueError as e:
        print(f"Configuration error: {e}")
