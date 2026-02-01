# Universal Trading Strategy Schema (UTSS)

## Project Scope

**This is a monorepo containing the UTSS schema, backtesting engine, and LLM integration tools.**

```
┌─────────────────────────────────────────────────────────────────┐
│                         THIS MONOREPO                           │
│                                                                 │
│  packages/utss (pip install utss)                              │
│  • JSON Schema definition (source of truth)                    │
│  • Pydantic models for validation                              │
│  • Capabilities export for engine sync                         │
│                                                                 │
│  packages/pyutss (pip install pyutss)                          │
│  • Backtesting engine                                          │
│  • Data providers (Yahoo Finance, J-Quants)                    │
│  • Indicator calculations                                       │
│  • Performance metrics                                          │
│                                                                 │
│  packages/utss-llm (pip install utss-llm)                      │
│  • Conversational strategy builder                             │
│  • Guided question flow                                         │
│  • Natural language to UTSS parsing                            │
│                                                                 │
│  packages/utss-mcp (pip install utss-mcp)                      │
│  • MCP server for Claude Code integration                      │
│  • Tools: build, validate, backtest, revise strategies         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Install
pip install utss       # Schema only
pip install pyutss     # With backtesting engine
pip install utss-llm   # With LLM/conversation features
pip install utss-mcp   # MCP server for Claude Code

# Validate a strategy file
python -c "from utss import validate_yaml; print(validate_yaml(open('examples/rsi-reversal.yaml').read()))"

# Run MCP server (for Claude Code integration)
utss-mcp

# Development
uv sync              # Install all workspace packages
uv run pytest        # Run all tests
uv run mkdocs build  # Build documentation
```

---

## Project Structure

```
utss/
├── packages/
│   ├── utss/                       # Schema package (pip install utss)
│   │   ├── pyproject.toml
│   │   ├── src/utss/
│   │   │   ├── __init__.py         # Public API exports
│   │   │   ├── models.py           # Pydantic v2 models
│   │   │   ├── validator.py        # YAML/dict validation
│   │   │   └── capabilities.py     # Exported capabilities for engine sync
│   │   └── tests/
│   │
│   ├── pyutss/                     # Backtesting engine (pip install pyutss)
│   │   ├── pyproject.toml
│   │   ├── src/pyutss/
│   │   │   ├── data/               # Data providers
│   │   │   │   └── providers/      # Yahoo, J-Quants, etc.
│   │   │   ├── engine/             # Backtest execution
│   │   │   ├── metrics/            # Performance metrics
│   │   │   └── results/            # Result handling
│   │   └── tests/
│   │
│   ├── utss-llm/                   # LLM integration (pip install utss-llm)
│   │   ├── pyproject.toml
│   │   ├── src/utss_llm/
│   │   │   ├── conversation/       # Conversational strategy builder
│   │   │   │   ├── session.py      # ConversationSession main class
│   │   │   │   ├── builder.py      # StrategyBuilder guided flow
│   │   │   │   ├── questions.py    # Predefined questions/options
│   │   │   │   └── state.py        # State management
│   │   │   └── parser.py           # Natural language parser
│   │   └── tests/
│   │
│   └── utss-mcp/                   # MCP server (pip install utss-mcp)
│       ├── pyproject.toml
│       ├── src/utss_mcp/
│       │   ├── server.py           # MCP server implementation
│       │   └── tools.py            # Tool definitions
│       └── tests/
│
├── schema/v1/
│   └── strategy.schema.json        # JSON Schema (SOURCE OF TRUTH)
│
├── patterns/                       # Reusable condition formulas
│   ├── crossovers.yaml             # cross_above, cross_below
│   ├── ranges.yaml                 # in_range, overbought, oversold
│   ├── temporal.yaml               # for_n_bars, within_n_bars
│   ├── price_action.yaml           # higher_high, consecutive_up
│   ├── chart_patterns.yaml         # double_bottom, breakout
│   └── momentum.yaml               # divergences, rsi_reversal
│
├── examples/                       # Example strategy files
│   ├── rsi-reversal.yaml
│   ├── golden-cross.yaml
│   ├── earnings-play.yaml
│   └── monday-friday.yaml
│
├── docs/                           # Documentation
│   ├── quickstart.md
│   ├── architecture.md
│   └── specification.md
│
├── tests/
│   └── integration/                # Cross-package tests
│
├── pyproject.toml                  # Workspace root (uv workspaces)
├── mkdocs.yml                      # Documentation config
└── .claude/
    └── CLAUDE.md                   # This file
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

## Schema-Engine Sync

The `utss` package exports capabilities that `pyutss` validates against:

```python
# utss exports
from utss import (
    SCHEMA_VERSION,
    SUPPORTED_INDICATORS,
    SUPPORTED_CONDITION_TYPES,
    SUPPORTED_SIGNAL_TYPES,
    SUPPORTED_ACTION_TYPES,
    SUPPORTED_SIZING_TYPES,
)

