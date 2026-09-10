# -*- coding: utf-8 -*-
"""Tests for history-capability heuristics."""

from __future__ import annotations

from tgju_collector.history_support import filter_history_capable, is_history_capable


def test_numeric_html_ids_not_capable() -> None:
    assert is_history_capable("131398") is False
    assert is_history_capable("999999") is False


def test_known_prefixes_are_capable() -> None:
    assert is_history_capable("sekee") is True
    assert is_history_capable("price_dollar_rl") is True
    assert is_history_capable("crypto-bitcoin") is True
    assert is_history_capable("oil_brent") is True
    assert is_history_capable("nima_buy_aed") is True
    assert is_history_capable("retail_nim") is True


def test_api_type_forces_capable() -> None:
    assert is_history_capable("zzz_custom", api_type="ارز") is True
    assert is_history_capable("zzz_custom", meta={"api_type": "طلا و سکه"}) is True


def test_filter_list_of_dicts() -> None:
    items = [
        {"symbol": "sekee", "meta": {}},
        {"symbol": "131398", "meta": {}},
        {"symbol": "price_dollar_rl", "meta": {}},
    ]
    kept = filter_history_capable(items)
    assert [x["symbol"] for x in kept] == ["sekee", "price_dollar_rl"]
