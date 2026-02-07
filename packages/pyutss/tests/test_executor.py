"""Tests for Executor interface and BacktestExecutor."""

import pytest

from pyutss.engine.executor import BacktestExecutor, Fill, OrderRequest


class TestOrderRequest:
    """Test OrderRequest dataclass."""

    def test_basic_order(self):
        order = OrderRequest(symbol="AAPL", direction="buy", quantity=100, price=150.0)
        assert order.symbol == "AAPL"
        assert order.direction == "buy"
        assert order.quantity == 100
        assert order.price == 150.0
        assert order.order_type == "market"


class TestFill:
    """Test Fill dataclass."""

    def test_total_cost(self):
        fill = Fill(
            symbol="AAPL", direction="buy", quantity=100,
            fill_price=150.075, commission=15.0, slippage=7.5,
        )
        assert fill.total_cost == 22.5


class TestBacktestExecutorBasic:
    """Test basic BacktestExecutor functionality."""

    def test_execute_buy(self):
        executor = BacktestExecutor(commission_rate=0.001, slippage_rate=0.0005)
        order = OrderRequest(symbol="AAPL", direction="buy", quantity=100, price=150.0)
        fill = executor.execute(order)
        assert fill is not None
        assert fill.symbol == "AAPL"
        assert fill.direction == "buy"
        assert fill.quantity == 100
        assert fill.fill_price > 150.0  # slippage makes buy price higher
        assert fill.commission > 0

    def test_execute_sell(self):
        executor = BacktestExecutor(commission_rate=0.001, slippage_rate=0.0005)
        order = OrderRequest(symbol="AAPL", direction="sell", quantity=100, price=150.0)
        fill = executor.execute(order)
        assert fill is not None
        assert fill.fill_price < 150.0  # slippage makes sell price lower

    def test_zero_quantity_returns_none(self):
        executor = BacktestExecutor()
        order = OrderRequest(symbol="AAPL", direction="buy", quantity=0, price=150.0)
        fill = executor.execute(order)
        assert fill is None

    def test_zero_commission_and_slippage(self):
        executor = BacktestExecutor(commission_rate=0.0, slippage_rate=0.0)
        order = OrderRequest(symbol="AAPL", direction="buy", quantity=50, price=100.0)
        fill = executor.execute(order)
        assert fill is not None
        assert fill.commission == 0.0
        assert fill.slippage == 0.0
        assert fill.fill_price == 100.0


class TestBacktestExecutorLotSize:
    """Test lot size rounding."""

    def test_lot_size_1(self):
        executor = BacktestExecutor(lot_size=1)
        order = OrderRequest(symbol="AAPL", direction="buy", quantity=15.7, price=150.0)
        fill = executor.execute(order)
        assert fill is not None
        assert fill.quantity == 15  # floor to int

    def test_lot_size_100_jp(self):
        executor = BacktestExecutor(lot_size=100)
        order = OrderRequest(symbol="7203.T", direction="buy", quantity=350, price=2500.0)
        fill = executor.execute(order)
        assert fill is not None
        assert fill.quantity == 300  # rounded down to 100-lot
        assert fill.quantity % 100 == 0

    def test_lot_size_100_small_quantity(self):
        executor = BacktestExecutor(lot_size=100)
        order = OrderRequest(symbol="7203.T", direction="buy", quantity=50, price=2500.0)
        fill = executor.execute(order)
        assert fill is None  # 50 < 100, rounds to 0

    def test_lot_size_100_exact(self):
        executor = BacktestExecutor(lot_size=100)
        order = OrderRequest(symbol="7203.T", direction="buy", quantity=200, price=2500.0)
        fill = executor.execute(order)
        assert fill is not None
        assert fill.quantity == 200


class TestBacktestExecutorSlippage:
    """Test slippage model."""

    def test_buy_slippage_increases_price(self):
        executor = BacktestExecutor(slippage_rate=0.01)  # 1%
        order = OrderRequest(symbol="AAPL", direction="buy", quantity=10, price=100.0)
        fill = executor.execute(order)
        assert fill is not None
        assert fill.fill_price == pytest.approx(101.0)

    def test_sell_slippage_decreases_price(self):
        executor = BacktestExecutor(slippage_rate=0.01)
        order = OrderRequest(symbol="AAPL", direction="sell", quantity=10, price=100.0)
        fill = executor.execute(order)
        assert fill is not None
        assert fill.fill_price == pytest.approx(99.0)

    def test_short_slippage_decreases_price(self):
        executor = BacktestExecutor(slippage_rate=0.01)
        order = OrderRequest(symbol="AAPL", direction="short", quantity=10, price=100.0)
        fill = executor.execute(order)
        assert fill is not None
        assert fill.fill_price == pytest.approx(99.0)

    def test_cover_slippage_increases_price(self):
        executor = BacktestExecutor(slippage_rate=0.01)
        order = OrderRequest(symbol="AAPL", direction="cover", quantity=10, price=100.0)
        fill = executor.execute(order)
        assert fill is not None
        assert fill.fill_price == pytest.approx(101.0)


