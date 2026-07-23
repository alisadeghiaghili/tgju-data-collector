# -*- coding: utf-8 -*-
"""Shared HTTP client with retry logic and rate limiting."""

import time
import random
import logging

import requests

logger = logging.getLogger('tgju')

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
REQUEST_DELAY_MIN = 0.5
REQUEST_DELAY_JITTER = 0.5


class HttpClient:
    """Shared HTTP session with retry, timeout, and rate limiting."""

    def __init__(self, user_agent: str = DEFAULT_USER_AGENT,
                 timeout: int = DEFAULT_TIMEOUT,
                 max_retries: int = MAX_RETRIES):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})
        self.timeout = timeout
        self.max_retries = max_retries

    def get(self, url: str, **kwargs) -> requests.Response | None:
        """
        Execute GET request with automatic retry and error handling.

        Returns:
            Response object if successful, None otherwise.
        """
        kwargs.setdefault('timeout', self.timeout)

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"GET {url} (attempt {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, **kwargs)
                response.raise_for_status()
                return response

            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError) as e:
                logger.warning(f"Connection error for {url} attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    delay = 2 + random.random()
                    time.sleep(delay)

            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP error for {url}: {e}")
                if attempt < self.max_retries - 1:
                    delay = REQUEST_DELAY_MIN + random.random() * REQUEST_DELAY_JITTER
                    time.sleep(delay)

        logger.error(f"Failed to fetch {url} after {self.max_retries} retries")
        return None

    def sleep_between_requests(self):
        """Polite delay between requests to avoid rate limiting."""
        delay = REQUEST_DELAY_MIN + random.random() * REQUEST_DELAY_JITTER
        time.sleep(delay)

    def close(self):
        """Close the underlying session."""
        self.session.close()
