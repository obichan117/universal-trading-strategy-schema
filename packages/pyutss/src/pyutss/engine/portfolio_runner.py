"""Multi-symbol portfolio backtest runner."""

from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING, Any

import pandas as pd

from pyutss.engine.data_resolver import prepare_data
from pyutss.engine.executor import OrderRequest
from pyutss.engine.portfolio import PortfolioManager
from pyutss.engine.rule_executor import (
    build_context,
    execute_rule,
    precompute_rules,
)
from pyutss.engine.weight_manager import (
    get_current_weights,
    get_weight_scheme,
    get_weight_scheme_name,
    rebalance,
)
from pyutss.portfolio.result import PortfolioResult
from pyutss.portfolio.weights import WeightScheme
from pyutss.results.types import BacktestResult

if TYPE_CHECKING:
    from pyutss.engine.engine import Engine

logger = logging.getLogger(__name__)


def run_multi(
    engine: Engine,
    strategy: dict[str, Any],
    data: dict[str, pd.DataFrame],
    symbols: list[str],
    start_date: date | str | None,
    end_date: date | str | None,
    parameters: dict[str, float] | None,
    weights: str | WeightScheme | dict[str, float],
) -> PortfolioResult:
    """Run multi-symbol portfolio backtest.

    Args:
        engine: Engine instance providing evaluators, executor, and config.
        strategy: Parsed UTSS strategy dict.
        data: Dict mapping symbol -> OHLCV DataFrame.
        symbols: List of symbols to trade.
        start_date: Optional start date filter.
        end_date: Optional end date filter.
        parameters: Strategy parameter overrides.
        weights: Weight scheme specification.

    Returns:
        PortfolioResult with per-symbol results, weights history, etc.
    """
    engine.signal_evaluator.clear_cache()

    # Prepare data
    aligned_data = {}
    for sym, df in data.items():
        prepared = prepare_data(df, start_date, end_date)
        if not prepared.empty:
            aligned_data[sym] = prepared

    if not aligned_data:
        raise ValueError("No overlapping data across symbols")

    # Setup weight scheme
    weight_scheme = get_weight_scheme(weights)

    # Setup rebalancer
    from pyutss.portfolio.rebalancer import RebalanceConfig, RebalanceFrequency, Rebalancer
    rebalancer = Rebalancer(RebalanceConfig(frequency=RebalanceFrequency.MONTHLY))

    # Get all dates
    all_dates = sorted(set(
        dt for df in aligned_data.values() for dt in df.index.tolist()
    ))
    if not all_dates:
        raise ValueError("No trading dates in data")

    pm = PortfolioManager(initial_capital=engine.initial_capital)

    # Pre-compute signals per symbol
    symbol_signals = {}
    for sym, df in aligned_data.items():
        ctx = build_context(strategy, df, parameters)
        rules = strategy.get("rules", [])
        rule_sigs = precompute_rules(engine.condition_evaluator, rules, ctx)
        symbol_signals[sym] = {"rules": rules, "signals": rule_sigs, "data": df}

    first_date = pd.Timestamp(all_dates[0])
    target_weights = weight_scheme.calculate(symbols, aligned_data, first_date)

    weights_history = []
    constraints = strategy.get("constraints", {})
    total_turnover = 0.0
    rebalance_count = 0

    for dt in all_dates:
        current_date = dt.date() if hasattr(dt, "date") else dt
        ts = pd.Timestamp(dt)

        prices = {}
        for sym, df in aligned_data.items():
            if ts in df.index:
                prices[sym] = df.loc[ts, "close"]

        if not prices:
            continue

        pm.update_positions(prices, current_date)

        # Check rebalancing
        current_weights = get_current_weights(pm, prices)
        if rebalancer.should_rebalance(current_date, current_weights, target_weights):
            target_weights = weight_scheme.calculate(symbols, aligned_data, ts)
            turnover = rebalance(engine.executor, pm, symbols, prices, target_weights)
            total_turnover += turnover
            rebalance_count += 1

        # Process signals
        for sym, sig_data in symbol_signals.items():
            if ts not in sig_data["data"].index:
                continue
            idx_pos = sig_data["data"].index.get_loc(ts)
            price = prices.get(sym)
            if price is None or price <= 0:
                continue

            for rule_idx, rule in enumerate(sig_data["rules"]):
                if not rule.get("enabled", True):
                    continue
                if sig_data["signals"][rule_idx].iloc[idx_pos]:
                    execute_rule(
                        engine.executor, rule, sym, price, current_date,
                        build_context(strategy, sig_data["data"], parameters),
                        constraints, pm, sig_data["data"],
                    )

        # Check exits
        pm.check_exits(prices, current_date, constraints, engine.commission_rate, engine.slippage_rate)
        pm.record_snapshot(current_date, prices)
        weights_history.append({"date": current_date, **current_weights})

    # Close remaining positions via executor
    final_prices = {}
    for sym, df in aligned_data.items():
        if len(df) > 0:
            final_prices[sym] = df.iloc[-1]["close"]

    final_date = all_dates[-1].date() if hasattr(all_dates[-1], "date") else all_dates[-1]
    for sym in list(pm.positions.keys()):
        if sym in final_prices:
            qty = pm.positions[sym].quantity
            order = OrderRequest(symbol=sym, direction="sell", quantity=qty, price=final_prices[sym])
            fill = engine.executor.execute(order)
            commission = fill.commission if fill else 0.0
            slippage_cost = fill.slippage if fill else 0.0
            pm.close_position(sym, final_prices[sym], final_date, "end_of_backtest", commission, slippage_cost)

    # Build per-symbol results
    per_symbol_results = {}
    for sym in symbols:
        sym_df = aligned_data.get(sym)
        if sym_df is None or sym_df.empty:
            continue

        sym_trades = [t for t in pm.trades if t.symbol == sym]
        initial_per = engine.initial_capital / len(symbols)

        equity = initial_per
        symbol_equity = []
        trade_pnl = {}
        for t in sym_trades:
            if not t.is_open and t.exit_date:
                trade_pnl[t.exit_date] = trade_pnl.get(t.exit_date, 0) + t.pnl

        for idx_dt in sym_df.index:
            d = idx_dt.date() if hasattr(idx_dt, "date") else idx_dt
            if d in trade_pnl:
                equity += trade_pnl[d]
            symbol_equity.append((idx_dt, equity))

        eq_series = pd.Series({d: eq for d, eq in symbol_equity}, name="equity")
        actual_start = sym_df.index[0].date() if hasattr(sym_df.index[0], "date") else sym_df.index[0]
        actual_end = sym_df.index[-1].date() if hasattr(sym_df.index[-1], "date") else sym_df.index[-1]

        per_symbol_results[sym] = BacktestResult(
            strategy_id=strategy.get("info", {}).get("id", "unknown"),
            symbol=sym,
            start_date=actual_start,
            end_date=actual_end,
            initial_capital=initial_per,
            final_equity=equity,
            trades=sym_trades,
            equity_curve=eq_series,
            parameters=parameters,
        )

    weights_df = pd.DataFrame(weights_history)
    if not weights_df.empty and "date" in weights_df.columns:
        weights_df = weights_df.set_index("date")

    avg_turnover = total_turnover / rebalance_count if rebalance_count > 0 else 0
    actual_start = all_dates[0].date() if hasattr(all_dates[0], "date") else all_dates[0]
    actual_end = all_dates[-1].date() if hasattr(all_dates[-1], "date") else all_dates[-1]

    return PortfolioResult(
        strategy_id=strategy.get("info", {}).get("id", "unknown"),
        symbols=symbols,
        start_date=actual_start,
        end_date=actual_end,
        initial_capital=engine.initial_capital,
        final_equity=pm.get_equity(final_prices),
        equity_curve=pm.build_equity_series(),
        portfolio_weights=weights_df,
        per_symbol_results=per_symbol_results,
        rebalance_count=rebalance_count,
        turnover=avg_turnover,
        parameters=parameters,
        weight_scheme=get_weight_scheme_name(weights),
        rebalance_frequency="monthly",
    )
