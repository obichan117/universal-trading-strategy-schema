"""
pyutss - Python backtesting engine for UTSS strategies.

A backtesting engine that executes UTSS (Universal Trading Strategy Schema) strategies
against historical market data.

Example:
    from pyutss import BacktestEngine, BacktestConfig
    from utss import load_yaml

    # Load strategy
    strategy = load_yaml("my_strategy.yaml")

    # Configure and run backtest
    engine = BacktestEngine(config=BacktestConfig(initial_capital=100000))
    result = engine.run(strategy, data=ohlcv_df, symbol="AAPL")

    print(f"Total return: {result.total_return_pct:.2f}%")

Advanced features:
    # Multi-symbol portfolio backtesting
    from pyutss.portfolio import PortfolioBacktester, PortfolioConfig

    # Walk-forward optimization
    from pyutss.optimization import WalkForwardOptimizer

    # Monte Carlo analysis
    from pyutss.analysis import MonteCarloSimulator

    # Performance visualization
    from pyutss.visualization import TearSheet
"""

__version__ = "0.1.0"

# Data models
from pyutss.data.models import (
    OHLCV,
    FundamentalMetrics,
    Market,
    StockMetadata,
    Timeframe,
)

# Data providers
from pyutss.data.providers.base import BaseDataProvider, DataProviderError

# Engine components
from pyutss.engine.backtest import BacktestEngine
from pyutss.engine.evaluator import (
    ConditionEvaluator,
    EvaluationContext,
    EvaluationError,
    PortfolioState,
    SignalEvaluator,
)
from pyutss.engine.indicators import (
    BollingerBandsResult,
    IndicatorService,
    MACDResult,
    StochasticResult,
)

# Metrics
from pyutss.metrics.benchmark import (
    BenchmarkMetrics,
    calculate_benchmark_metrics,
)
from pyutss.metrics.calculator import (
    MetricsCalculator,
    PerformanceMetrics,
    PeriodBreakdown,
)

# Result types
from pyutss.results.types import (
    BacktestConfig,
    BacktestResult,
    PortfolioSnapshot,
    Position,
    Trade,
)

# Analysis
from pyutss.analysis.monte_carlo import (
    MonteCarloResult,
    MonteCarloSimulator,
)

# Note: Portfolio, optimization, and visualization modules are imported
# from their subpackages to avoid loading heavy dependencies at import time.
# Use: from pyutss.portfolio import PortfolioBacktester
#      from pyutss.optimization import WalkForwardOptimizer
#      from pyutss.visualization import TearSheet

__all__ = [
    # Version
    "__version__",
    # Data models
    "OHLCV",
    "StockMetadata",
    "FundamentalMetrics",
    "Market",
    "Timeframe",
    # Data providers
    "BaseDataProvider",
    "DataProviderError",
    # Engine
    "BacktestEngine",
    "BacktestConfig",
    "SignalEvaluator",
    "ConditionEvaluator",
    "EvaluationContext",
    "EvaluationError",
    "PortfolioState",
    "IndicatorService",
    "MACDResult",
    "BollingerBandsResult",
    "StochasticResult",
    # Results
    "BacktestResult",
    "Trade",
    "Position",
    "PortfolioSnapshot",
    # Metrics
    "MetricsCalculator",
    "PerformanceMetrics",
    "PeriodBreakdown",
    "BenchmarkMetrics",
    "calculate_benchmark_metrics",
    # Analysis
    "MonteCarloSimulator",
    "MonteCarloResult",
]
