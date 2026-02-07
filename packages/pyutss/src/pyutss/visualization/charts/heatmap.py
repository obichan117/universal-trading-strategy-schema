"""Monthly returns heatmap chart."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from pyutss.visualization.charts._guards import _check_matplotlib, _check_seaborn

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from pyutss.results.types import BacktestResult


def plot_monthly_heatmap(
    result: BacktestResult,
    ax: Axes | None = None,
    figsize: tuple[int, int] = (12, 6),
    cmap: str = "RdYlGn",
    annot_fmt: str = ".1f",
) -> Figure:
    """Plot monthly returns as a calendar heatmap.

    Args:
        result: BacktestResult from backtesting
        ax: Optional matplotlib axes
        figsize: Figure size
        cmap: Colormap for heatmap (diverging recommended)
        annot_fmt: Format string for annotations

    Returns:
        Matplotlib Figure object
    """
    _check_matplotlib()
    _check_seaborn()
    import matplotlib.pyplot as plt
    import seaborn as sns

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    equity = result.equity_curve
    if len(equity) < 2:
        ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center", transform=ax.transAxes)
        return fig

    # Calculate monthly returns
    monthly = equity.resample("ME").last()
    monthly_returns = monthly.pct_change() * 100

    # Create pivot table (years x months)
    monthly_returns = monthly_returns.dropna()
    if len(monthly_returns) == 0:
        ax.text(0.5, 0.5, "No monthly data", ha="center", va="center", transform=ax.transAxes)
        return fig

    pivot_data = pd.DataFrame({
        "year": monthly_returns.index.year,
        "month": monthly_returns.index.month,
        "return": monthly_returns.values,
    })

    pivot = pivot_data.pivot(index="year", columns="month", values="return")

    # Rename columns to month names
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    pivot.columns = [month_names[m - 1] for m in pivot.columns]

    # Calculate annual returns for side column
    annual_returns = equity.resample("YE").last().pct_change() * 100
    annual_returns = annual_returns.dropna()
    annual_dict = {dt.year: ret for dt, ret in annual_returns.items()}

    # Add annual column
    pivot["Year"] = [annual_dict.get(year, np.nan) for year in pivot.index]

    # Plot heatmap
    vmax = max(abs(pivot.values[~np.isnan(pivot.values)].min()),
               abs(pivot.values[~np.isnan(pivot.values)].max())) if len(pivot.values) > 0 else 10

    sns.heatmap(
        pivot,
        ax=ax,
        annot=True,
        fmt=annot_fmt,
        cmap=cmap,
        center=0,
        vmin=-vmax,
        vmax=vmax,
        linewidths=0.5,
        cbar_kws={"label": "Return (%)"},
    )

    ax.set_title("Monthly Returns (%)")
    ax.set_xlabel("")
    ax.set_ylabel("")

    plt.tight_layout()
    return fig
