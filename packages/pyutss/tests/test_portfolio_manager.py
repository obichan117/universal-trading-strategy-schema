"""Tests for PortfolioManager."""

from datetime import date

from pyutss.engine.portfolio import PortfolioManager


class TestPortfolioManagerBasic:
    """Test basic PortfolioManager operations."""

    def test_init_defaults(self):
        """Test default initialization."""
        pm = PortfolioManager()
        assert pm.initial_capital == 100000.0
        assert pm.cash == 100000.0
        assert pm.peak_equity == 100000.0
        assert pm.positions == {}
        assert pm.trades == []

    def test_init_custom_capital(self):
        """Test custom initial capital."""
        pm = PortfolioManager(initial_capital=50000)
        assert pm.cash == 50000
        assert pm.peak_equity == 50000

    def test_reset(self):
        """Test reset clears all state."""
        pm = PortfolioManager(initial_capital=100000)
        pm.open_position("AAPL", 10, 150.0, "long", date(2024, 1, 1))
        pm.reset()
        assert pm.cash == 100000
        assert pm.positions == {}
        assert pm.trades == []


class TestPortfolioManagerEquity:
    """Test equity calculation."""

    def test_equity_cash_only(self):
        """Equity with no positions equals cash."""
        pm = PortfolioManager(initial_capital=100000)
        assert pm.get_equity() == 100000

    def test_equity_with_position(self):
        """Equity includes position value."""
        pm = PortfolioManager(initial_capital=100000)
        pm.open_position("AAPL", 10, 150.0, "long", date(2024, 1, 1))
        # Cash reduced by cost, position value at avg_price
        equity = pm.get_equity({"AAPL": 160.0})
        # Cash = 100000 - (10 * 150) = 98500
        # Position value at 160 = 10 * 160 = 1600
        assert equity == pm.cash + 10 * 160.0

    def test_positions_value(self):
        """Test positions value calculation."""
        pm = PortfolioManager(initial_capital=100000)
        pm.open_position("AAPL", 10, 150.0, "long", date(2024, 1, 1))
        pv = pm.get_positions_value({"AAPL": 160.0})
        assert pv == 10 * 160.0


class TestPortfolioManagerOpenPosition:
    """Test opening positions."""

    def test_open_long(self):
        """Open a long position."""
        pm = PortfolioManager(initial_capital=100000)
        trade = pm.open_position("AAPL", 10, 150.0, "long", date(2024, 1, 1))
        assert trade is not None
        assert trade.direction == "long"
        assert trade.quantity == 10
        assert pm.cash == 100000 - 10 * 150
        assert "AAPL" in pm.positions
        assert pm.positions["AAPL"].quantity == 10

    def test_open_long_with_commission(self):
        """Open long with commission/slippage."""
        pm = PortfolioManager(initial_capital=100000)
        trade = pm.open_position(
            "AAPL", 10, 150.0, "long", date(2024, 1, 1),
            commission=15.0, slippage=7.5,
        )
        assert trade is not None
        assert pm.cash == 100000 - (10 * 150 + 15.0 + 7.5)

    def test_open_short(self):
        """Open a short position."""
        pm = PortfolioManager(initial_capital=100000)
        trade = pm.open_position("AAPL", 10, 150.0, "short", date(2024, 1, 1))
        assert trade is not None
        assert trade.direction == "short"
        assert "AAPL" in pm.positions
        assert pm.positions["AAPL"].direction == "short"

    def test_open_duplicate_rejected(self):
        """Cannot open position in same symbol twice."""
        pm = PortfolioManager(initial_capital=100000)
        pm.open_position("AAPL", 10, 150.0, "long", date(2024, 1, 1))
        trade2 = pm.open_position("AAPL", 5, 155.0, "long", date(2024, 1, 2))
        assert trade2 is None
        assert pm.positions["AAPL"].quantity == 10

    def test_open_zero_quantity_rejected(self):
        """Zero quantity is rejected."""
        pm = PortfolioManager(initial_capital=100000)
        trade = pm.open_position("AAPL", 0, 150.0, "long", date(2024, 1, 1))
        assert trade is None

    def test_open_adjusts_to_available_cash(self):
        """If not enough cash, quantity is reduced."""
        pm = PortfolioManager(initial_capital=1000)
        trade = pm.open_position("AAPL", 100, 150.0, "long", date(2024, 1, 1))
        assert trade is not None
        assert trade.quantity < 100  # Reduced to fit cash
        assert pm.cash >= 0


