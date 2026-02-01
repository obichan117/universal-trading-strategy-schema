"""Monte Carlo simulation for trading strategy analysis.

Provides statistical methods for analyzing strategy robustness:
- Trade shuffling: Randomize trade order to assess path-dependency
- Bootstrap returns: Resample daily returns for confidence intervals

Example:
    from pyutss.analysis import MonteCarloSimulator

    simulator = MonteCarloSimulator()

    # Analyze trade sequence robustness
    result = simulator.shuffle_trades(trades, n_iterations=1000)
    print(f"95% drawdown confidence: {result.drawdown_95:.2%}")

    # Analyze return distribution
    result = simulator.bootstrap_returns(daily_returns, n_iterations=1000)
    print(f"Sharpe 95% CI: [{result.sharpe_ci[0]:.2f}, {result.sharpe_ci[1]:.2f}]")
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


TRADING_DAYS_PER_YEAR = 252


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation.

    Attributes:
        n_iterations: Number of simulation iterations
        drawdown_95: 95th percentile max drawdown
        drawdown_99: 99th percentile max drawdown
        drawdown_median: Median max drawdown
        drawdown_mean: Mean max drawdown
        return_ci: 95% confidence interval for total return (low, high)
        sharpe_ci: 95% confidence interval for Sharpe ratio (low, high)
        final_equity_ci: 95% CI for final equity (low, high)
        win_rate_ci: 95% confidence interval for win rate (low, high)
        profit_factor_ci: 95% CI for profit factor (low, high)
        all_max_drawdowns: Array of max drawdowns from all iterations
        all_total_returns: Array of total returns from all iterations
        all_sharpe_ratios: Array of Sharpe ratios from all iterations
    """

    n_iterations: int
    drawdown_95: float
    drawdown_99: float
    drawdown_median: float
    drawdown_mean: float
    return_ci: tuple[float, float]
    sharpe_ci: tuple[float, float]
    final_equity_ci: tuple[float, float]
    win_rate_ci: tuple[float, float]
    profit_factor_ci: tuple[float, float]
    all_max_drawdowns: np.ndarray = field(repr=False)
    all_total_returns: np.ndarray = field(repr=False)
    all_sharpe_ratios: np.ndarray = field(repr=False)

    def to_dict(self) -> dict:
        """Convert results to dictionary (excludes large arrays)."""
        return {
            "n_iterations": self.n_iterations,
            "drawdown_95": self.drawdown_95,
            "drawdown_99": self.drawdown_99,
            "drawdown_median": self.drawdown_median,
            "drawdown_mean": self.drawdown_mean,
            "return_ci_low": self.return_ci[0],
            "return_ci_high": self.return_ci[1],
            "sharpe_ci_low": self.sharpe_ci[0],
            "sharpe_ci_high": self.sharpe_ci[1],
            "final_equity_ci_low": self.final_equity_ci[0],
            "final_equity_ci_high": self.final_equity_ci[1],
            "win_rate_ci_low": self.win_rate_ci[0],
            "win_rate_ci_high": self.win_rate_ci[1],
            "profit_factor_ci_low": self.profit_factor_ci[0],
            "profit_factor_ci_high": self.profit_factor_ci[1],
        }

    def summary(self) -> str:
        """Generate human-readable summary."""
        return (
            f"Monte Carlo Simulation Results ({self.n_iterations:,} iterations)\n"
            f"{'=' * 50}\n"
            f"Drawdown Analysis:\n"
            f"  Median Max Drawdown: {self.drawdown_median:.2%}\n"
            f"  95th Percentile:     {self.drawdown_95:.2%}\n"
            f"  99th Percentile:     {self.drawdown_99:.2%}\n"
            f"\nReturn Analysis (95% CI):\n"
            f"  Total Return: [{self.return_ci[0]:.2%}, {self.return_ci[1]:.2%}]\n"
            f"  Sharpe Ratio: [{self.sharpe_ci[0]:.2f}, {self.sharpe_ci[1]:.2f}]\n"
            f"\nTrade Statistics (95% CI):\n"
            f"  Win Rate:      [{self.win_rate_ci[0]:.1f}%, {self.win_rate_ci[1]:.1f}%]\n"
            f"  Profit Factor: [{self.profit_factor_ci[0]:.2f}, {self.profit_factor_ci[1]:.2f}]\n"
        )


@dataclass
class TradeInfo:
    """Simplified trade info for Monte Carlo simulation."""

    pnl: float
    duration_days: int = 1


