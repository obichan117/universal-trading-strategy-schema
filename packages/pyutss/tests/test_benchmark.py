"""Tests for benchmark comparison metrics."""

import numpy as np
import pandas as pd
import pytest

from pyutss.metrics.benchmark import (
    BenchmarkMetrics,
    calculate_benchmark_metrics,
    _calculate_capture_ratios,
)


class TestBenchmarkMetrics:
    """Tests for BenchmarkMetrics dataclass."""

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        metrics = BenchmarkMetrics(
            alpha=0.05,
            beta=1.2,
            information_ratio=0.8,
            tracking_error=0.06,
            excess_return=0.03,
            correlation=0.9,
            r_squared=0.81,
            up_capture=110.0,
            down_capture=90.0,
            capture_ratio=1.22,
        )

        result = metrics.to_dict()

        assert result["alpha"] == 0.05
        assert result["beta"] == 1.2
        assert result["information_ratio"] == 0.8
        assert result["tracking_error"] == 0.06
        assert result["excess_return"] == 0.03
        assert result["correlation"] == 0.9
        assert result["r_squared"] == 0.81
        assert result["up_capture"] == 110.0
        assert result["down_capture"] == 90.0
        assert result["capture_ratio"] == 1.22

    def test_str_representation(self) -> None:
        """Test string representation."""
        metrics = BenchmarkMetrics(
            alpha=0.05,
            beta=1.0,
            information_ratio=0.5,
            tracking_error=0.10,
            excess_return=0.05,
            correlation=0.8,
            r_squared=0.64,
            up_capture=100.0,
            down_capture=100.0,
            capture_ratio=1.0,
        )

        result = str(metrics)

        assert "alpha=" in result
        assert "beta=" in result
        assert "5.00%" in result  # alpha as percentage


