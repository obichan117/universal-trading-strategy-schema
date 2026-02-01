# Python API Reference

The `utss` package provides Pydantic models for all schema types and validation utilities.

---

## Installation

```bash
pip install utss
```

---

## Quick Start

```python
from utss import validate_yaml, Strategy

# Validate YAML
strategy = validate_yaml(yaml_content)

# Access strategy components
print(strategy.info.name)
print(strategy.universe.symbols)
print(len(strategy.rules))
```

---

## Validation Functions

### validate_yaml

Validate a YAML string and return a Strategy object.

```python
from utss import validate_yaml, ValidationError

yaml_content = """
info:
  id: my_strategy
  name: My Strategy
  version: "1.0"
universe:
  type: static
  symbols: [AAPL]
rules:
  - name: Buy
    when: { type: always }
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 100 }
"""

try:
    strategy = validate_yaml(yaml_content)
    print(f"Valid strategy: {strategy.info.name}")
except ValidationError as e:
    for error in e.errors:
        print(f"Error: {error}")
```

### validate_strategy

Validate a dictionary and return a Strategy object.

```python
from utss import validate_strategy

data = {
    "info": {"id": "test", "name": "Test", "version": "1.0"},
    "universe": {"type": "static", "symbols": ["AAPL"]},
    "rules": [
        {
            "name": "Buy",
            "when": {"type": "always"},
            "then": {
                "type": "trade",
                "direction": "buy",
                "sizing": {"type": "percent_of_equity", "percent": 100}
            }
        }
    ]
}

strategy = validate_strategy(data)
```

---

## Core Models

### Strategy

The top-level strategy model.

```python
from utss import Strategy

class Strategy:
    info: Info                              # Required
    universe: Universe                      # Required
    signals: dict[str, Signal] | None       # Optional
    conditions: dict[str, Condition] | None # Optional
    rules: list[Rule]                       # Required (min 1)
    constraints: Constraints | None         # Optional
    schedule: Schedule | None               # Optional
    parameters: dict[str, Parameter] | None # Optional
```

### Info

Strategy metadata.

```python
from utss import Info, Author, Visibility

info = Info(
    id="my_strategy",           # Required, pattern: ^[a-z0-9_-]+$
    name="My Strategy",         # Required, max 100 chars
    version="1.0",              # Required, pattern: ^\d+\.\d+(\.\d+)?$
    description="Description",  # Optional, max 2000 chars
    author=Author(id="user", name="User Name"),  # Optional
    tags=["momentum", "japan"], # Optional, max 10
    visibility=Visibility.PRIVATE  # public | private | unlisted
)
```

---

## Signal Types

All signal types produce numeric values.

### PriceSignal

```python
from utss import PriceSignal, PriceField

signal = PriceSignal(
    type="price",
    field=PriceField.CLOSE,  # open|high|low|close|volume|vwap
    offset=0,                 # Bars back (0=current)
    timeframe="daily",        # Optional, for MTF
    symbol="AAPL"             # Optional, cross-symbol
)
```

### IndicatorSignal

```python
from utss import IndicatorSignal, IndicatorType, IndicatorParams

signal = IndicatorSignal(
    type="indicator",
    indicator=IndicatorType.RSI,
    params=IndicatorParams(period=14),
    offset=0,
    timeframe=None,
    symbol=None
)
```

### FundamentalSignal

```python
from utss import FundamentalSignal, FundamentalMetric

signal = FundamentalSignal(
    type="fundamental",
    metric=FundamentalMetric.PE_RATIO
)
```

### PortfolioSignal

```python
from utss import PortfolioSignal, PortfolioField

signal = PortfolioSignal(
    type="portfolio",
    field=PortfolioField.UNREALIZED_PNL_PCT,
    symbol=None  # Optional, default: current symbol
)
```

### CalendarSignal

```python
from utss import CalendarSignal, CalendarField

signal = CalendarSignal(
    type="calendar",
    field=CalendarField.DAY_OF_WEEK  # Returns 1-5 (Mon-Fri)
)
```

### ConstantSignal

```python
from utss import ConstantSignal

signal = ConstantSignal(
    type="constant",
    value=30.0
)
```

