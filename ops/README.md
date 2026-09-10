# Operations

## Daily job

`ops/daily_job.bat` runs live snapshot, news, short-window history, and a
quality report. Point `PYTHON` and `TGJU_DB_URL` at your environment, then
register it with Task Scheduler:

```
schtasks /Create /TN "TGJU-Daily" /SC DAILY /ST 21:15 /TR "\"C:\path\to\ops\daily_job.bat\""
```

Prefer evening / off-peak slots. Keep `TGJU_REQUEST_DELAY_MIN` ≥ 1s.

## Rate profile

| Action | Typical volume | Notes |
|--------|----------------|-------|
| `sync-live --pages home` | 1 page | cheapest |
| `sync-news` | 1 API call | |
| `sync-history --from-catalog --days N` | 1 call per symbol | delay between symbols |
| `sync-catalog` | ~7 pages + N search calls | run weekly, not hourly |
| `backfill` | 1 call per gap range | use trading calendar |

Do not schedule full-catalog backfill more than once a day. Prefer narrow
`--days` windows for the daily job and a weekly wider backfill.

## Detectability posture

- Browser-like User-Agent and Accept headers (no self-identifying token).
- Session keep-alive; 1.2–2.8s jittered delay between requests by default.
- Search-API expansion paused extra 0.8s between queries.
- HTTP errors back off exponentially and stop after max retries.
- No parallel fan-out across hosts.

If you need higher throughput, raise delays in lockstep with volume — do not
drop them below ~0.5s.

## Health

```
tgju status
tgju quality
```

`quality` exits non-zero when OHLC integrity or coverage issues appear.
Wire that into the daily job log / monitoring.