class TestBacktestExecutorCommission:
    """Test commission calculation."""

    def test_flat_rate_commission(self):
        executor = BacktestExecutor(commission_rate=0.001, slippage_rate=0.0)
        order = OrderRequest(symbol="AAPL", direction="buy", quantity=100, price=100.0)
        fill = executor.execute(order)
        assert fill is not None
        # trade_value = 100 * 100 = 10000, commission = 10000 * 0.001 = 10
        assert fill.commission == pytest.approx(10.0)

    def test_tiered_commission_lowest(self):
        tiers = [
            {"up_to": 50000, "fee": 55},
            {"up_to": 100000, "fee": 99},
            {"up_to": 200000, "fee": 115},
            {"above": 200000, "fee": 275},
        ]
        executor = BacktestExecutor(tiered_commission=tiers, slippage_rate=0.0)
        order = OrderRequest(symbol="7203.T", direction="buy", quantity=100, price=200.0)
        fill = executor.execute(order)
        assert fill is not None
        # trade_value = 100 * 200 = 20000 <= 50000 → fee = 55
        assert fill.commission == 55

    def test_tiered_commission_mid(self):
        tiers = [
            {"up_to": 50000, "fee": 55},
            {"up_to": 100000, "fee": 99},
            {"above": 100000, "fee": 115},
        ]
        executor = BacktestExecutor(tiered_commission=tiers, slippage_rate=0.0)
        order = OrderRequest(symbol="7203.T", direction="buy", quantity=100, price=750.0)
        fill = executor.execute(order)
        assert fill is not None
        # trade_value = 100 * 750 = 75000 → up_to 100000 → fee = 99
        assert fill.commission == 99

    def test_tiered_commission_highest(self):
        tiers = [
            {"up_to": 50000, "fee": 55},
            {"up_to": 100000, "fee": 99},
            {"above": 100000, "fee": 115},
        ]
        executor = BacktestExecutor(tiered_commission=tiers, slippage_rate=0.0)
        order = OrderRequest(symbol="7203.T", direction="buy", quantity=100, price=1500.0)
        fill = executor.execute(order)
        assert fill is not None
        # trade_value = 100 * 1500 = 150000 > 100000 → fee = 115
        assert fill.commission == 115


class TestBacktestExecutorIntegration:
    """Test executor integration with engine patterns."""

    def test_engine_uses_executor(self):
        """Engine should respect custom executor settings."""
        from pyutss.engine.engine import Engine
        executor = BacktestExecutor(
            commission_rate=0.0, slippage_rate=0.0, lot_size=1,
        )
        engine = Engine(initial_capital=100000, executor=executor)
        assert engine.executor is executor

    def test_jp_market_executor(self):
        """Japanese market executor with lot size and tiered commission."""
        tiers = [
            {"up_to": 50000, "fee": 55},
            {"up_to": 100000, "fee": 99},
            {"up_to": 200000, "fee": 115},
            {"up_to": 500000, "fee": 275},
            {"up_to": 1000000, "fee": 535},
            {"up_to": 1500000, "fee": 640},
            {"up_to": 30000000, "fee": 1013},
            {"above": 30000000, "fee": 1070},
        ]
        executor = BacktestExecutor(
            lot_size=100,
            tiered_commission=tiers,
            slippage_rate=0.001,
        )

        # Small trade
        order = OrderRequest(symbol="7203.T", direction="buy", quantity=150, price=2500.0)
        fill = executor.execute(order)
        assert fill is not None
        assert fill.quantity == 100  # rounded to 100-lot
        # trade_value = 100 * fill_price ~= 250,250 → up_to 500000 → fee = 275
        assert fill.commission == 275

        # Large trade
        order = OrderRequest(symbol="7203.T", direction="buy", quantity=5000, price=2500.0)
        fill = executor.execute(order)
        assert fill is not None
        assert fill.quantity == 5000
        # trade_value ~= 12,512,500 → up_to 30,000,000 → fee = 1013
        assert fill.commission == 1013
