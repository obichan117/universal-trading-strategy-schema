"""Return metric calculations."""

from __future__ import annotations

import pandas as pd

from pyutss.results.types import BacktestResult

TRADING_DAYS_PER_YEAR = 252


def calculate_returns(result: BacktestResult) -> dict[str, float]:
    """Calculate return metrics."""
    total_return = result.final_equity - result.initial_capital
    total_return_pct = (total_return / result.initial_capital) * 100

    trading_days = len(result.equity_curve) if len(result.equity_curve) > 1 else 1
    years = trading_days / TRADING_DAYS_PER_YEAR

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


def get_daily_returns(equity_curve: pd.Series) -> pd.Series:
    """Calculate daily returns from equity curve."""
    if len(equity_curve) < 2:
        return pd.Series(dtype=float)

    returns = equity_curve.pct_change().dropna()
    return returns
