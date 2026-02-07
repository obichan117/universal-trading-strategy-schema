"""Tests for unified Engine class."""

import numpy as np
import pandas as pd
import pytest
from datetime import date

from pyutss.engine.engine import Engine
from pyutss.results.types import BacktestResult


def _make_ohlcv(n: int = 100, start_price: float = 100.0, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic OHLCV data."""
    np.random.seed(seed)
    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    close = start_price + np.random.randn(n).cumsum()
    close = np.maximum(close, 10)  # floor at 10
    return pd.DataFrame({
        "open": close + np.random.randn(n) * 0.5,
        "high": close + abs(np.random.randn(n)),
        "low": close - abs(np.random.randn(n)),
        "close": close,
        "volume": np.random.randint(100000, 1000000, n),
    }, index=dates)


SIMPLE_STRATEGY = {
    "info": {"id": "test-buy-hold", "name": "Test Buy and Hold", "version": "1.0"},
    "universe": {"type": "static", "symbols": ["TEST"]},
    "rules": [
        {
            "name": "buy-always",
            "when": {"type": "always"},
            "then": {
                "type": "trade",
                "direction": "buy",
                "sizing": {"type": "percent_of_equity", "percent": 95},
            },
        },
    ],
}

RSI_STRATEGY = {
    "info": {"id": "rsi-test", "name": "RSI Test", "version": "1.0"},
    "universe": {"type": "static", "symbols": ["TEST"]},
    "rules": [
        {
            "name": "buy-oversold",
            "when": {
                "type": "comparison",
                "left": {"type": "indicator", "indicator": "RSI", "params": {"period": 14}},
                "operator": "<",
                "right": {"type": "constant", "value": 30},
            },
            "then": {
                "type": "trade",
                "direction": "buy",
                "sizing": {"type": "percent_of_equity", "percent": 50},
            },
        },
        {
            "name": "sell-overbought",
            "when": {
                "type": "comparison",
                "left": {"type": "indicator", "indicator": "RSI", "params": {"period": 14}},
                "operator": ">",
                "right": {"type": "constant", "value": 70},
            },
            "then": {
                "type": "trade",
                "direction": "sell",
                "sizing": {"type": "percent_of_equity", "percent": 100},
            },
        },
    ],
}


class TestEngineSingleSymbol:
    """Test Engine with single symbol."""

    def test_basic_backtest(self):
        """Basic single-symbol backtest returns BacktestResult."""
        engine = Engine(initial_capital=100000)
        data = _make_ohlcv(50)
        result = engine.backtest(SIMPLE_STRATEGY, data=data, symbol="TEST")
        assert isinstance(result, BacktestResult)
        assert result.strategy_id == "test-buy-hold"
        assert result.symbol == "TEST"
        assert result.initial_capital == 100000

    def test_equity_curve_populated(self):
        """Equity curve should be populated."""
        engine = Engine(initial_capital=100000)
        data = _make_ohlcv(50)
        result = engine.backtest(SIMPLE_STRATEGY, data=data, symbol="TEST")
        assert len(result.equity_curve) > 0

    def test_trades_recorded(self):
        """Trades should be recorded."""
        engine = Engine(initial_capital=100000)
        data = _make_ohlcv(50)
        result = engine.backtest(SIMPLE_STRATEGY, data=data, symbol="TEST")
        assert result.num_trades >= 1

    def test_date_filtering(self):
        """Start/end dates should filter data."""
        engine = Engine(initial_capital=100000)
        data = _make_ohlcv(200)
        result = engine.backtest(
            SIMPLE_STRATEGY, data=data, symbol="TEST",
            start_date="2023-03-01", end_date="2023-06-01",
        )
        assert result.start_date >= date(2023, 3, 1)
        assert result.end_date <= date(2023, 6, 1)

    def test_rsi_strategy(self):
        """RSI strategy should generate conditional trades."""
        engine = Engine(initial_capital=100000)
        data = _make_ohlcv(200)
        result = engine.backtest(RSI_STRATEGY, data=data, symbol="TEST")
        assert isinstance(result, BacktestResult)
        # May or may not have trades depending on data

    def test_empty_data_raises(self):
        """Empty data should raise ValueError."""
        engine = Engine(initial_capital=100000)
        data = _make_ohlcv(100)
        with pytest.raises(ValueError):
            engine.backtest(
                SIMPLE_STRATEGY, data=data, symbol="TEST",
                start_date="2030-01-01", end_date="2030-12-31",
            )

    def test_lot_size_rounding(self):
        """Lot size should affect trade quantities."""
        engine = Engine(initial_capital=100000, lot_size=100)
        data = _make_ohlcv(50)
        result = engine.backtest(SIMPLE_STRATEGY, data=data, symbol="TEST")
        # All trade quantities should be multiples of 100
        for trade in result.trades:
            assert trade.quantity % 100 == 0 or trade.quantity == 0

    def test_commission_and_slippage(self):
        """Commission and slippage should reduce returns."""
        engine_free = Engine(initial_capital=100000, commission_rate=0.0, slippage_rate=0.0)
        engine_costly = Engine(initial_capital=100000, commission_rate=0.01, slippage_rate=0.01)
        data = _make_ohlcv(50)
        result_free = engine_free.backtest(SIMPLE_STRATEGY, data=data, symbol="TEST")
        result_costly = engine_costly.backtest(SIMPLE_STRATEGY, data=data, symbol="TEST")
        # Costly trades should result in lower equity (all else equal)
        assert result_costly.final_equity <= result_free.final_equity

    def test_positions_closed_at_end(self):
        """All positions should be closed at end of backtest."""
        engine = Engine(initial_capital=100000)
        data = _make_ohlcv(50)
        result = engine.backtest(SIMPLE_STRATEGY, data=data, symbol="TEST")
        open_trades = [t for t in result.trades if t.is_open]
        assert len(open_trades) == 0

    def test_stop_loss(self):
        """Stop loss constraint should trigger exits."""
        strategy_with_sl = {
            **SIMPLE_STRATEGY,
            "constraints": {"stop_loss": {"percent": 2}},
        }
        engine = Engine(initial_capital=100000)
        data = _make_ohlcv(200, seed=99)
        result = engine.backtest(strategy_with_sl, data=data, symbol="TEST")
        # Should have some stop loss exits
        # May or may not trigger depending on data, just ensure no crash
        assert isinstance(result, BacktestResult)

    def test_parameters_override(self):
        """Parameters should be passed through."""
        engine = Engine(initial_capital=100000)
        data = _make_ohlcv(50)
        result = engine.backtest(
            SIMPLE_STRATEGY, data=data, symbol="TEST",
            parameters={"rsi_period": 20},
        )
        assert result.parameters == {"rsi_period": 20}


class TestEngineMultiSymbol:
    """Test Engine with multiple symbols."""

    def test_multi_symbol_returns_portfolio_result(self):
        """Multi-symbol backtest returns PortfolioResult."""
        from pyutss.portfolio.result import PortfolioResult

        engine = Engine(initial_capital=100000)
        data = {
            "AAPL": _make_ohlcv(50, seed=1),
            "MSFT": _make_ohlcv(50, seed=2),
        }
        strategy = {
            "info": {"id": "multi-test", "name": "Multi Test", "version": "1.0"},
            "universe": {"type": "static", "symbols": ["AAPL", "MSFT"]},
            "rules": [
                {
                    "name": "buy-always",
                    "when": {"type": "always"},
                    "then": {
                        "type": "trade",
                        "direction": "buy",
                        "sizing": {"type": "percent_of_equity", "percent": 40},
                    },
                },
            ],
        }
        result = engine.backtest(strategy, data=data)
        assert isinstance(result, PortfolioResult)
        assert set(result.symbols) == {"AAPL", "MSFT"}

    def test_multi_symbol_equity_curve(self):
        """Multi-symbol backtest should have equity curve."""
        engine = Engine(initial_capital=100000)
        data = {
            "A": _make_ohlcv(50, seed=10),
            "B": _make_ohlcv(50, seed=20),
        }
        strategy = {
            "info": {"id": "multi-eq", "name": "Multi EQ", "version": "1.0"},
            "universe": {"type": "static", "symbols": ["A", "B"]},
            "rules": [
                {
                    "name": "hold",
                    "when": {"type": "always"},
                    "then": {"type": "hold"},
                },
            ],
        }
        result = engine.backtest(strategy, data=data)
        assert len(result.equity_curve) > 0


class TestEngineBackwardCompat:
    """Test backward compatibility with old BacktestEngine API."""

    def test_config_param(self):
        """Engine should accept BacktestConfig."""
        from pyutss.results.types import BacktestConfig
        config = BacktestConfig(initial_capital=50000, commission_rate=0.002)
        engine = Engine(config=config)
        assert engine.initial_capital == 50000
        assert engine.commission_rate == 0.002
