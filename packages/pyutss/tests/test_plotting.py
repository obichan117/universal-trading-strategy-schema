"""Tests for plotting functionality."""

from datetime import date

import pandas as pd
import pytest

from pyutss.results.types import (
    BacktestResult,
    Trade,
    PortfolioSnapshot,
)
from pyutss.results.plotting import print_summary


@pytest.fixture
def sample_data() -> pd.DataFrame:
    """Create sample OHLCV data for testing."""
    dates = pd.date_range("2024-01-01", periods=20, freq="D")
    return pd.DataFrame(
        {
            "open": [100 + i for i in range(20)],
            "high": [102 + i for i in range(20)],
            "low": [98 + i for i in range(20)],
            "close": [101 + i for i in range(20)],
            "volume": [1000000] * 20,
        },
        index=dates,
    )


@pytest.fixture
def sample_result() -> BacktestResult:
    """Create sample backtest result for testing."""
    trades = [
        Trade(
            symbol="AAPL",
            direction="long",
            entry_date=date(2024, 1, 5),
            entry_price=105.0,
            quantity=100,
            exit_date=date(2024, 1, 10),
            exit_price=110.0,
            pnl=500.0,
            pnl_pct=4.76,
            is_open=False,
        ),
        Trade(
            symbol="AAPL",
            direction="long",
            entry_date=date(2024, 1, 12),
            entry_price=112.0,
            quantity=100,
            exit_date=date(2024, 1, 15),
            exit_price=108.0,
            pnl=-400.0,
            pnl_pct=-3.57,
            is_open=False,
        ),
    ]

    portfolio_history = [
        PortfolioSnapshot(
            date=date(2024, 1, 1),
            cash=100000,
            positions_value=0,
            equity=100000,
            drawdown=0,
            drawdown_pct=0,
        ),
        PortfolioSnapshot(
            date=date(2024, 1, 10),
            cash=89500,
            positions_value=11000,
            equity=100500,
            drawdown=0,
            drawdown_pct=0,
        ),
        PortfolioSnapshot(
            date=date(2024, 1, 15),
            cash=100100,
            positions_value=0,
            equity=100100,
            drawdown=400,
            drawdown_pct=0.4,
        ),
    ]

    equity_curve = pd.Series(
        [100000, 100500, 100100],
        index=pd.to_datetime(["2024-01-01", "2024-01-10", "2024-01-15"]),
    )

    return BacktestResult(
        strategy_id="test_strategy",
        symbol="AAPL",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 20),
        initial_capital=100000,
        final_equity=100100,
        trades=trades,
        portfolio_history=portfolio_history,
        equity_curve=equity_curve,
    )


class TestPrintSummary:
    """Tests for print_summary function."""

    def test_summary_contains_symbol(self, sample_result: BacktestResult):
        """Summary should include the symbol."""
        output = print_summary(sample_result)
        assert "AAPL" in output

    def test_summary_contains_return(self, sample_result: BacktestResult):
        """Summary should include return percentage."""
        output = print_summary(sample_result)
        assert "0.10%" in output  # 100100 / 100000 - 1 = 0.1%

    def test_summary_contains_trade_count(self, sample_result: BacktestResult):
        """Summary should include trade count."""
        output = print_summary(sample_result)
        assert "Total Trades:" in output
        assert "2" in output

    def test_summary_contains_win_rate(self, sample_result: BacktestResult):
        """Summary should include win rate."""
        output = print_summary(sample_result)
        assert "Win Rate:" in output
        assert "50.0%" in output  # 1 win, 1 loss

    def test_summary_contains_dates(self, sample_result: BacktestResult):
        """Summary should include date range."""
        output = print_summary(sample_result)
        assert "2024-01-01" in output
        assert "2024-01-20" in output


class TestBacktestResultSummary:
    """Tests for BacktestResult.summary() method."""

    def test_summary_method_returns_string(self, sample_result: BacktestResult):
        """summary() should return a string."""
        output = sample_result.summary(print_output=False)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_summary_method_prints_when_requested(
        self, sample_result: BacktestResult, capsys
    ):
        """summary() should print when print_output=True."""
        sample_result.summary(print_output=True)
        captured = capsys.readouterr()
        assert "AAPL" in captured.out


class TestBacktestResultPlot:
    """Tests for BacktestResult.plot() method."""

    def test_plot_raises_without_mplfinance(
        self, sample_result: BacktestResult, sample_data: pd.DataFrame, monkeypatch
    ):
        """plot() should raise ImportError if mplfinance not installed."""
        # Mock the import to fail
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "mplfinance":
                raise ImportError("No module named 'mplfinance'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        # Clear the module from cache if it exists
        import sys

        if "mplfinance" in sys.modules:
            del sys.modules["mplfinance"]
        if "pyutss.results.plotting" in sys.modules:
            del sys.modules["pyutss.results.plotting"]

        with pytest.raises(ImportError, match="mplfinance"):
            sample_result.plot(sample_data)


class TestEmptyResults:
    """Tests for edge cases with empty results."""

    def test_summary_with_no_trades(self):
        """Summary should handle empty trade list."""
        result = BacktestResult(
            strategy_id="empty_test",
            symbol="TEST",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
            initial_capital=100000,
            final_equity=100000,
            trades=[],
            portfolio_history=[],
        )

        output = print_summary(result)
        assert "TEST" in output
        assert "Total Trades:" in output
        assert "0" in output

    def test_summary_with_all_winners(self):
        """Summary should handle all winning trades."""
        trades = [
            Trade(
                symbol="TEST",
                direction="long",
                entry_date=date(2024, 1, 1),
                entry_price=100.0,
                quantity=100,
                exit_date=date(2024, 1, 5),
                exit_price=110.0,
                pnl=1000.0,
                pnl_pct=10.0,
                is_open=False,
            ),
        ]

        result = BacktestResult(
            strategy_id="winner_test",
            symbol="TEST",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
            initial_capital=100000,
            final_equity=101000,
            trades=trades,
            portfolio_history=[],
        )

        output = print_summary(result)
        assert "100.0%" in output  # 100% win rate
        assert "∞" in output  # Infinite profit factor (no losses)
