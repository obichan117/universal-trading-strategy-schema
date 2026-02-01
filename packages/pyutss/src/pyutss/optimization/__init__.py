"""Optimization module for strategy parameter tuning.

Provides walk-forward optimization and grid search capabilities.

Example:
    from pyutss.optimization import WalkForwardOptimizer

    optimizer = WalkForwardOptimizer(
        strategy=strategy,
        param_grid={
            "rsi_period": [10, 14, 20],
            "rsi_oversold": [25, 30, 35],
        },
        n_splits=5,
        optimize_metric="sharpe_ratio",
    )

    result = optimizer.run(data, symbol="AAPL")
    print(f"Best params: {result.best_params}")
    print(f"Out-of-sample Sharpe: {result.out_of_sample_sharpe}")
"""

from pyutss.optimization.grid_search import GridSearchOptimizer, RandomSearchOptimizer
from pyutss.optimization.result import OptimizationResult, WalkForwardResult
from pyutss.optimization.splits import PurgedKFold, TimeSeriesSplit
from pyutss.optimization.walkforward import WalkForwardOptimizer

__all__ = [
    "WalkForwardOptimizer",
    "GridSearchOptimizer",
    "RandomSearchOptimizer",
    "TimeSeriesSplit",
    "PurgedKFold",
    "OptimizationResult",
    "WalkForwardResult",
]
