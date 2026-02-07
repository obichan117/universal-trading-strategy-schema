"""Tests for rule_executor module."""

from datetime import date

import pandas as pd
import pytest

from pyutss.engine.evaluator import ConditionEvaluator, EvaluationContext, SignalEvaluator
from pyutss.engine.executor import BacktestExecutor
from pyutss.engine.portfolio import PortfolioManager
from pyutss.engine.rule_executor import (
    build_context,
    execute_rule,
    execute_trade,
    precompute_rules,
)


def _make_ohlcv(n: int = 50, base_price: float = 100.0) -> pd.DataFrame:
    """Create synthetic OHLCV data for testing."""
    dates = pd.bdate_range("2024-01-01", periods=n, freq="B")
    close = [base_price + i * 0.5 for i in range(n)]
    return pd.DataFrame(
        {
            "open": [c - 0.5 for c in close],
            "high": [c + 1.0 for c in close],
            "low": [c - 1.0 for c in close],
            "close": close,
            "volume": [1_000_000] * n,
        },
        index=dates,
    )


@pytest.fixture
def data():
    return _make_ohlcv()


@pytest.fixture
def executor():
    return BacktestExecutor(commission_rate=0.001, slippage_rate=0.0005, lot_size=1)


@pytest.fixture
def pm():
    return PortfolioManager(initial_capital=100_000)


@pytest.fixture
def context(data):
    return EvaluationContext(
        primary_data=data,
        signal_library={},
        condition_library={},
        parameters={},
    )


# ── execute_rule: routing ──────────────────────────────────────


class TestExecuteRuleRouting:
    def test_trade_action(self, executor, pm, context, data):
        """Trade action routes to execute_trade."""
        rule = {
            "then": {
                "type": "trade",
                "direction": "buy",
                "sizing": {"type": "percent_of_equity", "percent": 10},
            }
        }
        execute_rule(
            executor, rule, "AAPL", 100.0, date(2024, 3, 1),
            context, {}, pm, data,
        )
        assert "AAPL" in pm.positions

    def test_alert_action(self, executor, pm, context, data):
        """Alert action logs but does not trade."""
        rule = {"then": {"type": "alert", "message": "Signal fired"}}
        execute_rule(
            executor, rule, "AAPL", 100.0, date(2024, 3, 1),
            context, {}, pm, data,
        )
        assert len(pm.positions) == 0

    def test_hold_action(self, executor, pm, context, data):
        """Hold action is a no-op."""
        rule = {"then": {"type": "hold"}}
        execute_rule(
            executor, rule, "AAPL", 100.0, date(2024, 3, 1),
            context, {}, pm, data,
        )
        assert len(pm.positions) == 0

    def test_default_is_trade(self, executor, pm, context, data):
        """Missing action type defaults to trade."""
        rule = {
            "then": {
                "direction": "buy",
                "sizing": {"type": "percent_of_equity", "percent": 10},
            }
        }
        execute_rule(
            executor, rule, "AAPL", 100.0, date(2024, 3, 1),
            context, {}, pm, data,
        )
        assert "AAPL" in pm.positions


# ── execute_trade: direction normalization ─────────────────────


class TestExecuteTradeDirection:
    def test_buy_opens_long(self, executor, pm, context, data):
        action = {"direction": "buy", "sizing": {"type": "percent_of_equity", "percent": 10}}
        execute_trade(executor, action, "AAPL", 100.0, date(2024, 3, 1), context, {}, pm, data)
        assert pm.positions["AAPL"].direction == "long"

    def test_long_opens_long(self, executor, pm, context, data):
        action = {"direction": "long", "sizing": {"type": "percent_of_equity", "percent": 10}}
        execute_trade(executor, action, "AAPL", 100.0, date(2024, 3, 1), context, {}, pm, data)
        assert pm.positions["AAPL"].direction == "long"

    def test_sell_closes_position(self, executor, pm, context, data):
        """sell/close direction closes existing position."""
        pm.open_position("AAPL", 10, 100.0, "long", date(2024, 2, 1))
        action = {"direction": "sell"}
        execute_trade(executor, action, "AAPL", 110.0, date(2024, 3, 1), context, {}, pm, data)
        assert "AAPL" not in pm.positions

    def test_close_closes_position(self, executor, pm, context, data):
        pm.open_position("AAPL", 10, 100.0, "long", date(2024, 2, 1))
        action = {"direction": "close"}
        execute_trade(executor, action, "AAPL", 110.0, date(2024, 3, 1), context, {}, pm, data)
        assert "AAPL" not in pm.positions

    def test_sell_noop_without_position(self, executor, pm, context, data):
        """Sell with no position is a no-op."""
        action = {"direction": "sell"}
        execute_trade(executor, action, "AAPL", 100.0, date(2024, 3, 1), context, {}, pm, data)
        assert len(pm.positions) == 0
        assert len(pm.trades) == 0

    def test_cover_closes_short(self, executor, pm, context, data):
        pm.open_position("AAPL", 10, 100.0, "short", date(2024, 2, 1))
        action = {"direction": "cover"}
        execute_trade(executor, action, "AAPL", 90.0, date(2024, 3, 1), context, {}, pm, data)
        assert "AAPL" not in pm.positions

    def test_cover_noop_on_long(self, executor, pm, context, data):
        """Cover on a long position is a no-op."""
        pm.open_position("AAPL", 10, 100.0, "long", date(2024, 2, 1))
        action = {"direction": "cover"}
        execute_trade(executor, action, "AAPL", 110.0, date(2024, 3, 1), context, {}, pm, data)
        assert "AAPL" in pm.positions  # Still open


