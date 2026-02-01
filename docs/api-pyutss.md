# pyutss API Reference

`pyutss` is the Python backtesting engine for UTSS strategies. It executes strategies against historical market data and provides comprehensive performance analysis.

## Installation

```bash
# Basic installation
pip install pyutss

# With optional dependencies for visualization
pip install pyutss[visualization]

# Development installation
pip install pyutss[dev]
```

## Quick Start

```python
from pyutss import BacktestEngine, BacktestConfig
from utss import load_yaml
import pandas as pd

# Load strategy
strategy = load_yaml("my_strategy.yaml")

# Get historical data (OHLCV DataFrame)
data = pd.read_csv("AAPL.csv", index_col="date", parse_dates=True)

# Configure backtest
config = BacktestConfig(
    initial_capital=100000,
    commission_rate=0.001,
    slippage_rate=0.0005,
)

# Run backtest
engine = BacktestEngine(config=config)
result = engine.run(strategy, data=data, symbol="AAPL")

# View results
print(f"Total Return: {result.total_return_pct:.2f}%")
print(f"Win Rate: {result.win_rate:.1f}%")
result.summary()
```

## BacktestEngine

The main entry point for running backtests.

### Constructor

```python
BacktestEngine(config: BacktestConfig | None = None)
```

### Methods

#### `run(strategy, data, symbol) -> BacktestResult`

Execute a backtest for a single symbol.

```python
result = engine.run(
    strategy=strategy,          # UTSS Strategy object
    data=ohlcv_dataframe,       # DataFrame with OHLCV columns
    symbol="AAPL",              # Symbol identifier
)
```

**Parameters:**

- `strategy`: Validated UTSS Strategy object
- `data`: pandas DataFrame with columns: `open`, `high`, `low`, `close`, `volume`
- `symbol`: String identifier for the symbol

**Returns:** `BacktestResult` with trades, equity curve, and metrics

## BacktestConfig

Configuration for backtest execution.

```python
@dataclass
class BacktestConfig:
    initial_capital: float = 100000.0
    commission_rate: float = 0.001      # 0.1% per trade
    slippage_rate: float = 0.0005       # 0.05% slippage
    risk_free_rate: float = 0.0         # Annual risk-free rate
    margin_requirement: float = 1.0     # 1.0 = no margin
```

## BacktestResult

Contains all results from a backtest run.

### Properties

```python
result.strategy_id      # Strategy identifier
result.symbol           # Symbol traded
result.start_date       # Backtest start date
result.end_date         # Backtest end date
result.initial_capital  # Starting capital
result.final_equity     # Ending equity
result.total_return     # Total return in currency
result.total_return_pct # Total return as percentage
result.num_trades       # Total number of trades
result.win_rate         # Win rate percentage
result.trades           # List of Trade objects
result.equity_curve     # pd.Series of daily equity
result.portfolio_history # List of PortfolioSnapshot
```

### Methods

#### `summary(print_output=True) -> str`

Generate and print a formatted summary.

```python
result.summary()
# ══════════════════════════════════════════════════
#  Backtest Results: AAPL
# ══════════════════════════════════════════════════
#  Period: 2023-01-01 to 2024-01-01
#  Initial Capital: $100,000.00
#  Final Equity: $115,432.50
#  ...
```

#### `plot(data, **kwargs)`

Plot backtest results with candlestick chart.

```python
result.plot(
    data=ohlcv_df,
    title="My Strategy",
    show_equity=True,
    show_volume=True,
    figsize=(14, 8),
)
```

## Data Providers

### YahooDataProvider

Fetch data from Yahoo Finance.

```python
from pyutss.data.providers import YahooDataProvider

provider = YahooDataProvider()

# Get historical data
data = provider.get_ohlcv(
    symbol="AAPL",
    start_date="2023-01-01",
    end_date="2024-01-01",
)
```

### JQuantsDataProvider

Fetch Japanese market data from J-Quants.

