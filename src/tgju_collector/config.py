# -*- coding: utf-8 -*-
"""Runtime configuration loaded from environment variables.

Credentials and endpoints are never hardcoded. See ``.env.example``.

Examples:
    >>> import os
    >>> os.environ["TGJU_DB_URL"] = "sqlite:///./local.db"
    >>> Settings.from_env().database_url
    'sqlite:///./local.db'
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: str | Path = ".env") -> None:
    """Load KEY=VALUE pairs from a dotenv file into ``os.environ``.

    Existing environment variables take priority. Lines starting with ``#``
    and blank lines are ignored. Values may be single- or double-quoted.

    Args:
        path: Path to the ``.env`` file. Missing files are ignored.
    """
    env_path = Path(path)
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings resolved from the environment.

    Attributes:
        database_url: SQLAlchemy database URL.
        http_timeout: Per-request timeout in seconds.
        http_max_retries: Maximum HTTP attempts per resource.
        request_delay_min: Minimum polite delay between requests (seconds).
        request_delay_max: Maximum polite delay between requests (seconds).
        user_agent: User-Agent header value.
        market_timezone: IANA timezone used for market dates.
        log_level: Logging level name.
        backfill_max_days: Maximum historical lookback for gap fill.
    """

    database_url: str = "sqlite:///tgju_collector.db"
    http_timeout: float = 30.0
    http_max_retries: int = 3
    request_delay_min: float = 1.2
    request_delay_max: float = 2.8
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
    market_timezone: str = "Asia/Tehran"
    log_level: str = "INFO"
    backfill_max_days: int = 730

    @classmethod
    def from_env(cls, load_dotenv: bool = True) -> Settings:
        """Build settings from environment variables.

        Args:
            load_dotenv: When True, load ``.env`` before reading variables.

        Returns:
            Settings: Fully resolved settings object.

        Examples:
            >>> Settings.from_env(load_dotenv=False).http_timeout
            30.0
        """
        if load_dotenv:
            _load_dotenv()
        defaults = cls()
        return cls(
            database_url=os.getenv("TGJU_DB_URL", defaults.database_url),
            http_timeout=float(os.getenv("TGJU_HTTP_TIMEOUT", defaults.http_timeout)),
            http_max_retries=int(os.getenv("TGJU_HTTP_MAX_RETRIES", defaults.http_max_retries)),
            request_delay_min=float(os.getenv("TGJU_REQUEST_DELAY_MIN", defaults.request_delay_min)),
            request_delay_max=float(os.getenv("TGJU_REQUEST_DELAY_MAX", defaults.request_delay_max)),
            user_agent=os.getenv("TGJU_USER_AGENT", defaults.user_agent),
            market_timezone=os.getenv("TGJU_MARKET_TZ", defaults.market_timezone),
            log_level=os.getenv("TGJU_LOG_LEVEL", defaults.log_level).upper(),
            backfill_max_days=int(os.getenv("TGJU_BACKFILL_MAX_DAYS", defaults.backfill_max_days)),
        )
