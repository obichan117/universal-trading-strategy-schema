# Changelog

All notable changes to the Universal Trading Strategy Schema.

---

## [1.0.0] - 2024-01

### Overview

UTSS v1.0 is a **clean, minimal design** with 6 condition types and an `expr` escape hatch for complex patterns.

### Design Philosophy

- **Minimal Primitives**: Only 6 condition types (comparison, and, or, not, expr, always)
- **expr for Complexity**: Crossovers, ranges, temporal patterns via formula expressions
- **No Sugar Bloat**: Avoids unbounded type additions
- **LLM-Friendly**: Predictable structure, clear type discriminators

### Signal Types

| Type | Description |
|------|-------------|
| `price` | Raw OHLCV data |
| `indicator` | 50+ technical indicators (SMA, RSI, MACD, etc.) |
| `fundamental` | 30+ company metrics (PE_RATIO, ROE, etc.) |
| `calendar` | Date patterns (day_of_week, is_month_end, etc.) |
| `event` | Market events (EARNINGS_RELEASE, DIVIDEND_EX_DATE, etc.) |
| `portfolio` | Position state (unrealized_pnl, days_in_position, etc.) |
| `constant` | Fixed numeric values |
| `expr` | Custom formula expressions |
| `external` | Runtime signals (webhook, file, provider) |

### Condition Types (Minimal Primitives)

| Type | Description | Example |
|------|-------------|---------|
| `comparison` | Compare signals | `RSI < 30` |
| `and` | All must be true | `RSI < 30 AND MACD > 0` |
| `or` | Any must be true | `Monday OR Friday` |
| `not` | Negate condition | `NOT in_position` |
| `expr` | Formula expression | `"SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"` |
| `always` | Unconditional | For scheduled rebalancing |

Complex patterns (crossovers, ranges, temporal, sequences) are expressed via `expr` formulas.
See `patterns/` directory for reusable formula library.

### Action Types

- **TradeAction** - Buy, sell, short, cover with various sizing methods
- **AlertAction** - Notifications via log, webhook, email, telegram, etc.
- **HoldAction** - Explicitly do nothing

### Sizing Types

- `fixed_amount`, `fixed_quantity`, `percent_of_equity`, `percent_of_cash`, `percent_of_position`
- `risk_based`, `kelly`, `volatility_adjusted`

### Universe Types

- `static` - Fixed symbol list
- `index` - Index members with filters/ranking (deprecated; use screener with base instead)
- `screener` - Dynamic screening (preferred for index-based strategies)

### Other Features

- **Parameters** - Optimizable values with `$param` references
- **Constraints** - Stop loss, take profit, trailing stop, position limits
- **Schedule** - Evaluation frequency, market hours, timezone
- **Execution** - Slippage/commission models as strategy design decisions
- **Extensibility** - `custom:`, `talib:`, `platform:` prefixes for extensions

---

## Versioning

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible schema changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

Schema version is specified in strategy documents:

```yaml
$schema: https://obichan117.github.io/universal-trading-strategy-schema/schema/v1/strategy.json
```
