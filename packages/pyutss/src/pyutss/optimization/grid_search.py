"""Grid search optimization for strategy parameters.

Provides exhaustive and random search over parameter grids.
"""

from __future__ import annotations

import itertools
import logging
import random
import time
from datetime import date
from typing import Any, Callable

import pandas as pd

from pyutss.engine.backtest import BacktestEngine
from pyutss.metrics.calculator import MetricsCalculator
from pyutss.optimization.result import OptimizationResult, ParameterResult
from pyutss.results.types import BacktestConfig

logger = logging.getLogger(__name__)


class GridSearchOptimizer:
    """Exhaustive grid search over parameter combinations.

    Runs backtest for every combination of parameters and returns
    the best performing set.

    Example:
        optimizer = GridSearchOptimizer(
            strategy=strategy,
            param_grid={
                "rsi_period": [10, 14, 20],
                "rsi_oversold": [25, 30, 35],
            },
            optimize_metric="sharpe_ratio",
        )

        result = optimizer.run(data, symbol="AAPL")
        print(f"Best params: {result.best_params}")
    """

    SUPPORTED_METRICS = [
        "sharpe_ratio",
        "sortino_ratio",
        "calmar_ratio",
        "total_return_pct",
        "win_rate",
        "profit_factor",
    ]

    def __init__(
        self,
        strategy: dict[str, Any],
        param_grid: dict[str, list[Any]],
        optimize_metric: str = "sharpe_ratio",
        config: BacktestConfig | None = None,
        progress_callback: Callable[[int, int, dict], None] | None = None,
    ) -> None:
        """Initialize grid search optimizer.

        Args:
            strategy: UTSS strategy definition
            param_grid: Dict mapping parameter names to lists of values
            optimize_metric: Metric to optimize (see SUPPORTED_METRICS)
            config: Backtest configuration
            progress_callback: Optional callback(current, total, params)
        """
        if optimize_metric not in self.SUPPORTED_METRICS:
            raise ValueError(
                f"Unsupported metric: {optimize_metric}. "
                f"Supported: {self.SUPPORTED_METRICS}"
            )

        self.strategy = strategy
        self.param_grid = param_grid
        self.optimize_metric = optimize_metric
        self.config = config or BacktestConfig()
        self.progress_callback = progress_callback

    def run(
        self,
        data: pd.DataFrame,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> OptimizationResult:
        """Run grid search optimization.

        Args:
            data: OHLCV DataFrame
            symbol: Stock symbol
            start_date: Backtest start date
            end_date: Backtest end date

        Returns:
            OptimizationResult with best parameters and all results
        """
        start_time = time.time()

        # Generate all parameter combinations
        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())
        combinations = list(itertools.product(*param_values))

        total_combinations = len(combinations)
        logger.info(f"Grid search: {total_combinations} combinations")

        all_results: list[ParameterResult] = []
        best_result: ParameterResult | None = None

        engine = BacktestEngine(config=self.config)
        calculator = MetricsCalculator(risk_free_rate=self.config.risk_free_rate)

        for i, values in enumerate(combinations):
            params = dict(zip(param_names, values))

            if self.progress_callback:
                self.progress_callback(i + 1, total_combinations, params)

            try:
                # Run backtest with these parameters
                result = engine.run(
                    strategy=self.strategy,
                    data=data,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    parameters=params,
                )

                # Calculate metrics
                metrics = calculator.calculate(result)

                # Get optimization metric value
                metric_value = self._get_metric_value(metrics)

                param_result = ParameterResult(
                    params=params,
                    metric_value=metric_value,
                    total_return_pct=metrics.total_return_pct,
                    sharpe_ratio=metrics.sharpe_ratio,
                    sortino_ratio=metrics.sortino_ratio,
                    max_drawdown_pct=metrics.max_drawdown_pct,
                    win_rate=metrics.win_rate,
                    num_trades=metrics.total_trades,
                )

                all_results.append(param_result)

                # Track best
                if best_result is None or metric_value > best_result.metric_value:
                    best_result = param_result

            except Exception as e:
                logger.warning(f"Backtest failed for params {params}: {e}")
                continue

        elapsed = time.time() - start_time

        if best_result is None:
            return OptimizationResult(
                best_params={},
                best_metric_value=0.0,
                optimize_metric=self.optimize_metric,
                all_results=[],
                total_combinations=total_combinations,
                elapsed_time_seconds=elapsed,
            )

        return OptimizationResult(
            best_params=best_result.params,
            best_metric_value=best_result.metric_value,
            optimize_metric=self.optimize_metric,
            all_results=all_results,
            total_combinations=total_combinations,
            elapsed_time_seconds=elapsed,
        )

    def _get_metric_value(self, metrics) -> float:
        """Extract metric value from PerformanceMetrics."""
        return getattr(metrics, self.optimize_metric, 0.0)


