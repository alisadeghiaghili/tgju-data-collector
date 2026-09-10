# -*- coding: utf-8 -*-
"""Tests for HTTP client retry behavior using a stub session."""

from __future__ import annotations

import pytest
import requests

from tgju_collector.http import HttpClient


class StubResponse:
    def __init__(self, status_code: int = 200, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = "{}"

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")

    def json(self):
        return self._payload


class StubSession:
    def __init__(self, responses: list[Exception | StubResponse]) -> None:
        self.responses = list(responses)
        self.calls = 0
        self.headers: dict[str, str] = {}

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls += 1
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def close(self) -> None:
        pass


def test_retries_then_succeeds() -> None:
    session = StubSession(
        [
            requests.exceptions.ConnectTimeout("t1"),
            requests.exceptions.ConnectionError("c1"),
            StubResponse(200, {"ok": True}),
        ]
    )
    client = HttpClient(
        session=session,
        max_retries=3,
        backoff_base=0.01,
        backoff_cap=0.02,
        delay_min=0.0,
        delay_max=0.0,
    )
    response = client.get("https://example.com")
    assert response.status_code == 200
    assert session.calls == 3


def test_raises_after_max_retries() -> None:
    session = StubSession(
        [
            requests.exceptions.ConnectTimeout("t"),
            requests.exceptions.ConnectTimeout("t"),
            requests.exceptions.ConnectTimeout("t"),
        ]
    )
    client = HttpClient(
        session=session,
        max_retries=3,
        backoff_base=0.01,
        backoff_cap=0.02,
        delay_min=0.0,
        delay_max=0.0,
    )
    with pytest.raises(requests.exceptions.ConnectTimeout):
        client.get("https://example.com")
    assert session.calls == 3


def test_http_error_retried() -> None:
    session = StubSession(
        [
            StubResponse(500),
            StubResponse(200, {"ok": 1}),
        ]
    )
    client = HttpClient(
        session=session,
        max_retries=3,
        backoff_base=0.01,
        backoff_cap=0.02,
        delay_min=0.0,
        delay_max=0.0,
    )
    response = client.get("https://example.com")
    assert response.status_code == 200


def test_invalid_timeout_rejected() -> None:
    with pytest.raises(ValueError):
        HttpClient(timeout=0)
    with pytest.raises(ValueError):
        HttpClient(max_retries=0)
