"""Performance metrics calculator."""

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from pyutss.results.types import BacktestResult


@dataclass
class PerformanceMetrics:
    """Complete performance metrics for a backtest."""

    # Return metrics
    total_return: float
    total_return_pct: float
    annualized_return: float
    annualized_return_pct: float

    # Risk-adjusted metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

    # Drawdown metrics
    max_drawdown: float
    max_drawdown_pct: float
    max_drawdown_duration_days: int
    avg_drawdown: float
    avg_drawdown_pct: float

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_trade_pnl: float
    avg_trade_duration_days: float

    # Risk metrics
    volatility: float
    volatility_annualized: float
    downside_deviation: float

    # Exposure metrics
    total_exposure_days: int
    exposure_pct: float

    def to_dict(self) -> dict[str, float]:
        """Convert metrics to dictionary."""
        return {
            "total_return": self.total_return,
            "total_return_pct": self.total_return_pct,
            "annualized_return": self.annualized_return,
            "annualized_return_pct": self.annualized_return_pct,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "calmar_ratio": self.calmar_ratio,
            "max_drawdown": self.max_drawdown,
            "max_drawdown_pct": self.max_drawdown_pct,
            "max_drawdown_duration_days": float(self.max_drawdown_duration_days),
            "avg_drawdown": self.avg_drawdown,
            "avg_drawdown_pct": self.avg_drawdown_pct,
            "total_trades": float(self.total_trades),
            "winning_trades": float(self.winning_trades),
            "losing_trades": float(self.losing_trades),
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "largest_win": self.largest_win,
            "largest_loss": self.largest_loss,
            "avg_trade_pnl": self.avg_trade_pnl,
            "avg_trade_duration_days": self.avg_trade_duration_days,
            "volatility": self.volatility,
            "volatility_annualized": self.volatility_annualized,
            "downside_deviation": self.downside_deviation,
            "total_exposure_days": float(self.total_exposure_days),
            "exposure_pct": self.exposure_pct,
        }


