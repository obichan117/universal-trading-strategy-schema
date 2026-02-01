"""Result types for portfolio backtesting.

Extends BacktestResult with portfolio-specific metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from pyutss.results.types import BacktestResult


@dataclass
class SymbolContribution:
    """Contribution metrics for a single symbol in portfolio."""

    symbol: str
    weight_avg: float  # Average weight over period
    return_contribution: float  # Contribution to total return
    return_contribution_pct: float  # % of total return from this symbol
    volatility_contribution: float  # Contribution to portfolio volatility
    trades: int  # Number of trades
    win_rate: float  # Win rate for this symbol


@dataclass
class PortfolioResult:
    """Complete portfolio backtest result.

    Extends single-symbol BacktestResult with portfolio-level metrics
    including correlations, contributions, and per-symbol breakdowns.
    """

    # Basic info
    strategy_id: str
    symbols: list[str]
    start_date: date
    end_date: date
    initial_capital: float
    final_equity: float

    # Equity and history
    equity_curve: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    portfolio_weights: pd.DataFrame = field(default_factory=pd.DataFrame)

    # Per-symbol results
    per_symbol_results: dict[str, BacktestResult] = field(default_factory=dict)

    # Portfolio metrics
    rebalance_count: int = 0
    turnover: float = 0.0  # Average turnover per rebalance

    # Parameters used
    parameters: dict | None = None
    weight_scheme: str = "equal"
    rebalance_frequency: str = "monthly"

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
        """Total number of trades across all symbols."""
        return sum(
            r.num_trades for r in self.per_symbol_results.values()
        )

    @property
    def win_rate(self) -> float:
        """Overall win rate across all symbols."""
        total_trades = 0
        total_winners = 0

        for result in self.per_symbol_results.values():
            closed = [t for t in result.trades if not t.is_open]
            total_trades += len(closed)
            total_winners += sum(1 for t in closed if t.pnl > 0)

        if total_trades == 0:
            return 0.0
        return (total_winners / total_trades) * 100

    def correlation_matrix(self) -> pd.DataFrame:
        """Calculate return correlation matrix between symbols.

        Returns:
            DataFrame with pairwise correlations
        """
        if not self.per_symbol_results:
            return pd.DataFrame()

        # Build returns DataFrame
        returns_dict = {}
        for symbol, result in self.per_symbol_results.items():
            if len(result.equity_curve) > 1:
                returns_dict[symbol] = result.equity_curve.pct_change().dropna()

        if len(returns_dict) < 2:
            return pd.DataFrame()

        returns_df = pd.DataFrame(returns_dict)
        return returns_df.corr()

    def contribution_by_symbol(self) -> list[SymbolContribution]:
        """Calculate return/risk contribution by symbol.

        Returns:
            List of SymbolContribution objects
        """
        contributions = []

        total_return = self.total_return
        if total_return == 0:
            total_return = 1e-10  # Avoid division by zero

        for symbol, result in self.per_symbol_results.items():
            # Calculate contribution
            symbol_return = result.total_return

            # Average weight (if we have weight history)
            if not self.portfolio_weights.empty and symbol in self.portfolio_weights.columns:
                weight_avg = self.portfolio_weights[symbol].mean()
            else:
                weight_avg = 1.0 / len(self.symbols) if self.symbols else 0

            # Trades and win rate
            closed_trades = [t for t in result.trades if not t.is_open]
            num_trades = len(closed_trades)
            winners = sum(1 for t in closed_trades if t.pnl > 0)
            win_rate = (winners / num_trades * 100) if num_trades > 0 else 0

            # Volatility contribution (simplified)
            if len(result.equity_curve) > 1:
                vol = result.equity_curve.pct_change().std()
            else:
                vol = 0

            contributions.append(SymbolContribution(
                symbol=symbol,
                weight_avg=weight_avg,
                return_contribution=symbol_return,
                return_contribution_pct=(symbol_return / abs(total_return)) * 100 if total_return else 0,
                volatility_contribution=vol * weight_avg,
                trades=num_trades,
                win_rate=win_rate,
            ))

        return contributions

    def diversification_ratio(self) -> float:
        """Calculate diversification ratio.

        DR = weighted_avg_vol / portfolio_vol
        A ratio > 1 indicates diversification benefit.

        Returns:
            Diversification ratio
        """
        if len(self.per_symbol_results) < 2:
            return 1.0

        # Get returns for each symbol
        returns_dict = {}
        weights = {}

        for symbol, result in self.per_symbol_results.items():
            if len(result.equity_curve) > 1:
                returns_dict[symbol] = result.equity_curve.pct_change().dropna()
                # Use average weight or equal weight
                if not self.portfolio_weights.empty and symbol in self.portfolio_weights.columns:
                    weights[symbol] = self.portfolio_weights[symbol].mean()
                else:
                    weights[symbol] = 1.0 / len(self.symbols)

        if len(returns_dict) < 2:
            return 1.0

        # Calculate weighted average volatility
        weighted_vol = 0.0
        for symbol, rets in returns_dict.items():
            weighted_vol += weights.get(symbol, 0) * rets.std()

        # Calculate portfolio volatility
        returns_df = pd.DataFrame(returns_dict)
        returns_df = returns_df.dropna()

        if len(returns_df) < 2:
            return 1.0

        # Weight vector
        w = np.array([weights.get(s, 0) for s in returns_df.columns])
        w = w / w.sum() if w.sum() > 0 else w

        # Portfolio variance
        cov = returns_df.cov().values
        port_var = w @ cov @ w
        port_vol = np.sqrt(port_var) if port_var > 0 else 1e-10

        if port_vol > 0:
            return weighted_vol / port_vol
        return 1.0

    def summary(self, print_output: bool = True) -> str:
        """Generate and optionally print a summary of portfolio results.

        Args:
            print_output: Whether to print the summary

        Returns:
            Formatted string with portfolio statistics
        """
        lines = [
            "=" * 60,
            f" Portfolio Backtest Results",
            "=" * 60,
            f" Symbols:       {', '.join(self.symbols)}",
            f" Period:        {self.start_date} to {self.end_date}",
            f" Initial:       ${self.initial_capital:,.0f}",
            f" Final:         ${self.final_equity:,.2f}",
            "-" * 60,
            f" Total Return:  {'+' if self.total_return >= 0 else ''}{self.total_return_pct:.2f}%",
            f" Rebalances:    {self.rebalance_count}",
            f" Avg Turnover:  {self.turnover:.1f}%",
            "-" * 60,
            f" Total Trades:  {self.num_trades}",
            f" Win Rate:      {self.win_rate:.1f}%",
            "-" * 60,
            " Symbol Contributions:",
        ]

        for contrib in self.contribution_by_symbol():
            sign = "+" if contrib.return_contribution >= 0 else ""
            lines.append(
                f"   {contrib.symbol}: {sign}{contrib.return_contribution_pct:.1f}% "
                f"(avg wt: {contrib.weight_avg*100:.1f}%, trades: {contrib.trades})"
            )

        lines.append("=" * 60)

        output = "\n".join(lines)
        if print_output:
            print(output)
        return output
