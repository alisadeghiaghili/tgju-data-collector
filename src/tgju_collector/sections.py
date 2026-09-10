# -*- coding: utf-8 -*-
"""Product-section taxonomy and symbol classification rules.

Classification is deterministic and testable. Rules are ordered from most
specific to least specific so that e.g. ``crypto-bitcoin`` is not classified
as ``currency`` just because it may contain price-like data.

Examples:
    >>> classify_symbol("crypto-bitcoin")
    <ProductSection.CRYPTO: 'crypto'>
    >>> classify_symbol("oil_brent")
    <ProductSection.ENERGY: 'energy'>
    >>> classify_symbol("sekee")
    <ProductSection.GOLD_COIN: 'gold_coin'>
"""

from __future__ import annotations

from .models import ProductSection

# Ordered (predicate keywords, section) pairs. First match wins.
_KEYWORD_RULES: tuple[tuple[tuple[str, ...], ProductSection], ...] = (
    (("crypto-", "crypto_", "bitcoin", "ethereum", "tether", "binance", "xrp", "solana"), ProductSection.CRYPTO),
    (("oil_", "brent", "opec", "wti", "natural_gas", "gasoline", "energy_", "natgas"), ProductSection.ENERGY),
    (("silver", "platinum", "palladium", "basemetal", "ons", "aluminum", "aluminium", "copper"), ProductSection.METAL),
    (("commodit", "wheat", "corn", "soybean", "cattle", "lumber", "coffee", "cocoa"), ProductSection.COMMODITY),
    (("gold_", "geram", "mesghal", "sekee", "sekeb", "coin_", "blubber", "ayar", "ime_fund", "melted"), ProductSection.GOLD_COIN),
    (("price_", "dollar", "euro", "nima", "sana", "dirham", "pound", "sterling", "yuan", "lira", "yen"), ProductSection.CURRENCY),
    (("bourse", "tedpix", "stock", "fund_", "bond", "index_"), ProductSection.BOURSE),
)

_LABEL_RULES: tuple[tuple[tuple[str, ...], ProductSection], ...] = (
    (("ارز دیجیتال", "رمزارز", "بیت کوین"), ProductSection.CRYPTO),
    (("نفت", "انرژی", "گاز"), ProductSection.ENERGY),
    (("فلز", "نقره", "پلاتین", "پالادیوم"), ProductSection.METAL),
    (("طلا", "سکه", "مثقال", "آب شده"), ProductSection.GOLD_COIN),
    (("دلار", "یورو", "ارز"), ProductSection.CURRENCY),
    (("بورس", "شاخص", "صندوق"), ProductSection.BOURSE),
    (("کالا",), ProductSection.COMMODITY),
    (("اقتصادی",), ProductSection.ECONOMICS),
)


def classify_symbol(
    symbol: str,
    *,
    labels: list[str] | None = None,
    api_type: str | None = None,
) -> ProductSection:
    """Classify a symbol into a product section.

    Args:
        symbol: Symbol identifier (e.g. ``price_dollar_rl``).
        labels: Optional Persian/English labels used as fallback signals.
        api_type: Optional ``type`` field from the TGJU search API.

    Returns:
        ProductSection: Best-effort section. Defaults to ``OTHER``.

    Examples:
        >>> classify_symbol("price_dollar_rl")
        <ProductSection.CURRENCY: 'currency'>
        >>> classify_symbol("unknown_symbol")
        <ProductSection.OTHER: 'other'>
    """
    if not symbol or not symbol.strip():
        return ProductSection.OTHER

    lowered = symbol.lower()

    # Ambiguous prefixes resolved by label before generic keyword rules.
    if lowered.startswith("retail_"):
        return ProductSection.GOLD_COIN
    if lowered.startswith("gc") and lowered[2:3].isdigit():
        # gc14–gc19 are coin series; gc30 is the bourse index.
        label_blob = " ".join(labels or []).lower()
        if any(token in label_blob for token in ("سکه", "coin")):
            return ProductSection.GOLD_COIN
        if any(token in label_blob for token in ("بورس", "شاخص", "bourse")):
            return ProductSection.BOURSE

    for keywords, section in _KEYWORD_RULES:
        if any(keyword in lowered for keyword in keywords):
            return section

    haystacks: list[str] = []
    if labels:
        haystacks.extend(labels)
    if api_type:
        haystacks.append(api_type)
    joined = " ".join(haystacks).lower()

    for keywords, section in _LABEL_RULES:
        if any(keyword in joined for keyword in keywords):
            return section

    if api_type:
        mapped = _API_TYPE_MAP.get(api_type.strip())
        if mapped is not None:
            return mapped

    return ProductSection.OTHER


_API_TYPE_MAP: dict[str, ProductSection] = {
    "طلا و سکه": ProductSection.GOLD_COIN,
    "ارز": ProductSection.CURRENCY,
    "ارزهای دیجیتال": ProductSection.CRYPTO,
    "بازارهای کالایی": ProductSection.COMMODITY,
    "فلزات": ProductSection.METAL,
    "انرژی": ProductSection.ENERGY,
    "بورس": ProductSection.BOURSE,
    "شاخص‌های اقتصادی": ProductSection.ECONOMICS,
}


SECTION_PAGE_URLS: dict[str, str] = {
    "home": "https://www.tgju.org/",
    "coin": "https://www.tgju.org/coin",
    "currency": "https://www.tgju.org/currency",
    "crypto": "https://www.tgju.org/crypto",
    "energy": "https://www.tgju.org/energy",
    "global_market": "https://www.tgju.org/global-market",
    "economics": "https://www.tgju.org/economics",
}
