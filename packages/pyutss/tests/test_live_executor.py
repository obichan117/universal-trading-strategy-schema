"""Tests for PaperExecutor and LiveExecutor."""

from pyutss.engine.executor import OrderRequest
from pyutss.engine.live_executor import AccountInfo, PaperExecutor


class TestPaperExecutor:
    def test_basic_buy(self):
        """Paper buy should reduce cash and add position."""
        executor = PaperExecutor(initial_cash=100000, commission_rate=0.001, slippage_rate=0.0)
        order = OrderRequest(symbol="AAPL", direction="buy", quantity=10, price=150.0)
        fill = executor.execute(order)

        assert fill is not None
        assert fill.symbol == "AAPL"
        assert fill.quantity == 10
        assert fill.fill_price == 150.0
        assert fill.commission == 10 * 150.0 * 0.001

        assert executor.positions["AAPL"] == 10
        assert executor.cash < 100000

    def test_basic_sell(self):
        """Paper sell should increase cash and remove position."""
        executor = PaperExecutor(initial_cash=100000, commission_rate=0.0, slippage_rate=0.0)

        # Buy first
        executor.execute(OrderRequest("AAPL", "buy", 10, 150.0))
        assert executor.positions["AAPL"] == 10

        # Sell
        fill = executor.execute(OrderRequest("AAPL", "sell", 10, 160.0))
        assert fill is not None
        assert "AAPL" not in executor.positions  # Fully closed

    def test_insufficient_cash_rejected(self):
        """Buy exceeding cash should be rejected."""
        executor = PaperExecutor(initial_cash=1000, slippage_rate=0.0)
        order = OrderRequest("AAPL", "buy", 100, 150.0)  # $15,000 > $1,000
        fill = executor.execute(order)
        assert fill is None

    def test_slippage_applied(self):
        """Slippage should worsen fill price."""
        executor = PaperExecutor(
            initial_cash=100000, commission_rate=0.0, slippage_rate=0.01
        )
        order = OrderRequest("AAPL", "buy", 10, 100.0)
        fill = executor.execute(order)
        assert fill.fill_price == 101.0  # 100 * 1.01

        # Sell gets worse (lower) price
        sell_order = OrderRequest("AAPL", "sell", 10, 100.0)
        fill = executor.execute(sell_order)
        assert fill.fill_price == 99.0  # 100 * 0.99

    def test_zero_quantity_rejected(self):
        """Zero or negative quantity should return None."""
        executor = PaperExecutor()
        fill = executor.execute(OrderRequest("AAPL", "buy", 0, 100.0))
        assert fill is None

    def test_order_log_tracked(self):
        """All executions should be logged."""
        executor = PaperExecutor(initial_cash=100000, slippage_rate=0.0, commission_rate=0.0)
        executor.execute(OrderRequest("AAPL", "buy", 10, 150.0))
        executor.execute(OrderRequest("MSFT", "buy", 5, 300.0))
        assert len(executor.order_log) == 2
        assert len(executor.fills) == 2

    def test_get_account(self):
        """Account info should reflect current state."""
        executor = PaperExecutor(initial_cash=100000, slippage_rate=0.0, commission_rate=0.0)
        executor.execute(OrderRequest("AAPL", "buy", 10, 150.0))

        account = executor.get_account()
        assert isinstance(account, AccountInfo)
        assert account.cash == 100000 - 10 * 150.0
        assert account.positions["AAPL"] == 10

    def test_reset(self):
        """Reset should restore initial state."""
        executor = PaperExecutor(initial_cash=100000, slippage_rate=0.0, commission_rate=0.0)
        executor.execute(OrderRequest("AAPL", "buy", 10, 150.0))
        assert len(executor.fills) == 1

        executor.reset()
        assert executor.cash == 100000
        assert executor.positions == {}
        assert executor.fills == []
        assert executor.order_log == []

    def test_price_feed_callback(self):
        """Custom price feed should override order price."""
        def fake_feed(symbol):
            return {"AAPL": 155.0}.get(symbol)

        executor = PaperExecutor(
            initial_cash=100000,
            commission_rate=0.0,
            slippage_rate=0.0,
            price_feed=fake_feed,
        )
        fill = executor.execute(OrderRequest("AAPL", "buy", 10, 150.0))
        assert fill.fill_price == 155.0  # Uses feed price, not order price

    def test_multiple_buys_accumulate(self):
        """Multiple buys of same symbol should accumulate."""
        executor = PaperExecutor(initial_cash=100000, slippage_rate=0.0, commission_rate=0.0)
        executor.execute(OrderRequest("AAPL", "buy", 10, 150.0))
        executor.execute(OrderRequest("AAPL", "buy", 5, 160.0))
        assert executor.positions["AAPL"] == 15

    def test_partial_sell(self):
        """Selling less than held should reduce position."""
        executor = PaperExecutor(initial_cash=100000, slippage_rate=0.0, commission_rate=0.0)
        executor.execute(OrderRequest("AAPL", "buy", 10, 150.0))
        executor.execute(OrderRequest("AAPL", "sell", 5, 160.0))
        assert executor.positions["AAPL"] == 5

    def test_works_with_engine(self):
        """PaperExecutor should work as Engine executor."""
        from pyutss import Engine
        import numpy as np
        import pandas as pd

        executor = PaperExecutor(initial_cash=100000, slippage_rate=0.0, commission_rate=0.0)
        engine = Engine(initial_capital=100000, executor=executor)

        dates = pd.bdate_range("2024-01-01", periods=100)
        close = 100 + np.cumsum(np.random.default_rng(42).normal(0, 1, 100))
        data = pd.DataFrame(
            {
                "open": close,
                "high": close * 1.01,
                "low": close * 0.99,
                "close": close,
                "volume": np.ones(100) * 1000000,
            },
            index=dates,
        )

        strategy = {
            "info": {"id": "test", "name": "Test", "version": "1.0"},
            "universe": {"type": "static", "symbols": ["TEST"]},
            "rules": [
                {
                    "name": "buy",
                    "when": {
                        "type": "comparison",
                        "left": {"type": "indicator", "indicator": "RSI", "params": {"period": 14}},
                        "operator": "<",
                        "right": {"type": "constant", "value": 30},
                    },
                    "then": {
                        "type": "trade",
                        "direction": "buy",
                        "sizing": {"type": "percent_of_equity", "percent": 10},
                    },
                }
            ],
        }

        result = engine.backtest(strategy, data=data, symbol="TEST")
        assert result is not None
