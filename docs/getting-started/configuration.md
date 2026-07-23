# Configuration

TGJU Data Collector uses environment variables for configuration, following the [12-Factor App](https://12factor.net/config) methodology.

## Configuration Methods

### Option 1: Environment File (Recommended)

```bash
cp .env.example .env
```

Edit `.env`:

```env
TGJU_DB_SERVER=localhost
TGJU_DB_NAME=tgju
TGJU_DB_USER=sa
TGJU_DB_PASSWORD=YourSecurePassword123!
TGJU_DB_DRIVER=ODBC Driver 17 for SQL Server
TGJU_DB_PORT=1433
TGJU_DB_TABLE_NAME=TgjuAssets
```

!!! warning "Security"
    Never commit `.env` to version control. It's already in `.gitignore`.

### Option 2: Direct Environment Variables

=== "PowerShell"

    ```powershell
    $env:TGJU_DB_SERVER="localhost"
    $env:TGJU_DB_NAME="tgju"
    $env:TGJU_DB_USER="sa"
    $env:TGJU_DB_PASSWORD="YourSecurePassword123!"
    ```

=== "Bash"

    ```bash
    export TGJU_DB_SERVER=localhost
    export TGJU_DB_NAME=tgju
    export TGJU_DB_USER=sa
    export TGJU_DB_PASSWORD="YourSecurePassword123!"
    ```

### Option 3: Complete Connection String

```env
TGJU_DB_CONNECTION_STRING=mssql+pyodbc://username:password@server:1433/database?driver=ODBC+Driver+17+for+SQL+Server
```

**Priority**: Complete connection string > Individual components

---

## Environment Variables Reference

### Database Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TGJU_DB_SERVER` | Yes* | — | SQL Server hostname or IP |
| `TGJU_DB_NAME` | Yes* | — | Database name |
| `TGJU_DB_USER` | Yes* | — | Database username |
| `TGJU_DB_PASSWORD` | Yes* | — | Database password |
| `TGJU_DB_DRIVER` | No | `ODBC Driver 17 for SQL Server` | ODBC driver name |
| `TGJU_DB_PORT` | No | `1433` | Database port |
| `TGJU_DB_TABLE_NAME` | No | `TgjuAssets` | Target table name |
| `TGJU_DB_CONNECTION_STRING` | No | — | Full connection string (overrides above) |

*Required unless `TGJU_DB_CONNECTION_STRING` is set.

### Logging Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LOG_LEVEL` | No | `INFO` | Minimum log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## Windows Authentication

For Windows Authentication (trusted connection):

```env
TGJU_DB_CONNECTION_STRING=mssql+pyodbc://user@server/db?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes
```

---

## Validating Configuration

Run the built-in validation:

```bash
python config.py
```

Expected output:

```
============================================================
TGJU Configuration Status
============================================================

.env file: ✓ Found

Database Configuration:
  TGJU_DB_SERVER: localhost
  TGJU_DB_NAME: tgju
  TGJU_DB_USER: sa
  TGJU_DB_PASSWORD: ********

Table Name: TgjuAssets

============================================================
✓ Connection string built successfully (length: 156 characters)
```

---

## Security Best Practices

1. **Use strong passwords** — Minimum 12 characters with mixed case, numbers, and symbols
2. **Never hardcode credentials** — Always use environment variables
3. **Protect `.env`** — It's in `.gitignore`, but verify before pushing
4. **Use Azure Key Vault** — For production deployments, consider secret management services
5. **Validate inputs** — The config module rejects placeholder values (e.g., `your_password`)
