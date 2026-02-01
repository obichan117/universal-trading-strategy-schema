"""Tests for visualization module."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from pyutss.results.types import BacktestResult, PortfolioSnapshot, Trade


def create_sample_result() -> BacktestResult:
    """Create a sample BacktestResult for testing."""
    # Create equity curve
    dates = pd.date_range("2023-01-01", periods=252, freq="B")
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 252)
    equity = 100000 * np.cumprod(1 + returns)
    equity_curve = pd.Series(equity, index=dates, name="equity")

    # Create trades
    trades = [
        Trade(
            symbol="AAPL",
            direction="long",
            entry_date=date(2023, 1, 10),
            entry_price=150.0,
            quantity=100,
            exit_date=date(2023, 1, 20),
            exit_price=155.0,
            pnl=500.0,
            pnl_pct=3.33,
            is_open=False,
            entry_reason="buy_signal",
            exit_reason="sell_signal",
        ),
        Trade(
            symbol="AAPL",
            direction="long",
            entry_date=date(2023, 2, 1),
            entry_price=160.0,
            quantity=100,
            exit_date=date(2023, 2, 15),
            exit_price=155.0,
            pnl=-500.0,
            pnl_pct=-3.125,
            is_open=False,
            entry_reason="buy_signal",
            exit_reason="stop_loss",
        ),
        Trade(
            symbol="AAPL",
            direction="long",
            entry_date=date(2023, 3, 1),
            entry_price=152.0,
            quantity=100,
            exit_date=date(2023, 3, 20),
            exit_price=165.0,
            pnl=1300.0,
            pnl_pct=8.55,
            is_open=False,
            entry_reason="buy_signal",
            exit_reason="take_profit",
        ),
    ]

    # Create portfolio history
    history = []
    for i, (dt, eq) in enumerate(zip(dates, equity)):
        d = dt.date() if hasattr(dt, "date") else dt
        history.append(PortfolioSnapshot(
            date=d,
            cash=eq * 0.3,
            positions_value=eq * 0.7,
            equity=eq,
            drawdown=max(0, equity[:i+1].max() - eq),
            drawdown_pct=max(0, (1 - eq / equity[:i+1].max()) * 100),
        ))

    return BacktestResult(
        strategy_id="test_strategy",
        symbol="AAPL",
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        initial_capital=100000.0,
        final_equity=float(equity[-1]),
        trades=trades,
        portfolio_history=history,
        equity_curve=equity_curve,
    )


class TestTearSheet:
    """Tests for TearSheet class."""

    def test_init(self):
        """Test TearSheet initialization."""
        from pyutss.visualization import TearSheet

        result = create_sample_result()
        sheet = TearSheet(result)

        assert sheet.result is result
        assert sheet.benchmark is None
        assert sheet.risk_free_rate == 0.0

    def test_summary_stats(self):
        """Test summary statistics calculation."""
        from pyutss.visualization import TearSheet

        result = create_sample_result()
        sheet = TearSheet(result)
        stats = sheet.summary_stats()

        assert "Total Return (%)" in stats
        assert "Sharpe Ratio" in stats
        assert "Max Drawdown (%)" in stats
        assert "Win Rate (%)" in stats
        assert "Total Trades" in stats

    def test_summary_table(self):
        """Test summary table generation."""
        from pyutss.visualization import TearSheet

        result = create_sample_result()
        sheet = TearSheet(result)
        df = sheet.summary_table()

        assert isinstance(df, pd.DataFrame)
        assert "Metric" in df.columns
        assert "Value" in df.columns
        assert len(df) > 0

    def test_metrics_cached(self):
        """Test that metrics are cached."""
        from pyutss.visualization import TearSheet

        result = create_sample_result()
        sheet = TearSheet(result)

        metrics1 = sheet.metrics
        metrics2 = sheet.metrics

        assert metrics1 is metrics2


class TestCharts:
    """Tests for chart generation functions."""

    @pytest.fixture
    def sample_result(self):
        return create_sample_result()

    def test_plot_equity_curve(self, sample_result):
        """Test equity curve plot generation."""
        pytest.importorskip("matplotlib")
        from pyutss.visualization import plot_equity_curve

        fig = plot_equity_curve(sample_result)
        assert fig is not None

        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_equity_curve_no_drawdown(self, sample_result):
        """Test equity curve without drawdown."""
        pytest.importorskip("matplotlib")
        from pyutss.visualization import plot_equity_curve

        fig = plot_equity_curve(sample_result, show_drawdown=False)
        assert fig is not None

        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_drawdown(self, sample_result):
        """Test drawdown plot generation."""
        pytest.importorskip("matplotlib")
        from pyutss.visualization import plot_drawdown

        fig = plot_drawdown(sample_result)
        assert fig is not None

        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_monthly_heatmap(self, sample_result):
        """Test monthly heatmap generation."""
        pytest.importorskip("matplotlib")
        pytest.importorskip("seaborn")
        from pyutss.visualization import plot_monthly_heatmap

        fig = plot_monthly_heatmap(sample_result)
        assert fig is not None

        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_rolling_metrics(self, sample_result):
        """Test rolling metrics plot generation."""
        pytest.importorskip("matplotlib")
        from pyutss.visualization import plot_rolling_metrics

        fig = plot_rolling_metrics(sample_result)
        assert fig is not None

        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_distribution(self, sample_result):
        """Test distribution plot generation."""
        pytest.importorskip("matplotlib")
        pytest.importorskip("scipy")
        from pyutss.visualization import plot_distribution

        fig = plot_distribution(sample_result)
        assert fig is not None

        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_trade_analysis(self, sample_result):
        """Test trade analysis plot generation."""
        pytest.importorskip("matplotlib")
        from pyutss.visualization import plot_trade_analysis

        fig = plot_trade_analysis(sample_result)
        assert fig is not None

        import matplotlib.pyplot as plt
        plt.close(fig)


class TestHTMLReport:
    """Tests for HTML report generation."""

    def test_full_report_generation(self, tmp_path):
        """Test full HTML report generation."""
        pytest.importorskip("matplotlib")
        pytest.importorskip("seaborn")
        pytest.importorskip("scipy")

        from pyutss.visualization import TearSheet

        result = create_sample_result()
        sheet = TearSheet(result)

        output_path = tmp_path / "report.html"
        sheet.full_report(str(output_path))

        assert output_path.exists()
        content = output_path.read_text()

        # Check for key elements
        assert "<!DOCTYPE html>" in content
        assert "test_strategy" in content
        assert "AAPL" in content
        assert "data:image/png;base64" in content
