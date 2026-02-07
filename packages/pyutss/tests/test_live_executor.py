"""Tests for PaperExecutor, AlpacaExecutor, and LiveExecutor protocol."""

from unittest.mock import MagicMock, patch

import pytest

from pyutss.engine.executor import OrderRequest
from pyutss.engine.live_executor import AccountInfo, AlpacaExecutor, LiveExecutor, PaperExecutor


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


class TestLiveExecutorProtocol:
    """Tests for LiveExecutor protocol conformance."""

    def test_paper_executor_has_execute_method(self):
        """PaperExecutor should have execute method matching Executor protocol."""
        executor = PaperExecutor()
        assert hasattr(executor, "execute")
        assert callable(executor.execute)

    def test_alpaca_executor_satisfies_live_protocol(self):
        """AlpacaExecutor should satisfy LiveExecutor protocol."""
        executor = AlpacaExecutor(api_key="test", secret_key="test")
        assert isinstance(executor, LiveExecutor)


class TestAlpacaExecutor:
    """Tests for AlpacaExecutor with mocked Alpaca API."""

    def test_init_stores_config(self):
        """Should store API keys and paper flag."""
        executor = AlpacaExecutor(api_key="pk", secret_key="sk", paper=False)
        assert executor.api_key == "pk"
        assert executor.secret_key == "sk"
        assert executor.paper is False
        assert executor._client is None

    def test_lazy_client_creation(self):
        """Client should not be created until first use."""
        executor = AlpacaExecutor(api_key="pk", secret_key="sk")
        assert executor._client is None

    @patch("pyutss.engine.live_executor.AlpacaExecutor._get_client")
    def test_execute_buy(self, mock_get_client):
        """Should submit buy order and return fill."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.id = "order-123"
        mock_result.filled_avg_price = "151.50"
        mock_result.filled_qty = "10"
        mock_client.submit_order.return_value = mock_result
        mock_get_client.return_value = mock_client

        executor = AlpacaExecutor(api_key="pk", secret_key="sk")

        with patch.dict("sys.modules", {
            "alpaca": MagicMock(),
            "alpaca.trading": MagicMock(),
            "alpaca.trading.requests": MagicMock(),
            "alpaca.trading.enums": MagicMock(),
        }):
            # Patch the imports inside execute()
            mock_order_side = MagicMock()
            mock_order_side.BUY = "buy"
            mock_order_side.SELL = "sell"
            mock_time_in_force = MagicMock()
            mock_time_in_force.DAY = "day"
            mock_market_order = MagicMock()

            with patch("alpaca.trading.enums.OrderSide", mock_order_side), \
                 patch("alpaca.trading.enums.TimeInForce", mock_time_in_force), \
                 patch("alpaca.trading.requests.MarketOrderRequest", mock_market_order):
                order = OrderRequest(symbol="AAPL", direction="buy", quantity=10, price=150.0)
                fill = executor.execute(order)

        assert fill is not None
        assert fill.symbol == "AAPL"
        assert fill.direction == "buy"
        assert fill.quantity == 10.0
        assert fill.fill_price == 151.50
        assert fill.commission == 0.0

    @patch("pyutss.engine.live_executor.AlpacaExecutor._get_client")
    def test_execute_sell(self, mock_get_client):
        """Should submit sell order."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.id = "order-456"
        mock_result.filled_avg_price = "155.00"
        mock_result.filled_qty = "5"
        mock_client.submit_order.return_value = mock_result
        mock_get_client.return_value = mock_client

        executor = AlpacaExecutor(api_key="pk", secret_key="sk")

        with patch.dict("sys.modules", {
            "alpaca": MagicMock(),
            "alpaca.trading": MagicMock(),
            "alpaca.trading.requests": MagicMock(),
            "alpaca.trading.enums": MagicMock(),
        }):
            mock_order_side = MagicMock()
            mock_order_side.BUY = "buy"
            mock_order_side.SELL = "sell"
            mock_time_in_force = MagicMock()
            mock_time_in_force.DAY = "day"
            mock_market_order = MagicMock()

            with patch("alpaca.trading.enums.OrderSide", mock_order_side), \
                 patch("alpaca.trading.enums.TimeInForce", mock_time_in_force), \
                 patch("alpaca.trading.requests.MarketOrderRequest", mock_market_order):
                order = OrderRequest(symbol="AAPL", direction="sell", quantity=5, price=155.0)
                fill = executor.execute(order)

        assert fill is not None
        assert fill.direction == "sell"
        assert fill.quantity == 5.0

    def test_execute_zero_quantity_rejected(self):
        """Zero quantity should return None without calling API."""
        executor = AlpacaExecutor(api_key="pk", secret_key="sk")

        with patch.dict("sys.modules", {
            "alpaca": MagicMock(),
            "alpaca.trading": MagicMock(),
            "alpaca.trading.requests": MagicMock(),
            "alpaca.trading.enums": MagicMock(),
        }):
            mock_order_side = MagicMock()
            mock_order_side.BUY = "buy"
            mock_time_in_force = MagicMock()
            mock_time_in_force.DAY = "day"

            with patch("alpaca.trading.enums.OrderSide", mock_order_side), \
                 patch("alpaca.trading.enums.TimeInForce", mock_time_in_force), \
                 patch("alpaca.trading.requests.MarketOrderRequest", MagicMock()):
                order = OrderRequest(symbol="AAPL", direction="buy", quantity=0, price=150.0)
                fill = executor.execute(order)

        assert fill is None

    @patch("pyutss.engine.live_executor.AlpacaExecutor._get_client")
    def test_execute_api_failure_returns_none(self, mock_get_client):
        """API failure should return None, not raise."""
        mock_client = MagicMock()
        mock_client.submit_order.side_effect = Exception("API error")
        mock_get_client.return_value = mock_client

        executor = AlpacaExecutor(api_key="pk", secret_key="sk")

        with patch.dict("sys.modules", {
            "alpaca": MagicMock(),
            "alpaca.trading": MagicMock(),
            "alpaca.trading.requests": MagicMock(),
            "alpaca.trading.enums": MagicMock(),
        }):
            mock_order_side = MagicMock()
            mock_order_side.BUY = "buy"
            mock_time_in_force = MagicMock()
            mock_time_in_force.DAY = "day"

            with patch("alpaca.trading.enums.OrderSide", mock_order_side), \
                 patch("alpaca.trading.enums.TimeInForce", mock_time_in_force), \
                 patch("alpaca.trading.requests.MarketOrderRequest", MagicMock()):
                order = OrderRequest(symbol="AAPL", direction="buy", quantity=10, price=150.0)
                fill = executor.execute(order)

        assert fill is None

    @patch("pyutss.engine.live_executor.AlpacaExecutor._get_client")
    def test_execute_no_fill_price_uses_order_price(self, mock_get_client):
        """When filled_avg_price is None, should use order price."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.id = "order-789"
        mock_result.filled_avg_price = None
        mock_result.filled_qty = "10"
        mock_client.submit_order.return_value = mock_result
        mock_get_client.return_value = mock_client

        executor = AlpacaExecutor(api_key="pk", secret_key="sk")

        with patch.dict("sys.modules", {
            "alpaca": MagicMock(),
            "alpaca.trading": MagicMock(),
            "alpaca.trading.requests": MagicMock(),
            "alpaca.trading.enums": MagicMock(),
        }):
            mock_order_side = MagicMock()
            mock_order_side.BUY = "buy"
            mock_time_in_force = MagicMock()
            mock_time_in_force.DAY = "day"

            with patch("alpaca.trading.enums.OrderSide", mock_order_side), \
                 patch("alpaca.trading.enums.TimeInForce", mock_time_in_force), \
                 patch("alpaca.trading.requests.MarketOrderRequest", MagicMock()):
                order = OrderRequest(symbol="AAPL", direction="buy", quantity=10, price=150.0)
                fill = executor.execute(order)

        assert fill is not None
        assert fill.fill_price == 150.0

    @patch("pyutss.engine.live_executor.AlpacaExecutor._get_client")
    def test_get_account(self, mock_get_client):
        """Should return AccountInfo from Alpaca API."""
        mock_client = MagicMock()
        mock_account = MagicMock()
        mock_account.cash = "50000.00"
        mock_account.equity = "75000.00"
        mock_account.buying_power = "100000.00"
        mock_client.get_account.return_value = mock_account

        mock_pos = MagicMock()
        mock_pos.symbol = "AAPL"
        mock_pos.qty = "10"
        mock_client.get_all_positions.return_value = [mock_pos]
        mock_get_client.return_value = mock_client

        executor = AlpacaExecutor(api_key="pk", secret_key="sk")
        account = executor.get_account()

        assert isinstance(account, AccountInfo)
        assert account.cash == 50000.0
        assert account.equity == 75000.0
        assert account.buying_power == 100000.0
        assert account.positions == {"AAPL": 10.0}

    @patch("pyutss.engine.live_executor.AlpacaExecutor._get_client")
    def test_cancel_all(self, mock_get_client):
        """Should cancel all orders and return count."""
        mock_client = MagicMock()
        mock_client.cancel_orders.return_value = [MagicMock(), MagicMock()]
        mock_get_client.return_value = mock_client

        executor = AlpacaExecutor(api_key="pk", secret_key="sk")
        count = executor.cancel_all()

        assert count == 2
        mock_client.cancel_orders.assert_called_once()

    def test_get_client_import_error(self):
        """Should raise ImportError with helpful message when alpaca-py missing."""
        executor = AlpacaExecutor(api_key="pk", secret_key="sk")

        with patch.dict("sys.modules", {"alpaca": None, "alpaca.trading": None, "alpaca.trading.client": None}):
            with pytest.raises(ImportError, match="alpaca-py"):
                executor._get_client()