class TestCalculateBenchmarkMetrics:
    """Tests for calculate_benchmark_metrics function."""

    def test_perfect_tracking(self) -> None:
        """Test when strategy perfectly tracks benchmark."""
        dates = pd.date_range("2023-01-01", periods=252, freq="D")
        returns = np.random.randn(252) * 0.01
        strategy_returns = pd.Series(returns, index=dates)
        benchmark_returns = pd.Series(returns, index=dates)

        metrics = calculate_benchmark_metrics(strategy_returns, benchmark_returns)

        assert abs(metrics.beta - 1.0) < 0.01
        assert abs(metrics.alpha) < 0.01
        assert abs(metrics.tracking_error) < 0.01
        assert abs(metrics.correlation - 1.0) < 0.01
        assert abs(metrics.r_squared - 1.0) < 0.01

    def test_outperforming_strategy(self) -> None:
        """Test strategy that consistently outperforms benchmark."""
        dates = pd.date_range("2023-01-01", periods=252, freq="D")
        np.random.seed(42)
        benchmark_returns = pd.Series(np.random.randn(252) * 0.01, index=dates)
        # Strategy has same pattern but higher returns
        strategy_returns = benchmark_returns + 0.001  # 0.1% daily outperformance

        metrics = calculate_benchmark_metrics(strategy_returns, benchmark_returns)

        assert metrics.alpha > 0  # Positive alpha
        assert metrics.excess_return > 0
        assert metrics.information_ratio > 0

    def test_underperforming_strategy(self) -> None:
        """Test strategy that consistently underperforms benchmark."""
        dates = pd.date_range("2023-01-01", periods=252, freq="D")
        np.random.seed(42)
        benchmark_returns = pd.Series(np.random.randn(252) * 0.01, index=dates)
        # Strategy has same pattern but lower returns
        strategy_returns = benchmark_returns - 0.001  # 0.1% daily underperformance

        metrics = calculate_benchmark_metrics(strategy_returns, benchmark_returns)

        assert metrics.alpha < 0  # Negative alpha
        assert metrics.excess_return < 0
        assert metrics.information_ratio < 0

    def test_high_beta_strategy(self) -> None:
        """Test strategy with high beta (amplifies benchmark moves)."""
        dates = pd.date_range("2023-01-01", periods=252, freq="D")
        np.random.seed(42)
        benchmark_returns = pd.Series(np.random.randn(252) * 0.01, index=dates)
        # Strategy has 2x the benchmark moves
        strategy_returns = benchmark_returns * 2

        metrics = calculate_benchmark_metrics(strategy_returns, benchmark_returns)

        assert metrics.beta > 1.8  # Should be close to 2
        assert metrics.beta < 2.2

    def test_low_beta_strategy(self) -> None:
        """Test strategy with low beta (dampens benchmark moves)."""
        dates = pd.date_range("2023-01-01", periods=252, freq="D")
        np.random.seed(42)
        benchmark_returns = pd.Series(np.random.randn(252) * 0.01, index=dates)
        # Strategy has 0.5x the benchmark moves
        strategy_returns = benchmark_returns * 0.5

        metrics = calculate_benchmark_metrics(strategy_returns, benchmark_returns)

        assert metrics.beta > 0.4  # Should be close to 0.5
        assert metrics.beta < 0.6

    def test_uncorrelated_strategy(self) -> None:
        """Test strategy uncorrelated with benchmark."""
        dates = pd.date_range("2023-01-01", periods=252, freq="D")
        np.random.seed(42)
        strategy_returns = pd.Series(np.random.randn(252) * 0.01, index=dates)
        np.random.seed(123)  # Different seed for independence
        benchmark_returns = pd.Series(np.random.randn(252) * 0.01, index=dates)

        metrics = calculate_benchmark_metrics(strategy_returns, benchmark_returns)

        # Correlation should be close to 0 (but not exactly due to randomness)
        assert abs(metrics.correlation) < 0.3
        assert metrics.r_squared < 0.1

    def test_with_risk_free_rate(self) -> None:
        """Test calculation with non-zero risk-free rate."""
        dates = pd.date_range("2023-01-01", periods=252, freq="D")
        np.random.seed(42)
        benchmark_returns = pd.Series(np.random.randn(252) * 0.01 + 0.0002, index=dates)
        strategy_returns = pd.Series(np.random.randn(252) * 0.01 + 0.0003, index=dates)

        metrics_no_rf = calculate_benchmark_metrics(
            strategy_returns, benchmark_returns, risk_free_rate=0.0
        )
        metrics_with_rf = calculate_benchmark_metrics(
            strategy_returns, benchmark_returns, risk_free_rate=0.02
        )

        # Alpha should differ due to risk-free rate adjustment
        assert metrics_no_rf.alpha != metrics_with_rf.alpha

    def test_aligned_series(self) -> None:
        """Test that misaligned series are properly aligned."""
        dates1 = pd.date_range("2023-01-01", periods=100, freq="D")
        dates2 = pd.date_range("2023-01-15", periods=100, freq="D")

        np.random.seed(42)
        strategy_returns = pd.Series(np.random.randn(100) * 0.01, index=dates1)
        benchmark_returns = pd.Series(np.random.randn(100) * 0.01, index=dates2)

        # Should work without error, using overlapping dates
        metrics = calculate_benchmark_metrics(strategy_returns, benchmark_returns)

        assert isinstance(metrics, BenchmarkMetrics)

    def test_empty_series_raises(self) -> None:
        """Test that empty series raises ValueError."""
        strategy_returns = pd.Series(dtype=float)
        benchmark_returns = pd.Series(dtype=float)

        with pytest.raises(ValueError, match="cannot be empty"):
            calculate_benchmark_metrics(strategy_returns, benchmark_returns)

    def test_no_overlap_raises(self) -> None:
        """Test that non-overlapping series raises ValueError."""
        dates1 = pd.date_range("2023-01-01", periods=10, freq="D")
        dates2 = pd.date_range("2024-01-01", periods=10, freq="D")

        strategy_returns = pd.Series([0.01] * 10, index=dates1)
        benchmark_returns = pd.Series([0.01] * 10, index=dates2)

        with pytest.raises(ValueError, match="Not enough overlapping"):
            calculate_benchmark_metrics(strategy_returns, benchmark_returns)