class TestPortfolioManagerClosePosition:
    """Test closing positions."""

    def test_close_long(self):
        """Close a long position at profit."""
        pm = PortfolioManager(initial_capital=100000)
        pm.open_position("AAPL", 10, 150.0, "long", date(2024, 1, 1))
        cash_before = pm.cash

        trade = pm.close_position("AAPL", 160.0, date(2024, 2, 1), "take_profit")
        assert trade is not None
        assert not trade.is_open
        assert trade.exit_price == 160.0
        assert "AAPL" not in pm.positions
        # Cash should increase by sale proceeds
        assert pm.cash > cash_before

    def test_close_long_at_loss(self):
        """Close a long position at loss."""
        pm = PortfolioManager(initial_capital=100000)
        pm.open_position("AAPL", 10, 150.0, "long", date(2024, 1, 1))
        trade = pm.close_position("AAPL", 140.0, date(2024, 2, 1), "stop_loss")
        assert trade is not None
        assert trade.pnl < 0

    def test_close_nonexistent(self):
        """Closing nonexistent position returns None."""
        pm = PortfolioManager(initial_capital=100000)
        trade = pm.close_position("AAPL", 150.0, date(2024, 1, 1), "test")
        assert trade is None

    def test_close_short(self):
        """Close a short position."""
        pm = PortfolioManager(initial_capital=100000)
        pm.open_position("AAPL", 10, 150.0, "short", date(2024, 1, 1))
        trade = pm.close_position("AAPL", 140.0, date(2024, 2, 1), "cover")
        assert trade is not None
        assert not trade.is_open


class TestPortfolioManagerUpdatePositions:
    """Test position updates."""

    def test_update_unrealized_pnl(self):
        """Update positions with new prices."""
        pm = PortfolioManager(initial_capital=100000)
        pm.open_position("AAPL", 10, 150.0, "long", date(2024, 1, 1))
        pm.update_positions({"AAPL": 160.0}, date(2024, 1, 15))
        assert pm.positions["AAPL"].unrealized_pnl == 100.0  # (160-150) * 10
        assert pm.positions["AAPL"].days_held == 14


class TestPortfolioManagerExitChecks:
    """Test automatic exit checks."""

    def test_stop_loss_long(self):
        """Stop loss triggers for long position."""
        pm = PortfolioManager(initial_capital=100000)
        pm.open_position("AAPL", 10, 100.0, "long", date(2024, 1, 1))
        closed = pm.check_exits(
            {"AAPL": 90.0}, date(2024, 1, 15),
            {"stop_loss": {"percent": 5}},
        )
        assert len(closed) == 1
        assert closed[0].exit_reason == "stop_loss"
        assert "AAPL" not in pm.positions

    def test_take_profit_long(self):
        """Take profit triggers for long position."""
        pm = PortfolioManager(initial_capital=100000)
        pm.open_position("AAPL", 10, 100.0, "long", date(2024, 1, 1))
        closed = pm.check_exits(
            {"AAPL": 120.0}, date(2024, 1, 15),
            {"take_profit": {"percent": 15}},
        )
        assert len(closed) == 1
        assert closed[0].exit_reason == "take_profit"

    def test_no_exit_within_bounds(self):
        """No exit when price is within stop/take-profit bounds."""
        pm = PortfolioManager(initial_capital=100000)
        pm.open_position("AAPL", 10, 100.0, "long", date(2024, 1, 1))
        closed = pm.check_exits(
            {"AAPL": 105.0}, date(2024, 1, 15),
            {"stop_loss": {"percent": 10}, "take_profit": {"percent": 20}},
        )
        assert len(closed) == 0
        assert "AAPL" in pm.positions


class TestPortfolioManagerSnapshot:
    """Test snapshot recording."""

    def test_record_snapshot(self):
        """Record a portfolio snapshot."""
        pm = PortfolioManager(initial_capital=100000)
        pm.open_position("AAPL", 10, 150.0, "long", date(2024, 1, 1))
        snapshot = pm.record_snapshot(date(2024, 1, 1), {"AAPL": 150.0})
        assert snapshot.equity > 0
        assert snapshot.cash == pm.cash
        assert len(pm.portfolio_history) == 1
        assert len(pm.equity_curve) == 1

    def test_peak_equity_tracking(self):
        """Peak equity is tracked for drawdown calculation."""
        pm = PortfolioManager(initial_capital=100000)
        pm.open_position("AAPL", 10, 150.0, "long", date(2024, 1, 1))

        # Price goes up
        pm.record_snapshot(date(2024, 1, 10), {"AAPL": 160.0})
        peak = pm.peak_equity

        # Price drops
        snapshot = pm.record_snapshot(date(2024, 1, 20), {"AAPL": 145.0})
        assert pm.peak_equity == peak  # Peak doesn't decrease
        assert snapshot.drawdown > 0
        assert snapshot.drawdown_pct > 0

    def test_build_equity_series(self):
        """Build equity curve as Series."""
        pm = PortfolioManager(initial_capital=100000)
        pm.record_snapshot(date(2024, 1, 1))
        pm.record_snapshot(date(2024, 1, 2))
        series = pm.build_equity_series()
        assert len(series) == 2
        assert series.name == "equity"
