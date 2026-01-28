"""Result types for backtesting."""

from dataclasses import dataclass, field
from datetime import date

import pandas as pd


@dataclass
class Trade:
    """Individual trade record."""

    symbol: str
    direction: str  # "long" or "short"
    entry_date: date
    entry_price: float
    quantity: float
    exit_date: date | None = None
    exit_price: float | None = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    is_open: bool = True
    entry_reason: str = ""
    exit_reason: str = ""

    def close(
        self,
        exit_date: date,
        exit_price: float,
        reason: str = "",
        commission: float = 0.0,
        slippage: float = 0.0,
    ) -> None:
        """Close the trade.

        Args:
            exit_date: Exit date
            exit_price: Exit price
            reason: Exit reason
            commission: Commission paid
            slippage: Slippage cost
        """
        self.exit_date = exit_date
        self.exit_price = exit_price
        self.exit_reason = reason
        self.commission += commission
        self.slippage += slippage
        self.is_open = False

        if self.direction == "long":
            self.pnl = (exit_price - self.entry_price) * self.quantity
        else:
            self.pnl = (self.entry_price - exit_price) * self.quantity

        self.pnl -= self.commission + self.slippage

        if self.entry_price > 0:
            self.pnl_pct = (self.pnl / (self.entry_price * self.quantity)) * 100


@dataclass
class Position:
    """Current position state."""

    symbol: str
    quantity: float
    avg_price: float
    direction: str
    entry_date: date
    unrealized_pnl: float = 0.0
    days_held: int = 0

    def update_unrealized(self, current_price: float, current_date: date) -> None:
        """Update unrealized P&L.

        Args:
            current_price: Current market price
            current_date: Current date
        """
        if self.direction == "long":
            self.unrealized_pnl = (current_price - self.avg_price) * self.quantity
        else:
            self.unrealized_pnl = (self.avg_price - current_price) * self.quantity

        self.days_held = (current_date - self.entry_date).days


@dataclass
class PortfolioSnapshot:
    """Portfolio state at a point in time."""

    date: date
    cash: float
    positions_value: float
    equity: float
    drawdown: float = 0.0
    drawdown_pct: float = 0.0


@dataclass
class BacktestConfig:
    """Configuration for backtesting."""

    initial_capital: float = 100000.0
    commission_rate: float = 0.001  # 0.1% per trade
    slippage_rate: float = 0.0005  # 0.05% slippage
    risk_free_rate: float = 0.0  # Annual risk-free rate
    margin_requirement: float = 1.0  # 1.0 = no margin


@dataclass
class BacktestResult:
    """Complete backtest result."""

    strategy_id: str
    symbol: str
    start_date: date
    end_date: date
    initial_capital: float
    final_equity: float
    trades: list[Trade] = field(default_factory=list)
    portfolio_history: list[PortfolioSnapshot] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    benchmark_curve: pd.Series | None = None
    parameters: dict | None = None

    @property
    def total_return(self) -> float:
        """Total return in currency."""
        return self.final_equity - self.initial_capital

    @property
    def total_return_pct(self) -> float:
        """Total return as percentage."""
        return (self.total_return / self.initial_capital) * 100

    @property
    def num_trades(self) -> int:
        """Total number of trades."""
        return len(self.trades)

    @property
    def win_rate(self) -> float:
        """Win rate as percentage."""
        closed = [t for t in self.trades if not t.is_open]
        if not closed:
            return 0.0
        winners = sum(1 for t in closed if t.pnl > 0)
        return (winners / len(closed)) * 100

    def plot(
        self,
        data: pd.DataFrame,
        title: str | None = None,
        show_equity: bool = True,
        show_volume: bool = True,
        figsize: tuple[int, int] = (14, 8),
    ) -> None:
        """Plot backtest results with entry/exit markers.

        Displays a candlestick chart with buy/sell markers overlaid,
        plus optional volume and equity curve subplots.

        Args:
            data: OHLCV DataFrame used in backtest (must have DatetimeIndex)
            title: Chart title (default: symbol + return summary)
            show_equity: Whether to show equity curve subplot
            show_volume: Whether to show volume subplot
            figsize: Figure size (width, height)

        Raises:
            ImportError: If mplfinance is not installed

        Example:
            >>> result = engine.run(strategy, data, "AAPL")
            >>> result.plot(data)
        """
        from pyutss.results.plotting import plot_backtest

        plot_backtest(
            result=self,
            data=data,
            title=title,
            show_equity=show_equity,
            show_volume=show_volume,
            figsize=figsize,
        )

    def summary(self, print_output: bool = True) -> str:
        """Generate and optionally print a summary of backtest results.

        Args:
            print_output: Whether to print the summary (default: True)

        Returns:
            Formatted string with backtest statistics

        Example:
            >>> result = engine.run(strategy, data, "AAPL")
            >>> result.summary()
            ══════════════════════════════════════════════════
             Backtest Results: AAPL
            ══════════════════════════════════════════════════
             ...
        """
        from pyutss.results.plotting import print_summary

        output = print_summary(self)
        if print_output:
            print(output)
        return output
