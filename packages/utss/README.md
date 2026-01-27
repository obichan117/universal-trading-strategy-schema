# UTSS - Universal Trading Strategy Schema

A comprehensive, composable schema for expressing any trading strategy.

## Installation

```bash
pip install utss
```

## Quick Start

```python
from utss import validate_yaml, Strategy

# Load and validate a strategy from YAML
strategy = validate_yaml("""
info:
  id: rsi-reversal
  name: RSI Reversal Strategy
  version: "1.0"

universe:
  type: static
  symbols: ["AAPL", "GOOGL"]

rules:
  - name: buy-oversold
    when:
      type: comparison
      left:
        type: indicator
        indicator: RSI
        params:
          period: 14
      operator: "<"
      right:
        type: constant
        value: 30
    then:
      type: trade
      direction: buy
      sizing:
        type: percent_of_equity
        percent: 10
""")

print(f"Strategy: {strategy.info.name}")
print(f"Universe: {strategy.universe}")
print(f"Rules: {len(strategy.rules)}")
```

## Features

- **LLM-friendly**: Predictable structure, clear type discriminators
- **Composable**: Signals → Conditions → Rules → Strategy
- **Extensible**: Support for custom indicators, metrics, and events
- **Validated**: Full Pydantic v2 validation

## Documentation

Full documentation: https://obichan117.github.io/utss

## License

MIT
