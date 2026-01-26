# Universal Trading Strategy Schema (UTSS)

## Project Scope

**This project defines a universal schema for expressing trading strategies.**

```
┌─────────────────────────────────────────────────────────────────┐
│                         THIS PROJECT                            │
│                                                                 │
│  • JSON Schema definition (source of truth)                    │
│  • Python types (Pydantic models for validation)               │
│  • Example strategies (documentation)                          │
│  • Specification documents                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ schema consumed by (OUT OF SCOPE)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DOWNSTREAM APPLICATIONS                      │
│                                                                 │
│  • LLM agents (natural language → UTSS strategy)               │
│  • Backtesting libraries (simulate strategy performance)       │
│  • Parameter optimizers (find optimal parameters)              │
│  • Live trading systems (execute strategies)                   │
│  • Strategy marketplaces (share/sell strategies)               │
│  • Web UIs (visual strategy builder)                           │
└─────────────────────────────────────────────────────────────────┘
```

**What this project IS:**
- Schema specification (JSON Schema, Pydantic models)
- Validation utilities (parse YAML/JSON, validate against schema)
- Documentation and examples

**What this project is NOT:**
- Backtesting engine
- Indicator calculation library
- Broker integration
- Execution system

---

## Design Principles

### 1. Schema as Contract
The schema is a contract between strategy authors and execution engines. Any valid UTSS document should be executable by any compliant engine.

### 2. LLM-Friendly
- Predictable structure (consistent patterns)
- Clear type discriminators (`type` field)
- Self-documenting enums (readable values)
- Reasonable defaults

### 3. Simple Things Simple, Complex Things Possible
- Simple strategies should be expressible concisely
- Complex strategies should be possible without escape hatches
- Progressive disclosure (shorthand expands to full form)

### 4. Composition Over Inheritance
- Strategies compose signals, conditions, rules
- Reusable components via `$ref`
- No inheritance hierarchy

### 5. Execution-Agnostic
- Schema defines WHAT, not HOW
- Indicator formulas computed by execution engine
- Slippage/commission models are engine concerns

---

## Quick Start

```bash
# Install
pip install utss
# or
uv add utss

# Validate a strategy file
python -c "from utss import validate_yaml; print(validate_yaml(open('examples/rsi-reversal.yaml').read()))"

# Development
cd python
uv sync
uv run pytest
uv run mypy utss --ignore-missing-imports
```

---

## Project Structure

```
universal-trading-strategy-schema/
├── schema/
│   └── v2/
│       └── strategy.schema.json      # Canonical JSON Schema (SOURCE OF TRUTH)
│
├── python/
│   └── utss/
│       ├── models.py                 # Pydantic v2 models
│       ├── validator.py              # YAML/dict validation
│       └── __init__.py               # Public API exports
│
├── examples/                         # Example strategy files
│   ├── rsi-reversal.yaml
│   ├── golden-cross.yaml
│   ├── earnings-play.yaml
│   └── monday-friday.yaml
│
├── docs/
│   ├── quickstart.md                # Getting started guide
│   ├── architecture.md              # Design philosophy & decisions
│   └── UTSS-v2.1-SPEC.md            # Complete specification
│
└── .claude/
    └── CLAUDE.md                     # This file
```

---

## Architecture

```
Signal → Condition → Rule → Strategy
  │          │         │        │
  │          │         │        └── Universe + rules + constraints + parameters
  │          │         └── When (condition) → Then (action)
  │          └── Boolean expression over signals
  └── Numeric value (price, indicator, fundamental, portfolio state)
```

### Key Sections in Strategy

| Section | Purpose |
|---------|---------|
| `info` | Metadata (id, name, version) |
| `universe` | What to trade |
| `signals` | Reusable signal definitions |
| `conditions` | Reusable condition definitions |
| `rules` | When (condition) → Then (action) |
| `constraints` | Risk limits and stops |
| `schedule` | When to evaluate |
| `parameters` | Optimizable values |

---

## Type Hierarchy

### Signal Types
| Type | Description | Example |
|------|-------------|---------|
| `price` | OHLCV data | `close`, `volume` |
| `indicator` | Technical indicators | `RSI(14)`, `SMA(20)` |
| `fundamental` | Company metrics | `PE_RATIO`, `MARKET_CAP` |
| `calendar` | Date patterns | `day_of_week`, `is_month_end` |
| `event` | Market events | `EARNINGS_RELEASE` |
| `portfolio` | Position state | `unrealized_pnl`, `days_in_position` |
| `constant` | Fixed value | `30`, `0.05` |
| `arithmetic` | Math operations | `SMA(20) - SMA(50)` |
| `expr` | Custom formula | `"(close - SMA(20)) / ATR(14)"` |
| `external` | Runtime signal | Webhook, ML model |
| `$ref` | Reference | `"#/signals/rsi_14"` |
| `$param` | Parameter ref | `"rsi_period"` |

