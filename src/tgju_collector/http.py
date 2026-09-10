# -*- coding: utf-8 -*-
"""HTTP client with retries, exponential backoff, and polite rate limiting.

Timeouts are explicit and bounded. Timeouts are detected by exception type,
never by matching error message substrings.

Examples:
    >>> client = HttpClient(timeout=5.0, max_retries=1)
    >>> # client.get("https://example.com")  # doctest: +SKIP
"""

from __future__ import annotations

import logging
import random
import time
from typing import Any

import requests

logger = logging.getLogger("tgju_collector.http")


class HttpClient:
    """Shared HTTP client for TGJU endpoints.

    Args:
        timeout: Request timeout in seconds. Must be > 0.
        max_retries: Number of attempts for retryable failures.
        backoff_base: Base delay for exponential backoff (seconds).
        backoff_cap: Maximum backoff delay (seconds).
        delay_min: Minimum sleep between successful page fetches.
        delay_max: Maximum sleep between successful page fetches.
        user_agent: Value for the ``User-Agent`` header.
        session: Optional pre-built session (useful in tests).
    """

    def __init__(
        self,
        *,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_base: float = 0.5,
        backoff_cap: float = 8.0,
        delay_min: float = 0.3,
        delay_max: float = 0.8,
        user_agent: str = "tgju-collector/0.1",
        session: requests.Session | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        if delay_max < delay_min:
            raise ValueError("delay_max must be >= delay_min")

        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_cap = backoff_cap
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", user_agent)
        self._last_request_at: float | None = None

    def close(self) -> None:
        """Close the underlying session."""
        self.session.close()

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _sleep_politely(self) -> None:
        if self._last_request_at is None:
            return
        elapsed = time.monotonic() - self._last_request_at
        target = random.uniform(self.delay_min, self.delay_max)
        if elapsed < target:
            time.sleep(target - elapsed)

    def _backoff_delay(self, attempt: int) -> float:
        delay = min(self.backoff_base * (2**attempt), self.backoff_cap)
        return delay + random.uniform(0, 0.25)

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        """Perform a GET request with retries and rate limiting.

        Args:
            url: Absolute URL.
            params: Optional query parameters.
            headers: Optional extra headers.

        Returns:
            requests.Response: Successful HTTP response (status < 400).

        Raises:
            requests.RequestException: After all retry attempts fail.
            requests.HTTPError: On final non-success status codes.
        """
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            self._sleep_politely()
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
                self._last_request_at = time.monotonic()
                response.raise_for_status()
                return response
            except (
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.RequestException,
            ) as exc:
                last_error = exc
                if attempt >= self.max_retries - 1:
                    break
                delay = self._backoff_delay(attempt)
                logger.warning(
                    "GET %s failed (attempt %s/%s): %s — retrying in %.2fs",
                    url,
                    attempt + 1,
                    self.max_retries,
                    exc,
                    delay,
                )
                time.sleep(delay)

        assert last_error is not None
        raise last_error

    def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """GET a URL and parse the body as JSON.

        Args:
            url: Absolute URL.
            params: Optional query parameters.
            headers: Optional extra headers.

        Returns:
            Any: Parsed JSON document.
        """
        response = self.get(url, params=params, headers=headers)
        return response.json()

    def get_text(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        """GET a URL and return decoded text.

        Args:
            url: Absolute URL.
            params: Optional query parameters.
            headers: Optional extra headers.

        Returns:
            str: Response body as text.
        """
        response = self.get(url, params=params, headers=headers)
        return response.text
