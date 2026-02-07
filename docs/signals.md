# Signal Types Guide

Signals are the atomic building blocks of any UTSS strategy. A signal produces a **numeric value at each point in time** (a pandas Series aligned to your OHLCV data). Conditions compare signals, rules trigger actions when conditions are met.

This guide covers every signal type, when to use it, and how the types relate to each other.

---

## Signal Type Taxonomy

UTSS defines **9 data-source types** and **3 composition types**:

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA SOURCE TYPES                          │
│  (where the numeric value comes from)                           │
├─────────────────────────────────────────────────────────────────┤
│  price       │ The asset's own OHLCV market data                │
│  indicator   │ Computed from price data (RSI, SMA, MACD, etc.)  │
│  fundamental │ Company/asset metrics (PE_RATIO, ROE, etc.)      │
│  calendar    │ Functions of the date/time itself                 │
│  event       │ Discrete occurrences with dates                  │
│  portfolio   │ Current state of positions and equity             │
│  constant    │ A literal numeric value                           │
│  expr        │ Custom formula over other signals                 │
│  external    │ Anything from outside the system                  │
├─────────────────────────────────────────────────────────────────┤
│                     COMPOSITION TYPES                            │
│  (reference another signal or parameter)                        │
├─────────────────────────────────────────────────────────────────┤
│  $ref        │ Pointer to a named signal in the strategy        │
│  $param      │ Pointer to an optimizable parameter              │
└─────────────────────────────────────────────────────────────────┘
```

### Design Principles

**Primitive and Exhaustive.** Each data-source type represents a fundamentally different *origin* of data. There are no overlaps in where the data comes from:

| Type | Data Origin | Updates |
|------|-------------|---------|
| `price` | Exchange/market feed | Every bar |
| `indicator` | Computed from `price` | Every bar |
| `fundamental` | Financial statements, analyst estimates | Quarterly/ad-hoc |
| `calendar` | The clock/calendar | Deterministic |
| `event` | Corporate actions, economic calendar | Irregular |
| `portfolio` | Your own positions and account | Every bar |
| `constant` | The strategy definition itself | Never |
| `expr` | Formula combining other signals | Every bar |
| `external` | Anything else (ML models, webhooks, files) | Varies |

`external` is the **escape hatch** that makes the list exhaustive. Any data source not covered by the other 8 types can be injected as an external signal.

---

## Data Source Types

### `price` — Market Data

The most fundamental signal type. Returns raw OHLCV data for the asset being evaluated.

```yaml
signals:
  closing_price:
    type: price
    field: close     # open | high | low | close | volume | vwap

  high_low_midpoint:
    type: price
    field: hl2       # Computed: (high + low) / 2
```

**Fields:** `open`, `high`, `low`, `close`, `volume`, `vwap`, `hl2`, `hlc3`, `ohlc4`

**When to use:**

- Comparing price to a level: `close > 100`
- Volume-based conditions: `volume > 1000000`
- As input to conditions: `close >= high` (breakout)

**When NOT to use:**

- If you need a moving average of price, use `indicator` instead
- If you need a formula like `(close - open) / open`, use `expr` instead

---

### `indicator` — Technical Indicators

Computed from price data using well-known formulas. UTSS supports 60+ indicators across 7 categories.

```yaml
signals:
  rsi_14:
    type: indicator
    indicator: RSI
    params:
      period: 14

  sma_cross_fast:
    type: indicator
    indicator: SMA
    params:
      period: 50
      source: close   # Which price field to compute on

  bb_upper:
    type: indicator
    indicator: BB_UPPER
    params:
      period: 20
      std_dev: 2.0