```python
from pyutss.data.providers import JQuantsDataProvider

provider = JQuantsDataProvider(
    mail_address="your@email.com",
    password="your_password",
)

# Get Japanese stock data
data = provider.get_ohlcv(
    symbol="7203.T",  # Toyota
    start_date="2023-01-01",
    end_date="2024-01-01",
)
```

### Custom Provider

Implement your own data provider:

```python
from pyutss.data.providers import BaseDataProvider

class MyProvider(BaseDataProvider):
    def get_ohlcv(self, symbol, start_date, end_date) -> pd.DataFrame:
        # Your implementation
        pass
```

## MetricsCalculator

Calculate comprehensive performance metrics.

```python
from pyutss import MetricsCalculator

calculator = MetricsCalculator(risk_free_rate=0.02)
metrics = calculator.calculate(result)

print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
print(f"Max Drawdown: {metrics.max_drawdown_pct:.2f}%")
print(f"Profit Factor: {metrics.profit_factor:.2f}")
```

### PerformanceMetrics

All calculated metrics:

```python
@dataclass
class PerformanceMetrics:
    # Returns
    total_return: float
    total_return_pct: float
    annualized_return: float
    annualized_return_pct: float

    # Risk-adjusted
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

    # Drawdown
    max_drawdown: float
    max_drawdown_pct: float
    max_drawdown_duration_days: int
    avg_drawdown: float
    avg_drawdown_pct: float

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_trade_pnl: float
    avg_trade_duration_days: float

    # Risk
    volatility: float
    volatility_annualized: float
    downside_deviation: float

    # Exposure
    total_exposure_days: int
    exposure_pct: float
```

### Period Breakdown

Get monthly or yearly breakdowns:

```python
monthly = calculator.monthly_breakdown(result)
for period in monthly:
    print(f"{period.period}: {period.return_pct:.2f}%")

yearly = calculator.yearly_breakdown(result)
```

## BenchmarkMetrics

Compare strategy performance against a benchmark.

```python
from pyutss import calculate_benchmark_metrics

# Get benchmark data
benchmark_returns = spy_data["close"].pct_change().dropna()
strategy_returns = result.equity_curve.pct_change().dropna()

metrics = calculate_benchmark_metrics(
    strategy_returns=strategy_returns,
    benchmark_returns=benchmark_returns,
    risk_free_rate=0.02,
)

print(f"Alpha: {metrics.alpha:.2%}")
print(f"Beta: {metrics.beta:.2f}")
print(f"Information Ratio: {metrics.information_ratio:.2f}")
print(f"Tracking Error: {metrics.tracking_error:.2%}")
print(f"Up Capture: {metrics.up_capture:.1f}%")
print(f"Down Capture: {metrics.down_capture:.1f}%")
```

## MonteCarloSimulator

Analyze strategy robustness with Monte Carlo simulation.

```python
from pyutss import MonteCarloSimulator

simulator = MonteCarloSimulator(seed=42)

# Shuffle trades to analyze path dependency
mc_result = simulator.shuffle_trades(
    trades=result.trades,
    initial_capital=100000,
    n_iterations=1000,
)

print(mc_result.summary())
# Monte Carlo Simulation Results (1,000 iterations)
# ==================================================
# Drawdown Analysis:
#   Median Max Drawdown: 8.50%
#   95th Percentile:     15.20%
#   99th Percentile:     19.80%
#
# Return Analysis (95% CI):
#   Total Return: [5.20%, 25.80%]
#   Sharpe Ratio: [0.52, 1.45]

# Bootstrap returns for confidence intervals
mc_result = simulator.bootstrap_returns(
    returns=result.equity_curve.pct_change().dropna(),
    n_iterations=1000,
    block_size=20,  # Block bootstrap
)
```

## Portfolio Backtester

Test strategies across multiple symbols.

