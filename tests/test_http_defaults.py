# -*- coding: utf-8 -*-
"""Tests for browser-like HTTP client defaults."""

from __future__ import annotations

import requests

from tgju_collector.http import DEFAULT_USER_AGENT, HttpClient


class StubSession:
    def __init__(self) -> None:
        self.headers: dict[str, str] = {}
        self.calls = 0

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls += 1

        class _R:
            status_code = 200
            text = "{}"

            def raise_for_status(self):
                return None

            def json(self):
                return {}

        return _R()

    def close(self):
        pass


def test_default_ua_is_browser_like() -> None:
    assert "Mozilla/5.0" in DEFAULT_USER_AGENT
    assert "tgju-collector" not in DEFAULT_USER_AGENT


def test_session_seeds_browser_headers() -> None:
    session = StubSession()
    HttpClient(session=session, delay_min=0.0, delay_max=0.0)
    assert session.headers["User-Agent"] == DEFAULT_USER_AGENT
    assert "fa-IR" in session.headers["Accept-Language"]
    assert session.headers["Referer"] == "https://www.tgju.org/"
    assert "application/json" in session.headers["Accept"]