```

**Categories:**

| Category | Indicators |
|----------|-----------|
| Moving Averages | SMA, EMA, WMA, DEMA, TEMA, KAMA, HULL, VWMA |
| Momentum | RSI, MACD, MACD_SIGNAL, MACD_HIST, STOCH_K, STOCH_D, ROC, CCI, MFI, CMO, TSI, WILLIAMS_R, STOCH_RSI, MOMENTUM |
| Volatility | ATR, STDDEV, VARIANCE, BB_UPPER/MIDDLE/LOWER/WIDTH/PERCENT, KC_UPPER/MIDDLE/LOWER, DC_UPPER/MIDDLE/LOWER |
| Trend | ADX, PLUS_DI, MINUS_DI, AROON_UP/DOWN/OSC, SUPERTREND, PSAR |
| Volume | OBV, VWAP, AD, CMF, KLINGER |
| Statistical | HIGHEST, LOWEST, RETURN, DRAWDOWN, ZSCORE, PERCENTILE, RANK, CORRELATION, BETA |
| Ichimoku | ICHIMOKU_TENKAN/KIJUN/SENKOU_A/SENKOU_B/CHIKOU |

**When to use:**

- Standard technical analysis: RSI overbought/oversold, MA crossovers, Bollinger Band breakouts
- Any well-known formula that takes price as input and produces a single numeric series

**When NOT to use:**

- For custom formulas not in the indicator list, use `expr` instead
- For raw price comparisons, use `price` directly

**Extensibility:** Custom indicators can be added via prefixes:

- `custom:MY_INDICATOR` — User-defined
- `talib:CDLHAMMER` — TA-Lib candlestick patterns
- `platform:tradingview:SQUEEZE` — Platform-specific

---

### `fundamental` — Company Metrics

Point-in-time company financial data. Returns a constant value across all bars (fundamentals don't change every bar).

```yaml
signals:
  pe_ratio:
    type: fundamental
    metric: PE_RATIO

  cross_symbol_roe:
    type: fundamental
    metric: ROE
    symbol: MSFT     # Look up a different symbol's fundamentals
```

**Supported metrics (30+):**

| Category | Metrics |
|----------|---------|
| Valuation | PE_RATIO, PB_RATIO, PS_RATIO, PEG_RATIO, EV_EBITDA, EARNINGS_YIELD |
| Profitability | ROE, ROA, ROIC, PROFIT_MARGIN, OPERATING_MARGIN, NET_MARGIN |
| Dividend | DIVIDEND_YIELD, PAYOUT_RATIO |
| Size | MARKET_CAP, ENTERPRISE_VALUE, REVENUE, EBITDA, NET_INCOME |
| Growth | EPS, EPS_GROWTH, REVENUE_GROWTH |
| Solvency | DEBT_TO_EQUITY, CURRENT_RATIO, QUICK_RATIO, INTEREST_COVERAGE |
| Quality | F_SCORE, ALTMAN_Z |
| Market | INDEX_WEIGHT, FREE_FLOAT, SHORT_INTEREST, ANALYST_RATING, PRICE_TARGET, EARNINGS_SURPRISE |

**When to use:**

- Value investing screens: `PE_RATIO < 15`
- Quality filters: `ROE > 0.15 AND DEBT_TO_EQUITY < 1.0`
- Screener universes with fundamental filters

**When NOT to use:**

- For price-derived metrics (like historical returns), use `indicator` with `RETURN`
- For fundamental data that needs complex transformations, use `external` with pre-processed data

**How to provide data:** Pass `fundamental_data` to `EvaluationContext`:

```python
ctx = EvaluationContext(
    primary_data=ohlcv_df,
    fundamental_data={
        "AAPL": {"pe_ratio": 28.5, "roe": 0.175, "market_cap": 2.8e12}
    },
)
```

---

### `calendar` — Date Patterns

Functions of the date/time. Deterministic — no external data needed.

```yaml
signals:
  day_of_week:
    type: calendar
    field: day_of_week    # Monday=0, Friday=4

  is_month_end:
    type: calendar
    field: is_month_end   # 1 on last trading day of month, 0 otherwise
```

**Fields:**

| Field | Returns | Example Values |
|-------|---------|----------------|
| `day_of_week` | Integer 0-4 | Mon=0, Tue=1, ..., Fri=4 |
| `day_of_month` | Integer 1-31 | 1, 2, ..., 31 |
| `month` | Integer 1-12 | Jan=1, ..., Dec=12 |
| `is_month_start` | 0 or 1 | 1 on first trading day of month |
| `is_month_end` | 0 or 1 | 1 on last trading day of month |
| `is_quarter_end` | 0 or 1 | 1 on last trading day of quarter |

**When to use:**

- Day-of-week effects: "Buy on Monday, sell on Friday"
- Month-end rebalancing: "Rebalance on last trading day"
- Seasonal strategies: "Sell in May and go away"

**When NOT to use:**

- For event-driven timing (earnings, dividends), use `event` instead
- For complex date logic, use `expr` with date formulas

---

### `event` — Market Events

Discrete occurrences that happen on specific dates. Returns 1 within a configurable window around the event, 0 otherwise.

```yaml
signals:
  near_earnings:
    type: event
    event: EARNINGS_RELEASE
    days_before: 5    # Signal = 1 for 5 days before earnings
    days_after: 1     # Signal = 1 for 1 day after earnings