class TestCaptureRatios:
    """Tests for capture ratio calculations."""

    def test_perfect_tracking_capture(self) -> None:
        """Test capture ratios when perfectly tracking benchmark."""
        returns = np.array([0.01, -0.02, 0.015, -0.01, 0.005])
        strategy = returns.copy()
        benchmark = returns.copy()

        up, down, ratio = _calculate_capture_ratios(strategy, benchmark)

        assert abs(up - 100.0) < 1.0
        assert abs(down - 100.0) < 1.0
        assert abs(ratio - 1.0) < 0.1

    def test_defensive_strategy_capture(self) -> None:
        """Test capture ratios for defensive strategy (captures less downside)."""
        benchmark = np.array([0.02, -0.03, 0.01, -0.02, 0.015])
        # Defensive: captures 80% of upside, 60% of downside
        strategy = np.array([0.016, -0.018, 0.008, -0.012, 0.012])

        up, down, ratio = _calculate_capture_ratios(strategy, benchmark)

        # Capture ratio should be > 1 (good for defensive)
        assert ratio > 1.0

    def test_aggressive_strategy_capture(self) -> None:
        """Test capture ratios for aggressive strategy (amplifies both)."""
        benchmark = np.array([0.01, -0.02, 0.015, -0.01, 0.005])
        # Aggressive: captures 150% of both directions
        strategy = benchmark * 1.5

        up, down, ratio = _calculate_capture_ratios(strategy, benchmark)

        assert up > 100.0
        assert down > 100.0
        # Ratio should be close to 1 since both sides amplified equally
        assert abs(ratio - 1.0) < 0.2

    def test_no_up_days(self) -> None:
        """Test when benchmark has no positive days."""
        benchmark = np.array([-0.01, -0.02, -0.005, -0.015])
        strategy = np.array([-0.005, -0.01, -0.002, -0.007])

        up, down, ratio = _calculate_capture_ratios(strategy, benchmark)

        # Up capture defaults to 100% when no up days
        assert up == 100.0
        # Down capture should be < 100% (less loss than benchmark)
        assert down < 100.0

    def test_no_down_days(self) -> None:
        """Test when benchmark has no negative days."""
        benchmark = np.array([0.01, 0.02, 0.005, 0.015])
        strategy = np.array([0.015, 0.025, 0.008, 0.02])

        up, down, ratio = _calculate_capture_ratios(strategy, benchmark)

        # Up capture should be > 100% (more gain than benchmark)
        assert up > 100.0
        # Down capture defaults to 100% when no down days
        assert down == 100.0


class TestBenchmarkMetricsIntegration:
    """Integration tests for benchmark metrics."""

    def test_full_calculation_workflow(self) -> None:
        """Test complete workflow from returns to metrics."""
        # Simulate a full year of trading
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=252, freq="B")  # Business days

        # Benchmark: S&P 500-like returns (10% annual with 15% vol)
        benchmark_daily = 0.10 / 252  # Daily expected return
        benchmark_vol = 0.15 / np.sqrt(252)  # Daily volatility
        benchmark_returns = pd.Series(
            np.random.normal(benchmark_daily, benchmark_vol, 252),
            index=dates,
        )

        # Strategy: Outperforms with similar volatility
        strategy_daily = 0.15 / 252  # 15% annual expected return
        strategy_vol = 0.18 / np.sqrt(252)  # Slightly higher volatility
        strategy_returns = pd.Series(
            np.random.normal(strategy_daily, strategy_vol, 252),
            index=dates,
        )

        # Calculate metrics
        metrics = calculate_benchmark_metrics(
            strategy_returns,
            benchmark_returns,
            risk_free_rate=0.02,  # 2% risk-free rate
        )

        # Verify all fields are populated and reasonable
        assert isinstance(metrics.alpha, float)
        assert isinstance(metrics.beta, float)
        assert isinstance(metrics.information_ratio, float)
        assert isinstance(metrics.tracking_error, float)
        assert isinstance(metrics.excess_return, float)
        assert isinstance(metrics.correlation, float)
        assert isinstance(metrics.r_squared, float)
        assert isinstance(metrics.up_capture, float)
        assert isinstance(metrics.down_capture, float)
        assert isinstance(metrics.capture_ratio, float)

        # Sanity checks
        assert -1.0 <= metrics.correlation <= 1.0
        assert 0.0 <= metrics.r_squared <= 1.0
        assert metrics.tracking_error >= 0.0

    def test_export_import_roundtrip(self) -> None:
        """Test that to_dict produces valid data."""
        metrics = BenchmarkMetrics(
            alpha=0.05,
            beta=1.1,
            information_ratio=0.7,
            tracking_error=0.08,
            excess_return=0.04,
            correlation=0.85,
            r_squared=0.72,
            up_capture=105.0,
            down_capture=95.0,
            capture_ratio=1.1,
        )

        data = metrics.to_dict()

        # Should be able to recreate
        recreated = BenchmarkMetrics(**data)

        assert recreated.alpha == metrics.alpha
        assert recreated.beta == metrics.beta
        assert recreated.information_ratio == metrics.information_ratio
