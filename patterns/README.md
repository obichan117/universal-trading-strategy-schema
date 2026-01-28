# UTSS Pattern Library

Reusable condition patterns for common trading scenarios. Import via `$ref` in your strategies.

## Design Philosophy

The UTSS v1.0 schema has **minimal condition types**:
- `comparison` - primitive: `a op b`
- `and` / `or` / `not` - boolean composition
- `expr` - formula for complex patterns
- `always` - constant true

All common patterns (crossovers, ranges, temporal, chart patterns) are implemented as **reusable formulas** in this library.

## Usage

```yaml
# Reference a pattern
conditions:
  golden_cross:
    $ref: "utss://patterns/crossovers#cross_above"
    params:
      fast: SMA(50)
      slow: SMA(200)

# Or use the formula directly
conditions:
  golden_cross:
    type: expr
    formula: "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"
```

## Pattern Categories

| File | Patterns |
|------|----------|
| [crossovers.yaml](./crossovers.yaml) | `cross_above`, `cross_below` |
| [ranges.yaml](./ranges.yaml) | `in_range`, `out_of_range`, `overbought`, `oversold` |
| [temporal.yaml](./temporal.yaml) | `for_n_bars`, `within_n_bars`, `first_time` |
| [price_action.yaml](./price_action.yaml) | `higher_high`, `lower_low`, `higher_low`, `lower_high` |
| [chart_patterns.yaml](./chart_patterns.yaml) | `double_bottom`, `double_top`, `breakout` |
| [momentum.yaml](./momentum.yaml) | `bullish_divergence`, `bearish_divergence` |

## Formula Syntax

Patterns use the UTSS expression language:

```
# Operators
and, or, not          # Boolean
<, <=, =, >=, >, !=   # Comparison
+, -, *, /            # Arithmetic

# Time offset (bars back)
close[-1]             # Previous bar's close
SMA(20)[-3]           # SMA value 3 bars ago

# Functions
all(cond, bars=N)     # True if cond was true for N consecutive bars
any(cond, bars=N)     # True if cond was true at least once in N bars
count(cond, bars=N)   # Count of bars where cond was true
highest(sig, bars=N)  # Highest value in N bars
lowest(sig, bars=N)   # Lowest value in N bars
```