### ArithmeticSignal

```python
from utss import ArithmeticSignal, ArithmeticOperator

signal = ArithmeticSignal(
    type="arithmetic",
    operator=ArithmeticOperator.SUBTRACT,
    operands=[sma_20_signal, sma_50_signal]
)
```

### ExpressionSignal

```python
from utss import ExpressionSignal

signal = ExpressionSignal(
    type="expr",
    formula="(close - SMA(close, 20)) / ATR(14)"
)
```

### ExternalSignal

```python
from utss import ExternalSignal, ExternalSource

signal = ExternalSignal(
    type="external",
    source=ExternalSource.WEBHOOK,
    url="https://api.example.com/signal",
    refresh="daily",
    default=0.5
)
```

---

## Condition Types

All condition types produce boolean values.

### ComparisonCondition

```python
from utss import ComparisonCondition, ComparisonOperator

condition = ComparisonCondition(
    type="comparison",
    left=rsi_signal,
    operator=ComparisonOperator.LT,  # < | <= | = | >= | > | !=
    right=ConstantSignal(type="constant", value=30)
)
```

### AndCondition / OrCondition

```python
from utss import AndCondition, OrCondition

and_cond = AndCondition(
    type="and",
    conditions=[condition1, condition2]  # Min 2
)

or_cond = OrCondition(
    type="or",
    conditions=[condition1, condition2]
)
```

### NotCondition

```python
from utss import NotCondition

condition = NotCondition(
    type="not",
    condition=overbought_condition
)
```

### ExpressionCondition

For complex patterns like crossovers, ranges, and temporal conditions, use the `expr` type
with a formula string. This provides maximum flexibility with minimal primitives.

```python
from utss import ExpressionCondition

# Golden cross: SMA(50) crosses above SMA(200)
condition = ExpressionCondition(
    type="expr",
    formula="SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"
)

# RSI in range
condition = ExpressionCondition(
    type="expr",
    formula="RSI(14) >= 40 and RSI(14) <= 60"
)

# Price breakout
condition = ExpressionCondition(
    type="expr",
    formula="close > BB(20, 2).upper"
)
```

See `patterns/` directory for reusable formula templates for common patterns like:
- Crossovers: `patterns/crossovers.yaml`
- Ranges: `patterns/ranges.yaml`
- Temporal: `patterns/temporal.yaml`

### AlwaysCondition

```python
from utss import AlwaysCondition

condition = AlwaysCondition(type="always")
```

---

## Action Types

### TradeAction

```python
from utss import TradeAction, TradeDirection, OrderType, TimeInForce

action = TradeAction(
    type="trade",
    direction=TradeDirection.BUY,  # buy|sell|short|cover
    sizing=PercentEquitySizing(type="percent_of_equity", percent=10),
    symbol=None,                   # Optional, default: current
    order_type=OrderType.MARKET,   # market|limit|stop|stop_limit
    time_in_force=TimeInForce.DAY  # day|gtc|ioc|fok
)
```

### RebalanceAction

```python
from utss import RebalanceAction, RebalanceMethod

action = RebalanceAction(
    type="rebalance",
    method=RebalanceMethod.EQUAL_WEIGHT,  # equal_weight|market_cap_weight|risk_parity|inverse_volatility|target_weights
    threshold=0.05
)
```

### AlertAction

```python
from utss import AlertAction, AlertLevel, AlertChannel

action = AlertAction(
    type="alert",
    message="RSI oversold on {symbol}!",
    level=AlertLevel.WARNING,  # info|warning|critical
    channels=[AlertChannel.LOG, AlertChannel.TELEGRAM],
    throttle_minutes=60
)
```

---

## Sizing Types

### PercentEquitySizing

```python
from utss import PercentEquitySizing

sizing = PercentEquitySizing(
    type="percent_of_equity",
    percent=10.0  # 0-100
)
```

### RiskBasedSizing

```python
from utss import RiskBasedSizing

sizing = RiskBasedSizing(
    type="risk_based",
    risk_percent=1.0,  # Risk 1% of portfolio
    stop_distance=atr_signal  # ATR(14) for stop distance
)
```

### ConditionalSizing

