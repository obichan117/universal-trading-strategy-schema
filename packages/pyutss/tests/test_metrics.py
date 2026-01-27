"""Tests for pyutss metrics calculator."""

from datetime import date

import pandas as pd
import pytest

from pyutss import (
    BacktestResult,
    MetricsCalculator,
    PerformanceMetrics,
    PortfolioSnapshot,
    Trade,
)


@pytest.fixture
def sample_result():
    """Create a sample backtest result for testing."""
    trades = [
        Trade(
            symbol="TEST",
            direction="long",
            entry_date=date(2024, 1, 10),
            entry_price=100,
            quantity=10,
            exit_date=date(2024, 1, 20),
            exit_price=110,
            pnl=100,
            pnl_pct=10,
            is_open=False,
        ),
        Trade(
            symbol="TEST",
            direction="long",
            entry_date=date(2024, 2, 1),
            entry_price=105,
            quantity=10,
            exit_date=date(2024, 2, 15),
            exit_price=100,
            pnl=-50,
            pnl_pct=-4.76,
            is_open=False,
        ),
        Trade(
            symbol="TEST",
            direction="long",
            entry_date=date(2024, 3, 1),
            entry_price=102,
            quantity=10,
            exit_date=date(2024, 3, 20),
            exit_price=115,
            pnl=130,
            pnl_pct=12.7,
            is_open=False,
        ),
    ]

    dates = pd.date_range("2024-01-01", periods=90, freq="D")
    equity_values = [100000 + i * 50 + (i % 10) * 10 for i in range(90)]
    equity_curve = pd.Series(equity_values, index=dates)

    portfolio_history = [
        PortfolioSnapshot(
            date=d.date(),
            cash=eq * 0.3,
            positions_value=eq * 0.7,
            equity=eq,
        )
        for d, eq in zip(dates, equity_values)
    ]

    return BacktestResult(
        strategy_id="test-strategy",
        symbol="TEST",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        initial_capital=100000,
        final_equity=104500,
        trades=trades,
        portfolio_history=portfolio_history,
        equity_curve=equity_curve,
    )


class TestMetricsCalculator:
    """Tests for MetricsCalculator."""

    def test_calculate_returns_all_metrics(self, sample_result):
        """Test that calculate returns all expected metrics."""
        calculator = MetricsCalculator()
        metrics = calculator.calculate(sample_result)

        assert isinstance(metrics, PerformanceMetrics)
        assert hasattr(metrics, "total_return")
        assert hasattr(metrics, "sharpe_ratio")
        assert hasattr(metrics, "max_drawdown")
        assert hasattr(metrics, "win_rate")

    def test_total_return_calculation(self, sample_result):
        """Test total return calculation."""
        calculator = MetricsCalculator()
        metrics = calculator.calculate(sample_result)

        expected_return = 104500 - 100000
        assert metrics.total_return == expected_return
        assert metrics.total_return_pct == pytest.approx(4.5, rel=0.01)

    def test_trade_statistics(self, sample_result):
        """Test trade statistics calculation."""
        calculator = MetricsCalculator()
        metrics = calculator.calculate(sample_result)

        assert metrics.total_trades == 3
        assert metrics.winning_trades == 2
        assert metrics.losing_trades == 1
        assert metrics.win_rate == pytest.approx(66.67, rel=0.1)

    def test_profit_factor(self, sample_result):
        """Test profit factor calculation."""
        calculator = MetricsCalculator()
        metrics = calculator.calculate(sample_result)

        # Gross profit = 100 + 130 = 230
        # Gross loss = 50
        # Profit factor = 230 / 50 = 4.6
        assert metrics.profit_factor == pytest.approx(4.6, rel=0.1)

    def test_metrics_to_dict(self, sample_result):
        """Test metrics to_dict method."""
        calculator = MetricsCalculator()
        metrics = calculator.calculate(sample_result)
        metrics_dict = metrics.to_dict()

        assert isinstance(metrics_dict, dict)
        assert "total_return" in metrics_dict
        assert "sharpe_ratio" in metrics_dict
        assert "win_rate" in metrics_dict

    def test_monthly_breakdown(self, sample_result):
        """Test monthly breakdown generation."""
        calculator = MetricsCalculator()
        monthly = calculator.monthly_breakdown(sample_result)

        assert len(monthly) > 0
        assert all(hasattr(m, "period") for m in monthly)
        assert all(hasattr(m, "return_pct") for m in monthly)

    def test_yearly_breakdown(self, sample_result):
        """Test yearly breakdown generation."""
        calculator = MetricsCalculator()
        yearly = calculator.yearly_breakdown(sample_result)

        assert len(yearly) > 0
        assert yearly[0].period == "2024"

    def test_empty_trades(self):
        """Test metrics with no trades."""
        result = BacktestResult(
            strategy_id="empty-strategy",
            symbol="TEST",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            initial_capital=100000,
            final_equity=100000,
            trades=[],
            portfolio_history=[],
            equity_curve=pd.Series(dtype=float),
        )

        calculator = MetricsCalculator()
        metrics = calculator.calculate(result)

        assert metrics.total_trades == 0
        assert metrics.win_rate == 0.0
        assert metrics.profit_factor == 0.0


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics dataclass."""

    def test_metrics_creation(self):
        """Test creating PerformanceMetrics directly."""
        metrics = PerformanceMetrics(
            total_return=1000,
            total_return_pct=10,
            annualized_return=500,
            annualized_return_pct=5,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            calmar_ratio=1.0,
            max_drawdown=500,
            max_drawdown_pct=5,
            max_drawdown_duration_days=10,
            avg_drawdown=200,
            avg_drawdown_pct=2,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=60,
            profit_factor=1.8,
            avg_win=200,
            avg_loss=150,
            largest_win=500,
            largest_loss=300,
            avg_trade_pnl=50,
            avg_trade_duration_days=5,
            volatility=2,
            volatility_annualized=30,
            downside_deviation=1.5,
            total_exposure_days=50,
            exposure_pct=50,
        )

        assert metrics.total_return == 1000
        assert metrics.sharpe_ratio == 1.5
        assert metrics.win_rate == 60
