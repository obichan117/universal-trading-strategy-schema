"""Plotting utilities for backtest results.

Provides visualization for backtest results including:
- Candlestick charts with entry/exit markers
- Equity curve overlay
- Summary statistics display
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from pyutss.results.types import BacktestResult


def plot_backtest(
    result: BacktestResult,
    data: pd.DataFrame,
    title: str | None = None,
    show_equity: bool = True,
    show_volume: bool = True,
    figsize: tuple[int, int] = (14, 8),
) -> None:
    """Plot backtest results with entry/exit markers.

    Args:
        result: BacktestResult from engine.run()
        data: OHLCV DataFrame used in backtest (must have DatetimeIndex)
        title: Chart title (default: symbol + return summary)
        show_equity: Whether to show equity curve subplot
        show_volume: Whether to show volume subplot
        figsize: Figure size (width, height)

    Raises:
        ImportError: If mplfinance is not installed

    Example:
        >>> result = engine.run(strategy, data, "AAPL")
        >>> plot_backtest(result, data)
    """
    try:
        import mplfinance as mpf
    except ImportError:
        raise ImportError(
            "mplfinance is required for plotting. "
            "Install it with: pip install pyutss[viz]"
        )

    # Ensure data has datetime index
    if not isinstance(data.index, pd.DatetimeIndex):
        data = data.copy()
        data.index = pd.to_datetime(data.index)

    # Normalize column names to lowercase
    data = data.copy()
    data.columns = [c.lower() for c in data.columns]

    # Build marker data for entries and exits
    buy_dates = []
    buy_prices = []
    sell_dates = []
    sell_prices = []

    for trade in result.trades:
        # Entry marker
        entry_dt = pd.Timestamp(trade.entry_date)
        if entry_dt in data.index:
            if trade.direction == "long":
                buy_dates.append(entry_dt)
                buy_prices.append(trade.entry_price)
            else:
                sell_dates.append(entry_dt)
                sell_prices.append(trade.entry_price)

        # Exit marker (if closed)
        if trade.exit_date is not None:
            exit_dt = pd.Timestamp(trade.exit_date)
            if exit_dt in data.index:
                if trade.direction == "long":
                    sell_dates.append(exit_dt)
                    sell_prices.append(trade.exit_price)
                else:
                    buy_dates.append(exit_dt)
                    buy_prices.append(trade.exit_price)

    # Create addplots for markers
    addplots = []

    # Buy markers (green triangles pointing up)
    if buy_dates:
        buy_series = pd.Series(index=data.index, dtype=float)
        for dt, price in zip(buy_dates, buy_prices):
            if dt in buy_series.index:
                buy_series[dt] = price
        addplots.append(
            mpf.make_addplot(
                buy_series,
                type="scatter",
                marker="^",
                markersize=100,
                color="green",
            )
        )

    # Sell markers (red triangles pointing down)
    if sell_dates:
        sell_series = pd.Series(index=data.index, dtype=float)
        for dt, price in zip(sell_dates, sell_prices):
            if dt in sell_series.index:
                sell_series[dt] = price
        addplots.append(
            mpf.make_addplot(
                sell_series,
                type="scatter",
                marker="v",
                markersize=100,
                color="red",
            )
        )

    # Equity curve as subplot
    if show_equity and len(result.equity_curve) > 0:
        # Align equity curve with data index
        equity_aligned = result.equity_curve.reindex(data.index)
        if not equity_aligned.isna().all():
            panel = 2 if show_volume else 1
            addplots.append(
                mpf.make_addplot(
                    equity_aligned,
                    panel=panel,
                    color="blue",
                    ylabel="Equity",
                )
            )

    # Build title with stats
    if title is None:
        return_pct = result.total_return_pct
        sign = "+" if return_pct >= 0 else ""
        title = f"{result.symbol} | Return: {sign}{return_pct:.1f}% | Trades: {result.num_trades}"

    # Determine panel ratios
    if show_equity and len(result.equity_curve) > 0:
        panel_ratios = (3, 1, 1) if show_volume else (4, 1)
    else:
        panel_ratios = (3, 1) if show_volume else None

    # Plot
    mpf.plot(
        data,
        type="candle",
        style="charles",
        title=title,
        addplot=addplots if addplots else None,
        volume=show_volume,
        panel_ratios=panel_ratios,
        figsize=figsize,
        warn_too_much_data=1000,
    )


def print_summary(result: BacktestResult) -> str:
    """Generate a text summary of backtest results.

    Args:
        result: BacktestResult from engine.run()

    Returns:
        Formatted string with backtest statistics

    Example:
        >>> result = engine.run(strategy, data, "AAPL")
        >>> print(print_summary(result))
    """
    # Calculate additional metrics
    closed_trades = [t for t in result.trades if not t.is_open]
    winning_trades = [t for t in closed_trades if t.pnl > 0]
    losing_trades = [t for t in closed_trades if t.pnl < 0]

    total_wins = sum(t.pnl for t in winning_trades) if winning_trades else 0
    total_losses = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0

    avg_win = total_wins / len(winning_trades) if winning_trades else 0
    avg_loss = total_losses / len(losing_trades) if losing_trades else 0

    profit_factor = total_wins / total_losses if total_losses > 0 else float("inf")

    # Calculate max drawdown from portfolio history
    max_dd_pct = 0.0
    if result.portfolio_history:
        max_dd_pct = max(s.drawdown_pct for s in result.portfolio_history)

    # Build summary
    lines = [
        "═" * 50,
        f" Backtest Results: {result.symbol}",
        "═" * 50,
        f" Period:        {result.start_date} to {result.end_date}",
        f" Initial:       ${result.initial_capital:,.0f}",
        f" Final:         ${result.final_equity:,.2f}",
        "─" * 50,
        f" Total Return:  {'+' if result.total_return >= 0 else ''}{result.total_return_pct:.2f}%",
        f" Max Drawdown:  -{max_dd_pct:.2f}%",
        "─" * 50,
        f" Total Trades:  {len(closed_trades)}",
        f" Win Rate:      {result.win_rate:.1f}%",
        f" Profit Factor: {profit_factor:.2f}" if profit_factor != float("inf") else " Profit Factor: ∞",
        f" Avg Win:       ${avg_win:,.2f}",
        f" Avg Loss:      ${avg_loss:,.2f}",
        "═" * 50,
    ]

    return "\n".join(lines)
