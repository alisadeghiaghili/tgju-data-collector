# HTTP Client

The HTTP Client provides resilient network requests with automatic retry, rate limiting, and error handling.

## Features

- **Automatic Retry** — Retries failed requests up to 3 times
- **Exponential Backoff** — Delay increases with each retry
- **Rate Limiting** — Polite delays between requests
- **Timeout Handling** — Configurable request timeout
- **User Agent Spoofing** — Appears as a regular browser

---

## Usage

```python
from src.http_client import HttpClient

http = HttpClient()

# Make a GET request
response = http.get('https://www.tgju.org')

if response:
    print(response.status_code)
    print(response.text)

# Polite delay between requests
http.sleep_between_requests()

# Close when done
http.close()
```

---

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `user_agent` | `Mozilla/5.0 (Windows NT 10.0; Win64; x64)` | Browser user agent |
| `timeout` | 30 seconds | Request timeout |
| `max_retries` | 3 | Maximum retry attempts |

---

## Retry Logic

```
Request Fails
    │
    ├─ Attempt 1: Immediate retry
    │
    ├─ Attempt 2: Wait 2-3 seconds
    │
    └─ Attempt 3: Wait 2-3 seconds
              │
              ▼
        All failed → Return None
```

### Error Types Handled

| Error | Strategy |
|-------|----------|
| `ConnectionError` | Retry with backoff |
| `Timeout` | Retry with backoff |
| `HTTPError` (4xx/5xx) | Retry with jitter |

---

## Rate Limiting

```python
def sleep_between_requests(self):
    delay = REQUEST_DELAY_MIN + random.random() * REQUEST_DELAY_JITTER
    time.sleep(delay)
```

- **Minimum delay**: 0.5 seconds
- **Maximum delay**: 1.0 seconds (0.5 + 0.5 jitter)

This prevents overloading TGJU.org's servers.

---

## Integration with Other Modules

All modules use the shared `HttpClient` instance:

```python
# Discovery
http = HttpClient()
registry = SymbolRegistry(http)
registry.discover_all()

# Collection
collector = OHLCVCollector(http)
data = collector.collect_batch(symbols)

# Cleanup
http.close()
```

!!! tip "Reuse Sessions"
    The `HttpClient` maintains a `requests.Session` for connection pooling. Reuse the same instance across multiple requests for better performance.
