"""Tests for optimization module."""

import numpy as np
import pandas as pd

from pyutss.optimization import (
    GridSearchOptimizer,
    OptimizationResult,
    PurgedKFold,
    RandomSearchOptimizer,
    TimeSeriesSplit,
    WalkForwardOptimizer,
    WalkForwardResult,
)


def create_sample_data(periods: int = 500) -> pd.DataFrame:
    """Create sample OHLCV data for testing."""
    dates = pd.date_range("2020-01-01", periods=periods, freq="B")
    np.random.seed(42)

    # Generate trending + mean-reverting price
    trend = np.cumsum(np.random.normal(0.0001, 0.01, periods))
    noise = np.random.normal(0, 0.02, periods)
    close = 100 * np.exp(trend + noise)

    df = pd.DataFrame({
        "open": close * (1 + np.random.uniform(-0.01, 0.01, periods)),
        "high": close * (1 + np.random.uniform(0, 0.02, periods)),
        "low": close * (1 - np.random.uniform(0, 0.02, periods)),
        "close": close,
        "volume": np.random.randint(1000000, 10000000, periods),
    }, index=dates)

    return df


def create_sample_strategy() -> dict:
    """Create a parametric RSI strategy."""
    return {
        "info": {"id": "rsi_test_strategy"},
        "signals": {
            "rsi": {
                "type": "indicator",
                "name": "RSI",
                "params": {"period": {"$param": "rsi_period"}},
            },
        },
        "rules": [
            {
                "when": {
                    "type": "comparison",
                    "left": {"$ref": "#/signals/rsi"},
                    "operator": "<",
                    "right": {"type": "constant", "value": {"$param": "rsi_oversold"}},
                },
                "then": {
                    "type": "trade",
                    "direction": "buy",
                    "sizing": {"type": "percent_of_equity", "value": 10},
                },
            },
            {
                "when": {
                    "type": "comparison",
                    "left": {"$ref": "#/signals/rsi"},
                    "operator": ">",
                    "right": {"type": "constant", "value": {"$param": "rsi_overbought"}},
                },
                "then": {
                    "type": "trade",
                    "direction": "sell",
                },
            },
        ],
        "parameters": {
            "defaults": {
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
            },
        },
    }


class TestTimeSeriesSplit:
    """Tests for TimeSeriesSplit."""

    def test_basic_split(self):
        """Test basic time series splitting."""
        splitter = TimeSeriesSplit(n_splits=5, train_pct=0.7, test_pct=0.3, min_train_size=20)
        data = create_sample_data(500)

        splits = list(splitter.split(data))

        assert len(splits) >= 3  # May have fewer if constraints not met
        for train_idx, test_idx in splits:
            # Train comes before test
            assert train_idx[1] <= test_idx[0]
            # Valid indices
            assert train_idx[0] >= 0
            assert test_idx[1] <= len(data)

    def test_split_with_gap(self):
        """Test split with gap between train and test."""
        gap = 10
        splitter = TimeSeriesSplit(
            n_splits=3,
            train_pct=0.7,
            test_pct=0.3,
            gap=gap,
        )
        data = create_sample_data(300)

        splits = list(splitter.split(data))

        for train_idx, test_idx in splits:
            # Gap between train and test
            assert test_idx[0] - train_idx[1] >= gap

    def test_expanding_window(self):
        """Test expanding window mode."""
        splitter = TimeSeriesSplit(
            n_splits=3,
            train_pct=0.7,
            test_pct=0.3,
            expanding=True,
        )
        data = create_sample_data(300)

        splits = list(splitter.split(data))

        # All training sets should start from 0
        for train_idx, _ in splits:
            assert train_idx[0] == 0

    def test_get_splits(self):
        """Test get_splits returns Split objects."""
        splitter = TimeSeriesSplit(n_splits=3, min_train_size=20)
        splits = splitter.get_splits(300)

        assert len(splits) >= 2  # May have fewer depending on constraints
        for split in splits:
            assert hasattr(split, "train_start")
            assert hasattr(split, "train_end")
            assert hasattr(split, "test_start")
            assert hasattr(split, "test_end")


class TestPurgedKFold:
    """Tests for PurgedKFold."""

    def test_basic_purged_fold(self):
        """Test basic purged k-fold split."""
        splitter = PurgedKFold(n_splits=5, purge_gap=5)
        data = create_sample_data(250)

        splits = list(splitter.split(data))

        # Should have fewer splits than standard k-fold
        # (first fold has no training data)
        assert len(splits) >= 1

        for train_idx, test_idx in splits:
            # Purge gap between train and test
            if train_idx[1] > 0:  # If there's training data
                assert test_idx[0] - train_idx[1] >= 5

    def test_purge_gap(self):
        """Test that purge gap is respected."""
        splitter = PurgedKFold(n_splits=4, purge_gap=10)
        splits = splitter.get_splits(200)

        for split in splits:
            if split.train_end > 0:
                gap = split.test_start - split.train_end
                assert gap >= 10


