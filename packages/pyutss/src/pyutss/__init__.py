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
]
