"""Few-shot examples and enhanced prompts for strategy generation."""

from utss_llm.prompts import SYSTEM_PROMPT

# Few-shot examples for better LLM output
FEW_SHOT_EXAMPLES = """
## Example 1: RSI Reversal

User: "RSI reversal strategy for tech stocks. Buy when oversold, sell when overbought."

```yaml
info:
  id: rsi_reversal
  name: RSI Reversal Strategy
  version: "1.0"
  description: Mean-reversion strategy using RSI(14) thresholds.
  tags: [reversal, RSI, mean-reversion]

universe:
  type: static
  symbols: [AAPL, MSFT, GOOGL]

signals:
  rsi_14:
    type: indicator
    indicator: RSI
    params:
      period: 14

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

  - name: Sell overbought
    when: { $ref: "#/conditions/overbought" }
    then:
      type: trade
      direction: sell
      sizing: { type: percent_of_position, percent: 100 }

constraints:
  max_positions: 5
  stop_loss: { percent: 5 }
  no_shorting: true
```

## Example 2: Golden Cross

User: "Moving average crossover strategy on SPY. Enter when 50-day crosses above 200-day."

```yaml
info:
  id: golden_cross
  name: Golden Cross Strategy
  version: "1.0"
  description: Trend-following strategy using SMA 50/200 crossover.
  tags: [trend, moving-average, crossover]

universe:
  type: static
  symbols: [SPY]

rules:
  - name: Golden Cross Entry
    when:
      type: expr
      formula: "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 100 }

  - name: Death Cross Exit
    when:
      type: expr
      formula: "SMA(50)[-1] >= SMA(200)[-1] and SMA(50) < SMA(200)"
    then:
      type: trade
      direction: sell
      sizing: { type: percent_of_position, percent: 100 }

constraints:
  trailing_stop: { percent: 10 }
```

## Example 3: Calendar Strategy

User: "Buy SPY every Monday, sell Friday."

```yaml
info:
  id: weekly_momentum
  name: Weekly Momentum Strategy
  version: "1.0"
  description: Calendar-based strategy trading the weekly cycle.
  tags: [calendar, momentum, weekly]

universe:
  type: static
  symbols: [SPY]

signals:
  day_of_week:
    type: calendar
    field: day_of_week

rules:
  - name: Monday Entry
    when:
      type: comparison
      left: { $ref: "#/signals/day_of_week" }
      operator: "="
      right: { type: constant, value: 0 }
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 50 }

  - name: Friday Exit
    when:
      type: comparison
      left: { $ref: "#/signals/day_of_week" }
      operator: "="
      right: { type: constant, value: 4 }
    then:
      type: trade
      direction: sell
      sizing: { type: percent_of_position, percent: 100 }

constraints:
  no_shorting: true

schedule:
  frequency: daily
  trading_days: [monday, friday]
```
"""

# Enhanced system prompt with schema details
ENHANCED_SYSTEM_PROMPT = SYSTEM_PROMPT + """

## UTSS v1.0 Condition Types (IMPORTANT - only use these):
- comparison: { type: comparison, left: signal, operator: "<|<=|=|>=|>|!=", right: signal }
- and: { type: and, conditions: [...] }
- or: { type: or, conditions: [...] }
- not: { type: not, condition: {...} }
- expr: { type: expr, formula: "..." } - For crossovers, ranges, complex patterns
- always: { type: always } - For unconditional rules

## Signal Types:
- price: { type: price, field: close|open|high|low|volume|vwap }
- indicator: { type: indicator, indicator: SMA|EMA|RSI|MACD|BB|ATR|..., params: {...} }
- fundamental: { type: fundamental, metric: PE_RATIO|MARKET_CAP|... }
- calendar: { type: calendar, field: day_of_week|is_month_end|... }
- event: { type: event, event_type: EARNINGS_RELEASE|DIVIDEND_EX_DATE|... }
- portfolio: { type: portfolio, field: unrealized_pnl|days_in_position|equity|... }
- constant: { type: constant, value: number }
- expr: { type: expr, formula: "..." } - Inline formula as signal
- external: { type: external, source: webhook|file|provider, ... }
- $ref: { $ref: "#/signals/my_signal" } - Reference to a defined signal
- $param: { $param: "param_name" } - Reference to a strategy parameter

## Common expr formulas:
- Crossover: "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"
- RSI range: "RSI(14) >= 40 and RSI(14) <= 60"
- Breakout: "close > BB(20, 2).upper"
- MACD signal cross: "MACD(12,26,9)[-1] <= MACD_SIGNAL(12,26,9)[-1] and MACD(12,26,9) > MACD_SIGNAL(12,26,9)"
- Normalized difference: "(close - SMA(20)) / ATR(14)"
- Consecutive bars: "RSI(14) > 50 and RSI(14)[-1] > 50 and RSI(14)[-2] > 50"
- Combined conditions: "ADX(14) > 25 and close > SMA(200) and RSI(14) < 70"

## Sizing Types (all 8):
- percent_of_equity: { type: percent_of_equity, percent: 10 }
- percent_of_cash: { type: percent_of_cash, percent: 20 }
- percent_of_position: { type: percent_of_position, percent: 100 }
- fixed_amount: { type: fixed_amount, amount: 10000, currency: "USD" }
- fixed_quantity: { type: fixed_quantity, quantity: 100 }
- risk_based: { type: risk_based, risk_percent: 1, stop_distance: <signal> }
- kelly: { type: kelly, fraction: 0.5, lookback: 100 }
- volatility_adjusted: { type: volatility_adjusted, target_volatility: 0.15, lookback: 20 }

## Constraints:
- max_positions: 5
- stop_loss: { percent: 5 } or { atr_multiple: 2 }
- take_profit: { percent: 15 } or { atr_multiple: 3 }
- trailing_stop: { percent: 10, activation_percent: 5 }
- max_drawdown: 20
- daily_loss_limit: 5
- no_shorting: true
- no_leverage: true
- min_holding_bars: 5

## References ($ref) and Parameters ($param):
- Define reusable signals: signals: { rsi_14: { type: indicator, indicator: RSI, params: { period: 14 } } }
- Reference them: when: { left: { $ref: "#/signals/rsi_14" }, ... }
- Define parameters: parameters: { rsi_period: { type: integer, default: 14, min: 5, max: 30 } }
- Use in signals: params: { period: { $param: "rsi_period" } }

## Required fields:
- info.id (lowercase with underscores)
- info.name
- info.version (e.g., "1.0")
- universe.type and universe.symbols (for static)
- At least one rule with when and then

""" + FEW_SHOT_EXAMPLES

__all__ = [
    "FEW_SHOT_EXAMPLES",
    "ENHANCED_SYSTEM_PROMPT",
]
