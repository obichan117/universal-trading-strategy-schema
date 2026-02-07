"""Equity curve and drawdown chart functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from pyutss.visualization.charts._guards import _check_matplotlib

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from pyutss.results.types import BacktestResult


def plot_equity_curve(
    result: BacktestResult,
    ax: Axes | None = None,
    figsize: tuple[int, int] = (12, 6),
    show_drawdown: bool = True,
    benchmark: pd.Series | None = None,
) -> Figure:
    """Plot equity curve with optional underwater drawdown.

    Args:
        result: BacktestResult from backtesting
        ax: Optional matplotlib axes to plot on
        figsize: Figure size (width, height)
        show_drawdown: Whether to show underwater drawdown on secondary axis
        benchmark: Optional benchmark returns series for comparison

    Returns:
        Matplotlib Figure object
    """
    _check_matplotlib()
    import matplotlib.pyplot as plt

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    equity = result.equity_curve
    if len(equity) == 0:
        ax.text(0.5, 0.5, "No equity data", ha="center", va="center", transform=ax.transAxes)
        return fig

    # Plot equity curve
    ax.plot(equity.index, equity.values, label="Portfolio", color="#1f77b4", linewidth=1.5)

    # Plot benchmark if provided
    if benchmark is not None and len(benchmark) > 0:
        # Normalize benchmark to start at initial capital
        benchmark_scaled = benchmark / benchmark.iloc[0] * result.initial_capital
        ax.plot(
            benchmark_scaled.index,
            benchmark_scaled.values,
            label="Benchmark",
            color="#7f7f7f",
            linewidth=1.0,
            alpha=0.7,
        )

    ax.set_ylabel("Portfolio Value ($)", color="#1f77b4")
    ax.tick_params(axis="y", labelcolor="#1f77b4")
    ax.set_xlabel("")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    # Add drawdown on secondary axis
    if show_drawdown:
        ax2 = ax.twinx()
        running_max = equity.cummax()
        drawdown_pct = ((running_max - equity) / running_max) * 100

        ax2.fill_between(
            drawdown_pct.index,
            drawdown_pct.values,
            0,
            alpha=0.3,
            color="red",
            label="Drawdown",
        )
        ax2.set_ylabel("Drawdown (%)", color="red")
        ax2.tick_params(axis="y", labelcolor="red")
        ax2.set_ylim(ax2.get_ylim()[1], 0)  # Invert y-axis for drawdown
        ax2.legend(loc="upper right")

    ax.set_title(f"Equity Curve - {result.symbol}")
    plt.tight_layout()

    return fig


def plot_drawdown(
    result: BacktestResult,
    ax: Axes | None = None,
    figsize: tuple[int, int] = (12, 4),
    top_n: int = 5,
) -> Figure:
    """Plot drawdown periods with top drawdowns highlighted.

    Args:
        result: BacktestResult from backtesting
        ax: Optional matplotlib axes
        figsize: Figure size
        top_n: Number of top drawdowns to highlight

    Returns:
        Matplotlib Figure object
    """
    _check_matplotlib()
    import matplotlib.pyplot as plt

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    equity = result.equity_curve
    if len(equity) == 0:
        ax.text(0.5, 0.5, "No equity data", ha="center", va="center", transform=ax.transAxes)
        return fig

    running_max = equity.cummax()
    drawdown = running_max - equity
    drawdown_pct = (drawdown / running_max) * 100

    # Plot drawdown
    ax.fill_between(
        drawdown_pct.index,
        drawdown_pct.values,
        0,
        alpha=0.5,
        color="red",
    )
    ax.plot(drawdown_pct.index, drawdown_pct.values, color="darkred", linewidth=0.5)

    # Find and highlight top drawdown periods
    drawdown_periods = _find_drawdown_periods(equity)
    drawdown_periods.sort(key=lambda x: x["max_dd_pct"], reverse=True)

    colors = plt.cm.Reds(np.linspace(0.3, 0.9, min(top_n, len(drawdown_periods))))
    for i, period in enumerate(drawdown_periods[:top_n]):
        ax.axvspan(
            period["start"],
            period["end"],
            alpha=0.2,
            color=colors[i],
            label=f"DD #{i+1}: {period['max_dd_pct']:.1f}%",
        )

    ax.set_ylabel("Drawdown (%)")
    ax.set_xlabel("")
    ax.set_ylim(ax.get_ylim()[1], 0)  # Invert y-axis
    ax.grid(True, alpha=0.3)
    ax.set_title("Drawdown Periods")

    if drawdown_periods:
        ax.legend(loc="lower right", fontsize=8)

    plt.tight_layout()
    return fig


def _find_drawdown_periods(equity: pd.Series) -> list[dict]:
    """Find distinct drawdown periods in equity curve."""
    running_max = equity.cummax()
    drawdown_pct = ((running_max - equity) / running_max) * 100

    periods = []
    in_drawdown = False
    period_start = None
    max_dd = 0
    max_dd_date = None

    for dt, dd in drawdown_pct.items():
        if dd > 0 and not in_drawdown:
            in_drawdown = True
            period_start = dt
            max_dd = dd
            max_dd_date = dt
        elif dd > 0 and in_drawdown:
            if dd > max_dd:
                max_dd = dd
                max_dd_date = dt
        elif dd == 0 and in_drawdown:
            in_drawdown = False
            periods.append({
                "start": period_start,
                "end": dt,
                "max_dd_pct": max_dd,
                "max_dd_date": max_dd_date,
            })
            max_dd = 0

    # Handle ongoing drawdown
    if in_drawdown:
        periods.append({
            "start": period_start,
            "end": equity.index[-1],
            "max_dd_pct": max_dd,
            "max_dd_date": max_dd_date,
        })

    return periods
