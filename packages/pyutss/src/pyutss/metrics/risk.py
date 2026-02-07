"""Risk-adjusted metric calculations."""

from __future__ import annotations

import numpy as np

from pyutss.metrics.returns import TRADING_DAYS_PER_YEAR, get_daily_returns
from pyutss.results.types import BacktestResult


def calculate_risk_metrics(
    result: BacktestResult,
    returns: dict[str, float],
    drawdown_metrics: dict[str, float],
    risk_free_rate: float = 0.0,
    trading_days: int = TRADING_DAYS_PER_YEAR,
) -> dict[str, float]:
    """Calculate risk-adjusted metrics.

    Args:
        result: BacktestResult with equity curve.
        returns: Return metrics dict (from calculate_returns).
        drawdown_metrics: Drawdown metrics dict (from calculate_drawdown_metrics).
        risk_free_rate: Annual risk-free rate.
        trading_days: Trading days per year.
    """
    daily_returns = get_daily_returns(result.equity_curve)

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
    volatility_annualized = volatility * np.sqrt(trading_days)

    downside_returns = daily_returns[daily_returns < 0]
    if len(downside_returns) > 0:
        downside_deviation = float(downside_returns.std())
        downside_deviation_annualized = downside_deviation * np.sqrt(trading_days)
    else:
        downside_deviation = 0.0
        downside_deviation_annualized = 0.0

    daily_rf = risk_free_rate / trading_days
    excess_returns = daily_returns - daily_rf
    avg_excess_return = float(excess_returns.mean())

    if volatility_annualized > 0:
        sharpe_ratio = (
            avg_excess_return * trading_days
        ) / volatility_annualized
    else:
        sharpe_ratio = 0.0

    if downside_deviation_annualized > 0:
        sortino_ratio = (
            avg_excess_return * trading_days
        ) / downside_deviation_annualized
    else:
        sortino_ratio = 0.0

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
