"""Rule execution logic for backtesting."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import pandas as pd

from pyutss.engine.evaluator import (
    ConditionEvaluator,
    EvaluationContext,
)
from pyutss.engine.executor import BacktestExecutor, OrderRequest
from pyutss.engine.portfolio import PortfolioManager
from pyutss.engine.sizing import calculate_size

logger = logging.getLogger(__name__)


def execute_rule(
    executor: BacktestExecutor,
    rule: dict[str, Any],
    symbol: str,
    price: float,
    current_date: date,
    context: EvaluationContext,
    constraints: dict[str, Any],
    pm: PortfolioManager,
    data: pd.DataFrame,
) -> None:
    """Execute a triggered rule."""
    action = rule.get("then", {})
    action_type = action.get("type", "trade")

    if action_type == "trade":
        execute_trade(executor, action, symbol, price, current_date, context, constraints, pm, data)
    elif action_type == "alert":
        logger.info(f"Alert: {action.get('message', 'Signal triggered')}")
    elif action_type == "hold":
        pass


def execute_trade(
    executor: BacktestExecutor,
    action: dict[str, Any],
    symbol: str,
    price: float,
    current_date: date,
    context: EvaluationContext,
    constraints: dict[str, Any],
    pm: PortfolioManager,
    data: pd.DataFrame,
) -> None:
    """Execute a trade action via the Executor."""
    direction = action.get("direction", "buy")

    # Check constraints
    if direction in ("buy", "long", "short"):
        max_positions = constraints.get("max_positions")
        if max_positions and len(pm.positions) >= max_positions:
            return

        if direction == "short" and constraints.get("no_shorting", False):
            return

    # Handle sell/cover via executor
    if direction in ("sell", "close"):
        if symbol in pm.positions:
            qty = pm.positions[symbol].quantity
            order = OrderRequest(symbol=symbol, direction="sell", quantity=qty, price=price)
            fill = executor.execute(order)
            if fill:
                pm.close_position(symbol, price, current_date, "sell_signal", fill.commission, fill.slippage)
        return

    if direction == "cover":
        if symbol in pm.positions and pm.positions[symbol].direction == "short":
            qty = pm.positions[symbol].quantity
            order = OrderRequest(symbol=symbol, direction="cover", quantity=qty, price=price)
            fill = executor.execute(order)
            if fill:
                pm.close_position(symbol, price, current_date, "cover_signal", fill.commission, fill.slippage)
        return

    # Calculate size
    sizing = action.get("sizing", {"type": "percent_of_equity", "percent": 10})
    equity = pm.get_equity({symbol: price})

    quantity = calculate_size(
        sizing, price, equity, pm.cash,
        positions=pm.positions, trades=pm.trades, data=data,
    )

    if quantity <= 0:
        return

    # Execute through executor (handles lot rounding, commission, slippage)
    trade_direction = "buy" if direction in ("buy", "long") else "short"
    order = OrderRequest(
        symbol=symbol, direction=trade_direction, quantity=quantity, price=price,
    )
    fill = executor.execute(order)
    if fill is None:
        return

    pm_direction = "long" if direction in ("buy", "long") else "short"
    pm.open_position(
        symbol, fill.quantity, price, pm_direction, current_date,
        commission=fill.commission, slippage=fill.slippage,
        reason=action.get("reason", "rule_triggered"),
    )


def precompute_rules(
    condition_evaluator: ConditionEvaluator,
    rules: list[dict[str, Any]],
    context: EvaluationContext,
) -> list[pd.Series]:
    """Pre-compute rule conditions for all bars."""
    signals = []
    for rule in rules:
        condition = rule.get("when", {"type": "always"})
        try:
            signal = condition_evaluator.evaluate_condition(condition, context)
            signals.append(signal)
        except Exception as e:
            logger.warning(f"Failed to evaluate rule condition: {e}")
            signals.append(pd.Series(False, index=context.primary_data.index))
    return signals


def build_context(
    strategy: dict[str, Any],
    data: pd.DataFrame,
    parameters: dict[str, float] | None,
) -> EvaluationContext:
    """Build evaluation context from strategy and data."""
    return EvaluationContext(
        primary_data=data,
        signal_library=strategy.get("signals", {}),
        condition_library=strategy.get("conditions", {}),
        parameters=parameters or strategy.get("parameters", {}).get("defaults", {}),
    )
