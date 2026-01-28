# utss-mcp

MCP (Model Context Protocol) server for building and backtesting UTSS trading strategies with Claude.

## Installation

```bash
pip install utss-mcp
```

## Usage with Claude Code

Add to your Claude Code MCP configuration:

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

Then use in Claude Code:

```
You: Help me build a mean reversion strategy for tech stocks

Claude: I'll help you build that strategy. Let me start the interactive builder.
        [calls build_strategy]

        What type of strategy would you like?
        1. Mean Reversion - Buy oversold, sell overbought
        2. Trend Following - Follow market direction
        3. Breakout - Trade price breakouts
        4. Calendar-based - Trade on day/week patterns

You: 1

Claude: [calls build_strategy with session_id]

        Which indicator should trigger entry?
        1. RSI - Relative Strength Index
        2. Stochastic - Stochastic Oscillator
        3. Williams %R
        ...
```

## Available Tools

### build_strategy

Build a trading strategy interactively through guided questions.

```python
await build_strategy(
    prompt="I want a mean reversion strategy",
    session_id=None,  # Omit for new session
)
```

### validate_strategy

Validate a UTSS strategy YAML.

```python
await validate_strategy(strategy_yaml="info:\n  id: test\n...")
```

### backtest_strategy

Run a backtest simulation.

```python
await backtest_strategy(
    strategy_yaml="...",
    symbol="AAPL",
    start_date="2023-01-01",
    end_date="2024-01-01",
    initial_capital=100000,
)
```

### list_indicators

List all supported technical indicators.

```python
await list_indicators()
```

## Development

```bash
# Install in development mode
uv sync

# Run tests
uv run pytest packages/utss-mcp/tests

# Run server directly
uv run utss-mcp
```

## License

MIT
