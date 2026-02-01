# MCP Integration Guide

`utss-mcp` provides a Model Context Protocol (MCP) server for integrating UTSS with Claude Code and other MCP-compatible tools.

## Installation

```bash
pip install utss-mcp
```

This installs both `utss` and `pyutss` as dependencies.

## Claude Code Configuration

### 1. Add to claude_desktop_config.json

Add the UTSS MCP server to your Claude Code configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "utss": {
      "command": "utss-mcp"
    }
  }
}
```

If you installed in a virtual environment:

```json
{
  "mcpServers": {
    "utss": {
      "command": "/path/to/venv/bin/utss-mcp"
    }
  }
}
```

### 2. Restart Claude Code

After updating the configuration, restart Claude Code to load the UTSS tools.

### 3. Verify Installation

In Claude Code, you should now see the UTSS tools available:

- `build_strategy`
- `validate_strategy`
- `backtest_strategy`
- `list_indicators`
- `revise_strategy`

## Available Tools

### build_strategy

Build a trading strategy interactively through guided conversation.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Strategy description or answer to current question |
| `session_id` | string | No | Session ID to continue (omit for new session) |

**Example:**

```
User: I want to build an RSI mean reversion strategy

Claude: [Uses build_strategy tool with prompt="I want to build an RSI mean reversion strategy"]

Response:
{
  "session_id": "abc123",
  "message": "Let's build your trading strategy step by step.",
  "question": {
    "id": "strategy_type",
    "text": "What type of strategy?",
    "options": [
      {"id": "mean_reversion", "label": "Mean Reversion"},
      {"id": "trend_following", "label": "Trend Following"},
      ...
    ]
  }
}

User: mean reversion

Claude: [Uses build_strategy tool with prompt="mean_reversion", session_id="abc123"]

... continues until strategy is complete ...
```

### validate_strategy

Validate a UTSS strategy YAML against the schema.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `strategy_yaml` | string | Yes | The UTSS strategy in YAML format |

**Example:**

```
User: Validate this strategy:
```yaml
info:
  id: test
  name: Test Strategy
  version: "1.0"
universe:
  type: static
  symbols: [AAPL]
rules:
  - name: Buy
    when:
      type: always
    then:
      type: trade
      direction: buy
```

Claude: [Uses validate_strategy tool]

Response:
{
  "valid": true,
  "strategy": {
    "info": {...},
    "universe": {...},
    ...
  }
}
```

### backtest_strategy

Run a backtest simulation on a UTSS strategy.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `strategy_yaml` | string | Yes | The UTSS strategy in YAML format |
| `symbol` | string | Yes | Stock symbol (e.g., "AAPL", "7203.T") |
| `start_date` | string | Yes | Start date (YYYY-MM-DD) |
| `end_date` | string | Yes | End date (YYYY-MM-DD) |
| `initial_capital` | number | No | Starting capital (default: 100000) |

**Example:**

```
User: Backtest this RSI strategy on AAPL from 2023-01-01 to 2024-01-01

Claude: [Uses backtest_strategy tool]

Response:
{
  "success": true,
  "metrics": {
    "total_return_pct": 15.32,
    "sharpe_ratio": 1.24,
    "max_drawdown_pct": 8.45,
    "win_rate": 58.3,
    "total_trades": 24,
    "profit_factor": 1.85
  },
  "trades": [
    {
      "entry_date": "2023-01-15",
      "exit_date": "2023-01-22",
      "direction": "long",
      "pnl": 234.50,
      "pnl_pct": 2.34
    },
    ...
  ]
}
```

### list_indicators

List all supported technical indicators for UTSS strategies.

**Parameters:** None

**Example:**

```
User: What indicators can I use?

Claude: [Uses list_indicators tool]

