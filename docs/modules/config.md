# Configuration Module

The Configuration Module manages environment variables and database connection settings.

## Functions

### `load_config()`

Loads configuration from `.env` file.

```python
from src.config import load_config

load_config()  # Loads .env file
load_config('/path/to/custom.env')  # Custom path
```

### `get_connection_string()`

Builds SQL Server connection string from environment variables.

```python
from src.config import get_connection_string

conn_str = get_connection_string()
# mssql+pyodbc://user:pass@server:1433/database?driver=ODBC+Driver+17+for+SQL+Server
```

**Priority**:

1. Explicit `connection_string_var` parameter
2. `{prefix}_CONNECTION_STRING` environment variable
3. Individual components: `{prefix}_SERVER`, `{prefix}_NAME`, etc.

### `get_table_name()`

Gets the target table name from environment or uses default.

```python
from src.config import get_table_name

table = get_table_name()  # Returns 'TgjuAssets' by default
```

---

## Environment Variable Prefix

All variables use the `TGJU_DB` prefix by default:

```python
get_connection_string(prefix='TGJU_DB')
# Reads: TGJU_DB_SERVER, TGJU_DB_NAME, TGJU_DB_USER, TGJU_DB_PASSWORD
```

Custom prefix for multiple databases:

```python
get_connection_string(prefix='ANOTHER_DB')
# Reads: ANOTHER_DB_SERVER, ANOTHER_DB_NAME, etc.
```

---

## Security Validation

The config module rejects placeholder values:

```python
# These will raise ValueError:
TGJU_DB_PASSWORD=your_password
TGJU_DB_PASSWORD=changeme
TGJU_DB_PASSWORD=placeholder
```

---

## Backwards Compatibility

The root `config.py` provides backwards compatibility with the original `tgjuScraper.py`:

```python
# Old code still works:
from config import load_env_file, get_connection_string, get_table_name

load_env_file()  # Alias for load_config()
conn = get_connection_string()
table = get_table_name()
```