@dataclass
class PeriodBreakdown:
    """Performance breakdown for a period (month or year)."""

    period: str
    start_date: date
    end_date: date
    start_equity: float
    end_equity: float
    return_pct: float
    trades: int
    winning_trades: int
    max_drawdown_pct: float


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

    TRADING_DAYS_PER_YEAR = 252
    DEFAULT_RISK_FREE_RATE = 0.0

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
        returns = self._calculate_returns(result)
        risk_metrics = self._calculate_risk_metrics(result, returns)
        drawdown_metrics = self._calculate_drawdown_metrics(result)
        trade_stats = self._calculate_trade_statistics(result)
        exposure = self._calculate_exposure(result)

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

    def _calculate_returns(self, result: BacktestResult) -> dict[str, float]:
        """Calculate return metrics."""
        total_return = result.final_equity - result.initial_capital
        total_return_pct = (total_return / result.initial_capital) * 100

        trading_days = len(result.equity_curve) if len(result.equity_curve) > 1 else 1
        years = trading_days / self.TRADING_DAYS_PER_YEAR

        if years > 0 and result.initial_capital > 0 and result.final_equity > 0:
            annualized_return_pct = (
                (result.final_equity / result.initial_capital) ** (1 / years) - 1
            ) * 100
            annualized_return = result.initial_capital * (annualized_return_pct / 100)
        else:
            annualized_return = 0.0
            annualized_return_pct = 0.0

        return {
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "annualized_return": annualized_return,
            "annualized_return_pct": annualized_return_pct,
        }

    def _calculate_risk_metrics(
        self, result: BacktestResult, returns: dict[str, float]
    ) -> dict[str, float]:
        """Calculate risk-adjusted metrics."""
        daily_returns = self._get_daily_returns(result.equity_curve)

        if len(daily_returns) < 2:
            return {
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "calmar_ratio": 0.0,
                "volatility": 0.0,
                "volatility_annualized": 0.0,
                "downside_deviation": 0.0,
            }

        volatility = float(daily_returns.std())
        volatility_annualized = volatility * np.sqrt(self.TRADING_DAYS_PER_YEAR)

        downside_returns = daily_returns[daily_returns < 0]
        if len(downside_returns) > 0:
            downside_deviation = float(downside_returns.std())
            downside_deviation_annualized = downside_deviation * np.sqrt(
                self.TRADING_DAYS_PER_YEAR
            )
        else:
            downside_deviation = 0.0
            downside_deviation_annualized = 0.0

        daily_rf = self.risk_free_rate / self.TRADING_DAYS_PER_YEAR
        excess_returns = daily_returns - daily_rf
        avg_excess_return = float(excess_returns.mean())

        if volatility_annualized > 0:
            sharpe_ratio = (
                avg_excess_return * self.TRADING_DAYS_PER_YEAR
            ) / volatility_annualized
        else:
            sharpe_ratio = 0.0

        if downside_deviation_annualized > 0:
            sortino_ratio = (
                avg_excess_return * self.TRADING_DAYS_PER_YEAR
            ) / downside_deviation_annualized
        else:
            sortino_ratio = 0.0

        drawdown_metrics = self._calculate_drawdown_metrics(result)
        if drawdown_metrics["max_drawdown_pct"] > 0:
            calmar_ratio = (
                returns["annualized_return_pct"] / drawdown_metrics["max_drawdown_pct"]
            )
        else:
            calmar_ratio = 0.0

        return {
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "calmar_ratio": calmar_ratio,
            "volatility": volatility * 100,
            "volatility_annualized": volatility_annualized * 100,
            "downside_deviation": downside_deviation * 100,
        }

    def _calculate_drawdown_metrics(self, result: BacktestResult) -> dict[str, float]:
        """Calculate drawdown metrics."""
        if len(result.equity_curve) < 1:
            return {
                "max_drawdown": 0.0,
                "max_drawdown_pct": 0.0,
                "max_drawdown_duration_days": 0,
                "avg_drawdown": 0.0,
                "avg_drawdown_pct": 0.0,
            }

        equity = result.equity_curve
        running_max = equity.cummax()
        drawdown = running_max - equity
        drawdown_pct = (drawdown / running_max) * 100

        max_drawdown = float(drawdown.max())
        max_drawdown_pct = float(drawdown_pct.max())

        max_dd_duration = self._calculate_max_drawdown_duration(equity)

        in_drawdown = drawdown[drawdown > 0]
        if len(in_drawdown) > 0:
            avg_drawdown = float(in_drawdown.mean())
            avg_drawdown_pct = float(drawdown_pct[drawdown > 0].mean())
        else:
            avg_drawdown = 0.0
            avg_drawdown_pct = 0.0

        return {
            "max_drawdown": max_drawdown,
            "max_drawdown_pct": max_drawdown_pct,
            "max_drawdown_duration_days": max_dd_duration,
            "avg_drawdown": avg_drawdown,
            "avg_drawdown_pct": avg_drawdown_pct,
        }

    def _calculate_max_drawdown_duration(self, equity: pd.Series) -> int:
        """Calculate maximum drawdown duration in days."""
        running_max = equity.cummax()
        is_at_high = equity == running_max

        max_duration = 0
        current_duration = 0

        for at_high in is_at_high:
            if at_high:
                max_duration = max(max_duration, current_duration)
                current_duration = 0
            else:
                current_duration += 1

        max_duration = max(max_duration, current_duration)
        return max_duration

    def _calculate_trade_statistics(self, result: BacktestResult) -> dict[str, float]:
        """Calculate trade statistics."""
        closed_trades = [t for t in result.trades if not t.is_open]

        if not closed_trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
                "avg_trade_pnl": 0.0,
                "avg_trade_duration_days": 0.0,
            }

        total_trades = len(closed_trades)
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl < 0]

        win_count = len(winning_trades)
        loss_count = len(losing_trades)

        win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0.0

        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))

        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        else:
            profit_factor = float("inf") if gross_profit > 0 else 0.0

        avg_win = gross_profit / win_count if win_count > 0 else 0.0
        avg_loss = gross_loss / loss_count if loss_count > 0 else 0.0

        largest_win = max((t.pnl for t in winning_trades), default=0.0)
        largest_loss = abs(min((t.pnl for t in losing_trades), default=0.0))

        avg_trade_pnl = sum(t.pnl for t in closed_trades) / total_trades

        durations = []
        for trade in closed_trades:
            if trade.exit_date is not None:
                duration = (trade.exit_date - trade.entry_date).days
                durations.append(duration)

        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return {
            "total_trades": total_trades,
            "winning_trades": win_count,
            "losing_trades": loss_count,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "largest_win": largest_win,
            "largest_loss": largest_loss,
            "avg_trade_pnl": avg_trade_pnl,
            "avg_trade_duration_days": avg_duration,
        }

    def _calculate_exposure(self, result: BacktestResult) -> dict[str, float]:
        """Calculate market exposure metrics."""
        if not result.portfolio_history:
            return {
                "total_exposure_days": 0,
                "exposure_pct": 0.0,
            }

        days_with_positions = sum(
            1 for snapshot in result.portfolio_history if snapshot.positions_value > 0
        )

        total_days = len(result.portfolio_history)
        exposure_pct = (days_with_positions / total_days) * 100 if total_days > 0 else 0.0

        return {
            "total_exposure_days": days_with_positions,
            "exposure_pct": exposure_pct,
        }

    def _get_daily_returns(self, equity_curve: pd.Series) -> pd.Series:
        """Calculate daily returns from equity curve."""
        if len(equity_curve) < 2:
            return pd.Series(dtype=float)

        returns = equity_curve.pct_change().dropna()
        return returns

    def monthly_breakdown(self, result: BacktestResult) -> list[PeriodBreakdown]:
        """Generate monthly performance breakdown."""
        return self._period_breakdown(result, period_type="month")

    def yearly_breakdown(self, result: BacktestResult) -> list[PeriodBreakdown]:
        """Generate yearly performance breakdown."""
        return self._period_breakdown(result, period_type="year")

    def _period_breakdown(
        self, result: BacktestResult, period_type: str
    ) -> list[PeriodBreakdown]:
        """Generate period breakdown."""
        if len(result.equity_curve) < 1 or not result.portfolio_history:
            return []

        breakdowns: list[PeriodBreakdown] = []
        period_format = "%Y-%m" if period_type == "month" else "%Y"

        periods: dict[str, list] = {}
        for snapshot in result.portfolio_history:
            period_key = snapshot.date.strftime(period_format)
            if period_key not in periods:
                periods[period_key] = []
            periods[period_key].append(snapshot)

        for period_key in sorted(periods.keys()):
            snapshots = periods[period_key]

            start_snapshot = snapshots[0]
            end_snapshot = snapshots[-1]

            start_equity = start_snapshot.equity
            end_equity = end_snapshot.equity

            return_pct = (
                ((end_equity - start_equity) / start_equity) * 100
                if start_equity > 0
                else 0.0
            )

            period_trades = [
                t
                for t in result.trades
                if t.entry_date.strftime(period_format) == period_key
            ]
            winning = sum(1 for t in period_trades if t.pnl > 0)

            period_equity = [s.equity for s in snapshots]
            if period_equity:
                running_max = 0.0
                max_dd_pct = 0.0
                for eq in period_equity:
                    running_max = max(running_max, eq)
                    if running_max > 0:
                        dd_pct = ((running_max - eq) / running_max) * 100
                        max_dd_pct = max(max_dd_pct, dd_pct)
            else:
                max_dd_pct = 0.0

            breakdowns.append(
                PeriodBreakdown(
                    period=period_key,
                    start_date=start_snapshot.date,
                    end_date=end_snapshot.date,
                    start_equity=start_equity,
                    end_equity=end_equity,
                    return_pct=return_pct,
                    trades=len(period_trades),
                    winning_trades=winning,
                    max_drawdown_pct=max_dd_pct,
                )
            )

        return breakdowns

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
