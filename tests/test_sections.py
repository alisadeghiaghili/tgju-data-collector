# -*- coding: utf-8 -*-
"""Tests for section classification."""

from __future__ import annotations

from tgju_collector.models import ProductSection
from tgju_collector.sections import classify_symbol


def test_crypto_symbol() -> None:
    assert classify_symbol("crypto-bitcoin") is ProductSection.CRYPTO
    assert classify_symbol("crypto-tether-irr") is ProductSection.CRYPTO


def test_energy_symbol() -> None:
    assert classify_symbol("oil_brent") is ProductSection.ENERGY
    assert classify_symbol("energy_natural_gas") is ProductSection.ENERGY


def test_gold_coin_symbol() -> None:
    assert classify_symbol("sekee") is ProductSection.GOLD_COIN
    assert classify_symbol("geram18") is ProductSection.GOLD_COIN
    assert classify_symbol("mesghal") is ProductSection.GOLD_COIN
    assert classify_symbol("gold_melted") is ProductSection.GOLD_COIN


def test_currency_symbol() -> None:
    assert classify_symbol("price_dollar_rl") is ProductSection.CURRENCY
    assert classify_symbol("nima_buy_usd") is ProductSection.CURRENCY


def test_metal_symbol() -> None:
    assert classify_symbol("silver") is ProductSection.METAL
    assert classify_symbol("platinum") is ProductSection.METAL
    assert classify_symbol("palladium") is ProductSection.METAL


def test_api_type_mapping() -> None:
    assert classify_symbol("unknown", api_type="ارز") is ProductSection.CURRENCY
    assert classify_symbol("unknown", api_type="طلا و سکه") is ProductSection.GOLD_COIN


def test_unknown_defaults_to_other() -> None:
    assert classify_symbol("zzz_unknown_token") is ProductSection.OTHER


def test_crypto_wins_over_generic_gold_label() -> None:
    # crypto_gold_dao contains gold but is crypto
    assert classify_symbol("crypto_gold_dao") is ProductSection.CRYPTO
