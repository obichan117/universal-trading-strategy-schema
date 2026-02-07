# Universal Trading Strategy Schema (UTSS)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/obichan117/universal-trading-strategy-schema/blob/main/examples/quickstart.ipynb)

A comprehensive, composable schema for expressing any trading strategy. Define your strategies in YAML/JSON and use them across different trading platforms, backtesting engines, and execution systems.

## Packages

| Package | Description | Install |
|---------|-------------|---------|
| **[utss](./packages/utss/)** | Schema definition & validation | `pip install utss` |
| **[pyutss](./packages/pyutss/)** | Backtesting engine (WIP) | `pip install pyutss` |

## Features

- **Composable Architecture**: Signal → Condition → Rule → Strategy hierarchy
- **LLM-Friendly**: Designed for natural language → strategy conversion
- **Reusable Components**: Define signals and conditions once, reference everywhere
- **Parameter Optimization**: Built-in support for optimizable parameters
- **Comprehensive**: Technical indicators, fundamental data, portfolio state, calendar patterns, and events
- **Japan Focus**: First-class support for Japanese stock indices (Nikkei, TOPIX, etc.)

## Installation

```bash
# Schema package only
pip install utss

# With backtesting engine (coming soon)
pip install pyutss
```

## Quick Start

### YAML Strategy Definition

```yaml
$schema: https://obichan117.github.io/universal-trading-strategy-schema/schema/v1/strategy.json

info:
  id: rsi_reversal
  name: RSI Reversal Strategy
  version: "1.0"
  description: Buy when RSI is oversold, sell when overbought

universe:
  type: static
  symbols:
    - AAPL
    - GOOGL

# Reusable signal definitions
signals:
  rsi_14:
    type: indicator
    indicator: RSI
    params:
      period: 14

rules:
  - name: Buy on oversold
    when:
      type: comparison
      left:
        $ref: "#/signals/rsi_14"
      operator: "<"
      right:
        type: constant
        value: 30
    then:
      type: trade
      direction: buy
      sizing:
        type: percent_of_equity
        percent: 10

  - name: Sell on overbought
    when:
      type: comparison
      left:
        $ref: "#/signals/rsi_14"
      operator: ">"
      right:
        type: constant
        value: 70
    then:
      type: trade
      direction: sell
      sizing:
        type: percent_of_position
        percent: 100

constraints:
  max_positions: 5
  stop_loss:
    percent: 5
  take_profit:
    percent: 10
```

### Python Usage

```python
from utss import validate_yaml, Strategy, IndicatorSignal, ComparisonCondition

# Validate YAML
strategy = validate_yaml(yaml_content)
print(f"Strategy: {strategy.info.name}")

# Build programmatically
rsi_signal = IndicatorSignal(
    type="indicator",
    indicator="RSI",
    params={"period": 14}
)
```

## Architecture

```
Signal → Condition → Rule → Strategy
  │          │         │        │
  │          │         │        └── Complete strategy with universe, rules, constraints
  │          │         └── When (condition) → Then (action)
  │          └── Compares signals, produces boolean
  └── Produces numeric value (price, indicator, fundamental, portfolio)
```

### Signal Types

| Type | Description | Example |
|------|-------------|---------|
| `price` | Raw OHLCV data | Close price, volume |
| `indicator` | Technical indicators | RSI, MACD, SMA, BB |
| `fundamental` | Company metrics | P/E ratio, ROE |
| `portfolio` | Position state | unrealized_pnl, days_in_position |
| `calendar` | Date patterns | Day of week, month end |
| `event` | Market events | Earnings, dividends |
| `relative` | Benchmark comparison | Beta, correlation |
| `constant` | Fixed numeric value | 30, 70 |
| `expr` | Custom formula | "(close - SMA(20)) / ATR(14)" |
| `external` | Runtime signal | Webhook, ML model |

### Condition Types

| Type | Description | Example |
|------|-------------|---------|
| `comparison` | Compare two signals | RSI < 30 |
| `and` | All conditions true | RSI < 30 AND MACD > 0 |
| `or` | Any condition true | Monday OR Friday |
| `not` | Negate condition | NOT (in position) |
| `expr` | Formula expression | "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)" |
| `always` | Unconditional | For scheduled rebalancing |

Complex patterns (crossovers, ranges, temporal, sequences) are expressed via `expr` formulas. See [patterns/](./patterns/) for reusable formulas.

### Action Types

| Type | Description |
|------|-------------|
| `trade` | Buy, sell, short, or cover |
| `alert` | Send notification |
| `hold` | Explicitly do nothing |

### Sizing Methods

| Type | Description |
|------|-------------|
| `fixed_amount` | Fixed currency amount |
| `fixed_quantity` | Fixed number of shares |
| `percent_of_equity` | % of portfolio |
| `percent_of_cash` | % of available cash |
| `percent_of_position` | % of existing position |
| `risk_based` | Based on stop distance |
| `kelly` | Kelly criterion |
| `volatility_adjusted` | Target volatility |

## Supported Indicators

