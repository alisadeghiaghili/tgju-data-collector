# Symbol Discovery

The Symbol Discovery system automatically finds all tradeable symbols from TGJU.org's various pages.

## How It Works

1. **Fetch** HTML from a TGJU page
2. **Parse** the DOM using BeautifulSoup + lxml
3. **Extract** symbol data using XPath expressions
4. **Deduplicate** by symbol code across all sources

## Architecture

```
SymbolRegistry
    │
    ├── MainPageDiscovery      (138 symbols)
    ├── EnergyDiscovery        (117 symbols)
    ├── SanaDiscovery          (27 symbols)
    ├── BankDiscovery          (46 symbols)
    ├── GlobalMarketDiscovery  (65 symbols)
    ├── GoldGlobalDiscovery    (2 symbols)
    ├── CryptoDiscovery        (0-12 symbols)
    ├── CommoditiesDiscovery   (15 symbols)
    ├── BaseMetalDiscovery     (10 symbols)
    ├── CoinDiscovery          (0-13 symbols)
    └── ParsianCoinDiscovery   (0-21 symbols)
              │
              ▼
    385+ unique symbols
```

## Usage

### Programmatic

```python
from src.http_client import HttpClient
from src.discovery.registry import SymbolRegistry

http = HttpClient()
registry = SymbolRegistry(http)

# Discover all symbols
total = registry.discover_all()

# Get all symbols
symbols = registry.get_all()

# Filter by category
gold_symbols = registry.get_by_category('gold')
currency_symbols = registry.get_by_category('currency')

# Filter by source
energy_symbols = registry.get_by_source('energy')

# Convert to DataFrame
df = registry.to_dataframe()

http.close()
```

### CLI

```bash
# Discover and print all symbols
python main.py discover

# Discover and save to database
python main.py discover --save-db
```

---

## Discovery Sources

### MainPageDiscovery

**Source**: `https://www.tgju.org`
**Category**: Mixed (inferred from symbol code)

Parses the main navigation menu to find all symbol profile links. Categories are inferred from the symbol code:

| Code Pattern | Category |
|-------------|----------|
| `gold_*`, `ons`, `silver_*` | gold |
| `seke*`, `coin_*`, `nim`, `rob` | coin |
| `price_*`, `dollar`, `eur` | currency |
| `crypto-*` | crypto |
| `energy-*`, `oil*` | energy |
| `commodities-*` | commodity |
| `basemetal-*` | metal |
| `gc*`, `go*` | fund |

### EnergyDiscovery

**Source**: `https://www.tgju.org/energy`
**Category**: energy

Parses the energy market table, extracting symbols from `onclick` attributes.

### SanaDiscovery

**Source**: Sana exchange rates page
**Category**: currency

Finds Sana exchange rates for various currencies.

### BankDiscovery

**Source**: Bank rates page
**Category**: currency

Extracts official bank exchange rates.

### GlobalMarketDiscovery

**Source**: Global markets page
**Category**: mixed

Discovers global indices (Dow Jones, S&P 500, etc.), forex pairs, and cryptocurrency prices.

### CommoditiesDiscovery / BaseMetalDiscovery

**Source**: Commodities and metals pages
**Category**: commodity / metal

Finds commodity futures (wheat, corn, etc.) and base metal prices (copper, aluminum, etc.).

### CoinDiscovery / ParsianCoinDiscovery

**Source**: Coin market pages
**Category**: coin / other

Discovers Iranian coin prices (Bahar Azadi, Imami) and Parsian coin variants.

---

## Symbol Data Model

```python
@dataclass
class Symbol:
    code: str          # English code (e.g., 'price_dollar_rl')
    name_fa: str       # Persian name (e.g., 'دلار')
    name_en: str       # English name (same as code)
    source_page: str   # Source identifier (e.g., 'main', 'energy')
    category: str      # Category (e.g., 'currency', 'gold')
```

---

## Adding a New Discovery Source

To add a new TGJU page:

1. Create `src/discovery/my_page.py`:

```python
from .base import BaseDiscovery, Symbol
from typing import List

class MyPageDiscovery(BaseDiscovery):
    url = 'https://www.tgju.org/my-page'
    source_name = 'my_page'
    category = 'my_category'

    def _parse(self, response) -> List[Symbol]:
        xpath_mappings = {
            'name_fa': '//XPath/to/persian/name',
            'href': '//XPath/to/symbol/code'
        }

        extracted = self._extract_xpaths(response, xpath_mappings)
        if not extracted.get('href'):
            return []

        symbols = []
        for name_fa, href in zip(extracted['name_fa'], extracted['href']):
            code = href.split('/')[-1]
            symbols.append(Symbol(
                code=code,
                name_fa=name_fa.strip(),
                name_en=code,
                source_page=self.source_name,
                category=self.category
            ))
        return symbols
```

2. Register in `src/discovery/registry.py`:

```python
from .my_page import MyPageDiscovery

ALL_DISCOVERERS = [
    # ... existing discoverers ...
    MyPageDiscovery,
]
```
