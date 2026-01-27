"""Integration tests for running UTSS example strategies through pyutss.

These tests load the example YAML strategies and run them through the
backtesting engine to ensure end-to-end compatibility.
"""

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from pyutss import BacktestEngine, BacktestConfig, BacktestResult


# Path to examples directory
EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data for testing strategies."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=300, freq="D")

    # Create somewhat realistic price movement
    returns = np.random.randn(300) * 0.02  # 2% daily volatility
    prices = 100 * np.exp(np.cumsum(returns))

    close = pd.Series(prices, index=dates)
    high = close * (1 + np.abs(np.random.randn(300) * 0.01))
    low = close * (1 - np.abs(np.random.randn(300) * 0.01))
    open_ = close.shift(1).fillna(100)
    volume = pd.Series(np.random.randint(100000, 1000000, 300), index=dates)

    return pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


@pytest.fixture
def backtest_engine():
    """Create a configured backtest engine."""
    config = BacktestConfig(
        initial_capital=100000,
        commission_rate=0.001,
        slippage_rate=0.0005,
    )
    return BacktestEngine(config=config)


def load_strategy(filename: str) -> dict:
    """Load a strategy YAML file."""
    filepath = EXAMPLES_DIR / filename
    with open(filepath) as f:
        return yaml.safe_load(f)


class TestExampleStrategiesLoad:
    """Tests that all example strategies can be loaded."""

    def test_examples_directory_exists(self):
        """Examples directory should exist."""
        assert EXAMPLES_DIR.exists(), f"Examples directory not found: {EXAMPLES_DIR}"

    def test_rsi_reversal_loads(self):
        """RSI reversal strategy should load."""
        strategy = load_strategy("rsi-reversal.yaml")
        assert strategy is not None
        assert strategy["info"]["id"] == "rsi_reversal"

    def test_golden_cross_loads(self):
        """Golden cross strategy should load."""
        strategy = load_strategy("golden-cross.yaml")
        assert strategy is not None
        assert strategy["info"]["id"] == "golden_cross"

    def test_monday_friday_loads(self):
        """Monday-Friday strategy should load."""
        strategy = load_strategy("monday-friday.yaml")
        assert strategy is not None
        assert strategy["info"]["id"] == "weekly_momentum"

    def test_earnings_play_loads(self):
        """Earnings play strategy should load."""
        strategy = load_strategy("earnings-play.yaml")
        assert strategy is not None
        assert strategy["info"]["id"] == "earnings_play"


class TestRSIReversalStrategy:
    """Tests for the RSI reversal example strategy."""

    def test_strategy_structure(self):
        """Strategy should have required sections."""
        strategy = load_strategy("rsi-reversal.yaml")

        assert "info" in strategy
        assert "universe" in strategy
        assert "signals" in strategy
        assert "conditions" in strategy
        assert "rules" in strategy
        assert "constraints" in strategy

    def test_signals_defined(self):
        """Signals should be properly defined."""
        strategy = load_strategy("rsi-reversal.yaml")

        assert "rsi_14" in strategy["signals"]
        assert strategy["signals"]["rsi_14"]["type"] == "indicator"
        assert strategy["signals"]["rsi_14"]["indicator"] == "RSI"

    def test_conditions_defined(self):
        """Conditions should be properly defined."""
        strategy = load_strategy("rsi-reversal.yaml")

        assert "oversold" in strategy["conditions"]
        assert "overbought" in strategy["conditions"]
        assert strategy["conditions"]["oversold"]["type"] == "comparison"

    def test_backtest_runs(self, backtest_engine, sample_ohlcv_data):
        """Strategy should run through backtest engine."""
        strategy = load_strategy("rsi-reversal.yaml")

        # Simplify strategy for testing - use inline conditions instead of refs
        simplified_strategy = {
            "info": strategy["info"],
            "rules": [
                {
                    "when": {
                        "type": "comparison",
                        "left": {"type": "indicator", "indicator": "RSI", "params": {"period": 14}},
                        "operator": "<",
                        "right": {"type": "constant", "value": 30},
                    },
                    "then": {
                        "type": "trade",
                        "direction": "buy",
                        "sizing": {"type": "percent_of_equity", "value": 10},
                    },
                },
                {
                    "when": {
                        "type": "comparison",
                        "left": {"type": "indicator", "indicator": "RSI", "params": {"period": 14}},
                        "operator": ">",
                        "right": {"type": "constant", "value": 70},
                    },
                    "then": {
                        "type": "trade",
                        "direction": "sell",
                        "sizing": {"type": "percent_of_position", "value": 100},
                    },
                },
            ],
            "constraints": strategy.get("constraints", {}),
        }

        result = backtest_engine.run(
            strategy=simplified_strategy,
            data=sample_ohlcv_data,
            symbol="TEST",
        )

        assert isinstance(result, BacktestResult)
        assert result.strategy_id == "rsi_reversal"
        assert result.initial_capital == 100000


