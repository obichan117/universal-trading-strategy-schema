"""Chart generation functions for backtest visualization.

Provides QuantStats-style charts for performance analysis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from pyutss.results.types import BacktestResult


def _check_matplotlib() -> None:
    """Check if matplotlib is available."""
    try:
        import matplotlib.pyplot as plt  # noqa: F401
    except ImportError:
        raise ImportError(
            "matplotlib is required for visualization. "
            "Install it with: pip install matplotlib"
        )


def _check_seaborn() -> None:
    """Check if seaborn is available."""
    try:
        import seaborn as sns  # noqa: F401
    except ImportError:
        raise ImportError(
            "seaborn is required for heatmaps. "
            "Install it with: pip install seaborn"
        )


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


def plot_trade_analysis(
    result: BacktestResult,
    ax: Axes | None = None,
    figsize: tuple[int, int] = (12, 5),
) -> Figure:
    """Plot trade P&L scatter with win/loss analysis.

    Args:
        result: BacktestResult from backtesting
        ax: Optional matplotlib axes
        figsize: Figure size

    Returns:
        Matplotlib Figure object
    """
    _check_matplotlib()
    import matplotlib.pyplot as plt

    if ax is None:
        fig, axes = plt.subplots(1, 2, figsize=figsize)
    else:
        fig = ax.get_figure()
        axes = [ax, ax]

    closed_trades = [t for t in result.trades if not t.is_open]
    if not closed_trades:
        axes[0].text(0.5, 0.5, "No closed trades", ha="center", va="center",
                     transform=axes[0].transAxes)
        return fig

    # Left plot: Trade P&L scatter
    ax1 = axes[0]
    entry_dates = [t.entry_date for t in closed_trades]
    pnls = [t.pnl for t in closed_trades]
    colors = ["green" if pnl > 0 else "red" for pnl in pnls]
    sizes = [min(abs(pnl) / 10 + 20, 200) for pnl in pnls]

    ax1.scatter(entry_dates, pnls, c=colors, s=sizes, alpha=0.6, edgecolors="black", linewidth=0.5)
    ax1.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax1.set_xlabel("Entry Date")
    ax1.set_ylabel("P&L ($)")
    ax1.set_title("Trade P&L by Entry Date")
    ax1.grid(True, alpha=0.3)

    # Rotate x-axis labels
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Right plot: Win/Loss distribution
    ax2 = axes[1] if len(axes) > 1 else ax1

    wins = [t.pnl for t in closed_trades if t.pnl > 0]
    losses = [abs(t.pnl) for t in closed_trades if t.pnl < 0]

    win_rate = len(wins) / len(closed_trades) * 100 if closed_trades else 0
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0

    categories = ["Winners", "Losers"]
    values = [len(wins), len(losses)]
    bar_colors = ["green", "red"]

    bars = ax2.bar(categories, values, color=bar_colors, alpha=0.7, edgecolor="black")

    # Add count labels on bars
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax2.annotate(
            f"{val}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            ha="center", va="bottom",
            fontsize=12, fontweight="bold",
        )

    # Add statistics
    stats_text = (
        f"Win Rate: {win_rate:.1f}%\n"
        f"Avg Win: ${avg_win:,.0f}\n"
        f"Avg Loss: ${avg_loss:,.0f}\n"
        f"Expectancy: ${(win_rate/100 * avg_win - (1-win_rate/100) * avg_loss):,.0f}"
    )
    ax2.text(
        0.95, 0.95, stats_text,
        transform=ax2.transAxes,
        fontsize=10,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    ax2.set_ylabel("Number of Trades")
    ax2.set_title("Win/Loss Distribution")
    ax2.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    return fig
