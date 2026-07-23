# Troubleshooting

## Common Issues

### 1. Configuration Issues

**Problem**: Missing environment variables

```
ValueError: Missing required environment variables: TGJU_DB_SERVER, TGJU_DB_NAME
```

**Solution**:

```bash
# Verify .env file exists
ls .env

# Test configuration
python config.py

# If missing, create from template
cp .env.example .env
# Edit .env with your credentials
```

---

### 2. Database Connection Failed

**Problem**: Cannot connect to SQL Server

```
ERROR: Database error: (pyodbc.OperationalError) ...
```

**Solution**:

1. **Verify ODBC Driver**:

    ```bash
    # Windows
    odbcad32.exe
    
    # Linux
    odbcinst -j
    ```

2. **Test connection string**:

    ```bash
    python config.py
    ```

3. **Check SQL Server status**:

    - Ensure SQL Server service is running
    - Verify firewall allows connections on port 1433
    - Test credentials via SQL Server Management Studio

---

### 3. No Symbols Found

**Problem**: Discovery returns 0 symbols

**Solution**:

1. **Check internet connection**

2. **Verify TGJU.org is accessible**:

    ```bash
    curl https://www.tgju.org
    ```

3. **Check if website structure changed**:

    - XPath expressions may need updating
    - Inspect HTML using browser DevTools

---

### 4. Backfill Finds No Gaps

**Problem**: Backfill reports no gaps, but data is missing

**Solution**:

1. **Check date format** in database:

    ```sql
    SELECT TOP 10 PersianDate, Symbol_En 
    FROM TgjuAssets 
    ORDER BY Symbol_En, PersianDate
    ```

2. **Verify Persian date parsing**:

    - Format should be `YYYY-MM-DD` (e.g., `1405-11-18`)
    - Not `YYYYMMDD` or other formats

3. **Manually trigger backfill**:

    ```sql
    DELETE FROM TgjuAssets 
    WHERE Symbol_En = 'gold_melted' 
    AND PersianDate BETWEEN '1405-01-01' AND '1405-01-10'
    ```

    Then run backfill again.

---

### 5. Collection Fails for Specific Symbols

**Problem**: Some symbols fail while others succeed

**Solution**:

1. **Check logs** for specific error messages

2. **Test individual symbol**:

    ```python
    from src.http_client import HttpClient
    from src.collectors.ohlcv import OHLCVCollector

    http = HttpClient()
    collector = OHLCVCollector(http)

    df = collector.collect_latest('SYMBOL_CODE', '1D')
    print(df)
    http.close()
    ```

3. **Skip problematic symbols**:

    The collector automatically skips symbols that fail. Check logs for which symbols are failing.

---

### 6. Volume Data Missing

**Problem**: Volume column is always 0

**Explanation**: TGJU API often returns empty volume arrays for certain symbols. This is normal behavior — the API doesn't provide volume data for all symbols.

---

### 7. Persian Date Conversion Errors

**Problem**: `jdatetime` conversion fails

**Solution**:

1. **Check date format**:

    ```python
    import jdatetime
    from datetime import date

    # Correct format
    gregorian = date(2026, 7, 21)
    persian = jdatetime.date.fromgregorian(date=gregorian)
    print(persian)  # 1405-04-31
    ```

2. **Handle edge cases**:

    ```python
    # Handle None/empty dates
    if date_str:
        persian_date = to_persian_date(date_obj)
    ```

---

### 8. Logging Issues

**Problem**: No log files created

**Solution**:

1. **Check logs directory**:

    ```bash
    ls logs/
    ```

2. **Verify permissions**:

    ```bash
    # Create logs directory manually
    mkdir logs
    ```

3. **Check log level**:

    ```bash
    set LOG_LEVEL=DEBUG
    python main.py collect
    ```

---

## Performance Issues

### Collection Takes Too Long

**Possible causes**:

1. **Many symbols**: 385+ symbols × 0.5s delay = ~3 minutes minimum
2. **Network latency**: Slow connection to TGJU.org
3. **Rate limiting**: TGJU.org may slow down responses

**Solutions**:

1. **Reduce symbol count**: Only collect needed symbols
2. **Use faster network**: Switch to a faster connection
3. **Schedule off-peak**: Run during low-traffic hours

### Backfill Takes Too Long

**Possible causes**:

1. **Large date gaps**: 2 years of missing data
2. **Many symbols**: Each symbol requires multiple API calls

**Solutions**:

1. **Limit backfill window**:

    ```bash
    python main.py backfill --max-days 30
    ```

2. **Backfill specific symbols**:

    ```bash
    python main.py backfill --symbols ons price_dollar_rl
    ```

---

## Getting Help

If you encounter issues not covered here:

1. **Check logs** in `logs/` directory
2. **Run diagnostics**:

    ```bash
    python config.py
    python main.py status
    ```

3. **Open an issue** on GitHub with:

    - Error message
    - Relevant log excerpts
    - Environment details (Python version, OS, SQL Server version)
