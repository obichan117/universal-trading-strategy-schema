"""Trade analysis charts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyutss.visualization.charts._guards import _check_matplotlib

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from pyutss.results.types import BacktestResult


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
