"""Performance metric types."""

from dataclasses import dataclass
from datetime import date


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
