# UTSS Quickstart Guide

Get started with the Universal Trading Strategy Schema in 5 minutes.

---

## Installation

```bash
pip install utss
# or
uv add utss
```

---

## Your First Strategy

Create a file `my_strategy.yaml`:

```yaml
info:
  id: my_first_strategy
  name: My First Strategy
  version: "1.0"

universe:
  type: static
  symbols:
    - AAPL

rules:
  - name: Buy signal
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
```

---

## Validate Your Strategy

```python
from utss import validate_yaml

with open("my_strategy.yaml") as f:
    strategy = validate_yaml(f.read())

print(f"Loaded: {strategy.info.name}")
print(f"Trading: {strategy.universe.symbols}")
print(f"Rules: {len(strategy.rules)}")
```

---

## Building Blocks

### Signals (Numbers)

Signals produce numeric values. Use them to represent market data.

```yaml
# Price data
close_price:
  type: price
  field: close

# Technical indicator
rsi_14:
  type: indicator
  indicator: RSI
  params:
    period: 14

# Fundamental data
pe_ratio:
  type: fundamental
  metric: PE_RATIO

# Portfolio state
unrealized_pnl:
  type: portfolio
  field: unrealized_pnl_pct

# Fixed value
threshold:
  type: constant
  value: 30
```

### Conditions (True/False)

Conditions combine signals to produce boolean values.

```yaml
# Comparison
oversold:
  type: comparison
  left: { $ref: "#/signals/rsi_14" }
  operator: "<"
  right: { type: constant, value: 30 }

# Crossover
golden_cross:
  type: cross
  signal: { type: indicator, indicator: SMA, params: { period: 50 } }
  threshold: { type: indicator, indicator: SMA, params: { period: 200 } }
  direction: above

# Range
neutral_zone:
  type: range
  signal: { $ref: "#/signals/rsi_14" }
  min: { type: constant, value: 40 }
  max: { type: constant, value: 60 }

# Logical AND
buy_setup:
  type: and
  conditions:
    - { $ref: "#/conditions/oversold" }
    - { $ref: "#/conditions/volume_spike" }
```

### Actions (What to Do)

Actions define what happens when conditions are met.

```yaml
# Trade
buy_action:
  type: trade
  direction: buy
  sizing:
    type: percent_of_equity
    percent: 10

# Rebalance
monthly_rebalance:
  type: rebalance
  method: equal_weight
  threshold: 0.05

# Alert
send_alert:
  type: alert
  message: "RSI oversold on {symbol}!"
  level: warning
  channels: [telegram, log]
```

---

## Common Patterns

### Pattern 1: Mean Reversion (RSI)

```yaml
info:
  id: rsi_mean_reversion
  name: RSI Mean Reversion
  version: "1.0"

universe:
  type: static
  symbols: [AAPL, MSFT, GOOGL]

signals:
  rsi:
    type: indicator
    indicator: RSI
    params: { period: 14 }

rules:
  - name: Buy oversold
    when:
      type: comparison
      left: { $ref: "#/signals/rsi" }
      operator: "<"
      right: { type: constant, value: 30 }
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 10 }

  - name: Sell overbought
    when:
      type: comparison
      left: { $ref: "#/signals/rsi" }
      operator: ">"
      right: { type: constant, value: 70 }
    then:
      type: trade
      direction: sell
      sizing: { type: percent_of_position, percent: 100 }

constraints:
  stop_loss: { percent: 5 }
  take_profit: { percent: 15 }
```

### Pattern 2: Trend Following (Moving Average Crossover)

```yaml
info:
  id: golden_cross
  name: Golden Cross
  version: "1.0"

universe:
  type: index
  index: SP500
  limit: 50

signals:
  sma_fast:
    type: indicator
    indicator: SMA
    params: { period: 50 }
  sma_slow:
    type: indicator
    indicator: SMA
    params: { period: 200 }

rules:
  - name: Buy on golden cross
    when:
      type: cross
      signal: { $ref: "#/signals/sma_fast" }
      threshold: { $ref: "#/signals/sma_slow" }
      direction: above
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 5 }

  - name: Sell on death cross
    when:
      type: cross
      signal: { $ref: "#/signals/sma_fast" }
      threshold: { $ref: "#/signals/sma_slow" }
      direction: below
    then:
      type: trade
      direction: sell
      sizing: { type: percent_of_position, percent: 100 }

constraints:
  trailing_stop: { percent: 10 }
```

