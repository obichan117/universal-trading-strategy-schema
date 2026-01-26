# Examples

This page showcases complete, working strategy examples.

---

## RSI Reversal Strategy

A mean-reversion strategy that buys when RSI is oversold and sells when overbought.

```yaml
--8<-- "examples/rsi-reversal.yaml"
```

**Key Features:**

- Uses reusable `signals` and `conditions` sections
- References components with `$ref`
- Includes stop loss and take profit constraints

[:octicons-file-code-24: View on GitHub](https://github.com/obichan117/universal-trading-strategy-schema/blob/main/examples/rsi-reversal.yaml)

---

## Golden Cross Strategy

A trend-following strategy using moving average crossovers.

```yaml
--8<-- "examples/golden-cross.yaml"
```

**Key Features:**

- Uses `cross` condition type for MA crossovers
- Index-based universe (SP500)
- Trailing stop for risk management

[:octicons-file-code-24: View on GitHub](https://github.com/obichan117/universal-trading-strategy-schema/blob/main/examples/golden-cross.yaml)

---

## Earnings Play Strategy

An event-driven strategy that trades around earnings announcements.

```yaml
--8<-- "examples/earnings-play.yaml"
```

**Key Features:**

- Uses `event` signal type for earnings detection
- Screener-based universe with fundamental filters
- Risk-based position sizing with ATR

[:octicons-file-code-24: View on GitHub](https://github.com/obichan117/universal-trading-strategy-schema/blob/main/examples/earnings-play.yaml)

---

## Weekly Calendar Strategy

A calendar-based strategy that buys Monday and sells Friday.

```yaml
--8<-- "examples/monday-friday.yaml"
```

**Key Features:**

- Uses `calendar` signal type
- Simple day-of-week logic
- Specific trading days in schedule

[:octicons-file-code-24: View on GitHub](https://github.com/obichan117/universal-trading-strategy-schema/blob/main/examples/monday-friday.yaml)

---

## More Examples

### Minimal Strategy

The simplest possible valid strategy:

```yaml
info:
  id: minimal
  name: Minimal Strategy
  version: "1.0"

universe:
  type: static
  symbols: [SPY]

rules:
  - name: Always buy
    when:
      type: always
    then:
      type: trade
      direction: buy
      sizing:
        type: percent_of_equity
        percent: 100
```

### Risk Parity Portfolio

Monthly rebalancing with risk parity weights:

```yaml
info:
  id: risk_parity
  name: Risk Parity Portfolio
  version: "1.0"

universe:
  type: static
  symbols: [SPY, TLT, GLD, VNQ]

rules:
  - name: Monthly rebalance
    when:
      type: comparison
      left:
        type: calendar
        field: is_month_start
      operator: "="
      right:
        type: constant
        value: 1
    then:
      type: rebalance
      method: risk_parity
      threshold: 0.05

constraints:
  max_drawdown: 15

schedule:
  frequency: daily
```

### Parameter Optimization

Strategy with optimizable parameters:

```yaml
info:
  id: rsi_optimizable
  name: RSI with Parameters
  version: "1.0"

parameters:
  rsi_period:
    type: integer
    default: 14
    min: 5
    max: 30
    step: 1

  oversold:
    type: integer
    default: 30
    min: 20
    max: 40

  overbought:
    type: integer
    default: 70
    min: 60
    max: 80

universe:
  type: static
  symbols: [AAPL]

signals:
  rsi:
    type: indicator
    indicator: RSI
    params:
      period:
        $param: rsi_period

rules:
  - name: Buy oversold
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

  - name: Sell overbought
    when:
      type: comparison
      left:
        $ref: "#/signals/rsi"
      operator: ">"
      right:
        $param: overbought
    then:
      type: trade
      direction: sell
      sizing:
        type: percent_of_position
        percent: 100
```

### Japanese Market Momentum

Nikkei 225 momentum with hedging:

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
    params:
      period: 126
  limit: 10

signals:
  nikkei_etf_rsi:
    type: indicator
    indicator: RSI
    params:
      period: 14
    symbol: "1321.T"

rules:
  - name: Monthly rebalance
    when:
      type: comparison
      left:
        type: calendar
        field: is_month_start
      operator: "="
      right:
        type: constant
        value: 1
    then:
      type: rebalance
      method: equal_weight

  - name: Hedge when overbought
    when:
      type: comparison
      left:
        $ref: "#/signals/nikkei_etf_rsi"
      operator: ">"
      right:
        type: constant
        value: 70
    then:
      type: trade
      direction: short
      symbol: "1321.T"
      sizing:
        type: percent_of_equity
        percent: 30

constraints:
  max_positions: 11
  stop_loss:
    percent: 10

schedule:
  frequency: daily
  timezone: Asia/Tokyo
```

---

## Create Your Own

Use these examples as starting points:

1. Copy an example that's close to your idea
2. Modify the universe for your target symbols
3. Adjust the signals and conditions
4. Set appropriate constraints
5. Validate with `validate_yaml()`

See the [Quickstart Guide](quickstart.md) for step-by-step instructions.
