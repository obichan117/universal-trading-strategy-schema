# Universal Trading Strategy Schema

A comprehensive, composable schema for expressing any trading strategy.

<div class="grid cards" markdown>

-   :material-clock-fast:{ .lg .middle } __Get Started in 5 Minutes__

    ---

    Install `utss` and create your first strategy

    [:octicons-arrow-right-24: Quickstart](quickstart.md)

-   :material-architecture:{ .lg .middle } __Understand the Design__

    ---

    Learn the architecture and design philosophy

    [:octicons-arrow-right-24: Architecture](architecture.md)

-   :material-file-document:{ .lg .middle } __Full Reference__

    ---

    Complete schema specification

    [:octicons-arrow-right-24: Specification](specification.md)

-   :material-code-tags:{ .lg .middle } __Python API__

    ---

    Pydantic models and validation

    [:octicons-arrow-right-24: API Reference](api.md)

</div>

---

## What is UTSS?

UTSS (Universal Trading Strategy Schema) is a **declarative schema** for expressing trading strategies. Instead of writing imperative code, you describe **what** your strategy does, and execution engines handle the **how**.

```yaml
# A complete trading strategy in YAML
info:
  id: rsi_reversal
  name: RSI Reversal Strategy
  version: "1.0"

universe:
  type: static
  symbols: [AAPL, MSFT, GOOGL]

rules:
  - name: Buy on oversold
    when:
      type: comparison
      left:
        type: indicator
        indicator: RSI
        params: { period: 14 }
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

## Why UTSS?

### The Problem

Trading strategies are typically expressed in:

| Format | Problem |
|--------|---------|
| **Imperative Code** | Tied to specific language/platform, hard to validate |
| **Natural Language** | Ambiguous, no validation, different interpretations |
| **Platform DSLs** | Vendor lock-in, limited expressiveness, not portable |

### The Solution

UTSS provides a **universal, declarative schema** that is:

- **Portable** - Same strategy works with any compliant engine
- **Validated** - Schema validation catches errors before execution
- **LLM-Friendly** - Designed for natural language → strategy conversion
- **Self-Contained** - Complete strategy in one document

---

## Core Concepts

```
Signal → Condition → Rule → Strategy
  │          │         │        │
  │          │         │        └── Complete trading system
  │          │         └── When (condition) → Then (action)
  │          └── Boolean expression (RSI < 30 = true/false)
  └── Numeric value (RSI = 45.2)
```

| Concept | What it does | Example |
|---------|--------------|---------|
| **Signal** | Produces a number | `RSI(14) = 45.2` |
| **Condition** | Produces true/false | `RSI < 30 = true` |
| **Rule** | When/then pair | If oversold, buy |
| **Strategy** | Complete system | Universe + rules + constraints |

---

## Features

### Signal Types

- **Price** - OHLCV data (`close`, `volume`)
- **Indicator** - Technical indicators (`RSI`, `MACD`, `SMA`)
- **Fundamental** - Company metrics (`PE_RATIO`, `ROE`)
- **Portfolio** - Position state (`unrealized_pnl`, `days_in_position`)
- **Calendar** - Date patterns (`day_of_week`, `is_month_end`)
- **Event** - Market events (`EARNINGS_RELEASE`)
- **Expression** - Custom formulas (`(close - SMA(20)) / ATR(14)`)
- **External** - Runtime signals (webhook, ML model)

### Condition Types

- **Comparison** - `RSI < 30`
- **Cross** - `SMA(50) crosses above SMA(200)`
- **Range** - `20 < RSI < 80`
- **Temporal** - `RSI < 30 for 3 bars`
- **Sequence** - `A then B within 5 bars`
- **Logical** - `AND`, `OR`, `NOT`

### Action Types

- **Trade** - Buy, sell, short, cover
- **Rebalance** - Adjust to target weights
- **Alert** - Send notifications

### Sizing Methods

- **Fixed Amount** - `$10,000`
- **Percent of Equity** - `10%`
- **Risk-Based** - `1% risk with ATR stop`
- **Kelly Criterion** - Optimal sizing
- **Conditional** - Different sizing by regime

---

## Supported Markets

### Japan (Primary Focus)

`NIKKEI225`, `TOPIX`, `TOPIX100`, `TOPIX500`, `JPXNIKKEI400`, `TSE_PRIME`, `TSE_STANDARD`, `TSE_GROWTH`

### US

`SP500`, `NASDAQ100`, `DOW30`, `RUSSELL2000`, `RUSSELL1000`

### Europe

`FTSE100`, `DAX40`, `CAC40`, `STOXX50`, `STOXX600`

### Asia Pacific

`HANG_SENG`, `SSE50`, `CSI300`, `KOSPI`, `ASX200`

### Global

`MSCI_WORLD`, `MSCI_EM`, `MSCI_ACWI`, `MSCI_EAFE`

---

## Quick Installation

=== "pip"

    ```bash
    pip install utss
    ```

=== "uv"

    ```bash
    uv add utss
    ```

=== "poetry"

    ```bash
    poetry add utss
    ```

---

## Quick Validation

```python
from utss import validate_yaml

yaml_content = """
info:
  id: my_strategy
  name: My Strategy
  version: "1.0"

universe:
  type: static
  symbols: [AAPL]

rules:
  - name: Buy signal
    when:
      type: always
    then:
      type: trade
      direction: buy
      sizing:
        type: percent_of_equity
        percent: 100
"""

strategy = validate_yaml(yaml_content)
print(f"Loaded: {strategy.info.name}")
```

---

## Use Cases

| Application | How UTSS Helps |
|-------------|----------------|
| **LLM Agents** | Natural language → validated strategy |
| **Backtesting** | Load strategy, simulate on historical data |
| **Parameter Optimization** | Extract parameters, run grid search |
| **Live Trading** | Same strategy, real execution |
| **Strategy Marketplace** | Share and distribute strategies |

---

## Next Steps

<div class="grid cards" markdown>

-   [:material-rocket-launch: __Quickstart__](quickstart.md)

    Create your first strategy

-   [:material-book-open-variant: __Examples__](examples.md)

    Browse working strategies

-   [:material-cog: __Architecture__](architecture.md)

    Understand the design

-   [:material-api: __API Reference__](api.md)

    Python types and validation

</div>