```

**Core event types:**

| Category | Events |
|----------|--------|
| Earnings | EARNINGS_RELEASE |
| Dividends | DIVIDEND_EX_DATE, DIVIDEND_PAY_DATE |
| Corporate | STOCK_SPLIT, IPO, DELISTING |
| Regulatory | FDA_APPROVAL, SEC_FILING_10K/10Q/8K |
| Market | INDEX_ADD, INDEX_REMOVE, PRODUCT_LAUNCH |
| Insider | INSIDER_BUY, INSIDER_SELL |
| Analyst | ANALYST_UPGRADE, ANALYST_DOWNGRADE |

**When to use:**

- Earnings plays: "Buy 3 days before earnings if RSI < 40"
- Dividend capture: "Buy before ex-dividend date"
- Event avoidance: "Don't hold through earnings"

**When NOT to use:**

- For recurring calendar patterns (month-end, day-of-week), use `calendar`
- For events your system generates (ML predictions), use `external`

**How to provide data:** Pass `event_data` to `EvaluationContext`:

```python
import datetime

ctx = EvaluationContext(
    primary_data=ohlcv_df,
    event_data={
        "EARNINGS_RELEASE": [
            datetime.date(2024, 1, 25),
            datetime.date(2024, 4, 25),
            datetime.date(2024, 7, 25),
        ],
    },
)
```

---

### `portfolio` — Position State

Current state of your portfolio. Values update as the backtest engine processes each bar.

```yaml
signals:
  current_pnl:
    type: portfolio
    field: unrealized_pnl

  position_in_aapl:
    type: portfolio
    field: position_value
    symbol: AAPL          # Check specific symbol
```

**Fields:**

| Field | Description |
|-------|-------------|
| `unrealized_pnl` | Open position P&L |
| `realized_pnl` | Closed trade P&L |
| `cash` | Available cash |
| `equity` | Total account value |
| `position_size` | Number of shares held |
| `position_value` | Dollar value of position |
| `days_in_position` | Days since entry |
| `exposure` | Position value as % of equity |
| `win_rate` | Winning trades / total trades (%) |
| `total_trades` | Number of completed trades |
| `has_position` | 1 if holding, 0 if flat |

**When to use:**

- Profit targets: "Sell if unrealized_pnl > 10%"
- Time stops: "Exit if days_in_position > 20"
- Position management: "Don't buy if has_position = 1"

**When NOT to use:**

- For price-based stops (trailing stop, ATR stop), use `constraints` section instead
- These are better expressed as constraint rules, not signal conditions

---

### `constant` — Fixed Values

A literal numeric value. Useful as the right side of comparisons.

```yaml
conditions:
  rsi_oversold:
    type: comparison
    left: { $ref: "#/signals/rsi_14" }
    operator: "<"
    right:
      type: constant
      value: 30             # Can also reference a parameter:
      # value: $param.rsi_threshold
```

**When to use:**

- Threshold comparisons: `RSI < 30`, `PE_RATIO > 25`
- Any fixed number in a condition

**When NOT to use:**

- If the value should be optimizable, use `$param` reference instead

---

### `expr` — Custom Formulas

Arbitrary mathematical expressions that can reference price fields and indicators.

```yaml
signals:
  custom_momentum:
    type: expr
    formula: "(close - SMA(20)) / ATR(14)"

  price_change:
    type: expr
    formula: "(close - open) / open * 100"
```

**When to use:**

- Custom indicators not in the built-in list
- Combining multiple indicators: `"(RSI(14) + RSI(28)) / 2"`
- Price ratios and spreads: `"close / SMA(200)"`
- Any formula that doesn't fit the other types

**When NOT to use:**

- If a built-in indicator already computes what you need, prefer `indicator` (clearer, cached, validated)
- For simple price field access, use `price` (more explicit)

---

### `external` — Outside Data

The escape hatch for any data that doesn't fit the other types. Data is pre-loaded into the evaluation context.

```yaml
signals:
  ml_prediction:
    type: external
    source: provider
    provider: my_ml_model
    default: 0.0           # Fallback when data is missing

  sentiment_score:
    type: external
    source: file
    path: sentiment_data
    default: 0.5
