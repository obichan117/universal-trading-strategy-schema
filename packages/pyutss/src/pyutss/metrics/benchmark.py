"""Benchmark comparison metrics for strategy performance analysis.

Provides industry-standard metrics for comparing strategy performance
against a benchmark (e.g., SPY, market index).

Example:
    from pyutss.metrics import calculate_benchmark_metrics

    benchmark_metrics = calculate_benchmark_metrics(
        strategy_returns=strategy_equity.pct_change().dropna(),
        benchmark_returns=spy_returns,
    )

    print(f"Alpha: {benchmark_metrics.alpha:.2%}")
    print(f"Beta: {benchmark_metrics.beta:.2f}")
    print(f"Information Ratio: {benchmark_metrics.information_ratio:.2f}")
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


TRADING_DAYS_PER_YEAR = 252


@dataclass
class BenchmarkMetrics:
    """Benchmark-relative performance metrics.

    Attributes:
        alpha: Jensen's alpha - excess return above CAPM prediction (annualized)
        beta: Market sensitivity - strategy volatility relative to benchmark
        information_ratio: Risk-adjusted excess return (alpha / tracking error)
        tracking_error: Standard deviation of excess returns (annualized)
        excess_return: Annualized return above benchmark
        correlation: Correlation with benchmark returns
        r_squared: R-squared of regression against benchmark
        up_capture: Upside capture ratio (% of benchmark gains captured)
        down_capture: Downside capture ratio (% of benchmark losses captured)
        capture_ratio: up_capture / down_capture (higher is better)
    """

    alpha: float
    beta: float
    information_ratio: float
    tracking_error: float
    excess_return: float
    correlation: float
    r_squared: float
    up_capture: float
    down_capture: float
    capture_ratio: float

    def to_dict(self) -> dict[str, float]:
        """Convert metrics to dictionary."""
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "information_ratio": self.information_ratio,
            "tracking_error": self.tracking_error,
            "excess_return": self.excess_return,
            "correlation": self.correlation,
            "r_squared": self.r_squared,
            "up_capture": self.up_capture,
            "down_capture": self.down_capture,
            "capture_ratio": self.capture_ratio,
        }

    def __str__(self) -> str:
        """Return formatted string representation."""
        return (
            f"BenchmarkMetrics(\n"
            f"  alpha={self.alpha:.4f} ({self.alpha * 100:.2f}%),\n"
            f"  beta={self.beta:.3f},\n"
            f"  information_ratio={self.information_ratio:.3f},\n"
            f"  tracking_error={self.tracking_error:.4f} ({self.tracking_error * 100:.2f}%),\n"
            f"  excess_return={self.excess_return:.4f} ({self.excess_return * 100:.2f}%),\n"
            f"  correlation={self.correlation:.3f},\n"
            f"  r_squared={self.r_squared:.3f},\n"
            f"  up_capture={self.up_capture:.2f}%,\n"
            f"  down_capture={self.down_capture:.2f}%,\n"
            f"  capture_ratio={self.capture_ratio:.2f}\n"
            f")"
        )


def calculate_benchmark_metrics(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.0,
) -> BenchmarkMetrics:
    """Calculate benchmark-relative performance metrics.

    Args:
        strategy_returns: Daily returns of the strategy (as decimals, not %)
        benchmark_returns: Daily returns of the benchmark (as decimals, not %)
        risk_free_rate: Annual risk-free rate (default: 0.0)

    Returns:
        BenchmarkMetrics with all calculated values

    Raises:
        ValueError: If returns series are empty or have different lengths

    Example:
        >>> strategy_returns = equity_curve.pct_change().dropna()
        >>> benchmark_returns = spy_prices.pct_change().dropna()
        >>> metrics = calculate_benchmark_metrics(strategy_returns, benchmark_returns)
        >>> print(f"Alpha: {metrics.alpha:.2%}")
    """
    # Validate inputs
    if len(strategy_returns) == 0 or len(benchmark_returns) == 0:
        raise ValueError("Returns series cannot be empty")

    # Align the series by index
    aligned = pd.concat(
        [strategy_returns, benchmark_returns], axis=1, join="inner"
    )
    aligned.columns = ["strategy", "benchmark"]

    if len(aligned) < 2:
        raise ValueError("Not enough overlapping data points")

    strat_ret = aligned["strategy"].values
    bench_ret = aligned["benchmark"].values

    # Calculate basic statistics
    n_days = len(strat_ret)

    # Excess returns (strategy - benchmark)
    excess_returns = strat_ret - bench_ret

    # Annualized excess return
    mean_excess = np.mean(excess_returns)
    excess_return_annualized = mean_excess * TRADING_DAYS_PER_YEAR

    # Tracking error (annualized std of excess returns)
    tracking_error = np.std(excess_returns, ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)

    # Information ratio
    if tracking_error > 0:
        information_ratio = excess_return_annualized / tracking_error
    else:
        information_ratio = 0.0

    # Beta and Alpha using OLS regression
    # y = alpha + beta * x + epsilon
    # where y = strategy returns, x = benchmark returns
    bench_mean = np.mean(bench_ret)
    strat_mean = np.mean(strat_ret)

    # Covariance and variance for beta
    cov = np.sum((bench_ret - bench_mean) * (strat_ret - strat_mean)) / (n_days - 1)
    var_bench = np.sum((bench_ret - bench_mean) ** 2) / (n_days - 1)

    if var_bench > 0:
        beta = cov / var_bench
    else:
        beta = 0.0

    # Jensen's alpha (annualized)
    # alpha = R_strategy - [R_f + beta * (R_benchmark - R_f)]
    strat_ann_return = strat_mean * TRADING_DAYS_PER_YEAR
    bench_ann_return = bench_mean * TRADING_DAYS_PER_YEAR

    alpha = strat_ann_return - (risk_free_rate + beta * (bench_ann_return - risk_free_rate))

    # Correlation and R-squared
    if var_bench > 0 and np.var(strat_ret) > 0:
        var_strat = np.sum((strat_ret - strat_mean) ** 2) / (n_days - 1)
        correlation = cov / np.sqrt(var_bench * var_strat)
        r_squared = correlation ** 2
    else:
        correlation = 0.0
        r_squared = 0.0

    # Capture ratios
    up_capture, down_capture, capture_ratio = _calculate_capture_ratios(
        strat_ret, bench_ret
    )

    return BenchmarkMetrics(
        alpha=alpha,
        beta=beta,
        information_ratio=information_ratio,
        tracking_error=tracking_error,
        excess_return=excess_return_annualized,
        correlation=correlation,
        r_squared=r_squared,
        up_capture=up_capture,
        down_capture=down_capture,
        capture_ratio=capture_ratio,
    )


def _calculate_capture_ratios(
    strategy_returns: np.ndarray,
    benchmark_returns: np.ndarray,
) -> tuple[float, float, float]:
    """Calculate upside and downside capture ratios.

    Up capture = (sum of strategy returns when benchmark > 0) / (sum of benchmark returns when > 0)
    Down capture = (sum of strategy returns when benchmark < 0) / (sum of benchmark returns when < 0)

    Args:
        strategy_returns: Array of strategy daily returns
        benchmark_returns: Array of benchmark daily returns

    Returns:
        Tuple of (up_capture, down_capture, capture_ratio) as percentages
    """
    # Up capture: when benchmark is positive
    up_mask = benchmark_returns > 0
    if np.any(up_mask):
        up_bench = benchmark_returns[up_mask]
        up_strat = strategy_returns[up_mask]

        # Geometric return calculation
        bench_up_total = np.prod(1 + up_bench) - 1
        strat_up_total = np.prod(1 + up_strat) - 1

        if bench_up_total > 0:
            up_capture = (strat_up_total / bench_up_total) * 100
        else:
            up_capture = 100.0
    else:
        up_capture = 100.0

    # Down capture: when benchmark is negative
    down_mask = benchmark_returns < 0
    if np.any(down_mask):
        down_bench = benchmark_returns[down_mask]
        down_strat = strategy_returns[down_mask]

        # Geometric return calculation
        bench_down_total = np.prod(1 + down_bench) - 1
        strat_down_total = np.prod(1 + down_strat) - 1

        if bench_down_total < 0:
            down_capture = (strat_down_total / bench_down_total) * 100
        else:
            down_capture = 100.0
    else:
        down_capture = 100.0

    # Capture ratio (higher is better)
    if down_capture > 0:
        capture_ratio = up_capture / down_capture
    else:
        capture_ratio = float("inf") if up_capture > 0 else 1.0

    return up_capture, down_capture, capture_ratio