Response:
{
  "moving_averages": {
    "SMA": "Simple Moving Average",
    "EMA": "Exponential Moving Average",
    "WMA": "Weighted Moving Average"
  },
  "momentum": {
    "RSI": "Relative Strength Index (0-100)",
    "STOCH": "Stochastic Oscillator",
    "CCI": "Commodity Channel Index",
    "MFI": "Money Flow Index",
    "ROC": "Rate of Change",
    "WILLIAMS_R": "Williams %R",
    "ADX": "Average Directional Index"
  },
  "volatility": {
    "ATR": "Average True Range",
    "BB": "Bollinger Bands"
  },
  "trend": {
    "MACD": "Moving Average Convergence Divergence"
  },
  "volume": {
    "OBV": "On-Balance Volume",
    "VWAP": "Volume Weighted Average Price"
  }
}
```

### revise_strategy

Revise a strategy being built in an active session.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | The session ID from build_strategy |
| `instruction` | string | Yes | What to change (e.g., "change RSI to 25") |

**Example:**

```
User: Change the RSI entry threshold to 25

Claude: [Uses revise_strategy tool with session_id="abc123", instruction="change RSI entry to 25"]

Response:
{
  "success": true,
  "message": "Strategy updated. Here's the revised version:",
  "preview_yaml": "info:\n  id: rsi_reversal\n  ...",
  "changes": [
    "Entry threshold changed from 30 to 25"
  ]
}
```

## Example Workflow

Here's a complete workflow using Claude Code with UTSS:

### 1. Build a Strategy

```
User: Help me create an RSI mean reversion strategy for AAPL

Claude: I'll help you build this strategy step by step.
[Uses build_strategy tool]

Let me start building your RSI strategy. I see you want a mean reversion
approach for AAPL. Let me configure this:

[Continues conversation, answering questions...]

Here's your completed strategy:

```yaml
info:
  id: rsi_reversal
  name: RSI Reversal Strategy
  version: "1.0"
...
```

### 2. Validate the Strategy

```
User: Make sure this is valid

Claude: [Uses validate_strategy tool]

✓ Strategy is valid and conforms to UTSS v1.0 schema.
```

### 3. Backtest

```
User: Backtest it on AAPL for 2023

Claude: [Uses backtest_strategy tool]

Backtest Results for AAPL (2023-01-01 to 2023-12-31):

| Metric | Value |
|--------|-------|
| Total Return | 15.32% |
| Sharpe Ratio | 1.24 |
| Max Drawdown | 8.45% |
| Win Rate | 58.3% |
| Total Trades | 24 |
```

### 4. Refine

```
User: The win rate is a bit low. Try RSI entry at 25 instead of 30

Claude: [Uses revise_strategy tool]

Updated the entry threshold to RSI < 25.

[Uses backtest_strategy tool]

With RSI entry at 25:
| Metric | Value |
|--------|-------|
| Total Return | 12.85% |
| Win Rate | 64.2% |

The win rate improved, though total return is slightly lower due to fewer
trades. Would you like to try other adjustments?
```

## Troubleshooting

### Server Not Found

If Claude Code doesn't find the `utss-mcp` command:

1. Verify installation: `which utss-mcp` or `where utss-mcp`
2. Use the full path in the config
3. Check that the Python environment is activated

### Import Errors

If you see import errors:

```bash
# Ensure all dependencies are installed
pip install utss-mcp[all]
```

### Backtest Errors

If backtests fail:

- Check date format is YYYY-MM-DD
- Verify the symbol exists (e.g., "AAPL" not "aapl")
- Ensure date range has sufficient data (at least 50 bars recommended)
- Check internet connection for data fetching

### Session Expired

Sessions are stored in memory. If Claude Code restarts, you'll need to start a new session:

```
User: Continue building my strategy

Claude: I don't have an active session. Let's start fresh.
[Uses build_strategy tool with no session_id]
```

## Advanced Configuration

### Custom Data Provider

By default, the MCP server uses Yahoo Finance. For other data sources, you'll need to modify the server or use pyutss directly.

### Logging

Enable verbose logging:

```json
{
  "mcpServers": {
    "utss": {
      "command": "utss-mcp",
      "env": {
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Rate Limiting

For high-frequency usage, consider implementing rate limiting on the data provider side to avoid API restrictions.

## API Reference

### Server Initialization

The MCP server is created with:

```python
from mcp.server import Server
server = Server("utss-mcp")
```

### Tool Registration

Tools are registered using decorators:

```python
@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    # Handle tool calls
    ...
```

### Running the Server

```python
from utss_mcp import main
main()  # Starts stdio server
```

Or via command line:

```bash
utss-mcp
```
