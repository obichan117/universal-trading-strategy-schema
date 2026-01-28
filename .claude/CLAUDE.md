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
├── schema/v2/
│   └── strategy.schema.json        # JSON Schema (SOURCE OF TRUTH)
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

1. **Update JSON Schema first** (`schema/v2/strategy.schema.json`)
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

## Conversational Strategy Building

The `utss-llm` package provides a guided conversation flow for building strategies:

```python
from utss_llm.conversation import ConversationSession

session = ConversationSession()

# Start conversation
response = await session.start("I want a mean reversion strategy")
print(response.message)      # "What type of strategy..."
print(response.question)     # Question with options

# Answer with option id or number
response = await session.answer("mean_reversion")  # or "1"

# Continue until complete
while not response.is_complete:
    response = await session.answer(user_input)

# Get final YAML
print(response.strategy_yaml)
```

### Conversation Flow

```
strategy_type → universe_type → universe_details → entry_indicator
     → entry_params → exit_params → position_size → stop_loss
     → take_profit → max_positions → confirm → COMPLETE
```

---

## MCP Server Integration

The `utss-mcp` package provides an MCP server for Claude Code:

```json
// Add to Claude Code MCP config
{
  "mcpServers": {
    "utss": {
      "command": "utss-mcp",
      "args": []
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `build_strategy` | Interactive strategy builder with guided questions |
| `validate_strategy` | Validate UTSS YAML against schema |
| `backtest_strategy` | Run backtest simulation with metrics |
| `list_indicators` | List supported technical indicators |
| `revise_strategy` | Modify strategy in active session |

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

---

## Design Principles

### 1. Schema as Contract
The schema is a contract between strategy authors and execution engines. Any valid UTSS document should be executable by any compliant engine.

### 2. LLM-Friendly
- Predictable structure (consistent patterns)
- Clear type discriminators (`type` field)
- Self-documenting enums (readable values)
- Reasonable defaults

### 3. Composition Over Inheritance
- Strategies compose signals, conditions, rules
- Reusable components via `$ref`
- No inheritance hierarchy

### 4. Execution-Agnostic
- Schema defines WHAT, not HOW
- Indicator formulas computed by execution engine
- Slippage/commission models are engine concerns

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
- Documentation: https://obichan117.github.io/utss/
