# Comparison with Existing Approaches

This document compares UTSS with existing strategy representation approaches used in popular backtesting libraries and trading platforms.

---

## Overview

| Approach | Examples | Portability | Validation | LLM-Friendly | Complexity |
|----------|----------|-------------|------------|--------------|------------|
| **Imperative Code** | Backtrader, Zipline, bt | Low | None | Poor | High |
| **Platform DSL** | Pine Script, MQL, EasyLanguage | Very Low | Partial | Poor | Medium |
| **Config + Code** | Freqtrade, Jesse | Low | Partial | Poor | Medium |
| **Visual Builder** | TradingView Strategy Tester | Very Low | Good | N/A | Low |
| **UTSS** | This project | **High** | **Full** | **Excellent** | Low-High |

---

## Detailed Comparisons

### 1. Imperative Code Libraries

**Examples:** Backtrader, Zipline, bt, VectorBT, QuantLib

#### How They Work

Strategies are written as Python/C++ classes with callbacks:

```python
# Backtrader Example
class RSIStrategy(bt.Strategy):
    params = (('period', 14), ('oversold', 30), ('overbought', 70))

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.period)

    def next(self):
        if not self.position:
            if self.rsi < self.params.oversold:
                self.buy(size=self.broker.getcash() * 0.1 / self.data.close[0])
        else:
            if self.rsi > self.params.overbought:
                self.close()
```

```python
# Zipline Example
def initialize(context):
    context.asset = symbol('AAPL')
    context.rsi_period = 14

def handle_data(context, data):
    prices = data.history(context.asset, 'price', context.rsi_period + 1, '1d')
    rsi = talib.RSI(prices.values, context.rsi_period)[-1]

    if rsi < 30:
        order_target_percent(context.asset, 0.1)
    elif rsi > 70:
        order_target_percent(context.asset, 0)
```

#### Comparison with UTSS

