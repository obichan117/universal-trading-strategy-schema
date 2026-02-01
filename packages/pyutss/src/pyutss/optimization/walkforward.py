"""Walk-forward optimization for robust parameter selection.

Provides rolling window optimization with in-sample training and
out-of-sample validation to detect overfitting.
"""

from __future__ import annotations

import logging
import time
from collections import Counter
from typing import Any, Callable

import pandas as pd

from pyutss.engine.backtest import BacktestEngine
from pyutss.metrics.calculator import MetricsCalculator
from pyutss.optimization.grid_search import GridSearchOptimizer
from pyutss.optimization.result import WalkForwardResult, WindowResult
from pyutss.optimization.splits import TimeSeriesSplit
from pyutss.results.types import BacktestConfig

logger = logging.getLogger(__name__)


class WalkForwardOptimizer:
    """Walk-forward optimization with rolling in-sample/out-of-sample validation.

    Divides the data into rolling windows, optimizes parameters on the
    in-sample portion, then validates on the out-of-sample portion.
    This helps detect overfitting and select robust parameters.

    Example:
        optimizer = WalkForwardOptimizer(
            strategy=strategy,
            param_grid={
                "rsi_period": [10, 14, 20],
                "rsi_oversold": [25, 30, 35],
            },
            n_splits=5,
            in_sample_pct=0.7,
            out_sample_pct=0.3,
            optimize_metric="sharpe_ratio",
        )

        result = optimizer.run(data, symbol="AAPL")
        print(f"Best params: {result.best_params}")
        print(f"Out-of-sample Sharpe: {result.out_of_sample_sharpe}")
        print(f"Efficiency ratio: {result.efficiency_ratio()}")
    """

    SUPPORTED_METRICS = [
        "sharpe_ratio",
        "sortino_ratio",
        "calmar_ratio",
        "total_return_pct",
        "win_rate",
    ]

    def __init__(
        self,
        strategy: dict[str, Any],
        param_grid: dict[str, list[Any]],
        n_splits: int = 5,
        in_sample_pct: float = 0.7,
        out_sample_pct: float = 0.3,
        optimize_metric: str = "sharpe_ratio",
        gap: int = 0,
        config: BacktestConfig | None = None,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> None:
        """Initialize walk-forward optimizer.

        Args:
            strategy: UTSS strategy definition
            param_grid: Dict mapping parameter names to lists of values
            n_splits: Number of rolling windows
            in_sample_pct: Percentage for in-sample training
            out_sample_pct: Percentage for out-of-sample validation
            optimize_metric: Metric to optimize
            gap: Number of periods between train and test (prevent leakage)
            config: Backtest configuration
            progress_callback: Optional callback(window_idx, total_windows, stage)
        """
        if optimize_metric not in self.SUPPORTED_METRICS:
            raise ValueError(
                f"Unsupported metric: {optimize_metric}. "
                f"Supported: {self.SUPPORTED_METRICS}"
            )

        self.strategy = strategy
        self.param_grid = param_grid
        self.n_splits = n_splits
        self.in_sample_pct = in_sample_pct
        self.out_sample_pct = out_sample_pct
        self.optimize_metric = optimize_metric
        self.gap = gap
        self.config = config or BacktestConfig()
        self.progress_callback = progress_callback

    def run(
        self,
        data: pd.DataFrame,
        symbol: str,
    ) -> WalkForwardResult:
        """Run walk-forward optimization.

        Args:
            data: OHLCV DataFrame with DatetimeIndex
            symbol: Stock symbol

        Returns:
            WalkForwardResult with per-window metrics and aggregate results
        """
        start_time = time.time()

        # Ensure datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            data = data.copy()
            data.index = pd.to_datetime(data.index)

        # Lowercase columns
        data.columns = data.columns.str.lower()

        # Create splitter
        splitter = TimeSeriesSplit(
            n_splits=self.n_splits,
            train_pct=self.in_sample_pct,
            test_pct=self.out_sample_pct,
            gap=self.gap,
            expanding=False,
            min_train_size=50,
        )

        splits = list(splitter.split(data))
        logger.info(f"Walk-forward: {len(splits)} windows")

        window_results: list[WindowResult] = []
        all_best_params: list[dict[str, Any]] = []

        engine = BacktestEngine(config=self.config)
        calculator = MetricsCalculator(risk_free_rate=self.config.risk_free_rate)

        for window_idx, (train_idx, test_idx) in enumerate(splits):
            if self.progress_callback:
                self.progress_callback(window_idx + 1, len(splits), "in_sample")

            train_start, train_end = train_idx
            test_start, test_end = test_idx

            train_data = data.iloc[train_start:train_end]
            test_data = data.iloc[test_start:test_end]

            if len(train_data) < 20 or len(test_data) < 5:
                logger.warning(f"Window {window_idx}: insufficient data, skipping")
                continue

            # Get date ranges
            train_start_date = train_data.index[0].date()
            train_end_date = train_data.index[-1].date()
            test_start_date = test_data.index[0].date()
            test_end_date = test_data.index[-1].date()

            # In-sample optimization
            try:
                in_sample_result = self._optimize_in_sample(
                    train_data, symbol, window_idx
                )

                if in_sample_result is None:
                    logger.warning(f"Window {window_idx}: in-sample optimization failed")
                    continue

                best_params = in_sample_result["params"]
                in_sample_metric = in_sample_result["metric_value"]
                in_sample_return = in_sample_result["return_pct"]
                in_sample_sharpe = in_sample_result["sharpe"]

                all_best_params.append(best_params)

            except Exception as e:
                logger.warning(f"Window {window_idx} in-sample failed: {e}")
                continue

            # Out-of-sample validation
            if self.progress_callback:
                self.progress_callback(window_idx + 1, len(splits), "out_of_sample")

            try:
                oos_result = engine.run(
                    strategy=self.strategy,
                    data=test_data,
                    symbol=symbol,
                    parameters=best_params,
                )

                oos_metrics = calculator.calculate(oos_result)

                window_result = WindowResult(
                    window_index=window_idx,
                    train_start=train_start_date,
                    train_end=train_end_date,
                    test_start=test_start_date,
                    test_end=test_end_date,
                    in_sample_params=best_params,
                    in_sample_metric=in_sample_metric,
                    in_sample_return_pct=in_sample_return,
                    in_sample_sharpe=in_sample_sharpe,
                    out_of_sample_return_pct=oos_metrics.total_return_pct,
                    out_of_sample_sharpe=oos_metrics.sharpe_ratio,
                    out_of_sample_sortino=oos_metrics.sortino_ratio,
                    out_of_sample_max_dd_pct=oos_metrics.max_drawdown_pct,
                    out_of_sample_trades=oos_metrics.total_trades,
                    out_of_sample_win_rate=oos_metrics.win_rate,
                )

                window_results.append(window_result)

            except Exception as e:
                logger.warning(f"Window {window_idx} out-of-sample failed: {e}")
                continue

        elapsed = time.time() - start_time

        if not window_results:
            return WalkForwardResult(
                best_params={},
                optimize_metric=self.optimize_metric,
                window_results=[],
                elapsed_time_seconds=elapsed,
            )

        # Aggregate out-of-sample metrics
        agg_return = sum(w.out_of_sample_return_pct for w in window_results)
        avg_sharpe = sum(w.out_of_sample_sharpe for w in window_results) / len(window_results)
        avg_sortino = sum(w.out_of_sample_sortino for w in window_results) / len(window_results)
        max_dd = max(w.out_of_sample_max_dd_pct for w in window_results)
        total_trades = sum(w.out_of_sample_trades for w in window_results)

        # Calculate weighted win rate
        total_win_trades = 0
        for w in window_results:
            total_win_trades += w.out_of_sample_trades * (w.out_of_sample_win_rate / 100)
        avg_win_rate = (total_win_trades / total_trades * 100) if total_trades > 0 else 0

        # Find most common best parameters
        best_params = self._find_consensus_params(all_best_params)
        param_stability = self._calculate_param_stability(all_best_params)

        return WalkForwardResult(
            best_params=best_params,
            optimize_metric=self.optimize_metric,
            window_results=window_results,
            out_of_sample_return_pct=agg_return,
            out_of_sample_sharpe=avg_sharpe,
            out_of_sample_sortino=avg_sortino,
            out_of_sample_max_dd_pct=max_dd,
            out_of_sample_win_rate=avg_win_rate,
            out_of_sample_total_trades=total_trades,
            param_stability=param_stability,
            elapsed_time_seconds=elapsed,
        )

    def _optimize_in_sample(
        self,
        train_data: pd.DataFrame,
        symbol: str,
        window_idx: int,
    ) -> dict[str, Any] | None:
        """Optimize parameters on in-sample data."""
        optimizer = GridSearchOptimizer(
            strategy=self.strategy,
            param_grid=self.param_grid,
            optimize_metric=self.optimize_metric,
            config=self.config,
        )

        result = optimizer.run(
            data=train_data,
            symbol=symbol,
        )

        if not result.best_params:
            return None

        # Find the full result for best params
        for param_result in result.all_results:
            if param_result.params == result.best_params:
                return {
                    "params": result.best_params,
                    "metric_value": result.best_metric_value,
                    "return_pct": param_result.total_return_pct,
                    "sharpe": param_result.sharpe_ratio,
                }

        return {
            "params": result.best_params,
            "metric_value": result.best_metric_value,
            "return_pct": 0.0,
            "sharpe": 0.0,
        }

    def _find_consensus_params(
        self,
        all_params: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Find most common parameter values across windows."""
        if not all_params:
            return {}

        consensus = {}
        param_names = all_params[0].keys()

        for param in param_names:
            values = [p[param] for p in all_params]
            counter = Counter(values)
            most_common = counter.most_common(1)
            if most_common:
                consensus[param] = most_common[0][0]

        return consensus

    def _calculate_param_stability(
        self,
        all_params: list[dict[str, Any]],
    ) -> dict[str, float]:
        """Calculate stability score for each parameter.

        Stability = frequency of most common value / total windows
        """
        if not all_params:
            return {}

        stability = {}
        param_names = all_params[0].keys()

        for param in param_names:
            values = [p[param] for p in all_params]
            counter = Counter(values)
            most_common_count = counter.most_common(1)[0][1]
            stability[param] = most_common_count / len(all_params)

        return stability
