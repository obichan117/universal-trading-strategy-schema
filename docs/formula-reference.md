# Formula Reference

UTSS supports a powerful expression language for defining conditions using the `expr` type. This reference documents the complete syntax and available functions.

## Expression Syntax

Expressions are strings that evaluate to boolean values. They support:

- **Comparisons**: `>`, `<`, `>=`, `<=`, `==`, `!=`
- **Logical operators**: `and`, `or`, `not`
- **Parentheses**: `(...)` for grouping
- **Historical indexing**: `[-1]`, `[-2]`, etc.

### Basic Example

```yaml
conditions:
  golden_cross:
    type: expr
    formula: "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"
```

## Price Fields

Access OHLCV data directly:

| Field | Description |
|-------|-------------|
| `close` | Closing price |
| `open` | Opening price |
| `high` | High price |
| `low` | Low price |
| `volume` | Trading volume |
| `hl2` | (high + low) / 2 |
| `hlc3` | (high + low + close) / 3 |
| `ohlc4` | (open + high + low + close) / 4 |

### Examples

```yaml
# Price above yesterday's high
formula: "close > high[-1]"

# Volume spike
formula: "volume > SMA(volume, 20) * 2"

# Price in upper half of range
formula: "close > hl2"
```

## Historical Indexing

Access previous values using bracket notation:

| Syntax | Meaning |
|--------|---------|
| `close[-1]` | Yesterday's close |
| `SMA(20)[-1]` | Yesterday's SMA(20) |
| `RSI(14)[-5]` | RSI value 5 days ago |

!!! note
    Index 0 (current bar) is the default and can be omitted: `close` = `close[0]`

## Indicator Functions

### Moving Averages

| Function | Parameters | Description |
|----------|------------|-------------|
| `SMA(period)` | period: int | Simple Moving Average |
| `EMA(period)` | period: int | Exponential Moving Average |
| `WMA(period)` | period: int | Weighted Moving Average |

```yaml
# Golden cross detection
formula: "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"

# Price above EMA
formula: "close > EMA(20)"
```

### Momentum Indicators

| Function | Parameters | Description |
|----------|------------|-------------|
| `RSI(period)` | period: int | Relative Strength Index (0-100) |
| `STOCH(k, d)` | k_period, d_period | Stochastic Oscillator |
| `CCI(period)` | period: int | Commodity Channel Index |
| `MFI(period)` | period: int | Money Flow Index |
| `ROC(period)` | period: int | Rate of Change |
| `WILLIAMS_R(period)` | period: int | Williams %R |
| `ADX(period)` | period: int | Average Directional Index |

```yaml
# RSI oversold bounce
formula: "RSI(14)[-1] < 30 and RSI(14) > 30"

# Strong trend (ADX > 25)
formula: "ADX(14) > 25"
```

### Volatility Indicators

| Function | Parameters | Description |
|----------|------------|-------------|
| `ATR(period)` | period: int | Average True Range |
| `BB(period, std)` | period, std_dev | Bollinger Bands |

Bollinger Bands return an object with `.upper`, `.middle`, `.lower`:

```yaml
# Bollinger Band breakout
formula: "close > BB(20, 2).upper"

# Price in lower band
formula: "close < BB(20, 2).lower"

# Band squeeze
formula: "BB(20, 2).upper - BB(20, 2).lower < ATR(14) * 2"
```

### Trend Indicators

| Function | Parameters | Description |
|----------|------------|-------------|
| `MACD(fast, slow, signal)` | 12, 26, 9 default | MACD Line |

MACD returns `.macd`, `.signal`, `.histogram`:

```yaml
# MACD crossover
formula: "MACD(12, 26, 9).macd[-1] <= MACD(12, 26, 9).signal[-1] and MACD(12, 26, 9).macd > MACD(12, 26, 9).signal"

# Positive histogram
formula: "MACD(12, 26, 9).histogram > 0"
```

### Volume Indicators

| Function | Parameters | Description |
|----------|------------|-------------|
| `OBV()` | none | On-Balance Volume |
| `VWAP()` | none | Volume Weighted Average Price |

```yaml
# OBV rising
formula: "OBV() > OBV()[-1]"

# Price above VWAP
formula: "close > VWAP()"
```

## Common Patterns

