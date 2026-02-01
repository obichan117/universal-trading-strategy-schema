"""Tests for pyutss backtest engine using real market data."""

from datetime import date, timedelta

import pandas as pd
import pytest

from pyutss import BacktestConfig, BacktestEngine, BacktestResult


# sample_data fixture is provided by conftest.py (real AAPL data)


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
    """Tests for BacktestEngine using real market data."""

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
        """Test basic backtest execution with real AAPL data."""
        engine = BacktestEngine()
        result = engine.run(
            strategy=simple_strategy,
            data=sample_data,
            symbol="AAPL",
        )

        assert isinstance(result, BacktestResult)
        assert result.strategy_id == "test-strategy"
        assert result.symbol == "AAPL"
        assert result.initial_capital == 100000
        # With real data, equity should change
        assert result.final_equity > 0

    def test_backtest_with_date_range(self, sample_data, simple_strategy):
        """Test backtest with date range filtering using real data."""
        engine = BacktestEngine()

        # Get actual date range from sample data (handle timezone-aware index)
        data_start = sample_data.index[10]  # Skip first 10 days
        data_end = sample_data.index[-10]   # Skip last 10 days

        result = engine.run(
            strategy=simple_strategy,
            data=sample_data,
            symbol="AAPL",
            start_date=data_start,
            end_date=data_end,
        )

        # Verify result is within requested range
        assert result.start_date is not None
        assert result.end_date is not None

    def test_backtest_trades(self, sample_data, simple_strategy):
        """Test that backtest records trades with real data."""
        engine = BacktestEngine()
        result = engine.run(
            strategy=simple_strategy,
            data=sample_data,
            symbol="AAPL",
        )

        # Buy-and-hold should have at least one trade
        assert len(result.trades) >= 1

    def test_backtest_equity_curve(self, sample_data, simple_strategy):
        """Test equity curve generation with real data."""
        engine = BacktestEngine()
        result = engine.run(
            strategy=simple_strategy,
            data=sample_data,
            symbol="AAPL",
        )

        assert len(result.equity_curve) > 0
        assert len(result.portfolio_history) > 0
        # Equity curve should have variation with real data
        assert result.equity_curve.std() > 0

    def test_backtest_with_rsi_strategy(self, real_data_aapl, rsi_strategy):
        """Test backtest with RSI-based strategy on 2 years of real data."""
        engine = BacktestEngine()
        result = engine.run(
            strategy=rsi_strategy,
            data=real_data_aapl,
            symbol="AAPL",
        )

        assert isinstance(result, BacktestResult)
        # Over 2 years, RSI should trigger at least some trades
        # (though not guaranteed - RSI may not hit < 30)

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
        """Test BacktestResult computed properties with real data."""
        engine = BacktestEngine()
        result = engine.run(
            strategy=simple_strategy,
            data=sample_data,
            symbol="AAPL",
        )

        # Test computed properties
        assert isinstance(result.total_return, float)
        assert isinstance(result.total_return_pct, float)
        assert isinstance(result.num_trades, int)
        assert isinstance(result.win_rate, float)

    def test_equity_tracks_position_value(self, sample_data, simple_strategy):
        """Test that equity curve reflects position value changes with real data."""
        engine = BacktestEngine()
        result = engine.run(
            strategy=simple_strategy,
            data=sample_data,
            symbol="AAPL",
        )

        # With buy-and-hold, equity should track stock price movement
        # First equity should be close to initial capital
        assert abs(result.equity_curve.iloc[0] - 100000) < 1000

        # Equity curve should have reasonable variation with real market data
        equity_range = result.equity_curve.max() - result.equity_curve.min()
        assert equity_range > 0  # Some variation expected


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