# pyutss validates it implements everything
```

### When Modifying the Schema

1. **Update JSON Schema first** (`schema/v1/strategy.schema.json`)
   - This is the source of truth

2. **Update Python models** (`packages/utss/src/utss/models.py`)
   - Must match JSON Schema exactly

3. **Update capabilities** (`packages/utss/src/utss/capabilities.py`)
   - Export new capabilities for engine sync

4. **Add example** (`examples/`)
   - Every new feature needs a working example

5. **Run all tests**
   ```bash
   uv run pytest
   ```

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

### Condition Types (v1.0 - Minimal Primitives)
| Type | Description | Example |
|------|-------------|---------|
| `comparison` | Compare signals | `RSI < 30` |
| `and`/`or`/`not` | Logical operators | `RSI < 30 AND MACD > 0` |
| `expr` | Formula expression | `"SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"` |
| `always` | Unconditional | For scheduled rebalancing |

Complex patterns (crossovers, ranges, temporal, sequences) are expressed via `expr` formulas. See `patterns/` for reusable formulas.

---

## Design Principles

### 1. Schema as Contract
The schema is a contract between strategy authors and execution engines. Any valid UTSS document should be executable by any compliant engine.

### 2. Minimal Primitives
- Only 6 condition types: comparison, and, or, not, expr, always
- Complex patterns via expr formulas (see patterns/)
- Avoids "sugar bloat" - no unbounded type additions

### 3. LLM-Friendly
- Predictable structure (consistent patterns)
- Clear type discriminators (`type` field)
- Self-documenting enums (readable values)
- Reasonable defaults

### 4. Composition Over Inheritance
- Strategies compose signals, conditions, rules
- Reusable components via `$ref`
- No inheritance hierarchy

### 5. Execution-Agnostic
- Schema defines WHAT, not HOW
- Indicator formulas computed by execution engine
- Slippage/commission models are engine concerns

---

## Version History

| Version | Status | Changes |
|---------|--------|---------|
| v1.0 | Current | Clean design with minimal condition types + expr |

---

## Notebook Quality Assurance

**Before publishing or committing any Jupyter notebook:**

1. **Test all cells locally** - Run every cell in sequence and verify no errors
2. **Test with fresh install** - Simulate Colab environment:
   ```bash
   # Create temp venv and test
   python -m venv /tmp/nb-test && source /tmp/nb-test/bin/activate
   pip install utss pyutss  # Install from PyPI, not local
   # Then run notebook cells
   ```
3. **Check data type compatibility** - Watch for:
   - Timezone-aware vs naive datetime indices
   - `datetime.date` vs `pd.Timestamp` mismatches
   - Index alignment issues between DataFrames/Series
4. **Verify PyPI packages are published** before adding Colab badge
5. **Test the actual Colab link** after pushing

---

## References

- JSON Schema: https://json-schema.org/
- Pydantic: https://docs.pydantic.dev/
- Documentation: https://obichan117.github.io/utss/