class RandomSearchOptimizer:
    """Random search over parameter space.

    Samples random parameter combinations, useful when grid is too large.

    Example:
        optimizer = RandomSearchOptimizer(
            strategy=strategy,
            param_grid={
                "rsi_period": range(5, 30),
                "rsi_oversold": range(20, 40),
            },
            n_iterations=100,
            optimize_metric="sharpe_ratio",
        )

        result = optimizer.run(data, symbol="AAPL")
    """

    SUPPORTED_METRICS = GridSearchOptimizer.SUPPORTED_METRICS

    def __init__(
        self,
        strategy: dict[str, Any],
        param_grid: dict[str, list[Any] | range],
        n_iterations: int = 100,
        optimize_metric: str = "sharpe_ratio",
        config: BacktestConfig | None = None,
        random_seed: int | None = None,
        progress_callback: Callable[[int, int, dict], None] | None = None,
    ) -> None:
        """Initialize random search optimizer.

        Args:
            strategy: UTSS strategy definition
            param_grid: Dict mapping parameter names to lists/ranges of values
            n_iterations: Number of random samples to try
            optimize_metric: Metric to optimize
            config: Backtest configuration
            random_seed: Random seed for reproducibility
            progress_callback: Optional callback(current, total, params)
        """
        if optimize_metric not in self.SUPPORTED_METRICS:
            raise ValueError(f"Unsupported metric: {optimize_metric}")

        self.strategy = strategy
        self.param_grid = {k: list(v) for k, v in param_grid.items()}
        self.n_iterations = n_iterations
        self.optimize_metric = optimize_metric
        self.config = config or BacktestConfig()
        self.progress_callback = progress_callback

        if random_seed is not None:
            random.seed(random_seed)

    def run(
        self,
        data: pd.DataFrame,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> OptimizationResult:
        """Run random search optimization.

        Args:
            data: OHLCV DataFrame
            symbol: Stock symbol
            start_date: Backtest start date
            end_date: Backtest end date

        Returns:
            OptimizationResult with best parameters and all results
        """
        start_time = time.time()

        # Calculate total possible combinations
        total_possible = 1
        for values in self.param_grid.values():
            total_possible *= len(values)

        actual_iterations = min(self.n_iterations, total_possible)
        logger.info(f"Random search: {actual_iterations} iterations (of {total_possible} possible)")

        # Sample unique combinations
        sampled_params = self._sample_params(actual_iterations)

        all_results: list[ParameterResult] = []
        best_result: ParameterResult | None = None

        engine = BacktestEngine(config=self.config)
        calculator = MetricsCalculator(risk_free_rate=self.config.risk_free_rate)

        for i, params in enumerate(sampled_params):
            if self.progress_callback:
                self.progress_callback(i + 1, actual_iterations, params)

            try:
                result = engine.run(
                    strategy=self.strategy,
                    data=data,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    parameters=params,
                )

                metrics = calculator.calculate(result)
                metric_value = getattr(metrics, self.optimize_metric, 0.0)

                param_result = ParameterResult(
                    params=params,
                    metric_value=metric_value,
                    total_return_pct=metrics.total_return_pct,
                    sharpe_ratio=metrics.sharpe_ratio,
                    sortino_ratio=metrics.sortino_ratio,
                    max_drawdown_pct=metrics.max_drawdown_pct,
                    win_rate=metrics.win_rate,
                    num_trades=metrics.total_trades,
                )

                all_results.append(param_result)

                if best_result is None or metric_value > best_result.metric_value:
                    best_result = param_result

            except Exception as e:
                logger.warning(f"Backtest failed for params {params}: {e}")
                continue

        elapsed = time.time() - start_time

        if best_result is None:
            return OptimizationResult(
                best_params={},
                best_metric_value=0.0,
                optimize_metric=self.optimize_metric,
                all_results=[],
                total_combinations=actual_iterations,
                elapsed_time_seconds=elapsed,
            )

        return OptimizationResult(
            best_params=best_result.params,
            best_metric_value=best_result.metric_value,
            optimize_metric=self.optimize_metric,
            all_results=all_results,
            total_combinations=actual_iterations,
            elapsed_time_seconds=elapsed,
        )

    def _sample_params(self, n: int) -> list[dict[str, Any]]:
        """Sample n unique parameter combinations."""
        param_names = list(self.param_grid.keys())

        # If n is large relative to total space, just enumerate all
        total_possible = 1
        for values in self.param_grid.values():
            total_possible *= len(values)

        if n >= total_possible * 0.5:
            # Sample from all combinations
            all_combos = list(itertools.product(*self.param_grid.values()))
            sampled = random.sample(all_combos, min(n, len(all_combos)))
            return [dict(zip(param_names, combo)) for combo in sampled]

        # Random sampling with deduplication
        seen = set()
        result = []

        while len(result) < n:
            values = tuple(
                random.choice(self.param_grid[name])
                for name in param_names
            )

            if values not in seen:
                seen.add(values)
                result.append(dict(zip(param_names, values)))

        return result
