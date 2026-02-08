"""Plotting utilities for backtest results.

Provides visualization for backtest results including:
- Candlestick charts with entry/exit markers
- Equity curve overlay
- Summary statistics display
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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

    # Ensure data has datetime index and lowercase columns
    data = data.copy()
    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = pd.to_datetime(data.index)
    # Normalize to tz-naive for consistent matching
    if data.index.tz is not None:
        data.index = data.index.tz_localize(None)
    data.columns = [c.lower() for c in data.columns]

    # Build a date->timestamp lookup for matching trade dates to data index
    date_to_ts = {ts.date(): ts for ts in data.index}

    def _to_date(d: object) -> object:
        """Convert any date-like to datetime.date for lookup."""
        if isinstance(d, pd.Timestamp):
            return d.date()
        if hasattr(d, "date") and callable(d.date):
            return d.date()
        if hasattr(d, "year") and not hasattr(d, "hour"):
            return d  # already datetime.date
        return pd.Timestamp(d).date()

    # Build marker data for entries and exits
    buy_dates: list[pd.Timestamp] = []
    buy_prices: list[float] = []
    sell_dates: list[pd.Timestamp] = []
    sell_prices: list[float] = []

    for trade in result.trades:
        # Entry marker
        entry_ts = date_to_ts.get(_to_date(trade.entry_date))
        if entry_ts is not None:
            if trade.direction == "long":
                buy_dates.append(entry_ts)
                buy_prices.append(trade.entry_price)
            else:
                sell_dates.append(entry_ts)
                sell_prices.append(trade.entry_price)

        # Exit marker (if closed)
        if trade.exit_date is not None:
            exit_ts = date_to_ts.get(_to_date(trade.exit_date))
            if exit_ts is not None:
                if trade.direction == "long":
                    sell_dates.append(exit_ts)
                    sell_prices.append(trade.exit_price)
                else:
                    buy_dates.append(exit_ts)
                    buy_prices.append(trade.exit_price)

    def _make_scatter(dates: list[Any], prices: list[float], marker: str, color: str) -> dict[str, Any] | None:
        """Create scatter addplot only if series has non-NaN data."""
        series = pd.Series(index=data.index, dtype=float)
        for dt, price in zip(dates, prices):
            if dt in series.index:
                series[dt] = price
        if series.notna().any():
            return mpf.make_addplot(
                series, type="scatter", marker=marker, markersize=100, color=color,
            )
        return None

    # Create addplots for markers (only if they have actual data)
    addplots: list[dict] = []

    if buy_dates:
        ap = _make_scatter(buy_dates, buy_prices, "^", "green")
        if ap is not None:
            addplots.append(ap)

    if sell_dates:
        ap = _make_scatter(sell_dates, sell_prices, "v", "red")
        if ap is not None:
            addplots.append(ap)

    # Equity curve as subplot
    if show_equity and len(result.equity_curve) > 0:
        equity = result.equity_curve.copy()
        if not isinstance(equity.index, pd.DatetimeIndex):
            equity.index = pd.to_datetime(equity.index)
        if equity.index.tz is not None:
            equity.index = equity.index.tz_localize(None)
        equity_aligned = equity.reindex(data.index, method="ffill")
        if equity_aligned.notna().any():
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

    # Determine panel ratios based on what's actually plotted
    has_equity = any(
        ap.get("panel", 0) > 0 for ap in addplots if isinstance(ap, dict)
    )
    if has_equity:
        panel_ratios = (3, 1, 1) if show_volume else (4, 1)
    else:
        panel_ratios = (3, 1) if show_volume else None

    # Plot — never pass addplot=None or addplot=[]
    plot_kwargs: dict[str, Any] = dict(
        type="candle",
        style="charles",
        title=title,
        volume=show_volume,
        panel_ratios=panel_ratios,
        figsize=figsize,
        warn_too_much_data=1000,
    )
    if addplots:
        plot_kwargs["addplot"] = addplots

    mpf.plot(data, **plot_kwargs)


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
