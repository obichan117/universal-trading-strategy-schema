# Universal Trading Strategy Schema (UTSS)

A comprehensive, composable schema for expressing any trading strategy. Define your strategies in YAML/JSON and use them across different trading platforms, backtesting engines, and execution systems.

## Features

- **Composable Architecture**: Signal → Condition → Rule → Strategy hierarchy
- **Multi-Language Support**: TypeScript and Python bindings
- **LLM-Friendly**: Designed for natural language → strategy conversion
- **Reusable Components**: Define signals and conditions once, reference everywhere
- **Comprehensive**: Supports technical indicators, fundamental data, calendar patterns, and events

## Installation

### TypeScript/JavaScript

```bash
npm install utss
# or
pnpm add utss
```

### Python

```bash
pip install utss
# or
uv add utss
```

## Quick Start

### YAML Strategy Definition

```yaml
$schema: https://utss.dev/schema/v2/strategy.json

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

rules:
  - name: Buy on oversold
    when:
      type: comparison
      left:
        type: indicator
        indicator: RSI
        params:
          period: 14
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
        type: indicator
        indicator: RSI
        params:
          period: 14
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

### TypeScript Usage

```typescript
import { validateYAML, Strategy, indicator, compare, buy, percentOfEquity } from 'utss';

// Validate YAML
const result = validateYAML(yamlContent);
if (result.valid) {
  const strategy: Strategy = result.strategy;
  console.log(`Strategy: ${strategy.info.name}`);
}

// Build programmatically
const rsiSignal = indicator('RSI', { period: 14 });
const oversold = compare(rsiSignal, '<', 30);
const buyAction = buy(percentOfEquity(10));
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
  └── Produces numeric value (price, indicator, fundamental)
```

### Signal Types

| Type | Description | Example |
|------|-------------|---------|
| `price` | Raw OHLCV data | Close price, volume |
| `indicator` | Technical indicators | RSI, MACD, SMA, BB |
| `fundamental` | Company metrics | P/E ratio, ROE |
| `calendar` | Date patterns | Day of week, month end |
| `event` | Market events | Earnings, dividends |
| `relative` | Benchmark comparison | Beta, correlation |
| `constant` | Fixed numeric value | 30, 70 |
| `arithmetic` | Math operations | SMA(20) - SMA(50) |

### Condition Types

| Type | Description | Example |
|------|-------------|---------|
| `comparison` | Compare two signals | RSI < 30 |
| `cross` | Signal crossing threshold | SMA crosses above price |
| `range` | Signal within bounds | 20 < RSI < 80 |
| `and` | All conditions true | RSI < 30 AND MACD > 0 |
| `or` | Any condition true | Monday OR Friday |
| `not` | Negate condition | NOT (in position) |
| `temporal` | Time-based | RSI < 30 for 3 bars |

### Action Types

| Type | Description |
|------|-------------|
| `trade` | Buy, sell, short, or cover |
| `rebalance` | Adjust to target weights |
| `hold` | Explicitly do nothing |

### Sizing Methods

| Type | Description |
|------|-------------|
| `fixed_amount` | Fixed dollar amount |
| `percent_of_equity` | % of portfolio |
| `percent_of_position` | % of existing position |
| `risk_based` | Based on stop distance |
| `kelly` | Kelly criterion |
| `volatility_adjusted` | Target volatility |

## Supported Indicators

### Moving Averages
SMA, EMA, WMA, DEMA, TEMA

### Momentum
RSI, MACD, MACD_SIGNAL, MACD_HIST, STOCH_K, STOCH_D, STOCH_RSI

### Volatility
BB_UPPER, BB_MIDDLE, BB_LOWER, BB_WIDTH, BB_PERCENT, ATR, ADX, PLUS_DI, MINUS_DI

### Volume & Other
CCI, MFI, OBV, VWAP, SUPERTREND, ICHIMOKU_*

## Reusable Components

Define signals and conditions once, reference them by name:

```yaml
components:
  signals:
    rsi_14:
      type: indicator
      indicator: RSI
      params:
        period: 14
    sma_20:
      type: indicator
      indicator: SMA
      params:
        period: 20

  conditions:
    oversold:
      type: comparison
      left:
        $ref: "#/components/signals/rsi_14"
      operator: "<"
      right:
        type: constant
        value: 30

rules:
  - name: Buy signal
    when:
      $ref: "#/components/conditions/oversold"
    then:
      type: trade
      direction: buy
      sizing:
        type: percent_of_equity
        percent: 10
```

## Schema Validation

### TypeScript

```typescript
import Ajv from 'ajv';
import schema from 'utss/schema';

const ajv = new Ajv();
const validate = ajv.compile(schema);

if (!validate(strategyData)) {
  console.error(validate.errors);
}
```

### Python

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

## License

MIT

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## Links

- [JSON Schema](./schema/v2/strategy.schema.json)
- [TypeScript Package](./typescript/)
- [Python Package](./python/)
- [Examples](./docs/examples/)
