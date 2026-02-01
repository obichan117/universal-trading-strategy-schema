"""Visualization module for pyutss.

Provides QuantStats-style tear sheets and performance charts.

Example:
    from pyutss.visualization import TearSheet

    sheet = TearSheet(result)
    sheet.full_report("report.html")  # HTML tear sheet
    sheet.plot_equity()               # Equity + drawdown
    sheet.plot_monthly_heatmap()      # Calendar heatmap
"""

from pyutss.visualization.charts import (
    plot_distribution,
    plot_drawdown,
    plot_equity_curve,
    plot_monthly_heatmap,
    plot_rolling_metrics,
    plot_trade_analysis,
)
from pyutss.visualization.tearsheet import TearSheet

__all__ = [
    "TearSheet",
    "plot_equity_curve",
    "plot_drawdown",
    "plot_monthly_heatmap",
    "plot_rolling_metrics",
    "plot_distribution",
    "plot_trade_analysis",
]
