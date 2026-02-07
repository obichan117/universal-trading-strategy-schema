"""Tests for weight_manager module."""

from datetime import date

import pytest

from pyutss.engine.executor import BacktestExecutor
from pyutss.engine.portfolio import PortfolioManager
from pyutss.engine.weight_manager import (
    get_current_weights,
    get_weight_scheme,
    get_weight_scheme_name,
    rebalance,
)
from pyutss.portfolio.weights import EqualWeight, WeightScheme


@pytest.fixture
def executor():
    return BacktestExecutor(commission_rate=0.0, slippage_rate=0.0, lot_size=1)


@pytest.fixture
def pm():
    return PortfolioManager(initial_capital=100_000)


# ── get_weight_scheme ──────────────────────────────────────────


class TestGetWeightScheme:
    def test_string_equal(self):
        scheme = get_weight_scheme("equal")
        assert isinstance(scheme, EqualWeight)

    def test_string_inverse_vol(self):
        scheme = get_weight_scheme("inverse_vol")
        assert isinstance(scheme, WeightScheme)

    def test_string_risk_parity(self):
        scheme = get_weight_scheme("risk_parity")
        assert isinstance(scheme, WeightScheme)

    def test_string_unknown_defaults_to_equal(self):
        scheme = get_weight_scheme("unknown_scheme")
        assert isinstance(scheme, EqualWeight)

    def test_dict_target_weights(self):
        weights = {"AAPL": 0.6, "MSFT": 0.4}
        scheme = get_weight_scheme(weights)
        assert isinstance(scheme, WeightScheme)

    def test_weight_scheme_object_passthrough(self):
        eq = EqualWeight()
        scheme = get_weight_scheme(eq)
        assert scheme is eq


class TestGetWeightSchemeName:
    def test_string(self):
        assert get_weight_scheme_name("equal") == "equal"

    def test_dict(self):
        assert get_weight_scheme_name({"AAPL": 0.5}) == "custom"

    def test_object(self):
        assert get_weight_scheme_name(EqualWeight()) == "EqualWeight"


# ── get_current_weights ────────────────────────────────────────


class TestGetCurrentWeights:
    def test_empty_portfolio(self, pm):
        weights = get_current_weights(pm, {})
        assert weights == {}

    def test_single_position(self, pm):
        pm.open_position("AAPL", 100, 100.0, "long", date(2024, 1, 1))
        prices = {"AAPL": 100.0}
        weights = get_current_weights(pm, prices)
        assert "AAPL" in weights
        assert 0 < weights["AAPL"] <= 1.0

    def test_two_positions_sum_less_than_one(self, pm):
        """Position weights should sum to less than 1 since there's cash."""
        pm.open_position("AAPL", 100, 100.0, "long", date(2024, 1, 1))
        pm.open_position("MSFT", 50, 200.0, "long", date(2024, 1, 1))
        prices = {"AAPL": 100.0, "MSFT": 200.0}
        weights = get_current_weights(pm, prices)
        assert len(weights) == 2
        total = sum(weights.values())
        assert total < 1.0  # There's remaining cash

    def test_zero_equity_returns_empty(self):
        """Zero equity returns empty weights."""
        pm = PortfolioManager(initial_capital=0)
        pm.cash = 0
        weights = get_current_weights(pm, {})
        assert weights == {}

    def test_uses_avg_price_when_market_price_missing(self, pm):
        pm.open_position("AAPL", 100, 100.0, "long", date(2024, 1, 1))
        # No market price → falls back to avg_price
        weights = get_current_weights(pm, {})
        assert "AAPL" in weights


# ── rebalance ──────────────────────────────────────────────────


class TestRebalance:
    def test_buy_into_empty_portfolio(self, executor, pm):
        """Rebalance into empty portfolio creates positions."""
        prices = {"AAPL": 100.0, "MSFT": 200.0}
        targets = {"AAPL": 0.5, "MSFT": 0.5}
        turnover = rebalance(executor, pm, ["AAPL", "MSFT"], prices, targets)
        assert turnover > 0
        assert "AAPL" in pm.positions
        assert "MSFT" in pm.positions

    def test_rebalance_returns_turnover(self, executor, pm):
        prices = {"AAPL": 100.0}
        targets = {"AAPL": 0.5}
        turnover = rebalance(executor, pm, ["AAPL"], prices, targets)
        assert isinstance(turnover, float)
        assert turnover > 0

    def test_sell_overweight_position(self, executor, pm):
        """Rebalance sells overweight positions."""
        pm.open_position("AAPL", 500, 100.0, "long", date(2024, 1, 1))
        prices = {"AAPL": 100.0}
        # Target only 10% but currently ~50%
        targets = {"AAPL": 0.1}
        turnover = rebalance(executor, pm, ["AAPL"], prices, targets)
        assert turnover > 0
        # Should have reduced position
        if "AAPL" in pm.positions:
            assert pm.positions["AAPL"].quantity < 500

    def test_tiny_adjustment_skipped(self, executor, pm):
        """Adjustments < 0.01 shares are skipped."""
        pm.open_position("AAPL", 100, 100.0, "long", date(2024, 1, 1))
        prices = {"AAPL": 100.0}
        equity = pm.get_equity(prices)
        # Set target to exactly the current weight
        current_value = 100 * 100.0
        targets = {"AAPL": current_value / equity}
        turnover = rebalance(executor, pm, ["AAPL"], prices, targets)
        assert turnover == 0.0

    def test_zero_price_skipped(self, executor, pm):
        """Symbols with zero price are skipped."""
        prices = {"AAPL": 0.0}
        targets = {"AAPL": 0.5}
        turnover = rebalance(executor, pm, ["AAPL"], prices, targets)
        assert turnover == 0.0
        assert "AAPL" not in pm.positions

    def test_missing_target_weight_defaults_to_zero(self, executor, pm):
        """Symbol not in targets gets target weight 0."""
        pm.open_position("AAPL", 100, 100.0, "long", date(2024, 1, 1))
        prices = {"AAPL": 100.0}
        # Empty targets → should sell everything
        targets = {}
        turnover = rebalance(executor, pm, ["AAPL"], prices, targets)
        assert turnover > 0