### Crossovers

A crossover occurs when one value crosses above or below another:

```yaml
# Cross above: was at or below, now above
formula: "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"

# Cross below: was at or above, now below
formula: "RSI(14)[-1] >= 70 and RSI(14) < 70"
```

### Ranges

Check if a value is within a range:

```yaml
# RSI in neutral zone
formula: "RSI(14) >= 40 and RSI(14) <= 60"

# Price in consolidation
formula: "ATR(14) < ATR(14)[-20] * 0.5"
```

### Breakouts

Detect when price breaks a key level:

```yaml
# Break above resistance (20-day high)
formula: "close > high[-1] and close[-1] <= high[-2]"

# Bollinger Band breakout
formula: "close > BB(20, 2).upper and close[-1] <= BB(20, 2).upper[-1]"

# Volume breakout
formula: "volume > SMA(volume, 20) * 2"
```

### Temporal Patterns

Patterns that consider multiple bars:

```yaml
# RSI oversold for 3 bars
formula: "RSI(14) < 30 and RSI(14)[-1] < 30 and RSI(14)[-2] < 30"

# Consecutive up days
formula: "close > close[-1] and close[-1] > close[-2] and close[-2] > close[-3]"

# Higher highs
formula: "high > high[-1] and high[-1] > high[-2]"
```

### Price Action

Common candlestick and price patterns:

```yaml
# Inside bar
formula: "high < high[-1] and low > low[-1]"

# Outside bar
formula: "high > high[-1] and low < low[-1]"

# Bullish candle (close in upper 30%)
formula: "(close - low) / (high - low) > 0.7"

# Bearish candle (close in lower 30%)
formula: "(close - low) / (high - low) < 0.3"

# Gap up
formula: "open > high[-1]"

# Gap down
formula: "open < low[-1]"
```

### Divergences

Detect divergence between price and indicator:

```yaml
# Bullish RSI divergence (price lower low, RSI higher low)
formula: "low < low[-5] and RSI(14) > RSI(14)[-5]"

# Bearish divergence
formula: "high > high[-5] and RSI(14) < RSI(14)[-5]"
```

## Complete Examples

### Mean Reversion Strategy

```yaml
conditions:
  oversold_bounce:
    type: expr
    formula: "RSI(14)[-1] < 30 and RSI(14) > RSI(14)[-1] and close > SMA(20)"

  overbought_reversal:
    type: expr
    formula: "RSI(14)[-1] > 70 and RSI(14) < RSI(14)[-1]"
```

### Trend Following Strategy

```yaml
conditions:
  trend_entry:
    type: expr
    formula: "close > SMA(50) and SMA(50) > SMA(200) and ADX(14) > 25"

  pullback_buy:
    type: expr
    formula: "close > SMA(200) and close <= SMA(20) and RSI(14) < 40"
```

### Volatility Breakout

```yaml
conditions:
  squeeze_release:
    type: expr
    formula: "BB(20, 2).upper - BB(20, 2).lower < ATR(14)[-1] * 3 and close > BB(20, 2).upper"

  volatility_expansion:
    type: expr
    formula: "ATR(14) > ATR(14)[-1] * 1.5 and volume > SMA(volume, 20) * 2"
```

## Best Practices

1. **Use parentheses for clarity**: Complex expressions benefit from explicit grouping
   ```yaml
   formula: "(RSI(14) < 30) and (close > SMA(20))"
   ```

2. **Break complex conditions into parts**: Use named conditions for readability
   ```yaml
   conditions:
     rsi_oversold:
       type: comparison
       left: { $ref: "#/signals/rsi_14" }
       operator: "<"
       right: { type: constant, value: 30 }

     price_above_ma:
       type: expr
       formula: "close > SMA(20)"

     entry_valid:
       type: and
       conditions:
         - $ref: "#/conditions/rsi_oversold"
         - $ref: "#/conditions/price_above_ma"
   ```

3. **Test expressions**: Use pyutss to validate your formulas
   ```python
   from pyutss import Engine
   # Engine will raise ExpressionError for invalid formulas
   ```

4. **Consider warmup periods**: Indicators need historical data
   - SMA(200) needs 200 bars
   - RSI(14) needs ~14 bars
   - Set `min_history` in execution section appropriately