```python
from pyutss.portfolio import PortfolioBacktester, PortfolioConfig

config = PortfolioConfig(
    initial_capital=1000000,
    rebalance_frequency="monthly",
    weight_scheme="equal",
)

backtester = PortfolioBacktester(config=config)

# Prepare data for multiple symbols
data_dict = {
    "AAPL": aapl_data,
    "MSFT": msft_data,
    "GOOGL": googl_data,
}

result = backtester.run(strategy, data_dict)
```

### Weight Schemes

- `equal`: Equal weight across all positions
- `inverse_volatility`: Weight inversely to volatility
- `risk_parity`: Target equal risk contribution
- `market_cap`: Weight by market capitalization

## Optimization

### Grid Search

```python
from pyutss.optimization import GridSearchOptimizer

optimizer = GridSearchOptimizer()

param_grid = {
    "rsi_period": [10, 14, 20],
    "entry_threshold": [25, 30, 35],
    "exit_threshold": [65, 70, 75],
}

results = optimizer.optimize(
    strategy=strategy,
    data=data,
    symbol="AAPL",
    param_grid=param_grid,
    metric="sharpe_ratio",
)

print(f"Best params: {results.best_params}")
print(f"Best Sharpe: {results.best_score:.2f}")
```

### Walk-Forward Optimization

```python
from pyutss.optimization import WalkForwardOptimizer

optimizer = WalkForwardOptimizer(
    train_period=252,  # 1 year training
    test_period=63,    # 3 month testing
    step=21,           # Step by 1 month
)

results = optimizer.optimize(
    strategy=strategy,
    data=data,
    symbol="AAPL",
    param_grid=param_grid,
)

# Results include out-of-sample performance
print(f"In-sample Sharpe: {results.in_sample_sharpe:.2f}")
print(f"Out-of-sample Sharpe: {results.out_of_sample_sharpe:.2f}")
```

## Visualization

### TearSheet

Generate comprehensive performance report.

```python
from pyutss.visualization import TearSheet

sheet = TearSheet(result)
sheet.generate()  # Opens in browser

# Or save to file
sheet.save("tearsheet.html")
```

### Charts

```python
from pyutss.visualization import plot_equity_curve, plot_drawdown

# Equity curve
plot_equity_curve(result.equity_curve)

# Drawdown chart
plot_drawdown(result.equity_curve)
```

### HTML Report

```python
from pyutss.visualization import HTMLReport

report = HTMLReport(result)
report.generate("backtest_report.html")
```

## Signal and Condition Evaluators

For advanced use cases, access evaluators directly:

```python
from pyutss import SignalEvaluator, ConditionEvaluator, EvaluationContext

# Create context
ctx = EvaluationContext(primary_data=ohlcv_df)

# Evaluate signals
signal_eval = SignalEvaluator()
rsi_values = signal_eval.evaluate_signal(
    {"type": "indicator", "indicator": "RSI", "params": {"period": 14}},
    ctx,
)

# Evaluate conditions
cond_eval = ConditionEvaluator(signal_eval)
is_oversold = cond_eval.evaluate_condition(
    {"type": "comparison", "left": ..., "operator": "<", "right": ...},
    ctx,
)
```

## Error Handling

```python
from pyutss import EvaluationError, DataProviderError

try:
    result = engine.run(strategy, data, "AAPL")
except EvaluationError as e:
    print(f"Strategy evaluation failed: {e}")
except DataProviderError as e:
    print(f"Data fetch failed: {e}")
```

## Type Exports

All major types are exported at the package level:

```python
from pyutss import (
    # Engine
    BacktestEngine,
    BacktestConfig,

    # Results
    BacktestResult,
    Trade,
    Position,
    PortfolioSnapshot,

    # Metrics
    MetricsCalculator,
    PerformanceMetrics,
    PeriodBreakdown,
    BenchmarkMetrics,
    calculate_benchmark_metrics,

    # Analysis
    MonteCarloSimulator,
    MonteCarloResult,

    # Data
    OHLCV,
    StockMetadata,
    BaseDataProvider,

    # Evaluation
    SignalEvaluator,
    ConditionEvaluator,
    EvaluationContext,
    IndicatorService,
)
```
