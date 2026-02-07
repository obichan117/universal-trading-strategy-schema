"""Single-symbol backtest runner."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

import pandas as pd

from pyutss.engine.executor import OrderRequest
from pyutss.engine.portfolio import PortfolioManager
from pyutss.results.types import BacktestResult

if TYPE_CHECKING:
    from pyutss.engine.engine import Engine


def run_single(
    engine: Engine,
    strategy: dict[str, Any],
    data: pd.DataFrame,
    symbol: str,
    start_date: date | str | None,
    end_date: date | str | None,
    parameters: dict[str, float] | None,
) -> BacktestResult:
    """Run single-symbol backtest.

    Args:
        engine: Engine instance providing evaluators, executor, and config.
        strategy: Parsed UTSS strategy dict.
        data: OHLCV DataFrame for the symbol.
        symbol: Stock symbol.
        start_date: Optional start date filter.
        end_date: Optional end date filter.
        parameters: Strategy parameter overrides.

    Returns:
        BacktestResult with trades, equity curve, etc.
    """
    engine.signal_evaluator.clear_cache()

    data = engine._prepare_data(data, start_date, end_date)
    if data.empty:
        raise ValueError("No data in specified date range")

    pm = PortfolioManager(initial_capital=engine.initial_capital)
    context = engine._build_context(strategy, data, parameters)
    rules = strategy.get("rules", [])
    constraints = strategy.get("constraints", {})
    rule_signals = engine._precompute_rules(rules, context)

    for i, (idx, row) in enumerate(data.iterrows()):
        current_date = idx.date() if hasattr(idx, "date") else idx
        current_price = row["close"]
        prices = {symbol: current_price}

        pm.update_positions(prices, current_date)
        pm.check_exits(
            prices, current_date, constraints,
            engine.commission_rate, engine.slippage_rate,
        )

        for rule_idx, rule in enumerate(rules):
            if not rule.get("enabled", True):
                continue
            if rule_signals[rule_idx].iloc[i]:
                engine._execute_rule(
                    rule, symbol, current_price, current_date,
                    context, constraints, pm, data,
                )

        pm.record_snapshot(current_date, prices)

    # Close remaining positions via executor
    if pm.positions:
        final_price = data.iloc[-1]["close"]
        final_date = data.index[-1].date() if hasattr(data.index[-1], "date") else data.index[-1]
        for sym in list(pm.positions.keys()):
            qty = pm.positions[sym].quantity
            order = OrderRequest(symbol=sym, direction="sell", quantity=qty, price=final_price)
            fill = engine.executor.execute(order)
            commission = fill.commission if fill else 0.0
            slippage_cost = fill.slippage if fill else 0.0
            pm.close_position(sym, final_price, final_date, "end_of_backtest", commission, slippage_cost)

    strategy_id = strategy.get("info", {}).get("id", "unknown")
    actual_start = data.index[0].date() if hasattr(data.index[0], "date") else data.index[0]
    actual_end = data.index[-1].date() if hasattr(data.index[-1], "date") else data.index[-1]

    return BacktestResult(
        strategy_id=strategy_id,
        symbol=symbol,
        start_date=actual_start,
        end_date=actual_end,
        initial_capital=engine.initial_capital,
        final_equity=pm.get_equity({symbol: data.iloc[-1]["close"]}),
        trades=pm.trades,
        portfolio_history=pm.portfolio_history,
        equity_curve=pm.build_equity_series(),
        parameters=parameters,
    )
