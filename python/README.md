# UTSS - Universal Trading Strategy Schema (Python)

Python implementation of the Universal Trading Strategy Schema v2.1.

## Installation

```bash
pip install utss
# or
uv add utss
```

## Quick Start

```python
from utss import validate_yaml, Strategy

# Validate a YAML strategy
yaml_content = """
info:
  id: my_strategy
  name: My Strategy
  version: "1.0"

universe:
  type: static
  symbols:
    - AAPL

signals:
  rsi_14:
    type: indicator
    indicator: RSI
    params:
      period: 14

rules:
  - name: Buy signal
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
"""

strategy = validate_yaml(yaml_content)
print(f"Strategy: {strategy.info.name}")
print(f"Rules: {len(strategy.rules)}")
```

## Models

All schema types are available as Pydantic models:

```python
from utss import (
    Strategy,
    Rule,
    IndicatorSignal,
    PortfolioSignal,
    ComparisonCondition,
    SequenceCondition,
    TradeAction,
    AlertAction,
    PercentEquitySizing,
    ConditionalSizing,
    Parameter,
)

# Build programmatically
signal = IndicatorSignal(
    type="indicator",
    indicator="RSI",
    params={"period": 14}
)

# Portfolio state signal (v2.1)
portfolio_signal = PortfolioSignal(
    type="portfolio",
    field="unrealized_pnl_pct"
)

condition = ComparisonCondition(
    type="comparison",
    left=signal,
    operator="<",
    right={"type": "constant", "value": 30}
)

# Alert action (v2.1)
alert = AlertAction(
    type="alert",
    message="RSI oversold alert!",
    level="warning",
    channels=["log", "telegram"]
)
```

## v2.1 Features

### Portfolio Signals
Access position and portfolio state:
- `position_qty`, `position_value`, `position_side`
- `unrealized_pnl`, `unrealized_pnl_pct`, `realized_pnl`
- `days_in_position`, `bars_in_position`
- `equity`, `cash`, `buying_power`, `margin_used`
- `daily_pnl`, `daily_pnl_pct`

### New Condition Types
- `sequence`: Detect ordered patterns
- `change`: Detect signal changes over time
- `always`: Always true (for scheduled actions)

### New Action Types
- `alert`: Send notifications with configurable channels

### Parameter Optimization
```python
from utss import Parameter

param = Parameter(
    type="integer",
    default=14,
    min=5,
    max=30,
    step=1,
    description="RSI period"
)
```

### Extended Indicators
50+ indicators including KAMA, HULL, ROC, Aroon, Keltner Channels, Donchian Channels

### Extended Indices
30+ indices with focus on Japanese markets (NIKKEI225, TOPIX, TSE_PRIME, etc.)

## Validation

```python
from utss import validate_strategy, ValidationError

try:
    strategy = validate_strategy(data_dict)
except ValidationError as e:
    for error in e.errors:
        print(f"{error['path']}: {error['message']}")
```

## License

MIT