```

**When to use:**

- ML model predictions
- Sentiment scores from NLP pipelines
- Alternative data (satellite, web traffic, social media)
- Data from external APIs or webhooks
- Pre-computed signals from other systems
- Macro data (interest rates, GDP) not in the fundamental metrics list

**When NOT to use:**

- For company fundamentals (PE_RATIO, ROE), use `fundamental` (better semantics)
- For calendar events (earnings dates), use `event` (has window logic built in)
- For standard technical indicators, use `indicator` (validated, cached)

**How to provide data:** Pass `external_data` to `EvaluationContext`:

```python
ctx = EvaluationContext(
    primary_data=ohlcv_df,
    external_data={
        "my_ml_model": pd.Series([0.8, 0.3, 0.6, ...], index=ohlcv_df.index),
        "sentiment_data": sentiment_series,  # Will be reindexed to match
    },
)
```

External series are automatically aligned to the primary data index. Missing dates are filled with the `default` value.

---

## Composition Types

### `$ref` — Signal References

Refer to a named signal defined in the strategy's `signals` section. Avoids duplication.

```yaml
signals:
  rsi_14:
    type: indicator
    indicator: RSI
    params: { period: 14 }

conditions:
  oversold:
    type: comparison
    left: { $ref: "#/signals/rsi_14" }    # Reuse the signal
    operator: "<"
    right: { type: constant, value: 30 }
```

### `$param` — Parameter References

Reference an optimizable parameter defined in the strategy's `parameters` section.

```yaml
parameters:
  rsi_period:
    type: integer
    default: 14
    min: 5
    max: 30

signals:
  rsi:
    type: indicator
    indicator: RSI
    params:
      period: $param.rsi_period           # Resolved at runtime
```

---

## Decision Flowchart

Use this to pick the right signal type:

```
Is the data from the asset's own price/volume?
├── Yes → Is it raw OHLCV?
│         ├── Yes → price
│         └── No (computed) → indicator
└── No → Is it from the company's financials?
          ├── Yes → fundamental
          └── No → Is it purely a function of the date?
                    ├── Yes (recurring pattern) → calendar
                    ├── Yes (specific dates) → event
                    └── No → Is it from your own portfolio state?
                              ├── Yes → portfolio
                              └── No → Is it a fixed number?
                                        ├── Yes → constant
                                        └── No → Is it a formula over other signals?
                                                  ├── Yes → expr
                                                  └── No → external
```

---

## Common Patterns

### Combining Multiple Signal Types

Real strategies often combine several signal types:

```yaml
signals:
  rsi_14:
    type: indicator
    indicator: RSI
    params: { period: 14 }

  near_earnings:
    type: event
    event: EARNINGS_RELEASE
    days_before: 5

conditions:
  buy_signal:
    type: and
    conditions:
      # Technical: RSI oversold
      - type: comparison
        left: { $ref: "#/signals/rsi_14" }
        operator: "<"
        right: { type: constant, value: 30 }
      # Calendar: Not on a Friday
      - type: comparison
        left: { type: calendar, field: day_of_week }
        operator: "<"
        right: { type: constant, value: 4 }
      # Event: Not near earnings
      - type: comparison
        left: { $ref: "#/signals/near_earnings" }
        operator: "="
        right: { type: constant, value: 0 }
```

### Cross-Asset Comparison via `expr`

To compare one asset against a benchmark (e.g., relative strength), use `expr`:

```yaml
signals:
  # Price relative to benchmark (requires benchmark data in context)
  price_vs_benchmark:
    type: expr
    formula: "close / SMA(200)"    # Simple relative strength
```

For more complex cross-asset analysis, pre-compute the comparison externally and inject via `external`:

```python
# Pre-compute beta, correlation, etc.
beta_series = compute_rolling_beta(asset_returns, benchmark_returns, window=60)

ctx = EvaluationContext(
    primary_data=ohlcv_df,
    external_data={"asset_beta": beta_series},
)
```

```yaml
signals:
  asset_beta:
    type: external
    source: provider
    provider: asset_beta
```

### Using Fundamentals in Screeners

```yaml
universe:
  type: screener
  base: SP500
  filters:
    - type: comparison
      left: { type: fundamental, metric: PE_RATIO }
      operator: "<"
      right: { type: constant, value: 20 }
    - type: comparison
      left: { type: fundamental, metric: ROE }
      operator: ">"
      right: { type: constant, value: 0.15 }
  rank_by:
    type: fundamental
    metric: DIVIDEND_YIELD
  order: desc
  limit: 20
```
