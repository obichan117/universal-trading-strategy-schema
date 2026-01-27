"""Tests for pyutss backtest engine."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from pyutss import BacktestConfig, BacktestEngine, BacktestResult


@pytest.fixture
def sample_data():
    """Create sample OHLCV data with trend."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    # Create an upward trend
    close = pd.Series(100 + np.arange(100) * 0.5 + np.random.randn(100) * 2, index=dates)
    return pd.DataFrame({
        "open": close.shift(1).fillna(100),
        "high": close + np.abs(np.random.randn(100) * 2),
        "low": close - np.abs(np.random.randn(100) * 2),
        "close": close,
        "volume": np.random.randint(1000, 10000, 100),
    })


@pytest.fixture
def simple_strategy():
    """Create a simple buy-and-hold strategy."""
    return {
        "info": {"id": "test-strategy", "name": "Test Strategy"},
        "rules": [
            {
                "when": {"type": "always"},
                "then": {
                    "type": "trade",
                    "direction": "buy",
                    "sizing": {"type": "percent_of_equity", "value": 100},
                },
            }
        ],
        "constraints": {},
    }


@pytest.fixture
def rsi_strategy():
    """Create an RSI-based strategy."""
    return {
        "info": {"id": "rsi-strategy", "name": "RSI Strategy"},
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
                    "sizing": {"type": "percent_of_equity", "value": 50},
                },
            }
        ],
        "constraints": {
            "stop_loss": {"percentage": 5},
            "take_profit": {"percentage": 10},
        },
    }


class TestBacktestEngine:
    """Tests for BacktestEngine."""

    def test_engine_initialization(self):
        """Test engine initializes with default config."""
        engine = BacktestEngine()
        assert engine.config.initial_capital == 100000

    def test_engine_custom_config(self):
        """Test engine with custom config."""
        config = BacktestConfig(initial_capital=50000, commission_rate=0.002)
        engine = BacktestEngine(config=config)
        assert engine.config.initial_capital == 50000
        assert engine.config.commission_rate == 0.002

    def test_simple_backtest(self, sample_data, simple_strategy):
        """Test basic backtest execution."""
        engine = BacktestEngine()
        result = engine.run(
            strategy=simple_strategy,
            data=sample_data,
            symbol="TEST",
        )

        assert isinstance(result, BacktestResult)
        assert result.strategy_id == "test-strategy"
        assert result.symbol == "TEST"
        assert result.initial_capital == 100000

    def test_backtest_with_date_range(self, sample_data, simple_strategy):
        """Test backtest with date range filtering."""
        engine = BacktestEngine()
        result = engine.run(
            strategy=simple_strategy,
            data=sample_data,
            symbol="TEST",
            start_date=date(2024, 1, 15),
            end_date=date(2024, 3, 15),
        )

        assert result.start_date >= date(2024, 1, 15)
        assert result.end_date <= date(2024, 3, 15)

    def test_backtest_trades(self, sample_data, simple_strategy):
        """Test that backtest records trades."""
        engine = BacktestEngine()
        result = engine.run(
            strategy=simple_strategy,
            data=sample_data,
            symbol="TEST",
        )

        # Should have at least one trade
        assert len(result.trades) >= 1

    def test_backtest_equity_curve(self, sample_data, simple_strategy):
        """Test equity curve generation."""
        engine = BacktestEngine()
        result = engine.run(
            strategy=simple_strategy,
            data=sample_data,
            symbol="TEST",
        )

        assert len(result.equity_curve) > 0
        assert len(result.portfolio_history) > 0

    def test_backtest_with_rsi_strategy(self, sample_data, rsi_strategy):
        """Test backtest with RSI-based strategy."""
        engine = BacktestEngine()
        result = engine.run(
            strategy=rsi_strategy,
            data=sample_data,
            symbol="TEST",
        )

        assert isinstance(result, BacktestResult)
        # RSI strategy may or may not trigger trades depending on data

    def test_empty_data_raises_error(self, simple_strategy):
        """Test that empty data raises ValueError."""
        engine = BacktestEngine()
        empty_data = pd.DataFrame()

        with pytest.raises(ValueError):
            engine.run(
                strategy=simple_strategy,
                data=empty_data,
                symbol="TEST",
            )

    def test_backtest_result_properties(self, sample_data, simple_strategy):
        """Test BacktestResult computed properties."""
        engine = BacktestEngine()
        result = engine.run(
            strategy=simple_strategy,
            data=sample_data,
            symbol="TEST",
        )

        # Test computed properties
        assert isinstance(result.total_return, float)
        assert isinstance(result.total_return_pct, float)
        assert isinstance(result.num_trades, int)
        assert isinstance(result.win_rate, float)


class TestBacktestConfig:
    """Tests for BacktestConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = BacktestConfig()
        assert config.initial_capital == 100000
        assert config.commission_rate == 0.001
        assert config.slippage_rate == 0.0005

    def test_custom_config(self):
        """Test custom configuration."""
        config = BacktestConfig(
            initial_capital=50000,
            commission_rate=0.002,
            slippage_rate=0.001,
        )
        assert config.initial_capital == 50000
        assert config.commission_rate == 0.002
        assert config.slippage_rate == 0.001
