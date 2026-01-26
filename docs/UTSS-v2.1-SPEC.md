# UTSS v2.1 Schema Specification

**Universal Trading Strategy Schema - Complete Reference**

> This document defines the schema. Execution semantics are left to consuming applications.

---

## Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [Schema Structure](#schema-structure)
4. [Type Definitions](#type-definitions)
5. [Enumerations](#enumerations)
6. [Extensibility](#extensibility)
7. [Examples](#examples)

---

## Overview

UTSS is a declarative schema for expressing trading strategies. A valid UTSS document contains all information needed to:

- Select which assets to trade (universe)
- Compute derived values (signals)
- Define trading logic (rules)
- Specify risk limits (constraints)
- Set evaluation schedule (schedule)

```
┌─────────────────────────────────────────────────────────────┐
│                      UTSS Document                          │
├─────────────────────────────────────────────────────────────┤
│  info        │ Metadata (id, name, version, author)        │
│  universe    │ What to trade                                │
│  signals     │ Named signal definitions (optional)         │
│  conditions  │ Named condition definitions (optional)      │
│  rules       │ When/then pairs (required)                  │
│  constraints │ Risk limits (optional)                      │
│  schedule    │ Evaluation timing (optional)                │
│  parameters  │ Optimizable values (optional)               │
└─────────────────────────────────────────────────────────────┘
```

---

## Design Principles

### 1. Declarative Over Imperative
Define WHAT should happen, not HOW to compute it.

```yaml
# GOOD: Declarative
when: RSI(14) < 30
then: buy 10%

# BAD: Imperative (not supported)
for each bar:
  rsi = calculate_rsi(close, 14)
  if rsi < 30:
    buy(0.10 * equity)
```

### 2. Consistent Type Discriminators
Every complex type has a `type` field for unambiguous parsing.

```yaml
signal:
  type: indicator    # Always present
  indicator: RSI
  params: { period: 14 }
```

### 3. Composition via References
Reuse components with `$ref` instead of duplication.

```yaml
signals:
  rsi_14:
    type: indicator
    indicator: RSI
    params: { period: 14 }

rules:
  - when:
      left: { $ref: "#/signals/rsi_14" }  # Reference
      operator: "<"
      right: { type: constant, value: 30 }
```

### 4. Progressive Disclosure
Simple strategies are concise; complexity is opt-in.

```yaml
# Minimal valid strategy
info: { id: simple, version: "1.0" }
universe: { type: static, symbols: [AAPL] }
rules:
  - name: Buy
    when: { type: always }
    then: { type: trade, direction: buy, sizing: { type: percent_of_equity, percent: 100 } }
```

### 5. Execution-Agnostic
Schema defines strategy logic. Execution details (slippage, fees, broker) are out of scope.

---

## Schema Structure

### Top-Level Document

```yaml
$schema: https://utss.dev/schema/v2/strategy.json  # Optional

info:          # Required - Strategy metadata
universe:      # Required - Asset selection
signals:       # Optional - Named signal definitions
conditions:    # Optional - Named condition definitions
rules:         # Required - Trading rules (min 1)
constraints:   # Optional - Risk management
schedule:      # Optional - Evaluation timing
parameters:    # Optional - Optimizable parameters
```

### Info (Required)

```yaml
info:
  id: string              # Required. Pattern: ^[a-z0-9_-]+$
  name: string            # Required. Max 100 chars
  version: string         # Required. Pattern: ^\d+\.\d+(\.\d+)?$
  description: string     # Optional. Max 2000 chars
  author:                 # Optional
    id: string
    name: string
  tags: [string]          # Optional. Max 10 items
  created_at: datetime    # Optional. ISO 8601
  updated_at: datetime    # Optional. ISO 8601
  visibility: enum        # Optional. public | private | unlisted
```

### Universe (Required)

```yaml
# Option A: Static list
universe:
  type: static
  symbols: [string]       # Required. Min 1 item

# Option B: Index-based
universe:
  type: index
  index: StockIndex       # Required. See enums
  filters: [Condition]    # Optional. Filter criteria
  rank_by: Signal         # Optional. Ranking signal
  order: asc | desc       # Optional. Default: desc
  limit: integer          # Optional. Max symbols

# Option C: Screener
universe:
  type: screener
  base: string            # Optional. Starting universe (index or "all")
  filters: [Condition]    # Required. Min 1
  rank_by: Signal         # Optional
  order: asc | desc       # Optional
  limit: integer          # Optional

# Option D: Dual (for long-short)
universe:
  type: dual
  long:                   # Same structure as index/screener
    type: index
    index: SP500
    rank_by: Signal
    limit: 50
    direction: top
  short:
    type: index
    index: SP500
    rank_by: Signal
    limit: 50
    direction: bottom
```

### Signals (Optional)

Named signal definitions for reuse.

```yaml
signals:
  signal_name:            # Key becomes reference name
    <Signal>              # Any Signal type
```

### Conditions (Optional)

Named condition definitions for reuse.

```yaml
conditions:
  condition_name:         # Key becomes reference name
    <Condition>           # Any Condition type
```

### Rules (Required)

```yaml
rules:
  - name: string          # Required. Human-readable name
    description: string   # Optional
    when: Condition       # Required. Trigger condition
    then: Action          # Required. Action to take
    priority: integer     # Optional. Higher = evaluated first. Default: 0
    enabled: boolean      # Optional. Default: true
    regime: string        # Optional. Only active in named regime
```

### Constraints (Optional)

```yaml
constraints:
  # Position limits
  max_positions: integer          # Max concurrent positions
  min_positions: integer          # Min positions (for diversification)
  max_position_size: number       # Max % of portfolio per position (0-100)

  # Stop losses
  stop_loss:
    percent: number               # Fixed % stop
    atr_multiple: number          # ATR-based stop
  trailing_stop:
    percent: number               # Trailing % from peak
    activation_percent: number    # Activate after this profit %
    atr_multiple: number          # ATR-based trailing
  time_stop:
    bars: integer                 # Exit after N bars

  # Take profit
  take_profit:
    percent: number
    atr_multiple: number

  # Portfolio limits
  max_drawdown: number            # Stop trading at this drawdown % (0-100)
  daily_loss_limit: number        # Max daily loss % (0-100)
  max_sector_exposure: number     # Max % in single sector (0-100)
  max_correlation: number         # Max correlation between positions (0-1)

  # Restrictions
  no_shorting: boolean            # Default: false
  no_leverage: boolean            # Default: true

  # Turnover
  max_daily_turnover: number      # Max % turnover per day
  min_holding_bars: integer       # Min bars before exit allowed
```

### Schedule (Optional)

```yaml
schedule:
  frequency: Frequency            # tick|1m|5m|15m|30m|1h|4h|daily|weekly|monthly
  market_hours_only: boolean      # Default: true
  timezone: string                # Default: "America/New_York" (e.g., "Asia/Tokyo")
  trading_days: [DayOfWeek]       # Default: [monday..friday]
  evaluate_at: [string]           # Specific times: ["09:30", "15:55"]
```

### Parameters (Optional)

For parameter optimization in downstream applications.

```yaml
parameters:
  param_name:
    type: integer | number | boolean | string
    default: value                # Required
    min: number                   # For numeric types
    max: number                   # For numeric types
    step: number                  # For numeric types
    choices: [value]              # For string type
    description: string           # Optional

# Usage in signals/conditions:
signals:
  rsi:
    type: indicator
    indicator: RSI
    params:
      period: { $param: param_name }  # Reference parameter
```

---

## Type Definitions

### Signal

Produces a numeric value.

```yaml
Signal:
  oneOf:
    - PriceSignal
    - IndicatorSignal
    - FundamentalSignal
    - CalendarSignal
    - EventSignal
    - PortfolioSignal
    - ConstantSignal
    - ArithmeticSignal
    - ExpressionSignal
    - ExternalSignal
    - Reference
```

#### PriceSignal

```yaml
type: price
field: PriceField           # Required. open|high|low|close|volume|vwap
offset: integer             # Optional. Bars back (0=current). Default: 0
timeframe: Timeframe        # Optional. For MTF
symbol: string              # Optional. Cross-symbol reference
```

#### IndicatorSignal

```yaml
type: indicator
indicator: IndicatorType    # Required. See enums
params:                     # Optional. Indicator-specific
  period: integer
  fast_period: integer
  slow_period: integer
  signal_period: integer
  std_dev: number
  source: open|high|low|close|hl2|hlc3|ohlc4
offset: integer             # Optional. Default: 0
timeframe: Timeframe        # Optional
symbol: string              # Optional. Cross-symbol reference
```

#### FundamentalSignal

```yaml
type: fundamental
metric: FundamentalMetric   # Required. See enums
symbol: string              # Optional
```

#### CalendarSignal

```yaml
type: calendar
field: CalendarField        # Required
# Returns 1 if matches, 0 otherwise (or actual value for some fields)
```

CalendarField options:
- `day_of_week`: Returns 1-5 (Mon-Fri)
- `day_of_month`: Returns 1-31 (or -1 for last day)
- `week_of_month`: Returns 1-5
- `month`: Returns 1-12
- `quarter`: Returns 1-4
- `year`: Returns year number
- `is_month_start`: Returns 1 or 0
- `is_month_end`: Returns 1 or 0
- `is_quarter_start`: Returns 1 or 0
- `is_quarter_end`: Returns 1 or 0

#### EventSignal

```yaml
type: event
event: EventType            # Required. See enums
days_before: integer        # Optional. Days before event
days_after: integer         # Optional. Days after event
# Returns 1 if within window, 0 otherwise
```

#### PortfolioSignal

```yaml
type: portfolio
field: PortfolioField       # Required. See below
symbol: string              # Optional. Default: current universe symbol
```

PortfolioField options:
- `position_qty`: Current position quantity (negative for short)
- `position_value`: Current position market value
- `position_side`: 1 (long), -1 (short), 0 (flat)
- `avg_entry_price`: Volume-weighted average entry
- `unrealized_pnl`: Unrealized P/L in currency
- `unrealized_pnl_pct`: Unrealized P/L as % of entry
- `realized_pnl`: Realized P/L for session
- `days_in_position`: Calendar days since entry
- `bars_in_position`: Bars since entry
- `equity`: Total account equity
- `cash`: Available cash
- `buying_power`: Available buying power
- `daily_pnl`: Today's P/L
- `daily_pnl_pct`: Today's P/L as %

#### ConstantSignal

```yaml
type: constant
value: number               # Required
```

#### ArithmeticSignal

```yaml
type: arithmetic
operator: ArithmeticOp      # Required. add|subtract|multiply|divide|min|max|avg|abs|pow
operands: [Signal]          # Required. Min 2 items (1 for abs)
```

#### ExpressionSignal

For custom formulas not expressible with built-in types.

```yaml
type: expr
formula: string             # Required. Expression string
# Examples:
# "(SMA(close, 20) - SMA(close, 50)) / ATR(14)"
# "close / HIGHEST(close, 52)"
# "IF(RSI(14) < 30, 1, 0)"
```

Expression language supports:
- Arithmetic: `+`, `-`, `*`, `/`, `^`
- Functions: `SMA(source, period)`, `RSI(period)`, etc.
- Conditionals: `IF(condition, then, else)`
- Comparisons: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Logical: `AND`, `OR`, `NOT`

#### ExternalSignal

For runtime-resolved signals (ML models, webhooks).

```yaml
type: external
source: webhook | file | provider
url: string                 # For webhook
path: string                # For file
provider: string            # For registered provider
refresh: Frequency          # How often to refresh
default: number             # Fallback value if unavailable
```

#### Reference

```yaml
$ref: string                # JSON Pointer path
# Examples:
# "#/signals/rsi_14"
# "#/conditions/oversold"
```

---

### Condition

Produces a boolean value.

```yaml
Condition:
  oneOf:
    - ComparisonCondition
    - CrossCondition
    - RangeCondition
    - AndCondition
    - OrCondition
    - NotCondition
    - TemporalCondition
    - SequenceCondition
    - ChangeCondition
    - AlwaysCondition
    - Reference
```

#### ComparisonCondition

```yaml
type: comparison
left: Signal                # Required
operator: ComparisonOp      # Required. <|<=|=|>=|>|!=
right: Signal               # Required
```

#### CrossCondition

```yaml
type: cross
signal: Signal              # Required. The crossing signal
threshold: Signal           # Required. What it crosses
direction: above | below    # Required
```

#### RangeCondition

```yaml
type: range
signal: Signal              # Required
min: Signal                 # Required
max: Signal                 # Required
inclusive: boolean          # Optional. Default: true
```

#### AndCondition

```yaml
type: and
conditions: [Condition]     # Required. Min 2
```

#### OrCondition

```yaml
type: or
conditions: [Condition]     # Required. Min 2
```

#### NotCondition

```yaml
type: not
condition: Condition        # Required
```

#### TemporalCondition

```yaml
type: temporal
condition: Condition        # Required. Base condition
modifier: TemporalMod       # Required
bars: integer               # Required for most modifiers
n: integer                  # For nth_time modifier
```

TemporalMod options:
- `for_bars`: True if condition held for N consecutive bars
- `within_bars`: True if condition was true at least once in last N bars
- `since_bars`: True if N bars have passed since condition was last true
- `first_time`: True only the first time condition becomes true
- `nth_time`: True only the Nth time condition becomes true

#### SequenceCondition

```yaml
type: sequence
steps:                      # Required. Min 2
  - condition: Condition    # Required
    within_bars: integer    # Optional. Max bars after previous step
    min_bars: integer       # Optional. Min bars after previous step
reset_on: Condition         # Optional. Resets sequence if true
expire_bars: integer        # Optional. Sequence expires after N bars from step 1
```

#### ChangeCondition

```yaml
type: change
signal: Signal              # Required
bars: integer               # Required. Period to measure change
direction: increase | decrease | any  # Optional. Default: any
min_amount: number          # Optional. Min absolute change
min_percent: number         # Optional. Min percent change
max_amount: number          # Optional. Max absolute change
max_percent: number         # Optional. Max percent change
```

#### AlwaysCondition

```yaml
type: always
# Always evaluates to true. Useful for scheduled rebalancing.
```

---

### Action

What to do when condition is met.

```yaml
Action:
  oneOf:
    - TradeAction
    - RebalanceAction
    - AlertAction
    - HoldAction
```

#### TradeAction

```yaml
type: trade
direction: buy | sell | short | cover  # Required
symbol: string              # Optional. Default: current universe symbol
sizing: Sizing              # Required
order_type: OrderType       # Optional. Default: market
limit_price: Signal         # Optional. For limit orders
stop_price: Signal          # Optional. For stop orders
time_in_force: TimeInForce  # Optional. Default: day
```

#### RebalanceAction

```yaml
type: rebalance
method: RebalanceMethod     # Required
targets:                    # Required for target_weights method
  - symbol: string
    weight: number          # 0-1
threshold: number           # Optional. Min deviation to trigger. Default: 0.05
```

RebalanceMethod options:
- `equal_weight`: Equal allocation to all universe symbols
- `market_cap_weight`: Weight by market cap
- `risk_parity`: Weight by inverse volatility (equal risk contribution)
- `inverse_volatility`: Weight by inverse volatility
- `target_weights`: Use explicit targets

#### AlertAction

```yaml
type: alert
message: string             # Required. Supports placeholders: {symbol}, {price}, {indicator:NAME}
level: info | warning | critical  # Optional. Default: info
channels: [Channel]         # Optional. Default: [log]
throttle_minutes: integer   # Optional. Min minutes between repeated alerts
```

Channel options: `log`, `webhook`, `email`, `sms`, `telegram`, `discord`, `slack`

#### HoldAction

```yaml
type: hold
reason: string              # Optional. Explanation for why holding
```

---

### Sizing

How much to trade.

```yaml
Sizing:
  oneOf:
    - FixedAmountSizing
    - PercentEquitySizing
    - PercentPositionSizing
    - RiskBasedSizing
    - KellySizing
    - VolatilityAdjustedSizing
    - ConditionalSizing
```

#### FixedAmountSizing

```yaml
type: fixed_amount
amount: number              # Required. Currency amount
currency: string            # Optional. Default: USD
```

#### PercentEquitySizing

```yaml
type: percent_of_equity
percent: number             # Required. 0-100
```

#### PercentPositionSizing

```yaml
type: percent_of_position
percent: number             # Required. 0-100
```

#### RiskBasedSizing

```yaml
type: risk_based
risk_percent: number        # Required. % of equity to risk (0-100)
stop_distance: Signal       # Required. Distance to stop in price units
```

#### KellySizing

```yaml
type: kelly
fraction: number            # Optional. Fraction of Kelly (0-1). Default: 0.5
lookback: integer           # Optional. Bars for win rate calc. Default: 100
```

#### VolatilityAdjustedSizing

```yaml
type: volatility_adjusted
target_volatility: number   # Required. Target annualized vol
lookback: integer           # Optional. Default: 20
```

#### ConditionalSizing

```yaml
type: conditional
cases:                      # Required. Min 1
  - when: Condition
    sizing: Sizing
default: Sizing             # Required. Fallback sizing
```

---

## Enumerations

### Timeframe

```
tick | 1m | 5m | 15m | 30m | 1h | 4h | daily | weekly | monthly
```

### DayOfWeek

```
monday | tuesday | wednesday | thursday | friday
```

### PriceField

```
open | high | low | close | volume | vwap
```

### IndicatorType

**Moving Averages:**
```
SMA | EMA | WMA | DEMA | TEMA | KAMA | HULL | VWMA
```

**Momentum:**
```
RSI | MACD | MACD_SIGNAL | MACD_HIST | STOCH_K | STOCH_D | STOCH_RSI |
ROC | MOMENTUM | WILLIAMS_R | CCI | MFI | CMO | TSI
```

**Trend:**
```
ADX | PLUS_DI | MINUS_DI | AROON_UP | AROON_DOWN | AROON_OSC |
SUPERTREND | PSAR
```

**Volatility:**
```
ATR | STDDEV | VARIANCE | BB_UPPER | BB_MIDDLE | BB_LOWER | BB_WIDTH | BB_PERCENT |
KC_UPPER | KC_MIDDLE | KC_LOWER | DC_UPPER | DC_MIDDLE | DC_LOWER
```

**Volume:**
```
OBV | VWAP | AD | CMF | KLINGER
```

**Price Patterns:**
```
HIGHEST | LOWEST | RETURN | DRAWDOWN
```

**Statistical:**
```
ZSCORE | PERCENTILE | RANK | CORRELATION | BETA
```

**Ichimoku:**
```
ICHIMOKU_TENKAN | ICHIMOKU_KIJUN | ICHIMOKU_SENKOU_A | ICHIMOKU_SENKOU_B | ICHIMOKU_CHIKOU
```

### FundamentalMetric

**Valuation:**
```
PE_RATIO | PB_RATIO | PS_RATIO | PEG_RATIO | EV_EBITDA | EARNINGS_YIELD
```

**Profitability:**
```
ROE | ROA | ROIC | PROFIT_MARGIN | OPERATING_MARGIN | NET_MARGIN
```

**Dividend:**
```
DIVIDEND_YIELD | PAYOUT_RATIO
```

**Size & Growth:**
```
MARKET_CAP | ENTERPRISE_VALUE | REVENUE | EBITDA | NET_INCOME |
EPS | EPS_GROWTH | REVENUE_GROWTH
```

**Financial Health:**
```
DEBT_TO_EQUITY | CURRENT_RATIO | QUICK_RATIO | INTEREST_COVERAGE
```

**Quality:**
```
F_SCORE | ALTMAN_Z
```

**Other:**
```
INDEX_WEIGHT | FREE_FLOAT | SHORT_INTEREST | ANALYST_RATING | PRICE_TARGET |
EARNINGS_SURPRISE
```

### EventType

```
EARNINGS_RELEASE | DIVIDEND_EX_DATE | DIVIDEND_PAY_DATE | STOCK_SPLIT |
IPO | DELISTING | FDA_APPROVAL | PRODUCT_LAUNCH | INDEX_ADD | INDEX_REMOVE |
INSIDER_BUY | INSIDER_SELL | ANALYST_UPGRADE | ANALYST_DOWNGRADE |
SEC_FILING_10K | SEC_FILING_10Q | SEC_FILING_8K
```

### StockIndex

**Japan:**
```
NIKKEI225 | TOPIX | TOPIX100 | TOPIX500 | JPXNIKKEI400 |
TSE_PRIME | TSE_STANDARD | TSE_GROWTH |
TOPIX_LARGE70 | TOPIX_MID400 | TOPIX_SMALL | MOTHERS
```

**US:**
```
SP500 | NASDAQ100 | DOW30 | RUSSELL2000 | RUSSELL1000 | SP400 | SP600
```

**Europe:**
```
FTSE100 | DAX40 | CAC40 | STOXX50 | STOXX600
```

**Asia-Pacific:**
```
HANG_SENG | SSE50 | CSI300 | KOSPI | KOSDAQ | TWSE | ASX200
```

**Global:**
```
MSCI_WORLD | MSCI_EM | MSCI_ACWI | MSCI_EAFE
```

### OrderType

```
market | limit | stop | stop_limit
```

### TimeInForce

```
day | gtc | ioc | fok
```

### ComparisonOp

```
< | <= | = | >= | > | !=
```

### ArithmeticOp

```
add | subtract | multiply | divide | min | max | avg | abs | pow
```

---

## Extensibility

### Layer 1: Strict Core

All enumerated types above. Fully validated, portable across all engines.

### Layer 2: Expression Language

For signals not expressible with strict types:

```yaml
signals:
  custom:
    type: expr
    formula: "(SMA(close, 20) - SMA(close, 50)) / ATR(14)"
```

Execution engines must implement an expression parser.

### Layer 3: External Signals

For runtime-resolved values:

```yaml
signals:
  ml_prediction:
    type: external
    source: webhook
    url: "https://api.mymodel.com/predict"
    refresh: daily
    default: 0.5
```

Execution engines must implement HTTP client / file reader.

### Layer 4: x-extensions

For platform-specific metadata (ignored by schema validation):

```yaml
x-backtest:
  slippage_pct: 0.1
  commission_pct: 0.05

x-live:
  broker: sbi
  account_type: margin
```

---

## Examples

### Minimal Strategy

```yaml
info:
  id: minimal
  name: Minimal Strategy
  version: "1.0"

universe:
  type: static
  symbols: [7203.T]  # Toyota

rules:
  - name: Always hold
    when: { type: always }
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 100 }
```

### RSI Mean Reversion

```yaml
info:
  id: rsi_reversal
  name: RSI Mean Reversion
  version: "1.0"
  tags: [mean-reversion, RSI]

universe:
  type: static
  symbols: [AAPL, MSFT, GOOGL]

signals:
  rsi_14:
    type: indicator
    indicator: RSI
    params: { period: 14 }

conditions:
  oversold:
    type: comparison
    left: { $ref: "#/signals/rsi_14" }
    operator: "<"
    right: { type: constant, value: 30 }

  overbought:
    type: comparison
    left: { $ref: "#/signals/rsi_14" }
    operator: ">"
    right: { type: constant, value: 70 }

rules:
  - name: Buy oversold
    when: { $ref: "#/conditions/oversold" }
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 10 }
    priority: 1

  - name: Sell overbought
    when: { $ref: "#/conditions/overbought" }
    then:
      type: trade
      direction: sell
      sizing: { type: percent_of_position, percent: 100 }
    priority: 2

constraints:
  max_positions: 5
  stop_loss: { percent: 5 }
  take_profit: { percent: 15 }

schedule:
  frequency: daily
  market_hours_only: true
  timezone: America/New_York
```

### Nikkei Momentum with Hedge

```yaml
info:
  id: nikkei_momentum_hedged
  name: Nikkei 225 Momentum with RSI Hedge
  version: "1.0"
  tags: [japan, momentum, hedged]

parameters:
  momentum_lookback:
    type: integer
    default: 126
    min: 60
    max: 252
  top_n:
    type: integer
    default: 5
    min: 3
    max: 10
  hedge_rsi_threshold:
    type: integer
    default: 70
    min: 60
    max: 80

universe:
  type: index
  index: NIKKEI225
  rank_by:
    type: indicator
    indicator: RETURN
    params: { period: { $param: momentum_lookback } }
  limit: { $param: top_n }

signals:
  nikkei_etf_rsi:
    type: indicator
    indicator: RSI
    params: { period: 14 }
    symbol: 1321.T

conditions:
  etf_overbought:
    type: comparison
    left: { $ref: "#/signals/nikkei_etf_rsi" }
    operator: ">"
    right: { type: constant, value: { $param: hedge_rsi_threshold } }

  etf_recovered:
    type: comparison
    left: { $ref: "#/signals/nikkei_etf_rsi" }
    operator: "<"
    right: { type: constant, value: 50 }

  not_hedged:
    type: comparison
    left: { type: portfolio, field: position_qty, symbol: 1321.T }
    operator: "="
    right: { type: constant, value: 0 }

  is_hedged:
    type: comparison
    left: { type: portfolio, field: position_qty, symbol: 1321.T }
    operator: "<"
    right: { type: constant, value: 0 }

rules:
  - name: Monthly rebalance
    when:
      type: calendar
      field: is_month_start
    then:
      type: rebalance
      method: equal_weight
    priority: 1

  - name: Activate hedge
    when:
      type: and
      conditions:
        - { $ref: "#/conditions/etf_overbought" }
        - { $ref: "#/conditions/not_hedged" }
    then:
      type: trade
      direction: short
      symbol: 1321.T
      sizing: { type: percent_of_equity, percent: 30 }
    priority: 2

  - name: Remove hedge
    when:
      type: and
      conditions:
        - { $ref: "#/conditions/etf_recovered" }
        - { $ref: "#/conditions/is_hedged" }
    then:
      type: trade
      direction: cover
      symbol: 1321.T
      sizing: { type: percent_of_position, percent: 100 }
    priority: 3

constraints:
  max_positions: 6
  stop_loss: { percent: 10 }
  no_leverage: false

schedule:
  frequency: daily
  market_hours_only: true
  timezone: Asia/Tokyo
```

### Risk Parity Portfolio

```yaml
info:
  id: risk_parity
  name: Risk Parity Portfolio
  version: "1.0"
  tags: [portfolio, risk-parity]

universe:
  type: static
  symbols: [SPY, TLT, GLD, VNQ]

rules:
  - name: Monthly risk parity rebalance
    when:
      type: calendar
      field: is_month_start
    then:
      type: rebalance
      method: risk_parity
      threshold: 0.05

constraints:
  max_drawdown: 15

schedule:
  frequency: daily
  timezone: America/New_York
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2024-01 | Initial release with signals, conditions, rules |
| 2.1.0 | 2024-01 | Portfolio signals, expressions, parameters, extended indicators/indices, alerts |

---

## References

- JSON Schema Draft-07: https://json-schema.org/draft-07/schema
- ISO 8601 Datetime: https://en.wikipedia.org/wiki/ISO_8601
- IANA Timezone Database: https://www.iana.org/time-zones