class TestGoldenCrossStrategy:
    """Tests for the golden cross example strategy."""

    def test_strategy_structure(self):
        """Strategy should have required sections."""
        strategy = load_strategy("golden-cross.yaml")

        assert "info" in strategy
        assert "signals" in strategy
        assert "rules" in strategy

    def test_sma_signals_defined(self):
        """SMA signals should be defined."""
        strategy = load_strategy("golden-cross.yaml")

        assert "sma_50" in strategy["signals"]
        assert "sma_200" in strategy["signals"]
        assert strategy["signals"]["sma_50"]["params"]["period"] == 50
        assert strategy["signals"]["sma_200"]["params"]["period"] == 200

    def test_cross_conditions(self):
        """Cross conditions should be in rules."""
        strategy = load_strategy("golden-cross.yaml")

        # Check that rules use cross conditions
        buy_rule = strategy["rules"][0]
        assert buy_rule["when"]["type"] == "cross"
        assert buy_rule["when"]["direction"] == "above"

    def test_backtest_runs(self, backtest_engine, sample_ohlcv_data):
        """Strategy should run through backtest engine."""
        # Simplified version for testing
        simplified_strategy = {
            "info": {"id": "golden_cross", "name": "Golden Cross"},
            "rules": [
                {
                    "when": {
                        "type": "cross",
                        "left": {"type": "indicator", "indicator": "SMA", "params": {"period": 50}},
                        "right": {"type": "indicator", "indicator": "SMA", "params": {"period": 200}},
                        "direction": "above",
                    },
                    "then": {
                        "type": "trade",
                        "direction": "buy",
                        "sizing": {"type": "percent_of_equity", "value": 10},
                    },
                },
            ],
            "constraints": {},
        }

        result = backtest_engine.run(
            strategy=simplified_strategy,
            data=sample_ohlcv_data,
            symbol="TEST",
        )

        assert isinstance(result, BacktestResult)


class TestMondayFridayStrategy:
    """Tests for the Monday-Friday calendar strategy."""

    def test_calendar_signal(self):
        """Calendar signal should be defined."""
        strategy = load_strategy("monday-friday.yaml")

        assert "day_of_week" in strategy["signals"]
        assert strategy["signals"]["day_of_week"]["type"] == "calendar"
        assert strategy["signals"]["day_of_week"]["field"] == "day_of_week"

    def test_backtest_runs(self, backtest_engine, sample_ohlcv_data):
        """Strategy should run through backtest engine."""
        simplified_strategy = {
            "info": {"id": "weekly_momentum", "name": "Weekly Momentum"},
            "rules": [
                {
                    "when": {
                        "type": "comparison",
                        "left": {"type": "calendar", "field": "day_of_week"},
                        "operator": "=",
                        "right": {"type": "constant", "value": 0},  # Monday = 0 in pandas
                    },
                    "then": {
                        "type": "trade",
                        "direction": "buy",
                        "sizing": {"type": "percent_of_equity", "value": 50},
                    },
                },
                {
                    "when": {
                        "type": "comparison",
                        "left": {"type": "calendar", "field": "day_of_week"},
                        "operator": "=",
                        "right": {"type": "constant", "value": 4},  # Friday = 4 in pandas
                    },
                    "then": {
                        "type": "trade",
                        "direction": "sell",
                        "sizing": {"type": "percent_of_position", "value": 100},
                    },
                },
            ],
            "constraints": {},
        }

        result = backtest_engine.run(
            strategy=simplified_strategy,
            data=sample_ohlcv_data,
            symbol="TEST",
        )

        assert isinstance(result, BacktestResult)
        # Calendar strategy should have trades (Mondays and Fridays)
        assert result.num_trades > 0


