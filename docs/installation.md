# Installation

## Python Packages

UTSS provides multiple packages for different use cases:

| Package | Description |
|---------|-------------|
| `utss` | Core schema and validation |
| `pyutss` | Backtesting engine with indicators and metrics |
| `utss-llm` | LLM integration and conversational strategy builder |
| `utss-mcp` | MCP server for Claude Code integration |

### Using pip

```bash
pip install utss           # Schema only
pip install pyutss         # With backtesting engine
pip install utss-llm       # With LLM/conversation features
pip install utss-mcp       # MCP server for Claude Code
```

### Using uv (recommended)

```bash
uv add utss           # Schema only
uv add pyutss         # With backtesting engine
uv add utss-llm       # With LLM features
uv add utss-mcp       # MCP server
```

### Using poetry

```bash
poetry add utss
poetry add pyutss
poetry add utss-llm
poetry add utss-mcp
```

### From source

```bash
git clone https://github.com/obichan117/universal-trading-strategy-schema.git
cd universal-trading-strategy-schema

# Install all packages in development mode
uv sync
```

---

## Requirements

- Python 3.10 or higher
- pydantic >= 1.0.0
- pyyaml >= 6.0

---

## Verify Installation

```python
import utss

print(f"UTSS version: {utss.__version__}")

# Test validation
from utss import validate_yaml

yaml = """
info:
  id: test
  name: Test
  version: "1.0"
universe:
  type: static
  symbols: [AAPL]
rules:
  - name: Buy
    when: { type: always }
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 100 }
"""

strategy = validate_yaml(yaml)
print(f"Strategy loaded: {strategy.info.name}")
```

Expected output:

```
UTSS version: 1.0.0
Strategy loaded: Test
```

---

## Development Installation

For contributing or running tests:

```bash
git clone https://github.com/obichan117/universal-trading-strategy-schema.git
cd universal-trading-strategy-schema

# Install all workspace packages with dev dependencies
uv sync

# Run all tests (132 tests across all packages)
uv run pytest

# Run tests for specific package
uv run pytest packages/utss-mcp/tests -v
```

---

## Documentation Development

To build and preview documentation locally:

```bash
# Install docs dependencies
uv sync --extra docs

# Serve locally
uv run mkdocs serve

# Build static site
uv run mkdocs build --strict
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

---

## MCP Server Setup (Claude Code)

To use UTSS with Claude Code:

1. Install the MCP package:
   ```bash
   pip install utss-mcp
   ```

2. Add to your Claude Code MCP configuration (`~/.claude/mcp.json` or project config):
   ```json
   {
     "mcpServers": {
       "utss": {
         "command": "utss-mcp",
         "args": []
       }
     }
   }
   ```

3. Use in Claude Code:
   ```
   You: Help me build a mean reversion strategy for tech stocks

   Claude: [calls build_strategy tool]
           What type of strategy would you like?
           1. Mean Reversion
           2. Trend Following
           3. Breakout
           ...
   ```

### Available MCP Tools

- **build_strategy** - Interactive strategy builder with guided questions
- **validate_strategy** - Validate UTSS YAML against schema
- **backtest_strategy** - Run backtest with performance metrics
- **list_indicators** - List supported technical indicators
- **revise_strategy** - Modify strategy in active session
