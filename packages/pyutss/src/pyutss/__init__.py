"""
pyutss - Python backtesting engine for UTSS strategies.

A backtesting engine that executes UTSS (Universal Trading Strategy Schema) strategies
against historical market data.

Example:
    from pyutss import Engine
    from utss import load_yaml

    # Load strategy
    strategy = load_yaml("my_strategy.yaml")

    # Run backtest
    engine = Engine(initial_capital=100000)
    result = engine.backtest(strategy, data=ohlcv_df, symbol="AAPL")

    print(f"Total return: {result.total_return_pct:.2f}%")

Advanced features:
    # Multi-symbol portfolio backtesting
    result = engine.backtest(strategy, data={"AAPL": df1, "MSFT": df2}, weights="equal")

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
from pyutss.engine.engine import Engine
from pyutss.engine.evaluator import (
    ConditionEvaluator,
    EvaluationContext,
    EvaluationError,
    EvaluationPortfolioState,
    PortfolioState,
    SignalEvaluator,
)
from pyutss.engine.indicators import (
    BollingerBandsResult,
    IndicatorService,
    MACDResult,
    StochasticResult,
)
from pyutss.engine.executor import BacktestExecutor, Fill, OrderRequest
from pyutss.engine.portfolio import PortfolioManager
from pyutss.engine.sizing import calculate_size, round_to_lot
from pyutss.engine.universe import UniverseResolver
from pyutss.engine.live_executor import (
    AccountInfo,
    AlpacaExecutor,
    LiveExecutorBase,
    PaperExecutor,
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
# Use: from pyutss.optimization import WalkForwardOptimizer
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
    "Engine",
    "BacktestConfig",
    "SignalEvaluator",
    "ConditionEvaluator",
    "EvaluationContext",
    "EvaluationError",
    "EvaluationPortfolioState",
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
    # Engine - new modules
    "BacktestExecutor",
    "OrderRequest",
    "Fill",
    "PortfolioManager",
    "calculate_size",
    "round_to_lot",
    "UniverseResolver",
    "PaperExecutor",
    "AlpacaExecutor",
    "LiveExecutorBase",
    "AccountInfo",
    # Analysis
    "MonteCarloSimulator",
    "MonteCarloResult",
]
