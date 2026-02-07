"""Tests for position sizing module."""

import pandas as pd
import numpy as np
from datetime import date

from pyutss.engine.sizing import calculate_size, round_to_lot


class TestCalculateSize:
    """Test calculate_size function."""

    def test_fixed_amount(self):
        """Fixed dollar amount sizing."""
        qty = calculate_size(
            {"type": "fixed_amount", "amount": 10000},
            price=100.0, equity=100000, cash=100000,
        )
        assert qty == 100.0  # $10,000 / $100 = 100 shares

    def test_fixed_quantity(self):
        """Fixed share quantity sizing."""
        qty = calculate_size(
            {"type": "fixed_quantity", "value": 50},
            price=100.0, equity=100000, cash=100000,
        )
        assert qty == 50.0

    def test_percent_of_equity(self):
        """Percent of equity sizing."""
        qty = calculate_size(
            {"type": "percent_of_equity", "percent": 10},
            price=100.0, equity=100000, cash=50000,
        )
        assert qty == 100.0  # 10% of $100,000 / $100 = 100 shares

    def test_percent_of_cash(self):
        """Percent of cash sizing."""
        qty = calculate_size(
            {"type": "percent_of_cash", "percent": 20},
            price=50.0, equity=100000, cash=50000,
        )
        assert qty == 200.0  # 20% of $50,000 / $50 = 200 shares

    def test_percent_of_position(self):
        """Percent of existing position sizing."""
        from pyutss.results.types import Position

        positions = {
            "AAPL": Position(
                symbol="AAPL", quantity=100, avg_price=150.0,
                direction="long", entry_date=date(2024, 1, 1),
            )
        }
        qty = calculate_size(
            {"type": "percent_of_position", "percent": 50, "symbol": "AAPL"},
            price=155.0, equity=100000, cash=50000,
            positions=positions,
        )
        assert qty == 50.0  # 50% of 100 shares

    def test_percent_of_position_no_position(self):
        """Percent of position when no position exists."""
        qty = calculate_size(
            {"type": "percent_of_position", "percent": 50, "symbol": "AAPL"},
            price=155.0, equity=100000, cash=50000,
            positions={},
        )
        assert qty == 0.0

    def test_risk_based(self):
        """Risk-based sizing."""
        qty = calculate_size(
            {"type": "risk_based", "risk_percent": 1.0, "stop_loss_percent": 2.0},
            price=100.0, equity=100000, cash=100000,
        )
        # Risk: 1% of $100,000 = $1,000
        # Risk per share: $100 * 2% = $2
        # Shares: $1,000 / $2 = 500
        assert qty == 500.0

    def test_kelly_default(self):
        """Kelly sizing with defaults (no trade history)."""
        qty = calculate_size(
            {"type": "kelly", "win_rate": 0.6, "avg_win": 2.0, "avg_loss": 1.0},
            price=100.0, equity=100000, cash=100000,
        )
        assert qty > 0

    def test_volatility_adjusted_with_data(self):
        """Volatility-adjusted sizing with data."""
        dates = pd.date_range("2024-01-01", periods=30)
        np.random.seed(42)
        prices = 100 + np.random.randn(30).cumsum()
        data = pd.DataFrame({
            "open": prices,
            "high": prices + abs(np.random.randn(30)),
            "low": prices - abs(np.random.randn(30)),
            "close": prices,
            "volume": np.random.randint(1000, 10000, 30),
        }, index=dates)

        qty = calculate_size(
            {"type": "volatility_adjusted", "target_risk": 1000, "atr_period": 14},
            price=100.0, equity=100000, cash=100000,
            data=data,
        )
        assert qty > 0

    def test_volatility_adjusted_no_data(self):
        """Volatility-adjusted sizing without data falls back to estimate."""
        qty = calculate_size(
            {"type": "volatility_adjusted", "target_risk": 1000},
            price=100.0, equity=100000, cash=100000,
        )
        # Fallback: $1000 / ($100 * 0.02) = 500
        assert qty == 500.0

    def test_unknown_type_defaults(self):
        """Unknown sizing type defaults to 10% equity."""
        qty = calculate_size(
            {"type": "unknown_type"},
            price=100.0, equity=100000, cash=100000,
        )
        assert qty == 100.0  # 10% of $100,000 / $100

    def test_zero_price(self):
        """Zero price returns 0."""
        qty = calculate_size(
            {"type": "fixed_amount", "amount": 10000},
            price=0.0, equity=100000, cash=100000,
        )
        assert qty == 0.0


class TestRoundToLot:
    """Test lot size rounding."""

    def test_us_stock_lot_1(self):
        """US stocks: lot size 1, floor to whole shares."""
        assert round_to_lot(100.7, lot_size=1) == 100.0
        assert round_to_lot(0.5, lot_size=1) == 0.0

    def test_japanese_stock_lot_100(self):
        """Japanese stocks: lot size 100."""
        assert round_to_lot(350, lot_size=100) == 300.0
        assert round_to_lot(99, lot_size=100) == 0.0
        assert round_to_lot(100, lot_size=100) == 100.0
        assert round_to_lot(250, lot_size=100) == 200.0

    def test_fractional_shares(self):
        """Fractional shares: no rounding."""
        assert round_to_lot(100.7, lot_size=100, fractional=True) == 100.7

    def test_etf_lot_1(self):
        """ETF lot size 1."""
        assert round_to_lot(5.8, lot_size=1) == 5.0

    def test_zero_quantity(self):
        """Zero quantity stays zero."""
        assert round_to_lot(0, lot_size=100) == 0.0
