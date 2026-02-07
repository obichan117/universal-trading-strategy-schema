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
- **Expression** - `SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)` (crossovers, ranges, temporal patterns)
- **Logical** - `AND`, `OR`, `NOT`
- **Always** - Unconditional (for scheduled actions)

### Action Types

- **Trade** - Buy, sell, short, cover
- **Alert** - Send notifications

### Sizing Methods

- **Fixed Amount** - `$10,000`
- **Fixed Quantity** - `100 shares`
- **Percent of Equity** - `10%`
- **Percent of Cash** - `20% of available cash`
- **Risk-Based** - `1% risk with ATR stop`
- **Kelly Criterion** - Optimal sizing

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

## Packages

| Package | Description | Install |
|---------|-------------|---------|
| `utss` | Core schema and validation | `pip install utss` |
| `pyutss` | Backtesting engine | `pip install pyutss` |
| `utss-llm` | Conversational strategy builder | `pip install utss-llm` |
| `utss-mcp` | Claude Code MCP server | `pip install utss-mcp` |

## Quick Installation

=== "pip"

    ```bash
    pip install utss           # Schema only
    pip install pyutss         # With backtesting
    pip install utss-mcp       # For Claude Code
    ```

=== "uv"

    ```bash
    uv add utss
    uv add pyutss
    uv add utss-mcp
    ```

=== "poetry"

    ```bash
    poetry add utss
    poetry add pyutss
    poetry add utss-mcp
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

## Claude Code Integration

Build strategies interactively with Claude Code using the MCP server:

```json
// Add to ~/.claude/mcp.json
{
  "mcpServers": {
    "utss": { "command": "utss-mcp" }
  }
}
```

Then in Claude Code:

```
You: Help me build a mean reversion RSI strategy

Claude: [uses build_strategy tool]
        What type of strategy? 1) Mean Reversion 2) Trend Following...

You: 1

Claude: [continues guided conversation...]
```

The MCP server provides:

- **build_strategy** - Interactive guided builder
- **validate_strategy** - Schema validation
- **backtest_strategy** - Run simulations
- **list_indicators** - Available indicators

---

## Use Cases

| Application | How UTSS Helps |
|-------------|----------------|
| **LLM Agents** | Natural language → validated strategy |
| **Claude Code** | MCP server with interactive builder |
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
