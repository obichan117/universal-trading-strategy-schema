"""TearSheet class for comprehensive backtest reporting.

Provides QuantStats-style tear sheets with multiple performance charts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from pyutss.metrics.calculator import MetricsCalculator, PerformanceMetrics
from pyutss.visualization.charts import (
    plot_distribution,
    plot_drawdown,
    plot_equity_curve,
    plot_monthly_heatmap,
    plot_rolling_metrics,
    plot_trade_analysis,
)

if TYPE_CHECKING:
    from pathlib import Path

    from matplotlib.figure import Figure

    from pyutss.results.types import BacktestResult


class TearSheet:
    """Performance tear sheet generator for backtest results.

    Provides comprehensive visualization and reporting for trading strategy
    backtests, inspired by QuantStats.

    Example:
        from pyutss.visualization import TearSheet

        sheet = TearSheet(result)

        # Generate full HTML report
        sheet.full_report("report.html")

        # Or plot individual charts
        sheet.plot_equity()
        sheet.plot_monthly_heatmap()
        sheet.plot_distribution()
    """

    def __init__(
        self,
        result: BacktestResult,
        benchmark: pd.Series | None = None,
        risk_free_rate: float = 0.0,
    ) -> None:
        """Initialize tear sheet with backtest result.

        Args:
            result: BacktestResult from backtesting engine
            benchmark: Optional benchmark equity curve for comparison
            risk_free_rate: Annual risk-free rate for Sharpe/Sortino calculation
        """
        self.result = result
        self.benchmark = benchmark
        self.risk_free_rate = risk_free_rate
        self._calculator = MetricsCalculator(risk_free_rate=risk_free_rate)
        self._metrics: PerformanceMetrics | None = None

    @property
    def metrics(self) -> PerformanceMetrics:
        """Get calculated performance metrics (cached)."""
        if self._metrics is None:
            self._metrics = self._calculator.calculate(self.result)
        return self._metrics

    def summary_stats(self) -> dict[str, float]:
        """Get summary statistics as dictionary.

        Returns:
            Dictionary with key performance metrics
        """
        m = self.metrics
        return {
            "Total Return (%)": m.total_return_pct,
            "Annualized Return (%)": m.annualized_return_pct,
            "Sharpe Ratio": m.sharpe_ratio,
            "Sortino Ratio": m.sortino_ratio,
            "Calmar Ratio": m.calmar_ratio,
            "Max Drawdown (%)": m.max_drawdown_pct,
            "Volatility (%)": m.volatility_annualized,
            "Win Rate (%)": m.win_rate,
            "Profit Factor": m.profit_factor,
            "Total Trades": m.total_trades,
            "Avg Trade P&L ($)": m.avg_trade_pnl,
            "Avg Trade Duration (days)": m.avg_trade_duration_days,
            "Exposure (%)": m.exposure_pct,
        }

    def summary_table(self) -> pd.DataFrame:
        """Get summary statistics as DataFrame.

        Returns:
            DataFrame with metric names and values
        """
        stats = self.summary_stats()
        return pd.DataFrame([
            {"Metric": k, "Value": v} for k, v in stats.items()
        ])

    def plot_equity(
        self,
        figsize: tuple[int, int] = (12, 6),
        show_drawdown: bool = True,
    ) -> Figure:
        """Plot equity curve with optional underwater drawdown.

        Args:
            figsize: Figure size (width, height)
            show_drawdown: Whether to show underwater drawdown

        Returns:
            Matplotlib Figure
        """
        return plot_equity_curve(
            self.result,
            figsize=figsize,
            show_drawdown=show_drawdown,
            benchmark=self.benchmark,
        )

    def plot_drawdown(
        self,
        figsize: tuple[int, int] = (12, 4),
        top_n: int = 5,
    ) -> Figure:
        """Plot drawdown periods with top drawdowns highlighted.

        Args:
            figsize: Figure size
            top_n: Number of top drawdowns to highlight

        Returns:
            Matplotlib Figure
        """
        return plot_drawdown(self.result, figsize=figsize, top_n=top_n)

    def plot_monthly_heatmap(
        self,
        figsize: tuple[int, int] = (12, 6),
        cmap: str = "RdYlGn",
    ) -> Figure:
        """Plot monthly returns calendar heatmap.

        Args:
            figsize: Figure size
            cmap: Colormap name

        Returns:
            Matplotlib Figure
        """
        return plot_monthly_heatmap(self.result, figsize=figsize, cmap=cmap)

    def plot_rolling_sharpe(
        self,
        figsize: tuple[int, int] = (12, 5),
        windows: list[int] | None = None,
    ) -> Figure:
        """Plot rolling Sharpe ratio.

        Args:
            figsize: Figure size
            windows: Rolling window sizes in trading days

        Returns:
            Matplotlib Figure
        """
        return plot_rolling_metrics(
            self.result,
            figsize=figsize,
            windows=windows,
            metric="sharpe",
            risk_free_rate=self.risk_free_rate,
        )

    def plot_rolling_sortino(
        self,
        figsize: tuple[int, int] = (12, 5),
        windows: list[int] | None = None,
    ) -> Figure:
        """Plot rolling Sortino ratio.

        Args:
            figsize: Figure size
            windows: Rolling window sizes in trading days

        Returns:
            Matplotlib Figure
        """
        return plot_rolling_metrics(
            self.result,
            figsize=figsize,
            windows=windows,
            metric="sortino",
            risk_free_rate=self.risk_free_rate,
        )

    def plot_distribution(
        self,
        figsize: tuple[int, int] = (10, 6),
        period: str = "daily",
    ) -> Figure:
        """Plot return distribution with statistics.

        Args:
            figsize: Figure size
            period: 'daily', 'weekly', or 'monthly'

        Returns:
            Matplotlib Figure
        """
        return plot_distribution(self.result, figsize=figsize, period=period)

    def plot_trade_analysis(
        self,
        figsize: tuple[int, int] = (12, 5),
    ) -> Figure:
        """Plot trade P&L analysis.

        Args:
            figsize: Figure size

        Returns:
            Matplotlib Figure
        """
        return plot_trade_analysis(self.result, figsize=figsize)

    def full_report(
        self,
        output_path: str | Path,
        title: str | None = None,
    ) -> None:
        """Generate full HTML tear sheet report.

        Creates an HTML file with all charts and statistics embedded.

        Args:
            output_path: Path to save HTML file
            title: Optional report title (default: Strategy ID + Symbol)

        Example:
            sheet = TearSheet(result)
            sheet.full_report("backtest_report.html")
        """
        from pyutss.visualization.html import generate_html_report

        if title is None:
            title = f"{self.result.strategy_id} - {self.result.symbol}"

        generate_html_report(
            result=self.result,
            metrics=self.metrics,
            output_path=output_path,
            title=title,
            benchmark=self.benchmark,
            risk_free_rate=self.risk_free_rate,
        )

    def show(self) -> None:
        """Display all charts interactively.

        Opens matplotlib figures for each chart. Useful for Jupyter notebooks.
        """
        import matplotlib.pyplot as plt

        self.plot_equity()
        self.plot_drawdown()
        self.plot_monthly_heatmap()
        self.plot_rolling_sharpe()
        self.plot_distribution()
        self.plot_trade_analysis()

        plt.show()