class TestEarningsPlayStrategy:
    """Tests for the earnings play event strategy."""

    def test_strategy_structure(self):
        """Strategy should have event-based signals."""
        strategy = load_strategy("earnings-play.yaml")

        # Check for event-based conditions in rules
        assert "rules" in strategy
        assert len(strategy["rules"]) >= 1

    def test_has_and_condition(self):
        """Strategy should use AND condition for multiple checks."""
        strategy = load_strategy("earnings-play.yaml")

        pre_earnings_rule = strategy["rules"][0]
        assert pre_earnings_rule["when"]["type"] == "and"

    # Note: Full earnings strategy test skipped because event signals
    # are not yet implemented in pyutss


class TestStrategyValidation:
    """Tests for strategy validation against UTSS schema."""

    def test_all_examples_have_info(self):
        """All example strategies should have info section."""
        for yaml_file in EXAMPLES_DIR.glob("*.yaml"):
            strategy = yaml.safe_load(yaml_file.read_text())
            assert "info" in strategy, f"{yaml_file.name} missing info section"
            assert "id" in strategy["info"], f"{yaml_file.name} missing info.id"

    def test_all_examples_have_rules(self):
        """All example strategies should have rules."""
        for yaml_file in EXAMPLES_DIR.glob("*.yaml"):
            strategy = yaml.safe_load(yaml_file.read_text())
            assert "rules" in strategy, f"{yaml_file.name} missing rules"
            assert len(strategy["rules"]) > 0, f"{yaml_file.name} has empty rules"


class TestBacktestResultsConsistency:
    """Tests for backtest result consistency."""

    def test_result_has_required_fields(self, backtest_engine, sample_ohlcv_data):
        """BacktestResult should have all required fields."""
        strategy = {
            "info": {"id": "test", "name": "Test"},
            "rules": [
                {
                    "when": {"type": "always"},
                    "then": {
                        "type": "trade",
                        "direction": "buy",
                        "sizing": {"type": "percent_of_equity", "value": 10},
                    },
                }
            ],
            "constraints": {},
        }

        result = backtest_engine.run(
            strategy=strategy,
            data=sample_ohlcv_data,
            symbol="TEST",
        )

        # Check required fields
        assert hasattr(result, "strategy_id")
        assert hasattr(result, "symbol")
        assert hasattr(result, "start_date")
        assert hasattr(result, "end_date")
        assert hasattr(result, "initial_capital")
        assert hasattr(result, "final_equity")
        assert hasattr(result, "trades")
        assert hasattr(result, "equity_curve")

    def test_equity_curve_matches_history(self, backtest_engine, sample_ohlcv_data):
        """Equity curve should match portfolio history."""
        strategy = {
            "info": {"id": "test", "name": "Test"},
            "rules": [
                {
                    "when": {"type": "always"},
                    "then": {
                        "type": "trade",
                        "direction": "buy",
                        "sizing": {"type": "percent_of_equity", "value": 10},
                    },
                }
            ],
            "constraints": {},
        }

        result = backtest_engine.run(
            strategy=strategy,
            data=sample_ohlcv_data,
            symbol="TEST",
        )

        # Equity curve and portfolio history should have same length
        assert len(result.equity_curve) == len(result.portfolio_history)
