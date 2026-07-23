# Daily Workflow

This guide covers the recommended daily operations for TGJU Data Collector.

## Morning Routine

### 1. Collect Fresh Data

```bash
python main.py collect
```

This fetches the latest OHLCV data for all discovered symbols and saves to the database.

**Expected duration**: 2-5 minutes (depending on symbol count)

**What happens**:

1. Discovers all symbols from TGJU.org
2. Fetches latest daily data for each symbol
3. Saves to `TgjuAssets` table

### 2. Check Collection Status

```bash
python main.py status
```

Verify:

- `.env` file exists
- Database connection works
- `TgjuAssets` table exists

---

## Weekly Maintenance

### Backfill Historical Gaps

Run weekly to fill any missed days:

```bash
python main.py backfill
```

Or limit to recent gaps:

```bash
python main.py backfill --max-days 30
```

### Verify Data Integrity

Check for missing dates:

```sql
-- Find symbols with missing dates
SELECT Symbol_En, COUNT(DISTINCT PersianDate) as days
FROM TgjuAssets
WHERE PersianDate >= '1405-04-01'
GROUP BY Symbol_En
HAVING COUNT(DISTINCT PersianDate) < 20
```

---

## Scheduling

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 6:00 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `main.py collect`
7. Start in: `C:\path\to\tgju-data-collector`

### Cron (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add daily at 6:00 AM
0 6 * * * cd /path/to/tgju-data-collector && python main.py collect >> logs/cron.log 2>&1

# Add weekly backfill on Sundays at 7:00 AM
0 7 * * 0 cd /path/to/tgju-data-collector && python main.py backfill >> logs/cron.log 2>&1
```

### PowerShell Scheduled Job

```powershell
# Create scheduled job
$trigger = New-JobTrigger -Daily -At "6:00AM"
$options = New-ScheduledJobOption -StartIfOnBatteryPower
Register-ScheduledJob -Name "TGJU-Collect" `
    -Trigger $trigger `
    -ScriptBlock {
        Set-Location "C:\path\to\tgju-data-collector"
        python main.py collect
    } `
    -ScheduledJobOption $options
```

---

## Monitoring

### Log Files

Logs are stored in `logs/` directory:

```
logs/
├── tgju_20260721.log    # Today's log
├── tgju_20260720.log    # Yesterday's log
└── ...
```

### Check Recent Logs

```bash
# View today's log
type logs\tgju_%date:~0,4%%date:~5,2%%date:~8,2%.log

# Or tail the latest log (Linux/Mac)
tail -f logs/tgju_*.log
```

### Database Monitoring

```sql
-- Count records by date
SELECT ScrapeDate, COUNT(*) as records
FROM TgjuAssets
GROUP BY ScrapeDate
ORDER BY ScrapeDate DESC
```

---

## Troubleshooting Daily Operations

### Collection Fails

1. Check internet connection
2. Verify TGJU.org is accessible
3. Check logs for specific error messages
4. Run `python main.py status` to verify configuration

### Backfill Takes Too Long

1. Limit the backfill window: `--max-days 30`
2. Backfill specific symbols: `--symbols ons price_dollar_rl`
3. Check network speed

### Database Connection Issues

1. Verify SQL Server is running
2. Check `.env` credentials
3. Test connection: `python config.py`
4. Verify ODBC driver is installed