### Moving Averages
SMA, EMA, WMA, DEMA, TEMA, KAMA, HULL, VWMA

### Momentum
RSI, MACD, MACD_SIGNAL, MACD_HIST, STOCH_K, STOCH_D, STOCH_RSI, ROC, MOMENTUM, WILLIAMS_R, CCI, MFI, CMO, TSI

### Trend
ADX, PLUS_DI, MINUS_DI, AROON_UP, AROON_DOWN, AROON_OSC, SUPERTREND, PSAR

### Volatility
ATR, STDDEV, VARIANCE, BB_UPPER, BB_MIDDLE, BB_LOWER, BB_WIDTH, BB_PERCENT, KC_UPPER, KC_MIDDLE, KC_LOWER, DC_UPPER, DC_MIDDLE, DC_LOWER

### Volume
OBV, VWAP, AD, CMF, KLINGER

### Statistical
HIGHEST, LOWEST, RETURN, DRAWDOWN, ZSCORE, PERCENTILE, RANK, CORRELATION, BETA

### Ichimoku
ICHIMOKU_TENKAN, ICHIMOKU_KIJUN, ICHIMOKU_SENKOU_A, ICHIMOKU_SENKOU_B, ICHIMOKU_CHIKOU

## Supported Indices

### Japan (Primary)
NIKKEI225, TOPIX, TOPIX100, TOPIX500, JPXNIKKEI400, TSE_PRIME, TSE_STANDARD, TSE_GROWTH, TOPIX_LARGE70, TOPIX_MID400, TOPIX_SMALL, MOTHERS

### US
SP500, NASDAQ100, DOW30, RUSSELL2000, RUSSELL1000, SP400, SP600

### Europe
FTSE100, DAX40, CAC40, STOXX50, STOXX600

### Asia Pacific
HANG_SENG, SSE50, CSI300, KOSPI, KOSDAQ, TWSE, ASX200

### Global
MSCI_WORLD, MSCI_EM, MSCI_ACWI, MSCI_EAFE

## Parameter Optimization

Define optimizable parameters for strategy tuning:

```yaml
parameters:
  rsi_period:
    type: integer
    default: 14
    min: 5
    max: 30
    step: 1
    description: RSI calculation period

  oversold:
    type: number
    default: 30
    min: 20
    max: 40

signals:
  rsi:
    type: indicator
    indicator: RSI
    params:
      period:
        $param: rsi_period

rules:
  - name: Buy on oversold
    when:
      type: comparison
      left:
        $ref: "#/signals/rsi"
      operator: "<"
      right:
        $param: oversold
    then:
      type: trade
      direction: buy
      sizing:
        type: percent_of_equity
        percent: 10
```

## Validation

```python
from utss import validate_strategy, ValidationError

try:
    strategy = validate_strategy(data)
except ValidationError as e:
    for error in e.errors:
        print(f"{error['path']}: {error['message']}")
```

## Use Cases

1. **Backtesting Engines**: Load strategies for historical simulation
2. **Trading Platforms**: Execute strategies in paper/live trading
3. **AI/LLM Integration**: Convert natural language to executable strategies
4. **Strategy Marketplaces**: Share and distribute trading strategies
5. **Portfolio Management**: Define rebalancing and allocation rules
6. **Parameter Optimization**: Grid search or genetic optimization

## Project Structure

```
utss/
├── packages/
│   ├── utss/                    # Schema package (pip install utss)
│   │   └── src/utss/
│   │       ├── models.py        # Pydantic models
│   │       ├── validator.py     # YAML/dict validation
│   │       └── capabilities.py  # Exported capabilities for engine sync
│   │
│   └── pyutss/                  # Backtesting engine (pip install pyutss)
│       └── src/pyutss/
│           ├── data/            # Data providers (Yahoo, J-Quants)
│           ├── engine/          # Backtest execution
│           └── metrics/         # Performance metrics
│
├── schema/v1/
│   └── strategy.schema.json     # JSON Schema (source of truth)
│
├── patterns/                    # Reusable condition formulas
│   ├── crossovers.yaml
│   ├── ranges.yaml
│   ├── temporal.yaml
│   ├── price_action.yaml
│   ├── chart_patterns.yaml
│   └── momentum.yaml
│
├── examples/                    # Example strategies
│
└── docs/                        # Documentation
```

## Development

```bash
# Clone and setup
git clone https://github.com/obichan117/utss.git
cd utss

# Install dependencies (uses uv workspaces)
uv sync

# Run tests
uv run pytest

# Build docs
uv run mkdocs build
```

## License

MIT

## Documentation

- **[Quickstart Guide](./docs/quickstart.md)** - Get started in 5 minutes
- **[Architecture & Design](./docs/architecture.md)** - Design philosophy and decisions
- **[Specification](./docs/specification.md)** - Complete schema reference
- **[Examples](./examples/)** - Working strategy files

## Links

- [JSON Schema](./schema/v1/strategy.schema.json)
- [PyPI - utss](https://pypi.org/project/utss/)
- [Documentation](https://obichan117.github.io/utss/)