class MonteCarloSimulator:
    """Monte Carlo simulator for trading strategy analysis.

    Provides two main analysis methods:
    1. shuffle_trades: Randomly reorder trades to assess path-dependency
    2. bootstrap_returns: Resample daily returns for statistical confidence

    Example:
        simulator = MonteCarloSimulator(seed=42)

        # From trade list
        trades = [TradeInfo(pnl=100), TradeInfo(pnl=-50), TradeInfo(pnl=75)]
        result = simulator.shuffle_trades(trades, initial_capital=10000)

        # From daily returns
        returns = pd.Series([0.01, -0.02, 0.015, ...])
        result = simulator.bootstrap_returns(returns)
    """

    def __init__(self, seed: int | None = None) -> None:
        """Initialize simulator.

        Args:
            seed: Random seed for reproducibility
        """
        self.rng = np.random.default_rng(seed)

    def shuffle_trades(
        self,
        trades: list[TradeInfo] | list[dict],
        initial_capital: float = 100000.0,
        n_iterations: int = 1000,
    ) -> MonteCarloResult:
        """Simulate different trade orderings via shuffling.

        Randomly reorders the trade sequence to analyze how much the
        strategy's performance depends on the specific order of trades.

        Args:
            trades: List of trades (TradeInfo or dicts with 'pnl' key)
            initial_capital: Starting capital
            n_iterations: Number of shuffle iterations

        Returns:
            MonteCarloResult with confidence intervals and statistics

        Example:
            >>> trades = [TradeInfo(pnl=100), TradeInfo(pnl=-50)]
            >>> result = simulator.shuffle_trades(trades)
            >>> print(f"95% DD: {result.drawdown_95:.2%}")
        """
        # Normalize to list of PnLs
        pnls = self._extract_pnls(trades)

        if len(pnls) == 0:
            return self._empty_result(n_iterations)

        # Run simulations
        max_drawdowns = []
        total_returns = []
        final_equities = []
        win_rates = []
        profit_factors = []
        sharpe_ratios = []

        for _ in range(n_iterations):
            shuffled = self.rng.permutation(pnls)
            equity_curve = self._build_equity_curve(shuffled, initial_capital)

            max_dd = self._calculate_max_drawdown(equity_curve)
            max_drawdowns.append(max_dd)

            final_eq = equity_curve[-1]
            final_equities.append(final_eq)

            total_ret = (final_eq - initial_capital) / initial_capital
            total_returns.append(total_ret)

            # Trade stats
            wins = np.sum(shuffled > 0)
            win_rate = (wins / len(shuffled)) * 100 if len(shuffled) > 0 else 0
            win_rates.append(win_rate)

            gross_profit = np.sum(shuffled[shuffled > 0])
            gross_loss = abs(np.sum(shuffled[shuffled < 0]))
            pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")
            profit_factors.append(pf if np.isfinite(pf) else 10.0)  # Cap at 10

            # Simplified Sharpe (using trade returns)
            daily_returns = shuffled / initial_capital
            if len(daily_returns) > 1 and np.std(daily_returns) > 0:
                sharpe = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252)
            else:
                sharpe = 0.0
            sharpe_ratios.append(sharpe)

        return self._build_result(
            n_iterations=n_iterations,
            max_drawdowns=np.array(max_drawdowns),
            total_returns=np.array(total_returns),
            final_equities=np.array(final_equities),
            win_rates=np.array(win_rates),
            profit_factors=np.array(profit_factors),
            sharpe_ratios=np.array(sharpe_ratios),
        )

    def bootstrap_returns(
        self,
        returns: pd.Series | np.ndarray,
        initial_capital: float = 100000.0,
        n_iterations: int = 1000,
        block_size: int | None = None,
    ) -> MonteCarloResult:
        """Bootstrap resample daily returns for confidence intervals.

        Uses block bootstrap to preserve some autocorrelation structure
        in the returns series.

        Args:
            returns: Daily returns (as decimals, e.g., 0.01 for 1%)
            initial_capital: Starting capital for equity curve
            n_iterations: Number of bootstrap iterations
            block_size: Block size for block bootstrap (default: sqrt(n))

        Returns:
            MonteCarloResult with confidence intervals

        Example:
            >>> returns = strategy_equity.pct_change().dropna()
            >>> result = simulator.bootstrap_returns(returns)
            >>> print(f"Sharpe CI: {result.sharpe_ci}")
        """
        if isinstance(returns, pd.Series):
            returns = returns.values

        n_samples = len(returns)
        if n_samples < 2:
            return self._empty_result(n_iterations)

        # Default block size: sqrt(n) for stationary bootstrap
        if block_size is None:
            block_size = max(1, int(np.sqrt(n_samples)))

        # Run simulations
        max_drawdowns = []
        total_returns = []
        final_equities = []
        sharpe_ratios = []

        for _ in range(n_iterations):
            # Block bootstrap
            resampled = self._block_bootstrap(returns, n_samples, block_size)

            # Build equity curve from returns
            equity = initial_capital * np.cumprod(1 + resampled)
            equity = np.insert(equity, 0, initial_capital)

            max_dd = self._calculate_max_drawdown(equity)
            max_drawdowns.append(max_dd)

            final_eq = equity[-1]
            final_equities.append(final_eq)

            total_ret = (final_eq - initial_capital) / initial_capital
            total_returns.append(total_ret)

            # Sharpe ratio
            if np.std(resampled) > 0:
                sharpe = np.mean(resampled) / np.std(resampled) * np.sqrt(252)
            else:
                sharpe = 0.0
            sharpe_ratios.append(sharpe)

        # For return-based bootstrap, win rate and profit factor don't apply
        dummy_win_rates = np.full(n_iterations, 50.0)
        dummy_profit_factors = np.full(n_iterations, 1.0)

        return self._build_result(
            n_iterations=n_iterations,
            max_drawdowns=np.array(max_drawdowns),
            total_returns=np.array(total_returns),
            final_equities=np.array(final_equities),
            win_rates=dummy_win_rates,
            profit_factors=dummy_profit_factors,
            sharpe_ratios=np.array(sharpe_ratios),
        )

    def _extract_pnls(self, trades: list) -> np.ndarray:
        """Extract PnL values from trade list."""
        pnls = []
        for trade in trades:
            if isinstance(trade, dict):
                pnls.append(trade.get("pnl", 0.0))
            elif hasattr(trade, "pnl"):
                pnls.append(trade.pnl)
            else:
                pnls.append(float(trade))
        return np.array(pnls)

    def _build_equity_curve(
        self, pnls: np.ndarray, initial_capital: float
    ) -> np.ndarray:
        """Build equity curve from PnL sequence."""
        cumulative = np.cumsum(pnls)
        equity = initial_capital + cumulative
        return np.insert(equity, 0, initial_capital)

    def _calculate_max_drawdown(self, equity: np.ndarray) -> float:
        """Calculate maximum drawdown percentage."""
        running_max = np.maximum.accumulate(equity)
        drawdown = (running_max - equity) / running_max
        return float(np.max(drawdown))

    def _block_bootstrap(
        self, data: np.ndarray, n_samples: int, block_size: int
    ) -> np.ndarray:
        """Perform block bootstrap resampling."""
        n_blocks = int(np.ceil(n_samples / block_size))
        resampled = []

        for _ in range(n_blocks):
            # Random starting point
            start = self.rng.integers(0, len(data) - block_size + 1)
            block = data[start : start + block_size]
            resampled.extend(block)

        return np.array(resampled[:n_samples])

    def _build_result(
        self,
        n_iterations: int,
        max_drawdowns: np.ndarray,
        total_returns: np.ndarray,
        final_equities: np.ndarray,
        win_rates: np.ndarray,
        profit_factors: np.ndarray,
        sharpe_ratios: np.ndarray,
    ) -> MonteCarloResult:
        """Build MonteCarloResult from simulation arrays."""
        return MonteCarloResult(
            n_iterations=n_iterations,
            drawdown_95=float(np.percentile(max_drawdowns, 95)),
            drawdown_99=float(np.percentile(max_drawdowns, 99)),
            drawdown_median=float(np.median(max_drawdowns)),
            drawdown_mean=float(np.mean(max_drawdowns)),
            return_ci=(
                float(np.percentile(total_returns, 2.5)),
                float(np.percentile(total_returns, 97.5)),
            ),
            sharpe_ci=(
                float(np.percentile(sharpe_ratios, 2.5)),
                float(np.percentile(sharpe_ratios, 97.5)),
            ),
            final_equity_ci=(
                float(np.percentile(final_equities, 2.5)),
                float(np.percentile(final_equities, 97.5)),
            ),
            win_rate_ci=(
                float(np.percentile(win_rates, 2.5)),
                float(np.percentile(win_rates, 97.5)),
            ),
            profit_factor_ci=(
                float(np.percentile(profit_factors, 2.5)),
                float(np.percentile(profit_factors, 97.5)),
            ),
            all_max_drawdowns=max_drawdowns,
            all_total_returns=total_returns,
            all_sharpe_ratios=sharpe_ratios,
        )

    def _empty_result(self, n_iterations: int) -> MonteCarloResult:
        """Return empty result for edge cases."""
        empty = np.array([0.0])
        return MonteCarloResult(
            n_iterations=n_iterations,
            drawdown_95=0.0,
            drawdown_99=0.0,
            drawdown_median=0.0,
            drawdown_mean=0.0,
            return_ci=(0.0, 0.0),
            sharpe_ci=(0.0, 0.0),
            final_equity_ci=(0.0, 0.0),
            win_rate_ci=(0.0, 0.0),
            profit_factor_ci=(0.0, 0.0),
            all_max_drawdowns=empty,
            all_total_returns=empty,
            all_sharpe_ratios=empty,
        )
