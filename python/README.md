# UTSS - Universal Trading Strategy Schema (Python)

Python implementation of the Universal Trading Strategy Schema.

## Installation

```bash
pip install utss
```

## Quick Start

```python
from utss import validate_yaml, Strategy

# Validate a YAML strategy
yaml_content = """
info:
  id: my_strategy
  name: My Strategy
  version: "1.0"

universe:
  type: static
  symbols:
    - AAPL

rules:
  - name: Buy signal
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
"""

strategy = validate_yaml(yaml_content)
print(f"Strategy: {strategy.info.name}")
print(f"Rules: {len(strategy.rules)}")
```

## Models

All schema types are available as Pydantic models:

```python
from utss import (
    Strategy,
    Rule,
    IndicatorSignal,
    ComparisonCondition,
    TradeAction,
    PercentEquitySizing,
)

# Build programmatically
signal = IndicatorSignal(
    type="indicator",
    indicator="RSI",
    params={"period": 14}
)

condition = ComparisonCondition(
    type="comparison",
    left=signal,
    operator="<",
    right={"type": "constant", "value": 30}
)
```

## Validation

```python
from utss import validate_strategy, ValidationError

try:
    strategy = validate_strategy(data_dict)
except ValidationError as e:
    for error in e.errors:
        print(f"{error['path']}: {error['message']}")
```

## License

MIT