```python
from utss import ConditionalSizing, ConditionalSizingCase

sizing = ConditionalSizing(
    type="conditional",
    cases=[
        ConditionalSizingCase(
            when=high_volatility_condition,
            sizing=PercentEquitySizing(type="percent_of_equity", percent=5)
        )
    ],
    default=PercentEquitySizing(type="percent_of_equity", percent=10)
)
```

---

## Universe Types

### StaticUniverse

```python
from utss import StaticUniverse

universe = StaticUniverse(
    type="static",
    symbols=["AAPL", "MSFT", "GOOGL"]
)
```

### IndexUniverse

```python
from utss import IndexUniverse, StockIndex

universe = IndexUniverse(
    type="index",
    index=StockIndex.NIKKEI225,
    rank_by=momentum_signal,  # Optional
    order="desc",             # asc|desc
    limit=10                  # Optional
)
```

### DualUniverse

```python
from utss import DualUniverse, DualUniverseSide

universe = DualUniverse(
    type="dual",
    long=DualUniverseSide(
        index=StockIndex.SP500,
        rank_by=momentum_signal,
        limit=50
    ),
    short=DualUniverseSide(
        index=StockIndex.SP500,
        rank_by=momentum_signal,
        order="asc",
        limit=50
    )
)
```

---

## Enums

### Indicators

```python
from utss import IndicatorType

# Moving Averages
IndicatorType.SMA, IndicatorType.EMA, IndicatorType.WMA, IndicatorType.KAMA, IndicatorType.HULL

# Momentum
IndicatorType.RSI, IndicatorType.MACD, IndicatorType.STOCH_K, IndicatorType.ROC, IndicatorType.CCI

# Volatility
IndicatorType.ATR, IndicatorType.BB_UPPER, IndicatorType.BB_LOWER, IndicatorType.KC_UPPER

# Volume
IndicatorType.OBV, IndicatorType.VWAP, IndicatorType.CMF

# Statistical
IndicatorType.ZSCORE, IndicatorType.PERCENTILE, IndicatorType.CORRELATION
```

### Stock Indices

```python
from utss import StockIndex

# Japan
StockIndex.NIKKEI225, StockIndex.TOPIX, StockIndex.TSE_PRIME

# US
StockIndex.SP500, StockIndex.NASDAQ100, StockIndex.DOW30

# Europe
StockIndex.FTSE100, StockIndex.DAX40

# Global
StockIndex.MSCI_WORLD, StockIndex.MSCI_EM
```

---

## Parameter System

```python
from utss import Parameter, ParameterType, ParameterReference

# Define parameter
param = Parameter(
    type=ParameterType.INTEGER,
    default=14,
    min=5,
    max=30,
    step=1,
    description="RSI period"
)

# Reference in signal (YAML uses $param)
# In Python, use ParameterReference
```

---

## Complete Example

```python
from utss import (
    Strategy, Info, StaticUniverse, Rule,
    IndicatorSignal, IndicatorType, IndicatorParams,
    ComparisonCondition, ComparisonOperator,
    ConstantSignal, TradeAction, TradeDirection,
    PercentEquitySizing, Constraints, StopConfig
)

strategy = Strategy(
    info=Info(
        id="rsi_reversal",
        name="RSI Reversal",
        version="1.0"
    ),
    universe=StaticUniverse(
        type="static",
        symbols=["AAPL", "MSFT"]
    ),
    rules=[
        Rule(
            name="Buy oversold",
            when=ComparisonCondition(
                type="comparison",
                left=IndicatorSignal(
                    type="indicator",
                    indicator=IndicatorType.RSI,
                    params=IndicatorParams(period=14)
                ),
                operator=ComparisonOperator.LT,
                right=ConstantSignal(type="constant", value=30)
            ),
            then=TradeAction(
                type="trade",
                direction=TradeDirection.BUY,
                sizing=PercentEquitySizing(
                    type="percent_of_equity",
                    percent=10
                )
            )
        )
    ],
    constraints=Constraints(
        max_positions=5,
        stop_loss=StopConfig(percent=5)
    )
)

# Convert to dict/JSON
print(strategy.model_dump_json(indent=2))
```
