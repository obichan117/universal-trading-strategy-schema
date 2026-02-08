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
- price: { type: price, field: close|open|high|low|volume }
- indicator: { type: indicator, indicator: SMA|EMA|RSI|MACD|BB|ATR|..., params: {...} }
- calendar: { type: calendar, field: day_of_week|is_month_end|... }
- constant: { type: constant, value: number }
- $ref: Reference to defined signals/conditions

## Common expr formulas:
- Crossover: "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"
- RSI range: "RSI(14) >= 40 and RSI(14) <= 60"
- Breakout: "close > BB(20, 2).upper"

## Sizing Types:
- percent_of_equity: { type: percent_of_equity, percent: 10 }
- percent_of_position: { type: percent_of_position, percent: 100 }
- fixed_amount: { type: fixed_amount, amount: 10000 }

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
