# Installation

## Python Package

### Using pip

```bash
pip install utss
```

### Using uv (recommended)

```bash
uv add utss
```

### Using poetry

```bash
poetry add utss
```

### From source

```bash
git clone https://github.com/obichan117/universal-trading-strategy-schema.git
cd universal-trading-strategy-schema/python
pip install -e .
```

---

## Requirements

- Python 3.10 or higher
- pydantic >= 2.0.0
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
UTSS version: 2.1.0
Strategy loaded: Test
```

---

## Development Installation

For contributing or running tests:

```bash
git clone https://github.com/obichan117/universal-trading-strategy-schema.git
cd universal-trading-strategy-schema/python

# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run type checker
uv run mypy utss --ignore-missing-imports
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
