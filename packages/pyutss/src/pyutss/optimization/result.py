"""Result types for optimization.

Contains result classes for grid search and walk-forward optimization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

import pandas as pd


@dataclass
class ParameterResult:
    """Result for a single parameter combination."""

    params: dict[str, Any]
    metric_value: float
    total_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    win_rate: float
    num_trades: int


@dataclass
class WindowResult:
    """Result for a single walk-forward window."""

    window_index: int
    train_start: date
    train_end: date
    test_start: date
    test_end: date

    # In-sample results
    in_sample_params: dict[str, Any]
    in_sample_metric: float
    in_sample_return_pct: float
    in_sample_sharpe: float

    # Out-of-sample results
    out_of_sample_return_pct: float
    out_of_sample_sharpe: float
    out_of_sample_sortino: float
    out_of_sample_max_dd_pct: float
    out_of_sample_trades: int
    out_of_sample_win_rate: float


@dataclass
class OptimizationResult:
    """Result from grid search optimization.

    Contains best parameters and all tested combinations.
    """

    best_params: dict[str, Any]
    best_metric_value: float
    optimize_metric: str
    all_results: list[ParameterResult] = field(default_factory=list)

    # Summary statistics
    total_combinations: int = 0
    elapsed_time_seconds: float = 0.0

    def to_dataframe(self) -> pd.DataFrame:
        """Convert all results to DataFrame.

        Returns:
            DataFrame with all parameter combinations and metrics
        """
        if not self.all_results:
            return pd.DataFrame()

        rows = []
        for result in self.all_results:
            row = {**result.params}
            row["metric_value"] = result.metric_value
            row["total_return_pct"] = result.total_return_pct
            row["sharpe_ratio"] = result.sharpe_ratio
            row["sortino_ratio"] = result.sortino_ratio
            row["max_drawdown_pct"] = result.max_drawdown_pct
            row["win_rate"] = result.win_rate
            row["num_trades"] = result.num_trades
            rows.append(row)

        return pd.DataFrame(rows)

    def top_n(self, n: int = 10) -> list[ParameterResult]:
        """Get top N parameter combinations.

        Args:
            n: Number of results to return

        Returns:
            List of top ParameterResult objects
        """
        sorted_results = sorted(
            self.all_results,
            key=lambda x: x.metric_value,
            reverse=True,
        )
        return sorted_results[:n]

    def summary(self, print_output: bool = True) -> str:
        """Generate summary of optimization results.

        Args:
            print_output: Whether to print the summary

        Returns:
            Formatted string summary
        """
        lines = [
            "=" * 60,
            " Optimization Results",
            "=" * 60,
            f" Optimize Metric:     {self.optimize_metric}",
            f" Total Combinations:  {self.total_combinations}",
            f" Elapsed Time:        {self.elapsed_time_seconds:.2f}s",
            "-" * 60,
            " Best Parameters:",
        ]

        for param, value in self.best_params.items():
            lines.append(f"   {param}: {value}")

        lines.extend([
            "-" * 60,
            f" Best {self.optimize_metric}: {self.best_metric_value:.4f}",
            "=" * 60,
        ])

        output = "\n".join(lines)
        if print_output:
            print(output)
        return output


@dataclass
class WalkForwardResult:
    """Result from walk-forward optimization.

    Contains per-window breakdown and aggregate out-of-sample metrics.
    """

    best_params: dict[str, Any]
    optimize_metric: str
    window_results: list[WindowResult] = field(default_factory=list)

    # Aggregate out-of-sample metrics
    out_of_sample_return_pct: float = 0.0
    out_of_sample_sharpe: float = 0.0
    out_of_sample_sortino: float = 0.0
    out_of_sample_max_dd_pct: float = 0.0
    out_of_sample_win_rate: float = 0.0
    out_of_sample_total_trades: int = 0

    # Stability metrics
    param_stability: dict[str, float] = field(default_factory=dict)

    # Timing
    elapsed_time_seconds: float = 0.0

    def to_dataframe(self) -> pd.DataFrame:
        """Convert window results to DataFrame.

        Returns:
            DataFrame with per-window metrics
        """
        if not self.window_results:
            return pd.DataFrame()

        rows = []
        for w in self.window_results:
            row = {
                "window": w.window_index,
                "train_start": w.train_start,
                "train_end": w.train_end,
                "test_start": w.test_start,
                "test_end": w.test_end,
                "in_sample_return_pct": w.in_sample_return_pct,
                "in_sample_sharpe": w.in_sample_sharpe,
                "out_of_sample_return_pct": w.out_of_sample_return_pct,
                "out_of_sample_sharpe": w.out_of_sample_sharpe,
                "out_of_sample_sortino": w.out_of_sample_sortino,
                "out_of_sample_max_dd_pct": w.out_of_sample_max_dd_pct,
                "out_of_sample_trades": w.out_of_sample_trades,
            }
            # Add parameters
            for param, value in w.in_sample_params.items():
                row[f"param_{param}"] = value
            rows.append(row)

        return pd.DataFrame(rows)

    def efficiency_ratio(self) -> float:
        """Calculate walk-forward efficiency ratio.

        Efficiency = Out-of-sample return / In-sample return

        A ratio close to 1.0 suggests robust parameters.
        Values much below 1.0 suggest overfitting.

        Returns:
            Efficiency ratio
        """
        if not self.window_results:
            return 0.0

        total_is_return = sum(w.in_sample_return_pct for w in self.window_results)
        total_oos_return = sum(w.out_of_sample_return_pct for w in self.window_results)

        if abs(total_is_return) < 0.0001:
            return 0.0

        return total_oos_return / total_is_return

    def summary(self, print_output: bool = True) -> str:
        """Generate summary of walk-forward results.

        Args:
            print_output: Whether to print the summary

        Returns:
            Formatted string summary
        """
        lines = [
            "=" * 60,
            " Walk-Forward Optimization Results",
            "=" * 60,
            f" Optimize Metric:     {self.optimize_metric}",
            f" Windows:             {len(self.window_results)}",
            f" Elapsed Time:        {self.elapsed_time_seconds:.2f}s",
            "-" * 60,
            " Out-of-Sample Performance:",
            f"   Total Return:      {self.out_of_sample_return_pct:+.2f}%",
            f"   Sharpe Ratio:      {self.out_of_sample_sharpe:.2f}",
            f"   Sortino Ratio:     {self.out_of_sample_sortino:.2f}",
            f"   Max Drawdown:      {self.out_of_sample_max_dd_pct:.2f}%",
            f"   Win Rate:          {self.out_of_sample_win_rate:.1f}%",
            f"   Total Trades:      {self.out_of_sample_total_trades}",
            "-" * 60,
            f" Efficiency Ratio:    {self.efficiency_ratio():.2f}",
            "-" * 60,
            " Most Common Best Parameters:",
        ]

        for param, value in self.best_params.items():
            stability = self.param_stability.get(param, 0)
            lines.append(f"   {param}: {value} (stability: {stability:.0%})")

        lines.extend([
            "-" * 60,
            " Per-Window Performance:",
        ])

        for w in self.window_results:
            lines.append(
                f"   Window {w.window_index + 1}: "
                f"IS: {w.in_sample_return_pct:+.1f}% | "
                f"OOS: {w.out_of_sample_return_pct:+.1f}%"
            )

        lines.append("=" * 60)

        output = "\n".join(lines)
        if print_output:
            print(output)
        return output
