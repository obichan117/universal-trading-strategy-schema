"""Rolling metrics and distribution charts."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pyutss.visualization.charts._guards import _check_matplotlib

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from pyutss.results.types import BacktestResult


def plot_rolling_metrics(
    result: BacktestResult,
    ax: Axes | None = None,
    figsize: tuple[int, int] = (12, 5),
    windows: list[int] | None = None,
    metric: str = "sharpe",
    risk_free_rate: float = 0.0,
) -> Figure:
    """Plot rolling Sharpe or Sortino ratio.

    Args:
        result: BacktestResult from backtesting
        ax: Optional matplotlib axes
        figsize: Figure size
        windows: Rolling window sizes in trading days (default: [126, 252] = 6m, 12m)
        metric: 'sharpe' or 'sortino'
        risk_free_rate: Annual risk-free rate

    Returns:
        Matplotlib Figure object
    """
    _check_matplotlib()
    import matplotlib.pyplot as plt

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    if windows is None:
        windows = [126, 252]  # 6-month, 12-month

    equity = result.equity_curve
    if len(equity) < max(windows):
        ax.text(0.5, 0.5, "Insufficient data for rolling metrics",
                ha="center", va="center", transform=ax.transAxes)
        return fig

    returns = equity.pct_change().dropna()
    daily_rf = risk_free_rate / 252

    colors = plt.cm.tab10(np.linspace(0, 1, len(windows)))
    labels = {126: "6-Month", 252: "12-Month", 63: "3-Month", 21: "1-Month"}

    for window, color in zip(windows, colors):
        if len(returns) < window:
            continue

        excess_returns = returns - daily_rf

        if metric == "sharpe":
            rolling_mean = excess_returns.rolling(window).mean()
            rolling_std = returns.rolling(window).std()
            rolling_metric = (rolling_mean / rolling_std) * np.sqrt(252)
        else:  # sortino
            rolling_mean = excess_returns.rolling(window).mean()
            neg_returns = returns.copy()
            neg_returns[neg_returns > 0] = 0
            rolling_downside = neg_returns.rolling(window).std()
            rolling_metric = (rolling_mean / rolling_downside) * np.sqrt(252)

        label = labels.get(window, f"{window}d")
        ax.plot(rolling_metric.index, rolling_metric.values,
                label=label, color=color, linewidth=1.5)

    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5, alpha=0.5)
    ax.axhline(y=1, color="green", linestyle="--", linewidth=0.5, alpha=0.5)
    ax.axhline(y=-1, color="red", linestyle="--", linewidth=0.5, alpha=0.5)

    metric_name = "Sharpe Ratio" if metric == "sharpe" else "Sortino Ratio"
    ax.set_ylabel(metric_name)
    ax.set_xlabel("")
    ax.set_title(f"Rolling {metric_name}")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_distribution(
    result: BacktestResult,
    ax: Axes | None = None,
    figsize: tuple[int, int] = (10, 6),
    period: str = "daily",
    bins: int = 50,
) -> Figure:
    """Plot return distribution with normal overlay and statistics.

    Args:
        result: BacktestResult from backtesting
        ax: Optional matplotlib axes
        figsize: Figure size
        period: 'daily', 'weekly', or 'monthly'
        bins: Number of histogram bins

    Returns:
        Matplotlib Figure object
    """
    _check_matplotlib()
    import matplotlib.pyplot as plt
    from scipy import stats

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.get_figure()

    equity = result.equity_curve
    if len(equity) < 2:
        ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center", transform=ax.transAxes)
        return fig

    # Calculate returns based on period
    if period == "weekly":
        resampled = equity.resample("W").last()
    elif period == "monthly":
        resampled = equity.resample("ME").last()
    else:
        resampled = equity

    returns = resampled.pct_change().dropna() * 100

    if len(returns) == 0:
        ax.text(0.5, 0.5, "No return data", ha="center", va="center", transform=ax.transAxes)
        return fig

    # Plot histogram
    n, bins_edges, patches = ax.hist(
        returns,
        bins=bins,
        density=True,
        alpha=0.7,
        color="#1f77b4",
        edgecolor="white",
    )

    # Fit normal distribution
    mu, std = returns.mean(), returns.std()
    x = np.linspace(returns.min(), returns.max(), 100)
    normal_dist = stats.norm.pdf(x, mu, std)
    ax.plot(x, normal_dist, "r-", linewidth=2, label="Normal Distribution")

    # Calculate statistics
    skewness = stats.skew(returns)
    kurtosis = stats.kurtosis(returns)

    # Add statistics box
    stats_text = (
        f"Mean: {mu:.2f}%\n"
        f"Std: {std:.2f}%\n"
        f"Skew: {skewness:.2f}\n"
        f"Kurt: {kurtosis:.2f}"
    )
    ax.text(
        0.95, 0.95, stats_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    period_label = period.capitalize()
    ax.set_xlabel(f"{period_label} Returns (%)")
    ax.set_ylabel("Density")
    ax.set_title(f"{period_label} Return Distribution")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig
