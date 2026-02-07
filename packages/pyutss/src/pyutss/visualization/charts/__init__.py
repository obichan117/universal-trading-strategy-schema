"""Chart generation functions for backtest visualization.

Provides QuantStats-style charts for performance analysis.
"""

from pyutss.visualization.charts.equity import plot_drawdown, plot_equity_curve
from pyutss.visualization.charts.heatmap import plot_monthly_heatmap
from pyutss.visualization.charts.metrics import plot_distribution, plot_rolling_metrics
from pyutss.visualization.charts.trades import plot_trade_analysis

__all__ = [
    "plot_equity_curve",
    "plot_drawdown",
    "plot_monthly_heatmap",
    "plot_rolling_metrics",
    "plot_distribution",
    "plot_trade_analysis",
]