### Pattern 3: Monthly Rebalancing

```yaml
info:
  id: monthly_rebalance
  name: Monthly Equal Weight
  version: "1.0"

universe:
  type: static
  symbols: [SPY, TLT, GLD, VNQ]

rules:
  - name: Monthly rebalance
    when:
      type: comparison
      left: { type: calendar, field: is_month_start }
      operator: "="
      right: { type: constant, value: 1 }
    then:
      type: rebalance
      method: equal_weight
      threshold: 0.05

schedule:
  frequency: daily
```

### Pattern 4: Risk-Based Position Sizing

```yaml
rules:
  - name: Buy with risk management
    when: { $ref: "#/conditions/entry_signal" }
    then:
      type: trade
      direction: buy
      sizing:
        type: risk_based
        risk_percent: 1  # Risk 1% of portfolio per trade
        stop_distance:
          type: indicator
          indicator: ATR
          params: { period: 14 }
```

### Pattern 5: Exit on Profit Target

```yaml
signals:
  pnl:
    type: portfolio
    field: unrealized_pnl_pct

rules:
  - name: Take profit at 20%
    when:
      type: comparison
      left: { $ref: "#/signals/pnl" }
      operator: ">="
      right: { type: constant, value: 20 }
    then:
      type: trade
      direction: sell
      sizing: { type: percent_of_position, percent: 100 }
```

---

## Parameter Optimization

Make your strategy optimizable:

```yaml
parameters:
  rsi_period:
    type: integer
    default: 14
    min: 5
    max: 30
    step: 1
    description: RSI calculation period

  oversold_threshold:
    type: integer
    default: 30
    min: 20
    max: 40
    description: RSI oversold level

signals:
  rsi:
    type: indicator
    indicator: RSI
    params:
      period: { $param: rsi_period }  # Reference parameter

rules:
  - name: Buy oversold
    when:
      type: comparison
      left: { $ref: "#/signals/rsi" }
      operator: "<"
      right: { $param: oversold_threshold }  # Reference parameter
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 10 }
```

---

## Japanese Market Example

```yaml
info:
  id: nikkei_momentum
  name: Nikkei 225 Momentum
  version: "1.0"
  tags: [japan, momentum]

universe:
  type: index
  index: NIKKEI225
  rank_by:
    type: indicator
    indicator: RETURN
    params: { period: 126 }  # 6-month return
  limit: 10  # Top 10 momentum stocks

rules:
  - name: Monthly rebalance
    when:
      type: comparison
      left: { type: calendar, field: is_month_start }
      operator: "="
      right: { type: constant, value: 1 }
    then:
      type: rebalance
      method: equal_weight

constraints:
  max_positions: 10
  stop_loss: { percent: 10 }

schedule:
  frequency: daily
  timezone: Asia/Tokyo
```

---

## Next Steps

1. **Read the [Architecture Guide](architecture.md)** - Understand design philosophy
2. **Browse [Examples](examples.md)** - See complete strategy files
3. **Read the [Specification](specification.md)** - Full reference documentation
4. **Build your own strategy** - Start with a simple idea, add complexity gradually

---

## Common Mistakes

### 1. Missing `type` field

```yaml
# Wrong
when:
  left: { indicator: RSI }  # Missing type!

# Correct
when:
  left:
    type: indicator  # Always include type
    indicator: RSI
```

### 2. Wrong reference path

```yaml
# Wrong
$ref: "#/components/signals/rsi"  # Old v1.0 path

# Correct (v1.0)
$ref: "#/signals/rsi"  # Direct path
```

### 3. Missing required fields

```yaml
# Wrong - missing operator
when:
  type: comparison
  left: { ... }
  right: { ... }

# Correct
when:
  type: comparison
  left: { ... }
  operator: "<"  # Required!
  right: { ... }
```

---

## Getting Help

- **Validation errors**: Use `validate_yaml()` to get detailed error messages
- **Examples**: Check the `examples/` directory for working strategies
- **Specification**: See [specification.md](specification.md) for complete reference