class TestGridSearchOptimizer:
    """Tests for GridSearchOptimizer."""

    def test_basic_grid_search(self):
        """Test basic grid search optimization."""
        strategy = create_sample_strategy()
        data = create_sample_data(200)

        optimizer = GridSearchOptimizer(
            strategy=strategy,
            param_grid={
                "rsi_period": [10, 14, 20],
                "rsi_oversold": [25, 30],
                "rsi_overbought": [70, 75],
            },
            optimize_metric="sharpe_ratio",
        )

        result = optimizer.run(data, symbol="TEST")

        assert isinstance(result, OptimizationResult)
        assert result.total_combinations == 3 * 2 * 2  # 12
        assert len(result.all_results) > 0
        assert result.best_params is not None

    def test_grid_search_with_callback(self):
        """Test grid search with progress callback."""
        strategy = create_sample_strategy()
        data = create_sample_data(200)

        progress = []

        def callback(current, total, params):
            progress.append((current, total))

        optimizer = GridSearchOptimizer(
            strategy=strategy,
            param_grid={
                "rsi_period": [10, 14],
                "rsi_oversold": [25, 30],
            },
            optimize_metric="total_return_pct",
            progress_callback=callback,
        )

        optimizer.run(data, symbol="TEST")

        assert len(progress) == 4
        assert progress[-1][0] == progress[-1][1]  # Last call: current == total

    def test_result_to_dataframe(self):
        """Test converting results to DataFrame."""
        strategy = create_sample_strategy()
        data = create_sample_data(200)

        optimizer = GridSearchOptimizer(
            strategy=strategy,
            param_grid={
                "rsi_period": [10, 14],
            },
            optimize_metric="sharpe_ratio",
        )

        result = optimizer.run(data, symbol="TEST")
        df = result.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert "rsi_period" in df.columns
        assert "sharpe_ratio" in df.columns
        assert len(df) == 2


class TestRandomSearchOptimizer:
    """Tests for RandomSearchOptimizer."""

    def test_basic_random_search(self):
        """Test basic random search optimization."""
        strategy = create_sample_strategy()
        data = create_sample_data(200)

        optimizer = RandomSearchOptimizer(
            strategy=strategy,
            param_grid={
                "rsi_period": list(range(5, 25)),
                "rsi_oversold": list(range(20, 40)),
                "rsi_overbought": list(range(60, 80)),
            },
            n_iterations=10,
            optimize_metric="sharpe_ratio",
            random_seed=42,
        )

        result = optimizer.run(data, symbol="TEST")

        assert isinstance(result, OptimizationResult)
        assert result.total_combinations == 10
        assert len(result.all_results) == 10

    def test_random_search_samples_unique_params(self):
        """Test that random search samples unique parameter combinations."""
        strategy = create_sample_strategy()
        data = create_sample_data(200)

        optimizer = RandomSearchOptimizer(
            strategy=strategy,
            param_grid={"rsi_period": list(range(5, 25))},
            n_iterations=5,
            random_seed=42,
        )

        result = optimizer.run(data, symbol="TEST")

        # All sampled params should be unique
        params = [r.params["rsi_period"] for r in result.all_results]
        assert len(params) == len(set(params))  # All unique


class TestWalkForwardOptimizer:
    """Tests for WalkForwardOptimizer."""

    def test_basic_walk_forward(self):
        """Test basic walk-forward optimization."""
        strategy = create_sample_strategy()
        data = create_sample_data(500)

        optimizer = WalkForwardOptimizer(
            strategy=strategy,
            param_grid={
                "rsi_period": [10, 14],
                "rsi_oversold": [25, 30],
            },
            n_splits=3,
            in_sample_pct=0.7,
            out_sample_pct=0.3,
            optimize_metric="sharpe_ratio",
        )

        result = optimizer.run(data, symbol="TEST")

        assert isinstance(result, WalkForwardResult)
        assert len(result.window_results) > 0
        assert result.best_params is not None

    def test_walk_forward_metrics(self):
        """Test walk-forward aggregated metrics."""
        strategy = create_sample_strategy()
        data = create_sample_data(500)

        optimizer = WalkForwardOptimizer(
            strategy=strategy,
            param_grid={"rsi_period": [10, 14]},
            n_splits=3,
            optimize_metric="sharpe_ratio",
        )

        result = optimizer.run(data, symbol="TEST")

        # Check aggregated metrics exist
        assert hasattr(result, "out_of_sample_return_pct")
        assert hasattr(result, "out_of_sample_sharpe")
        assert hasattr(result, "out_of_sample_total_trades")

    def test_efficiency_ratio(self):
        """Test efficiency ratio calculation."""
        strategy = create_sample_strategy()
        data = create_sample_data(500)

        optimizer = WalkForwardOptimizer(
            strategy=strategy,
            param_grid={"rsi_period": [10, 14]},
            n_splits=3,
            optimize_metric="sharpe_ratio",
        )

        result = optimizer.run(data, symbol="TEST")
        efficiency = result.efficiency_ratio()

        # Efficiency ratio should be a number
        assert isinstance(efficiency, float)

    def test_param_stability(self):
        """Test parameter stability calculation."""
        strategy = create_sample_strategy()
        data = create_sample_data(500)

        optimizer = WalkForwardOptimizer(
            strategy=strategy,
            param_grid={"rsi_period": [10, 14]},
            n_splits=4,
            optimize_metric="sharpe_ratio",
        )

        result = optimizer.run(data, symbol="TEST")

        # Stability should be between 0 and 1
        for param, stability in result.param_stability.items():
            assert 0 <= stability <= 1

    def test_result_to_dataframe(self):
        """Test converting walk-forward results to DataFrame."""
        strategy = create_sample_strategy()
        data = create_sample_data(500)

        optimizer = WalkForwardOptimizer(
            strategy=strategy,
            param_grid={"rsi_period": [10, 14]},
            n_splits=3,
            optimize_metric="sharpe_ratio",
        )

        result = optimizer.run(data, symbol="TEST")
        df = result.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        if len(result.window_results) > 0:
            assert "window" in df.columns
            assert "out_of_sample_return_pct" in df.columns
