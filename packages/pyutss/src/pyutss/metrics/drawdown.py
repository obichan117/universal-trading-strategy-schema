"""Drawdown metric calculations."""

from __future__ import annotations

import pandas as pd

from pyutss.results.types import BacktestResult


def calculate_drawdown_metrics(result: BacktestResult) -> dict[str, float]:
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

    max_dd_duration = calculate_max_drawdown_duration(equity)

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


def calculate_max_drawdown_duration(equity: pd.Series) -> int:
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
