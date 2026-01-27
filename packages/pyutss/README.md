# pyutss - Python Backtesting Engine for UTSS

A backtesting engine that executes [UTSS](https://github.com/obichan117/utss) (Universal Trading Strategy Schema) strategies.

## Installation

```bash
# Core package
pip install pyutss

# With J-Quants support (Japanese stocks)
pip install pyutss[jquants]

# With Yahoo Finance support
pip install pyutss[yahoo]

# With all data providers
pip install pyutss[all]
```

## Quick Start

```python
from utss import validate_yaml
from pyutss import BacktestEngine
from pyutss.data import YahooProvider

# Load strategy
strategy = validate_yaml(open("my_strategy.yaml").read())

# Setup data provider
provider = YahooProvider()

# Run backtest
engine = BacktestEngine(provider, initial_capital=100_000)
result = engine.run(strategy, start="2020-01-01", end="2024-01-01")

# View results
print(result.metrics.sharpe_ratio)
print(result.metrics.max_drawdown)
result.plot()
```

## Features

- **UTSS Native**: Directly executes UTSS strategy definitions
- **Multiple Data Sources**: J-Quants (Japan), Yahoo Finance (US/Global)
- **Comprehensive Metrics**: Sharpe, Sortino, max drawdown, win rate, and more
- **Indicator Support**: 50+ technical indicators matching UTSS schema

## Documentation

Full documentation: https://obichan117.github.io/utss

## License

MIT