| Aspect | Imperative Code | UTSS |
|--------|-----------------|------|
| **Portability** | Tied to specific library | Works with any compliant engine |
| **Validation** | Runtime errors only | Schema validation before execution |
| **Readability** | Requires understanding Python/library | Self-documenting YAML |
| **LLM Generation** | Prone to syntax errors, API misuse | Structured output, easy validation |
| **Testability** | Requires mocking broker, data | Logic is pure data, easily testable |
| **Debugging** | Step through code | Inspect signals/conditions directly |
| **Optimization** | Custom loop required | Parameters extracted from schema |
| **Flexibility** | Unlimited (it's code) | Bounded by schema (extensible) |

#### When to Use What

- **Use Imperative Code when:**
  - You need custom indicators not in UTSS
  - Complex position management (scaling in/out)
  - Integration with specific broker APIs
  - Real-time tick-by-tick logic

- **Use UTSS when:**
  - Strategy can be expressed declaratively
  - Need portability across platforms
  - LLM-generated strategies
  - Sharing/distributing strategies
  - Parameter optimization

---

### 2. Platform-Specific DSLs

**Examples:** TradingView Pine Script, MetaTrader MQL4/5, TradeStation EasyLanguage

#### How They Work

```pine
// TradingView Pine Script
//@version=5
strategy("RSI Strategy", overlay=true)

length = input(14, "RSI Length")
oversold = input(30, "Oversold")
overbought = input(70, "Overbought")

rsi = ta.rsi(close, length)

if (rsi < oversold)
    strategy.entry("Buy", strategy.long, qty=strategy.equity * 0.1 / close)

if (rsi > overbought)
    strategy.close("Buy")
```

```mql5
// MetaTrader MQL5
int OnInit() {
    rsiHandle = iRSI(_Symbol, PERIOD_D1, 14, PRICE_CLOSE);
    return INIT_SUCCEEDED;
}

void OnTick() {
    double rsi[];
    CopyBuffer(rsiHandle, 0, 0, 1, rsi);

    if (rsi[0] < 30 && PositionSelect(_Symbol) == false) {
        double lots = AccountInfoDouble(ACCOUNT_EQUITY) * 0.1 / SymbolInfoDouble(_Symbol, SYMBOL_ASK);
        trade.Buy(lots, _Symbol);
    }
    else if (rsi[0] > 70 && PositionSelect(_Symbol)) {
        trade.PositionClose(_Symbol);
    }
}
```

#### Comparison with UTSS

| Aspect | Platform DSL | UTSS |
|--------|--------------|------|
| **Lock-in** | Complete (Pine = TradingView only) | None |
| **Learning Curve** | New language per platform | YAML + schema |
| **Execution** | Platform handles everything | Bring your own engine |
| **Backtesting** | Built into platform | Separate concern |
| **Data Access** | Platform data only | Any data source |
| **Indicators** | Platform's library | Engine's library |
| **Sharing** | Within platform | Universal |

#### Migration Path

UTSS can represent most Pine Script strategies:

```yaml
# UTSS equivalent of Pine Script above
info:
  id: rsi_strategy
  name: RSI Strategy
  version: "1.0"

parameters:
  length:
    type: integer
    default: 14
  oversold:
    type: integer
    default: 30
  overbought:
    type: integer
    default: 70

universe:
  type: static
  symbols: [AAPL]

signals:
  rsi:
    type: indicator
    indicator: RSI
    params:
      period: { $param: length }

rules:
  - name: Buy oversold
    when:
      type: comparison
      left: { $ref: "#/signals/rsi" }
      operator: "<"
      right: { $param: oversold }
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 10 }

  - name: Sell overbought
    when:
      type: comparison
      left: { $ref: "#/signals/rsi" }
      operator: ">"
      right: { $param: overbought }
    then:
      type: trade
      direction: sell
      sizing: { type: percent_of_position, percent: 100 }
```

---

### 3. Configuration + Code Hybrids

**Examples:** Freqtrade, Jesse, Hummingbot

#### How They Work

These use configuration files for parameters but require code for strategy logic:

```python
# Freqtrade - strategy.py
class RSIStrategy(IStrategy):
    minimal_roi = {"0": 0.15, "30": 0.10, "60": 0.05}
    stoploss = -0.10
    timeframe = '1h'

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe['rsi'] < 30, 'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[dataframe['rsi'] > 70, 'exit_long'] = 1
        return dataframe
```

```json
// Freqtrade - config.json
{
    "max_open_trades": 5,
    "stake_currency": "USDT",
    "stake_amount": "unlimited",
    "tradable_balance_ratio": 0.99,
    "dry_run": true,
    "exchange": {
        "name": "binance",
        "key": "",
        "secret": ""
    }
}
```

#### Comparison with UTSS

| Aspect | Config + Code | UTSS |
|--------|---------------|------|
| **Strategy Logic** | In code | In schema |
| **Configuration** | In JSON/YAML | In schema |
| **Separation** | Config vs code split | All in one document |
| **Validation** | Config validated, code not | Everything validated |
| **Sharing** | Must share code + config | Single file |
| **Platform** | Framework-specific | Universal |

#### UTSS Advantage

UTSS puts **everything** in the schema:

```yaml
# UTSS - Complete strategy in one file
info:
  id: rsi_strategy
  name: RSI Strategy
  version: "1.0"

universe:
  type: static
  symbols: [BTC/USDT]

signals:
  rsi:
    type: indicator
    indicator: RSI
    params: { period: 14 }

rules:
  - name: Entry
    when:
      type: comparison
      left: { $ref: "#/signals/rsi" }
      operator: "<"
      right: { type: constant, value: 30 }
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 10 }

  - name: Exit
    when:
      type: comparison
      left: { $ref: "#/signals/rsi" }
      operator: ">"
      right: { type: constant, value: 70 }
    then:
      type: trade
      direction: sell
      sizing: { type: percent_of_position, percent: 100 }

constraints:
  max_positions: 5
  stop_loss: { percent: 10 }

# Platform-specific settings via x-extensions
x-freqtrade:
  stake_currency: USDT
  dry_run: true
  exchange: binance
```

---

### 4. Visual Strategy Builders

**Examples:** TradingView Strategy Builder, MetaTrader Strategy Tester, QuantConnect Algorithm Lab

#### How They Work

Drag-and-drop interfaces that generate code/config behind the scenes.

#### Comparison with UTSS

| Aspect | Visual Builder | UTSS |
|--------|----------------|------|
| **User Interface** | Graphical | Text (YAML) |
| **Accessibility** | Non-programmers | Technical users |
| **Expressiveness** | Limited to UI options | Full schema |
| **Version Control** | Difficult | Native (text files) |
| **Collaboration** | Platform-dependent | Standard tools |
| **Export** | Platform-specific | Universal |

#### UTSS as Backend

Visual builders could use UTSS as their export format:

```
┌─────────────────────────────────────────────────────────────┐
│                    Visual Strategy Builder                   │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│  │  RSI    │───▶│   <30   │───▶│   BUY   │                 │
│  │ Period:14│    │         │    │  10%    │                 │
│  └─────────┘    └─────────┘    └─────────┘                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ Export
┌─────────────────────────────────────────────────────────────┐
│  rules:                                                     │
│    - name: Buy signal                                       │
│      when:                                                  │
│        type: comparison                                     │
│        left: { type: indicator, indicator: RSI, ... }      │
│        operator: "<"                                        │
│        right: { type: constant, value: 30 }                │
│      then:                                                  │
│        type: trade                                          │
│        direction: buy                                       │
│        sizing: { type: percent_of_equity, percent: 10 }    │
└─────────────────────────────────────────────────────────────┘
```

---

### 5. Other Schema Approaches

#### QuantConnect LEAN Algorithm Framework

```csharp
// LEAN uses C# with a component architecture
public class RSIAlgorithm : QCAlgorithm
{
    private RelativeStrengthIndex _rsi;

    public override void Initialize()
    {
        SetStartDate(2020, 1, 1);
        AddEquity("AAPL", Resolution.Daily);
        _rsi = RSI("AAPL", 14);
    }

    public override void OnData(Slice data)
    {
        if (_rsi < 30 && !Portfolio.Invested)
            SetHoldings("AAPL", 0.1);
        else if (_rsi > 70 && Portfolio.Invested)
            Liquidate("AAPL");
    }
}
```

**Comparison:** LEAN is code-first but inspired UTSS's component architecture.

#### bt (Python Backtesting Library)

```python
# bt uses composable "algos"
import bt

data = bt.get('aapl', start='2020-01-01')

strategy = bt.Strategy('RSI Strategy', [
    bt.algos.RunDaily(),
    bt.algos.SelectWhere(data['rsi'] < 30),
    bt.algos.WeighEqually(),
    bt.algos.Rebalance()
])

backtest = bt.Backtest(strategy, data)
result = bt.run(backtest)
```

**Comparison:** bt's composable algos inspired UTSS's composition model, but bt is still Python code.

---

## Feature Matrix

| Feature | Backtrader | Zipline | Pine Script | Freqtrade | UTSS |
|---------|------------|---------|-------------|-----------|------|
| **Language** | Python | Python | Pine | Python | YAML/JSON |
| **Validation** | Runtime | Runtime | Compile | Runtime | Schema |
| **Portability** | None | None | None | None | Full |
| **LLM Generation** | Hard | Hard | Hard | Hard | Easy |
| **Parameter Optimization** | Manual | Manual | Built-in | Manual | Built-in |
| **Multi-Asset** | Yes | Yes | Limited | Yes | Yes |
| **Multi-Timeframe** | Yes | Yes | Yes | Yes | Yes |
| **Custom Indicators** | Yes | Yes | Yes | Yes | Via expr/external |
| **Portfolio Signals** | Code | Code | Limited | Code | Built-in |
| **Event-Driven** | Yes | Yes | Limited | Yes | Yes |
| **Risk Management** | Code | Code | Built-in | Config | Schema |
| **Live Trading** | Yes | No | Via broker | Yes | Engine-dependent |

---

## When to Use UTSS

### Ideal Use Cases

1. **LLM-Generated Strategies**
   - Structured output is easy to validate
   - Schema provides guardrails
   - Examples serve as few-shot prompts

2. **Strategy Distribution**
   - Single file contains everything
   - No code execution needed to understand
   - Version control friendly

3. **Cross-Platform Execution**
   - Same strategy, multiple engines
   - Test on one platform, deploy on another

4. **Parameter Optimization**
   - Parameters are explicit in schema
   - Easy to extract and iterate

5. **Strategy Marketplaces**
   - Standardized format
   - Easy to validate and display

### Less Ideal Use Cases

1. **Complex Position Management**
   - Scaling in/out with multiple entries
   - Grid trading, DCA strategies
   - (Consider x-extensions or custom engine)

2. **Tick-by-Tick Strategies**
   - HFT, market making
   - (UTSS supports tick frequency, but execution is engine-dependent)

3. **Custom Indicator Development**
   - Use `expr` or `external` signals
   - Or develop in execution engine

4. **Broker-Specific Features**
   - Use x-extensions for platform-specific settings

---

## Migration Guides

### From Backtrader to UTSS

```python
# Backtrader
class MyStrategy(bt.Strategy):
    params = (('period', 14),)

    def __init__(self):
        self.sma = bt.indicators.SMA(period=self.params.period)

    def next(self):
        if self.data.close > self.sma:
            self.buy()
```

```yaml
# UTSS
parameters:
  period: { type: integer, default: 14 }

signals:
  sma:
    type: indicator
    indicator: SMA
    params: { period: { $param: period } }

rules:
  - name: Buy above SMA
    when:
      type: comparison
      left: { type: price, field: close }
      operator: ">"
      right: { $ref: "#/signals/sma" }
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 100 }
```

### From Pine Script to UTSS

```pine
// Pine Script
//@version=5
strategy("Golden Cross")
fast = ta.sma(close, 50)
slow = ta.sma(close, 200)
if ta.crossover(fast, slow)
    strategy.entry("Long", strategy.long)
if ta.crossunder(fast, slow)
    strategy.close("Long")
```

```yaml
# UTSS
signals:
  sma_fast: { type: indicator, indicator: SMA, params: { period: 50 } }
  sma_slow: { type: indicator, indicator: SMA, params: { period: 200 } }

rules:
  - name: Golden Cross
    when:
      type: cross
      signal: { $ref: "#/signals/sma_fast" }
      threshold: { $ref: "#/signals/sma_slow" }
      direction: above
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 100 }

  - name: Death Cross
    when:
      type: cross
      signal: { $ref: "#/signals/sma_fast" }
      threshold: { $ref: "#/signals/sma_slow" }
      direction: below
    then:
      type: trade
      direction: sell
      sizing: { type: percent_of_position, percent: 100 }
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        STRATEGY REPRESENTATION SPECTRUM                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  More Flexible ◄─────────────────────────────────────────► More Portable   │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Imperative   │  │ Platform     │  │ Config +     │  │    UTSS      │   │
│  │ Code         │  │ DSL          │  │ Code         │  │              │   │
│  │              │  │              │  │              │  │              │   │
│  │ • Backtrader │  │ • Pine Script│  │ • Freqtrade  │  │ • Declarative│   │
│  │ • Zipline    │  │ • MQL        │  │ • Jesse      │  │ • Validated  │   │
│  │ • bt         │  │ • EasyLang   │  │              │  │ • Portable   │   │
│  │              │  │              │  │              │  │ • LLM-ready  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                             │
│  Flexibility: Can do anything    Portability: Works anywhere               │
│  Validation: None/runtime        Validation: Full schema                   │
│  LLM: Difficult                  LLM: Excellent                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

UTSS occupies a unique position: **maximum portability while maintaining expressiveness** through its layered extensibility (strict core → expressions → external → x-extensions).