### Condition Types
| Type | Description | Example |
|------|-------------|---------|
| `comparison` | Compare signals | `RSI < 30` |
| `cross` | Crossover detection | `SMA(50) crosses above SMA(200)` |
| `range` | Between bounds | `20 < RSI < 80` |
| `and`/`or`/`not` | Logical operators | `RSI < 30 AND MACD > 0` |
| `temporal` | Time-based | `RSI < 30 for 3 bars` |
| `sequence` | Ordered pattern | `A then B within 5 bars` |
| `change` | Delta detection | `RSI increased 10 in 3 bars` |
| `always` | Unconditional | For scheduled rebalancing |

### Action Types
| Type | Description |
|------|-------------|
| `trade` | Buy/sell/short/cover |
| `rebalance` | Adjust to target weights |
| `alert` | Send notification |
| `hold` | Explicit no-op |

### Sizing Types
| Type | Description |
|------|-------------|
| `fixed_amount` | Fixed currency amount |
| `percent_of_equity` | % of portfolio |
| `percent_of_position` | % of current position |
| `risk_based` | Based on stop distance |
| `kelly` | Kelly criterion |
| `volatility_adjusted` | Target volatility |
| `conditional` | Varies by condition |

---

## Supported Markets

### Indices
**Japan (Primary Focus):**
- `NIKKEI225`, `TOPIX`, `TOPIX100`, `TOPIX500`
- `JPXNIKKEI400`, `TSE_PRIME`, `TSE_STANDARD`, `TSE_GROWTH`
- `TOPIX_LARGE70`, `TOPIX_MID400`, `TOPIX_SMALL`, `MOTHERS`

**US:**
- `SP500`, `NASDAQ100`, `DOW30`, `RUSSELL2000`, `RUSSELL1000`, `SP400`, `SP600`

**Europe:**
- `FTSE100`, `DAX40`, `CAC40`, `STOXX50`, `STOXX600`

**Asia Pacific:**
- `HANG_SENG`, `SSE50`, `CSI300`, `KOSPI`, `KOSDAQ`, `TWSE`, `ASX200`

**Global:**
- `MSCI_WORLD`, `MSCI_EM`, `MSCI_ACWI`, `MSCI_EAFE`

---

## Extensibility Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Strict Core (fully validated, portable)          │
│    - Known indicators: RSI, SMA, MACD, ATR, ...            │
│    - Known conditions: comparison, cross, range, ...       │
│    - Known actions: trade, rebalance, alert                │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Expression Language (parsed, semi-portable)      │
│    - type: expr                                             │
│    - formula: "(SMA(20) - SMA(50)) / ATR(14)"              │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: External Signals (runtime-resolved)              │
│    - type: external                                         │
│    - source: webhook | file | provider                     │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: x-extensions (platform-specific, pass-through)   │
│    - x-backtest: { slippage: 0.001 }                       │
│    - x-freqtrade: { ... }                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Sync Rules

When modifying the schema:

1. **Update JSON Schema first** (`schema/v2/strategy.schema.json`)
   - This is the source of truth
   - All other implementations derive from this

2. **Update Python models** (`python/utss/models.py`)
   - Must match JSON Schema exactly
   - Run `uv run mypy utss --ignore-missing-imports` to verify types

3. **Add example** (`examples/`)
   - Every new feature needs a working example

4. **Run all tests**
   ```bash
   cd python && uv run pytest
   ```

---

## Downstream Application Considerations

### For LLM Integration
- Schema has consistent `type` discriminators
- Enums are human-readable
- Examples serve as few-shot prompts
- Validation provides clear error messages

### For Backtesting Engines
- All state needed for simulation is in schema
- No ambiguity in condition semantics
- Priority field determines rule evaluation order
- Schedule defines evaluation frequency

### For Parameter Optimization
- `parameters` section defines optimizable values
- Min/max/step for numeric parameters
- `$param` references in signals/conditions

### For Live Trading
- Order types and time-in-force specified
- Constraints define risk limits
- Schedule defines market hours

---

## Version History

| Version | Status | Changes |
|---------|--------|---------|
| v2.0 | Released | Initial schema with signals, conditions, rules |
| v2.1 | Current | Portfolio signals, expressions, parameters, extended indicators/indices |

---

## References

- JSON Schema: https://json-schema.org/
- Pydantic: https://docs.pydantic.dev/
- Similar projects studied:
  - QuantConnect LEAN (component architecture)
  - bt (composable algos)
  - TradingView Pine Script (expression language)
