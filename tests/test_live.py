# -*- coding: utf-8 -*-
"""Tests for live snapshot collection and number normalization."""

from __future__ import annotations

from tgju_collector.collectors.live import (
    LiveCollector,
    normalize_number,
    snapshots_from_html,
)


def test_normalize_persian_digits() -> None:
    assert normalize_number("۱۲۳") == 123.0


def test_normalize_thousands_separators() -> None:
    assert normalize_number("2,410,100") == 2410100.0
    assert normalize_number("۱٬۲۳۴") == 1234.0


def test_normalize_decimal() -> None:
    assert normalize_number("104.761") == 104.761
    assert normalize_number("۱٫۵") == 1.5


def test_normalize_invalid() -> None:
    assert normalize_number("n/a") is None
    assert normalize_number("") is None
    assert normalize_number(None) is None
    assert normalize_number("-") is None


def test_snapshots_from_html(sample_home_html: str, fixed_now) -> None:
    snaps = snapshots_from_html(sample_home_html, captured_at=fixed_now)
    assert len(snaps) == 4
    by_symbol = {s.symbol: s for s in snaps}
    assert by_symbol["sekee"].price == 2410100000.0
    assert by_symbol["price_dollar_rl"].price == 72350.0
    assert by_symbol["crypto-bitcoin"].price == 77026.63


class FakeHttp:
    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages

    def get_text(self, url: str, *, params: dict | None = None) -> str:
        return self.pages[url]


def test_live_collector(sample_home_html: str) -> None:
    http = FakeHttp({"https://www.tgju.org/": sample_home_html})
    collector = LiveCollector(http, pages={"home": "https://www.tgju.org/"})
    snaps = collector.collect(page_names=["home"])
    assert len(snaps) == 4
