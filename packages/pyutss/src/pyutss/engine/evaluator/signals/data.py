"""Data signal evaluators: fundamental, external, portfolio."""

from typing import Any

import pandas as pd

from pyutss.engine.evaluator.context import EvaluationContext, EvaluationError


def eval_fundamental_signal(
    signal: dict[str, Any], context: EvaluationContext
) -> pd.Series:
    """Evaluate fundamental signal.

    Looks up a fundamental metric (e.g. PE_RATIO) from context.fundamental_data.
    Returns a constant series (fundamentals are point-in-time snapshots).
    """
    metric = signal.get("metric", "PE_RATIO")
    symbol = signal.get("symbol")
    data = context.get_data()

    if context.fundamental_data is None:
        return pd.Series(float("nan"), index=data.index)

    # Look up by explicit symbol or use first available
    key = symbol or next(iter(context.fundamental_data), None)
    fund = context.fundamental_data.get(key) if key else None
    if fund is None:
        return pd.Series(float("nan"), index=data.index)

    # Map UPPER_CASE metric to snake_case attribute
    attr = metric.lower()
    value = getattr(fund, attr, None) if not isinstance(fund, dict) else fund.get(attr)
    return pd.Series(
        float(value) if value is not None else float("nan"),
        index=data.index,
    )


def eval_external_signal(
    signal: dict[str, Any], context: EvaluationContext
) -> pd.Series:
    """Evaluate external signal.

    Looks up a pre-loaded Series from context.external_data by key.
    Aligns to primary data index and fills gaps with default value.
    """
    source = signal.get("source", "file")
    default = signal.get("default", 0.0)
    data = context.get_data()

    if context.external_data is None:
        return pd.Series(default, index=data.index)

    # Build key from signal definition
    key = signal.get("url") or signal.get("path") or signal.get("provider") or source
    series = context.external_data.get(key)

    if series is None:
        return pd.Series(default, index=data.index)

    # Align to primary data index, fill gaps with default
    return series.reindex(data.index).fillna(default)


def eval_portfolio_signal(
    signal: dict[str, Any], context: EvaluationContext
) -> pd.Series:
    """Evaluate portfolio signal."""
    data = context.get_data()
    field = signal.get("field", "unrealized_pnl")
    symbol = signal.get("symbol")

    if context.portfolio_state is None:
        return pd.Series(0.0, index=data.index)

    ps = context.portfolio_state

    if field == "unrealized_pnl":
        value = ps.unrealized_pnl
    elif field == "realized_pnl":
        value = ps.realized_pnl
    elif field == "cash":
        value = ps.cash
    elif field == "equity":
        value = ps.equity
    elif field == "position_size":
        if symbol and symbol in ps.positions:
            value = ps.positions[symbol].quantity
        elif ps.positions:
            value = sum(p.quantity for p in ps.positions.values())
        else:
            value = 0.0
    elif field == "position_value":
        if symbol and symbol in ps.positions:
            pos = ps.positions[symbol]
            value = pos.quantity * pos.avg_price
        elif ps.positions:
            value = sum(p.quantity * p.avg_price for p in ps.positions.values())
        else:
            value = 0.0
    elif field == "days_in_position":
        if symbol and symbol in ps.positions:
            pos = ps.positions[symbol]
            value = pos.days_held if hasattr(pos, 'days_held') else 0
        elif ps.positions:
            value = max(
                (p.days_held if hasattr(p, 'days_held') else 0)
                for p in ps.positions.values()
            )
        else:
            value = 0
    elif field == "exposure":
        if ps.equity > 0:
            position_value = sum(
                p.quantity * p.avg_price for p in ps.positions.values()
            )
            value = (position_value / ps.equity) * 100
        else:
            value = 0.0
    elif field == "win_rate":
        if ps.total_trades > 0:
            value = (ps.winning_trades / ps.total_trades) * 100
        else:
            value = 0.0
    elif field == "total_trades":
        value = ps.total_trades
    elif field == "has_position":
        if symbol:
            value = 1.0 if symbol in ps.positions else 0.0
        else:
            value = 1.0 if ps.positions else 0.0
    else:
        raise EvaluationError(f"Unknown portfolio field: {field}")

    return pd.Series(float(value), index=data.index)
