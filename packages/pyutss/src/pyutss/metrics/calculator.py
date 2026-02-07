"""Performance metrics calculator (thin orchestrator)."""

import pandas as pd

from pyutss.metrics.drawdown import calculate_drawdown_metrics
from pyutss.metrics.exposure import calculate_exposure
from pyutss.metrics.periods import period_breakdown
from pyutss.metrics.returns import calculate_returns
from pyutss.metrics.risk import calculate_risk_metrics
from pyutss.metrics.trades import calculate_trade_statistics
from pyutss.metrics.types import PerformanceMetrics, PeriodBreakdown
from pyutss.results.types import BacktestResult

TRADING_DAYS_PER_YEAR = 252
DEFAULT_RISK_FREE_RATE = 0.0


class MetricsCalculator:
    """Calculator for trading performance metrics.

    Computes industry-standard metrics from backtest results including:
    - Return metrics (total, annualized)
    - Risk-adjusted metrics (Sharpe, Sortino, Calmar)
    - Drawdown analysis
    - Trade statistics (win rate, profit factor, etc.)
    - Period breakdowns (monthly, yearly)

    Example:
        calculator = MetricsCalculator()
        metrics = calculator.calculate(backtest_result)
        print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    """

    def __init__(self, risk_free_rate: float = DEFAULT_RISK_FREE_RATE) -> None:
        """Initialize metrics calculator.

        Args:
            risk_free_rate: Annual risk-free rate for Sharpe/Sortino calculation
        """
        self.risk_free_rate = risk_free_rate

    def calculate(self, result: BacktestResult) -> PerformanceMetrics:
        """Calculate all performance metrics.

        Args:
            result: BacktestResult from backtesting engine

        Returns:
            PerformanceMetrics with all calculated values
        """
        returns = calculate_returns(result)
        drawdown_metrics = calculate_drawdown_metrics(result)
        risk_metrics = calculate_risk_metrics(
            result, returns, drawdown_metrics,
            risk_free_rate=self.risk_free_rate,
            trading_days=TRADING_DAYS_PER_YEAR,
        )
        trade_stats = calculate_trade_statistics(result)
        exposure = calculate_exposure(result)

        return PerformanceMetrics(
            total_return=returns["total_return"],
            total_return_pct=returns["total_return_pct"],
            annualized_return=returns["annualized_return"],
            annualized_return_pct=returns["annualized_return_pct"],
            sharpe_ratio=risk_metrics["sharpe_ratio"],
            sortino_ratio=risk_metrics["sortino_ratio"],
            calmar_ratio=risk_metrics["calmar_ratio"],
            max_drawdown=drawdown_metrics["max_drawdown"],
            max_drawdown_pct=drawdown_metrics["max_drawdown_pct"],
            max_drawdown_duration_days=drawdown_metrics["max_drawdown_duration_days"],
            avg_drawdown=drawdown_metrics["avg_drawdown"],
            avg_drawdown_pct=drawdown_metrics["avg_drawdown_pct"],
            total_trades=trade_stats["total_trades"],
            winning_trades=trade_stats["winning_trades"],
            losing_trades=trade_stats["losing_trades"],
            win_rate=trade_stats["win_rate"],
            profit_factor=trade_stats["profit_factor"],
            avg_win=trade_stats["avg_win"],
            avg_loss=trade_stats["avg_loss"],
            largest_win=trade_stats["largest_win"],
            largest_loss=trade_stats["largest_loss"],
            avg_trade_pnl=trade_stats["avg_trade_pnl"],
            avg_trade_duration_days=trade_stats["avg_trade_duration_days"],
            volatility=risk_metrics["volatility"],
            volatility_annualized=risk_metrics["volatility_annualized"],
            downside_deviation=risk_metrics["downside_deviation"],
            total_exposure_days=exposure["total_exposure_days"],
            exposure_pct=exposure["exposure_pct"],
        )

    def monthly_breakdown(self, result: BacktestResult) -> list[PeriodBreakdown]:
        """Generate monthly performance breakdown."""
        return period_breakdown(result, period_type="month")

    def yearly_breakdown(self, result: BacktestResult) -> list[PeriodBreakdown]:
        """Generate yearly performance breakdown."""
        return period_breakdown(result, period_type="year")

    def compare_results(self, results: list[BacktestResult]) -> pd.DataFrame:
        """Compare metrics across multiple backtest results."""
        if not results:
            return pd.DataFrame()

        rows = []
        for result in results:
            metrics = self.calculate(result)
            row = {
                "strategy_id": result.strategy_id,
                "symbol": result.symbol,
                **metrics.to_dict(),
            }
            rows.append(row)

        return pd.DataFrame(rows)
