# UTSS Architecture & Design Philosophy

This document explains the key architectural decisions and design philosophy behind the Universal Trading Strategy Schema (UTSS).

---

## Table of Contents

1. [The Problem We're Solving](#the-problem-were-solving)
2. [Core Philosophy](#core-philosophy)
3. [Schema as Contract](#schema-as-contract)
4. [Type Hierarchy](#type-hierarchy)
5. [Composition Over Inheritance](#composition-over-inheritance)
6. [Progressive Disclosure](#progressive-disclosure)
7. [Extensibility Layers](#extensibility-layers)
8. [Design Decisions](#design-decisions)
9. [Anti-Patterns Avoided](#anti-patterns-avoided)
10. [Downstream Applications](#downstream-applications)

---

## The Problem We're Solving

Trading strategies are typically expressed in one of three ways:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     THE FRAGMENTATION PROBLEM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. IMPERATIVE CODE                                                         │
│     ┌─────────────────────────────────────────┐                            │
│     │  def strategy(data):                    │  - Tied to specific        │
│     │      rsi = ta.rsi(data.close, 14)       │    language/platform       │
│     │      if rsi < 30:                       │  - Hard to validate        │
│     │          buy(0.1 * equity)              │  - Can't analyze without   │
│     │      elif rsi > 70:                     │    executing               │
│     │          sell_all()                     │                            │
│     └─────────────────────────────────────────┘                            │
│                                                                             │
│  2. NATURAL LANGUAGE                                                        │
│     ┌─────────────────────────────────────────┐                            │
│     │  "Buy when RSI is oversold and          │  - Ambiguous               │
│     │   sell when overbought"                 │  - No validation           │
│     │                                         │  - Different interpretations│
│     └─────────────────────────────────────────┘                            │
│                                                                             │
│  3. PLATFORM-SPECIFIC DSL                                                   │
│     ┌─────────────────────────────────────────┐                            │
│     │  //@version=5                           │  - Vendor lock-in          │
│     │  strategy("RSI", ...)                   │  - Limited expressiveness  │
│     │  longCondition = ta.rsi(close, 14) < 30 │  - Can't transfer between  │
│     │  if (longCondition)                     │    platforms               │
│     │      strategy.entry("Long", ...)        │                            │
│     └─────────────────────────────────────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**UTSS provides a fourth option: a declarative, portable schema.**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          THE UTSS SOLUTION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  UNIVERSAL SCHEMA (Declarative, Validated, Portable)                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  info: { id: rsi_reversal, version: "1.0" }                         │   │
│  │  universe: { type: static, symbols: [AAPL] }                        │   │
│  │  rules:                                                              │   │
│  │    - when: RSI(14) < 30  →  buy 10%                                 │   │
│  │    - when: RSI(14) > 70  →  sell all                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│           ┌──────────────────┼──────────────────┐                          │
│           ▼                  ▼                  ▼                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐               │
│  │  LLM Agents     │ │  Backtesting    │ │  Live Trading   │               │
│  │  Natural lang → │ │  Historical     │ │  Real-time      │               │
│  │  UTSS strategy  │ │  simulation     │ │  execution      │               │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Philosophy

### 1. Define WHAT, Not HOW

UTSS is **declarative**, not imperative. The schema describes what the strategy does, not how to compute it.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DECLARATIVE vs IMPERATIVE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  IMPERATIVE (How)              DECLARATIVE (What)                          │
│  ─────────────────             ──────────────────                          │
│                                                                             │
│  rsi_values = []               signal:                                     │
│  for i in range(14, len(data)):  type: indicator                          │
│      gain = ...                   indicator: RSI                           │
│      loss = ...                   params: { period: 14 }                   │
│      rs = gain / loss                                                      │
│      rsi = 100 - (100/(1+rs))                                              │
│      rsi_values.append(rsi)                                                │
│                                                                             │
│  ▲ Implementation detail       ▲ Intent only                              │
│                                                                             │
│  - Execution engine decides    - Schema doesn't care how                   │
│    how to compute RSI            RSI is calculated                         │
│  - Could be pandas-ta, TA-Lib, - Same schema works with                    │
│    or custom implementation      any compliant engine                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Schema as Source of Truth

The strategy definition is complete in the schema. No external configuration needed.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SELF-CONTAINED STRATEGY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  strategy.yaml contains EVERYTHING needed:                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  info:        WHO created this, WHEN, WHY                           │   │
│  │  universe:    WHAT to trade                                         │   │
│  │  signals:     WHAT values to compute                                │   │
│  │  conditions:  WHAT states to detect                                 │   │
│  │  rules:       WHEN to act, WHAT action                              │   │
│  │  constraints: WHAT limits to enforce                                │   │
│  │  schedule:    WHEN to evaluate                                      │   │
│  │  parameters:  WHAT can be optimized                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NOT in schema (execution engine concerns):                                 │
│  - HOW to fetch market data                                                 │
│  - HOW to calculate indicators                                              │
│  - HOW to send orders to broker                                             │
│  - HOW to handle slippage/commission                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3. LLM-First Design

The schema is designed to be easily generated by Large Language Models.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LLM-FRIENDLY DESIGN                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  User: "Create a strategy that buys when RSI is oversold"                  │
│                              │                                              │
│                              ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │                          LLM                                       │     │
│  │                                                                    │     │
│  │  Predictable patterns:                                             │     │
│  │  ✓ Every object has "type" field                                  │     │
│  │  ✓ Enums are readable (not codes)                                 │     │
│  │  ✓ Clear naming conventions                                        │     │
│  │  ✓ Reasonable defaults                                             │     │
│  │  ✓ Examples as few-shot prompts                                    │     │
│  │                                                                    │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                              │                                              │
│                              ▼                                              │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │  rules:                                                            │     │
│  │    - name: Buy on oversold                                         │     │
│  │      when:                                                         │     │
│  │        type: comparison         ◄── Type discriminator             │     │
│  │        left:                                                       │     │
│  │          type: indicator        ◄── Type discriminator             │     │
│  │          indicator: RSI         ◄── Human-readable enum            │     │
│  │          params: { period: 14 }                                    │     │
│  │        operator: "<"            ◄── Intuitive operator             │     │
│  │        right:                                                      │     │
│  │          type: constant                                            │     │
│  │          value: 30                                                 │     │
│  │      then:                                                         │     │
│  │        type: trade                                                 │     │
│  │        direction: buy           ◄── Clear action                   │     │
│  │        sizing:                                                     │     │
│  │          type: percent_of_equity                                   │     │
│  │          percent: 10                                               │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Schema as Contract

The UTSS schema is a **contract** between strategy authors and execution engines.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SCHEMA AS CONTRACT                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                        ┌─────────────────┐                                  │
│                        │  UTSS Schema    │                                  │
│                        │  (Contract)     │                                  │
│                        └────────┬────────┘                                  │
│                                 │                                           │
│           ┌─────────────────────┴─────────────────────┐                    │
│           │                                           │                    │
│           ▼                                           ▼                    │
│  ┌─────────────────┐                         ┌─────────────────┐           │
│  │ Strategy Author │                         │ Execution Engine│           │
│  │                 │                         │                 │           │
│  │ Guarantees:     │                         │ Guarantees:     │           │
│  │ ─────────────── │                         │ ─────────────── │           │
│  │ • Valid syntax  │                         │ • Correct RSI   │           │
│  │ • Defined types │                         │ • Order routing │           │
│  │ • Clear intent  │                         │ • Risk limits   │           │
│  │                 │                         │ • Scheduling    │           │
│  └─────────────────┘                         └─────────────────┘           │
│                                                                             │
│  The CONTRACT ensures:                                                      │
│  ────────────────────                                                       │
│  • Any valid UTSS document works with any compliant engine                  │
│  • Authors don't need to know implementation details                        │
│  • Engines don't need to guess author's intent                              │
│  • Strategies are portable across platforms                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Type Hierarchy

UTSS uses a clear type hierarchy that mirrors the structure of trading decisions.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TYPE HIERARCHY                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Signal ────────► Condition ────────► Rule ────────► Strategy              │
│    │                  │                 │                │                  │
│    │                  │                 │                │                  │
│    ▼                  ▼                 ▼                ▼                  │
│  number            boolean           action          complete              │
│  (value)          (yes/no)         (do this)         (system)             │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SIGNAL (Produces a Number)                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  ┌─────────┐ ┌───────────┐ ┌─────────────┐ ┌──────────┐           │   │
│  │  │  price  │ │ indicator │ │ fundamental │ │ calendar │           │   │
│  │  │  ───────│ │ ──────────│ │ ────────────│ │ ─────────│           │   │
│  │  │ close:  │ │ RSI(14):  │ │ PE_RATIO:   │ │ day_of_  │           │   │
│  │  │   150.5 │ │     45.2  │ │      25.3   │ │ week: 3  │           │   │
│  │  └─────────┘ └───────────┘ └─────────────┘ └──────────┘           │   │
│  │                                                                     │   │
│  │  ┌─────────┐ ┌───────────┐ ┌─────────────┐ ┌──────────┐           │   │
│  │  │  event  │ │ portfolio │ │ arithmetic  │ │   expr   │           │   │
│  │  │  ───────│ │ ──────────│ │ ────────────│ │ ─────────│           │   │
│  │  │EARNINGS:│ │ unreal_pnl│ │ SMA20-SMA50 │ │ custom   │           │   │
│  │  │    1    │ │    2.5%   │ │     -3.2    │ │ formula  │           │   │
│  │  └─────────┘ └───────────┘ └─────────────┘ └──────────┘           │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CONDITION (Produces True/False)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌─────────────┐  ┌─────────────┐                │   │
│  │  │  comparison  │  │    cross    │  │    range    │                │   │
│  │  │  ────────────│  │  ──────────│  │  ──────────│                │   │
│  │  │ RSI < 30     │  │ SMA50 cross │  │ 20<RSI<80  │                │   │
│  │  │   = true     │  │ above SMA200│  │   = true   │                │   │
│  │  └──────────────┘  └─────────────┘  └─────────────┘                │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌─────────────┐  ┌─────────────┐                │   │
│  │  │   and/or     │  │  temporal   │  │  sequence   │                │   │
│  │  │  ────────────│  │  ──────────│  │  ──────────│                │   │
│  │  │ A AND B      │  │ A for 3bars │  │ A then B   │                │   │
│  │  │   = true     │  │   = true    │  │   = true   │                │   │
│  │  └──────────────┘  └─────────────┘  └─────────────┘                │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ACTION (What to Do)                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  ┌───────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐    │   │
│  │  │   trade   │  │  rebalance  │  │    alert    │  │   hold   │    │   │
│  │  │  ─────────│  │  ──────────│  │  ──────────│  │  ────────│    │   │
│  │  │ buy/sell  │  │ adjust to   │  │ send        │  │ do       │    │   │
│  │  │ short/    │  │ target      │  │ notification│  │ nothing  │    │   │
│  │  │ cover     │  │ weights     │  │             │  │          │    │   │
│  │  └───────────┘  └─────────────┘  └─────────────┘  └──────────┘    │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Composition Over Inheritance

UTSS favors **composition** (combining small pieces) over **inheritance** (hierarchies).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     COMPOSITION vs INHERITANCE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INHERITANCE (Avoided)                 COMPOSITION (Used)                  │
│  ─────────────────────                 ──────────────────                   │
│                                                                             │
│  class TrendStrategy:                  signals:                             │
│    def calculate(self): ...              sma_fast: SMA(20)                  │
│                                          sma_slow: SMA(50)                  │
│  class MACrossover(TrendStrategy):                                          │
│    def calculate(self):                conditions:                          │
│      super().calculate()                 golden_cross:                      │
│      # Override behavior                   sma_fast crosses above sma_slow │
│                                                                             │
│  class RSIMACross(MACrossover):        rules:                               │
│    # Fragile base class problem          - when: golden_cross              │
│    # Tight coupling                        then: buy                        │
│    # Hard to understand                                                     │
│                                                                             │
│  Problems:                             Benefits:                            │
│  ✗ Hard to mix unrelated ideas         ✓ Mix any signals freely            │
│  ✗ Inheritance hierarchy grows         ✓ No hierarchy to maintain          │
│  ✗ Changes break subclasses            ✓ Components are independent        │
│  ✗ Must understand all parents         ✓ Each piece is self-contained      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Reference System ($ref)

Components are reused through references, not inheritance.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REFERENCE SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Define once:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  signals:                                                           │   │
│  │    rsi_14:                           ◄── Named definition           │   │
│  │      type: indicator                                                │   │
│  │      indicator: RSI                                                 │   │
│  │      params: { period: 14 }                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Reference anywhere:                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  rules:                                                             │   │
│  │    - when:                                                          │   │
│  │        type: comparison                                             │   │
│  │        left: { $ref: "#/signals/rsi_14" }  ◄── Reference            │   │
│  │        operator: "<"                                                │   │
│  │        right: { type: constant, value: 30 }                         │   │
│  │      then: ...                                                      │   │
│  │                                                                     │   │
│  │    - when:                                                          │   │
│  │        type: comparison                                             │   │
│  │        left: { $ref: "#/signals/rsi_14" }  ◄── Same reference       │   │
│  │        operator: ">"                                                │   │
│  │        right: { type: constant, value: 70 }                         │   │
│  │      then: ...                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Benefits:                                                                  │
│  • Single source of truth (change once, updates everywhere)                 │
│  • Readable (named components convey intent)                                │
│  • Validated (references are checked)                                       │
│  • Composable (combine any components)                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Progressive Disclosure

Simple strategies are simple. Complexity is opt-in.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PROGRESSIVE DISCLOSURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LEVEL 1: Minimal Strategy (5 lines)                                        │
│  ────────────────────────────────────                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  info: { id: buy_hold, name: Buy and Hold, version: "1.0" }        │   │
│  │  universe: { type: static, symbols: [SPY] }                         │   │
│  │  rules:                                                             │   │
│  │    - name: Buy                                                      │   │
│  │      when: { type: always }                                         │   │
│  │      then: { type: trade, direction: buy,                           │   │
│  │              sizing: { type: percent_of_equity, percent: 100 } }    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LEVEL 2: Add Risk Management                                               │
│  ─────────────────────────────                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ...                                                                │   │
│  │  constraints:                          ◄── Add risk limits          │   │
│  │    max_positions: 5                                                 │   │
│  │    stop_loss: { percent: 5 }                                        │   │
│  │    max_drawdown: 20                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LEVEL 3: Add Reusable Components                                           │
│  ─────────────────────────────────                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  signals:                              ◄── Define reusable signals  │   │
│  │    rsi: { type: indicator, indicator: RSI, params: { period: 14 } } │   │
│  │  conditions:                           ◄── Define reusable conditions│  │
│  │    oversold: { type: comparison, left: { $ref: "#/signals/rsi" },   │   │
│  │               operator: "<", right: { type: constant, value: 30 } } │   │
│  │  rules:                                                             │   │
│  │    - when: { $ref: "#/conditions/oversold" }  ◄── Use references    │   │
│  │      then: ...                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LEVEL 4: Add Parameter Optimization                                        │
│  ────────────────────────────────────                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  parameters:                           ◄── Define optimizable params│   │
│  │    rsi_period: { type: integer, default: 14, min: 5, max: 30 }     │   │
│  │    threshold: { type: number, default: 30, min: 20, max: 40 }      │   │
│  │  signals:                                                           │   │
│  │    rsi:                                                             │   │
│  │      type: indicator                                                │   │
│  │      indicator: RSI                                                 │   │
│  │      params: { period: { $param: rsi_period } }  ◄── Param reference│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LEVEL 5: Advanced Features                                                 │
│  ──────────────────────────                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • Sequence conditions (A then B within 5 bars)                     │   │
│  │  • Portfolio signals (unrealized_pnl, days_in_position)             │   │
│  │  • Conditional sizing (different size based on regime)              │   │
│  │  • External signals (ML model predictions via webhook)              │   │
│  │  • Expression language (custom formulas)                            │   │
│  │  • Platform extensions (x-backtest, x-live)                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Extensibility Layers

UTSS has four layers of extensibility, each with different tradeoffs.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXTENSIBILITY LAYERS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 4: x-extensions (platform-specific, ignored by validators)    │ │
│  │                                                                       │ │
│  │    x-backtest: { slippage: 0.1%, commission: 0.05% }                 │ │
│  │    x-live: { broker: sbi, account: margin }                          │ │
│  │    x-freqtrade: { stake_amount: 100, dry_run: true }                 │ │
│  │                                                                       │ │
│  │    ✓ Zero portability (platform-specific)                            │ │
│  │    ✓ Maximum flexibility                                              │ │
│  │    ✓ Doesn't break validation                                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 3: External Signals (runtime-resolved)                        │ │
│  │                                                                       │ │
│  │    signals:                                                           │ │
│  │      ml_prediction:                                                   │ │
│  │        type: external                                                 │ │
│  │        source: webhook                                                │ │
│  │        url: "https://api.mymodel.com/predict"                        │ │
│  │        default: 0.5                                                   │ │
│  │                                                                       │ │
│  │    ✓ Low portability (requires external service)                     │ │
│  │    ✓ High flexibility (any value from any source)                    │ │
│  │    ✓ Validated structure, runtime value                               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 2: Expression Language (parsed, semi-portable)                │ │
│  │                                                                       │ │
│  │    signals:                                                           │ │
│  │      custom_zscore:                                                   │ │
│  │        type: expr                                                     │ │
│  │        formula: "(close - SMA(close, 20)) / STDDEV(close, 20)"       │ │
│  │                                                                       │ │
│  │    ✓ Medium portability (if engine supports expr)                    │ │
│  │    ✓ Medium flexibility (must follow expr syntax)                    │ │
│  │    ✓ Validated syntax, interpreted execution                          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 1: Strict Core (fully validated, fully portable)              │ │
│  │                                                                       │ │
│  │    signals:                                                           │ │
│  │      rsi_14:                                                          │ │
│  │        type: indicator                                                │ │
│  │        indicator: RSI          ◄── Known enum                        │ │
│  │        params: { period: 14 }  ◄── Validated params                  │ │
│  │                                                                       │ │
│  │    ✓ Full portability (all engines support core)                     │ │
│  │    ✓ Limited flexibility (only predefined types)                     │ │
│  │    ✓ Full validation, guaranteed execution                            │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Choose the layer based on your needs:                                      │
│  • Need maximum portability? → Use Layer 1 (Strict Core)                   │
│  • Need custom calculations? → Use Layer 2 (Expressions)                   │
│  • Need external data/ML? → Use Layer 3 (External Signals)                 │
│  • Need platform features? → Use Layer 4 (x-extensions)                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Design Decisions

### Why JSON Schema (not custom DSL)?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      WHY JSON SCHEMA?                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Option A: Custom DSL          Option B: JSON Schema (Chosen)              │
│  ────────────────────          ──────────────────────────────               │
│                                                                             │
│  strategy MyStrategy:          info:                                        │
│    universe = [AAPL]             id: my_strategy                            │
│    when RSI(14) < 30:          universe:                                    │
│      buy 10%                     type: static                               │
│                                  symbols: [AAPL]                            │
│                                rules:                                       │
│                                  - when: { RSI(14) < 30 }                   │
│                                    then: { buy 10% }                        │
│                                                                             │
│  ✗ Need to build parser        ✓ Standard tooling exists                   │
│  ✗ Need to build validator     ✓ Validators in every language              │
│  ✗ Documentation burden        ✓ JSON Schema is well-documented            │
│  ✗ Learning curve              ✓ YAML/JSON are universal                   │
│  ✗ IDE support from scratch    ✓ IDE support built-in                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Type Discriminators?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      WHY TYPE DISCRIMINATORS?                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Without discriminator:        With discriminator (chosen):                 │
│  ───────────────────────       ────────────────────────────                 │
│                                                                             │
│  signal:                       signal:                                      │
│    indicator: RSI                type: indicator    ◄── Clear type         │
│    period: 14                    indicator: RSI                             │
│    # Is this a fundamental?      params: { period: 14 }                    │
│    # A portfolio signal?                                                    │
│    # Parser must guess...      # Parser knows exactly                      │
│                                # what this is                               │
│                                                                             │
│  Benefits of discriminator:                                                 │
│  • Unambiguous parsing (LLMs don't guess)                                   │
│  • Clear validation (each type has own rules)                               │
│  • Self-documenting (type tells you what it is)                             │
│  • Extensible (new types don't conflict)                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Separate Signals and Conditions?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  WHY SEPARATE SIGNALS AND CONDITIONS?                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Combined (rejected):           Separated (chosen):                         │
│  ────────────────────           ────────────────────                        │
│                                                                             │
│  rule:                          signals:                                    │
│    when: RSI(14) < 30             rsi_14: RSI(14)     ◄── Number           │
│    # Is "RSI(14) < 30" a                                                    │
│    # signal or condition?       conditions:                                 │
│    # Hard to reuse pieces         oversold:                                 │
│                                     rsi_14 < 30      ◄── Boolean           │
│                                                                             │
│  Benefits of separation:                                                    │
│  • Clear semantics (signals=numbers, conditions=booleans)                   │
│  • Better reuse (same signal in multiple conditions)                        │
│  • Easier debugging (inspect signals and conditions separately)             │
│  • Cleaner composition (compose signals, then conditions, then rules)       │
│                                                                             │
│  Example of reuse:                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  signals:                                                           │   │
│  │    rsi: RSI(14)                   ◄── Define once                   │   │
│  │                                                                     │   │
│  │  conditions:                                                        │   │
│  │    oversold: rsi < 30             ◄── Use in multiple conditions   │   │
│  │    overbought: rsi > 70                                             │   │
│  │    neutral: 40 < rsi < 60                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Anti-Patterns Avoided

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ANTI-PATTERNS AVOIDED                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. STRING-BASED LOGIC                                                      │
│     ─────────────────────                                                   │
│     ✗ when: "RSI(close, 14) < 30 and MACD(12,26,9).hist > 0"              │
│       • Hard to validate (arbitrary string)                                 │
│       • Hard to analyze (must parse string)                                 │
│       • Security risk (code injection)                                      │
│                                                                             │
│     ✓ when:                                                                │
│         type: and                                                           │
│         conditions:                                                         │
│           - type: comparison                                                │
│             left: { type: indicator, indicator: RSI, params: {period: 14} } │
│             operator: "<"                                                   │
│             right: { type: constant, value: 30 }                            │
│           - type: comparison                                                │
│             left: { type: indicator, indicator: MACD_HIST, ... }            │
│             operator: ">"                                                   │
│             right: { type: constant, value: 0 }                             │
│                                                                             │
│  2. IMPLICIT STATE                                                          │
│     ──────────────────                                                      │
│     ✗ when: in_position and profit > 5%                                    │
│       • Where does "in_position" come from?                                 │
│       • What is "profit" relative to?                                       │
│                                                                             │
│     ✓ when:                                                                │
│         type: and                                                           │
│         conditions:                                                         │
│           - type: comparison                                                │
│             left: { type: portfolio, field: position_qty }  ◄── Explicit   │
│             operator: ">"                                                   │
│             right: { type: constant, value: 0 }                             │
│           - type: comparison                                                │
│             left: { type: portfolio, field: unrealized_pnl_pct } ◄── Clear │
│             operator: ">"                                                   │
│             right: { type: constant, value: 5 }                             │
│                                                                             │
│  3. MAGIC NUMBERS                                                           │
│     ──────────────────                                                      │
│     ✗ when: RSI(14) < 30                                                   │
│       • Why 14? Why 30? Hard to optimize                                    │
│                                                                             │
│     ✓ parameters:                                                          │
│         rsi_period: { type: integer, default: 14, min: 5, max: 30 }        │
│         oversold: { type: integer, default: 30, min: 20, max: 40 }         │
│       signals:                                                              │
│         rsi: { indicator: RSI, params: { period: { $param: rsi_period } } } │
│       when:                                                                 │
│         left: { $ref: "#/signals/rsi" }                                     │
│         operator: "<"                                                       │
│         right: { $param: oversold }                                         │
│                                                                             │
│  4. PREMATURE ABSTRACTION                                                   │
│     ─────────────────────────                                               │
│     ✗ Deeply nested inheritance hierarchies                                │
│     ✗ Abstract base strategies with override points                        │
│     ✗ Plugin systems for everything                                         │
│                                                                             │
│     ✓ Flat structure with references                                       │
│     ✓ Compose small, focused pieces                                         │
│     ✓ Extensions only where truly needed                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Downstream Applications

UTSS is designed to be consumed by various applications.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DOWNSTREAM APPLICATIONS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                         ┌─────────────────┐                                │
│                         │  UTSS Strategy  │                                │
│                         │    Document     │                                │
│                         └────────┬────────┘                                │
│                                  │                                          │
│         ┌──────────────┬─────────┼─────────┬──────────────┐                │
│         │              │         │         │              │                │
│         ▼              ▼         ▼         ▼              ▼                │
│  ┌─────────────┐ ┌──────────┐ ┌─────┐ ┌──────────┐ ┌──────────┐           │
│  │ LLM Agents  │ │Backtest  │ │Param│ │   Live   │ │ Strategy │           │
│  │             │ │ Engines  │ │Optim│ │ Trading  │ │Marketplace│          │
│  └─────────────┘ └──────────┘ └─────┘ └──────────┘ └──────────┘           │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LLM AGENTS                                                                 │
│  ──────────                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  User: "Create a momentum strategy for Japanese stocks"            │   │
│  │                              │                                      │   │
│  │                              ▼                                      │   │
│  │  LLM generates valid UTSS YAML:                                     │   │
│  │  • Uses schema for structured output                                │   │
│  │  • Examples as few-shot prompts                                     │   │
│  │  • Validation catches errors                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BACKTESTING ENGINES                                                        │
│  ───────────────────                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Engine responsibilities:                                           │   │
│  │  • Parse UTSS document                                              │   │
│  │  • Calculate indicators (RSI, SMA, etc.)                            │   │
│  │  • Evaluate conditions on each bar                                  │   │
│  │  • Execute actions (simulated fills)                                │   │
│  │  • Track portfolio state                                            │   │
│  │  • Generate performance metrics                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PARAMETER OPTIMIZATION                                                     │
│  ──────────────────────                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  parameters:                                                        │   │
│  │    rsi_period: { min: 5, max: 30, step: 1 }                        │   │
│  │    threshold: { min: 20, max: 40 }                                  │   │
│  │                                                                     │   │
│  │  Optimizer:                                                         │   │
│  │  • Extract parameter ranges from schema                             │   │
│  │  • Grid search / genetic algorithm / Bayesian                       │   │
│  │  • Generate strategy variants                                       │   │
│  │  • Run backtests                                                    │   │
│  │  • Find optimal parameters                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LIVE TRADING                                                               │
│  ────────────                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Same strategy document, different execution:                       │   │
│  │  • Real-time market data instead of historical                      │   │
│  │  • Real broker API instead of simulated fills                       │   │
│  │  • Same logic, different environment                                │   │
│  │                                                                     │   │
│  │  x-live:                                                            │   │
│  │    broker: sbi                                                      │   │
│  │    account_type: margin                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UTSS DESIGN SUMMARY                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CORE PRINCIPLES:                                                           │
│  • Declarative (WHAT, not HOW)                                             │
│  • Self-contained (complete strategy in one document)                       │
│  • LLM-friendly (predictable patterns, clear types)                         │
│  • Portable (works with any compliant engine)                               │
│                                                                             │
│  TYPE HIERARCHY:                                                            │
│  • Signal → number (RSI = 45.2)                                            │
│  • Condition → boolean (RSI < 30 = true)                                   │
│  • Rule → when/then (if oversold, buy)                                     │
│  • Strategy → complete system                                               │
│                                                                             │
│  COMPOSITION:                                                               │
│  • Define signals and conditions once                                       │
│  • Reference with $ref anywhere                                             │
│  • No inheritance, just composition                                         │
│                                                                             │
│  EXTENSIBILITY:                                                             │
│  • Layer 1: Strict core (portable)                                         │
│  • Layer 2: Expressions (semi-portable)                                     │
│  • Layer 3: External signals (runtime)                                      │
│  • Layer 4: x-extensions (platform-specific)                                │
│                                                                             │
│  PROGRESSIVE DISCLOSURE:                                                    │
│  • Minimal strategy: 5 lines                                                │
│  • Full strategy: 100+ lines with all features                              │
│  • Complexity is opt-in                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```