# ── Constraint enforcement ─────────────────────────────────────


class TestConstraints:
    def test_max_positions_blocks_entry(self, executor, pm, context, data):
        """Cannot open more positions than max_positions."""
        pm.open_position("AAPL", 10, 100.0, "long", date(2024, 2, 1))
        constraints = {"max_positions": 1}
        action = {"direction": "buy", "sizing": {"type": "percent_of_equity", "percent": 10}}
        execute_trade(executor, action, "MSFT", 200.0, date(2024, 3, 1), context, constraints, pm, data)
        assert "MSFT" not in pm.positions

    def test_no_shorting_blocks_short(self, executor, pm, context, data):
        constraints = {"no_shorting": True}
        action = {"direction": "short", "sizing": {"type": "percent_of_equity", "percent": 10}}
        execute_trade(executor, action, "AAPL", 100.0, date(2024, 3, 1), context, constraints, pm, data)
        assert len(pm.positions) == 0

    def test_max_positions_allows_sell(self, executor, pm, context, data):
        """Sell is allowed even when max_positions is reached."""
        pm.open_position("AAPL", 10, 100.0, "long", date(2024, 2, 1))
        constraints = {"max_positions": 1}
        action = {"direction": "sell"}
        execute_trade(executor, action, "AAPL", 110.0, date(2024, 3, 1), context, constraints, pm, data)
        assert "AAPL" not in pm.positions


# ── precompute_rules ───────────────────────────────────────────


class TestPrecomputeRules:
    def test_always_condition(self, data):
        ctx = EvaluationContext(
            primary_data=data,
            signal_library={},
            condition_library={},
            parameters={},
        )
        evaluator = ConditionEvaluator(SignalEvaluator())
        rules = [{"when": {"type": "always"}}]
        signals = precompute_rules(evaluator, rules, ctx)
        assert len(signals) == 1
        assert signals[0].all()

    def test_failed_condition_returns_false_series(self, data):
        """Invalid condition degrades to all-False series."""
        ctx = EvaluationContext(
            primary_data=data,
            signal_library={},
            condition_library={},
            parameters={},
        )
        evaluator = ConditionEvaluator(SignalEvaluator())
        rules = [{"when": {"type": "comparison", "left": {"type": "invalid"}, "operator": "<", "right": {"type": "constant", "value": 30}}}]
        signals = precompute_rules(evaluator, rules, ctx)
        assert len(signals) == 1
        assert not signals[0].any()

    def test_multiple_rules(self, data):
        ctx = EvaluationContext(
            primary_data=data,
            signal_library={},
            condition_library={},
            parameters={},
        )
        evaluator = ConditionEvaluator(SignalEvaluator())
        rules = [
            {"when": {"type": "always"}},
            {"when": {"type": "always"}},
        ]
        signals = precompute_rules(evaluator, rules, ctx)
        assert len(signals) == 2


# ── build_context ──────────────────────────────────────────────


class TestBuildContext:
    def test_basic_context(self, data):
        strategy = {
            "signals": {"rsi_14": {"type": "indicator", "indicator": "RSI"}},
            "conditions": {},
        }
        ctx = build_context(strategy, data, None)
        assert ctx.primary_data is data
        assert "rsi_14" in ctx.signal_library

    def test_parameters_override(self, data):
        strategy = {
            "parameters": {"defaults": {"rsi_period": 14}},
        }
        ctx = build_context(strategy, data, {"rsi_period": 20})
        assert ctx.parameters["rsi_period"] == 20

    def test_default_parameters(self, data):
        strategy = {
            "parameters": {"defaults": {"rsi_period": 14}},
        }
        ctx = build_context(strategy, data, None)
        assert ctx.parameters["rsi_period"] == 14

    def test_empty_strategy(self, data):
        ctx = build_context({}, data, None)
        assert ctx.signal_library == {}
        assert ctx.condition_library == {}
        assert ctx.parameters == {}
