# Symbol Categories

TGJU Data Collector discovers symbols from 10 market categories across TGJU.org.

## Category Overview

| Category | Count | Description |
|----------|-------|-------------|
| Currency | 98 | Iranian Rial exchange rates |
| Energy | 126 | Oil, gas, and energy commodities |
| Gold | 16 | Gold, silver, and precious metals |
| Coin | 13 | Iranian coins (Bahar Azadi, Imami) |
| Metal | 11 | Base metals (copper, aluminum, etc.) |
| Commodity | 24 | Agricultural and industrial commodities |
| Crypto | 12 | Cryptocurrencies |
| Index | 47 | Global stock indices and forex |
| Fund | 4 | Gold ETFs and investment funds |
| Other | 34 | Parsian coins, cross rates, misc |

**Total: 385+ unique symbols**

---

## Currency (98 symbols)

### Official Rates

| Code | Persian Name | Description |
|------|-------------|-------------|
| `price_dollar_rl` | دلار | US Dollar |
| `price_eur` | یورو | Euro |
| `price_gbp` | پوند | British Pound |
| `price_aed` | درهم امارات | UAE Dirham |
| `price_jpy` | ین ژاپن | Japanese Yen |
| `price_cny` | یوان چین | Chinese Yuan |

### Sana Exchange

| Code | Persian Name | Description |
|------|-------------|-------------|
| `sana_buy_usd'` | دلار آمریکا | Sana USD |
| `sana_buy_eur'` | یورو | Sana Euro |
| `sana_real_buy_usd'` | دلار صرافی ملی (خرید) | Mellat Bank Buy |
| `sana_real_sell_usd'` | دلار صرافی ملی (فروش) | Mellat Bank Sell |

### Bank Rates

| Code | Persian Name | Description |
|------|-------------|-------------|
| `bank_usd'` | دلار (بانکی) | Bank USD |
| `bank_eur'` | یورو (بانکی) | Bank Euro |
| `bank_gbp'` | پوند (بانکی) | Bank GBP |

---

## Gold (16 symbols)

| Code | Persian Name | Description |
|------|-------------|-------------|
| `ons` | انس طلا | Gold Ounce (USD) |
| `gold_melted_wholesale` | آبشده بنکداری | Melted Gold (Wholesale) |
| `gold_740k` | طلای 18 عیار / 740 | 18K Gold |
| `silver_999` | قیمت نقره | Silver 999 |
| `mesghal` | مثقال طلا | Mesghal Gold |
| `platinum` | انس پلاتین | Platinum Ounce |
| `palladium` | انس پالادیوم | Palladium Ounce |

---

## Coin (13 symbols)

| Code | Persian Name | Description |
|------|-------------|-------------|
| `sekeb` | سکه بهار آزادی | Bahar Azadi Coin |
| `sekee` | سکه امامی | Imami Coin |
| `nim` | نیم سکه | Half Coin |
| `rob` | ربع سکه | Quarter Coin |
| `gerami` | سکه گرمی | Gerami Coin |
| `coin_blubber` | حباب سکه امامی | Imami Bubble |

---

## Energy (126 symbols)

### Major Benchmarks

| Code | Persian Name | Description |
|------|-------------|-------------|
| `energy-crude-oil` | نفت خام (WTI) | WTI Crude Oil |
| `energy-brent-oil` | نفت برنت | Brent Crude |
| `energy-natural-gas` | گاز طبیعی | Natural Gas |
| `oil_opec` | نفت اپک | OPEC Basket |

### Iranian crude

| Code | Persian Name | Description |
|------|-------------|-------------|
| `iran-heavy-1` | نفت سنگین ایران | Iran Heavy |
| `iran-light` | نفت سبک ایران | Iran Light |
| `forozan-blend` | نفت میدان فروزان | Forozan Blend |
| `soroosh` | نفت میدان سروش | Soroosh |

---

## Metal (11 symbols)

| Code | Persian Name | Description |
|------|-------------|-------------|
| `basemetal-copper` | مس / بازار آمریکا | Copper (COMEX) |
| `basemetal-aluminum` | آلومینیوم | Aluminum (LME) |
| `basemetal-zinc` | روی | Zinc |
| `basemetal-nickel` | نیکل | Nickel |
| `basemetal-tin` | قلع | Tin |
| `basemetal-london-copper` | مس / بازار لندن | Copper (LME) |

---

## Commodity (24 symbols)

| Code | Persian Name | Description |
|------|-------------|-------------|
| `commodities-us-wheat` | گندم | Wheat |
| `commodities-us-corn` | ذرت | Corn |
| `commodities-us-cotton` | پنبه | Cotton |
| `commodities-us-soybeans` | سویا | Soybeans |
| `commodities-us-sugar` | شکر | Sugar |
| `commodities-us-cocoa` | کاکائو | Cocoa |

---

## Crypto (12 symbols)

| Code | Persian Name | Description |
|------|-------------|-------------|
| `crypto-bitcoin` | بیت کوین | Bitcoin |
| `crypto-ethereum` | اتریوم | Ethereum |
| `crypto-ripple` | ریپل | Ripple |
| `crypto-litecoin` | لایت کوین | Litecoin |
| `crypto-cardano` | کاردانو | Cardano |

---

## Index (47 symbols)

### US Indices

| Code | Persian Name | Description |
|------|-------------|-------------|
| `oil` | داوجونز | Dow Jones |
| `s_p_500_us` | اس & پی 500 | S&P 500 |
| `nasdaq_us` | نزدک | NASDAQ |

### European Indices

| Code | Persian Name | Description |
|------|-------------|-------------|
| `cac-40'` | CAC 40 | CAC 40 (France) |
| `ftse_100` | فتسی بریتانیا | FTSE 100 (UK) |

### Forex

| Code | Description |
|------|-------------|
| `eur-usd-ask` | EUR/USD |
| `gbp-usd-ask` | GBP/USD |
| `usd-jpy-ask` | USD/JPY |
