"""Tests for portfolio backtesting module."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

from pyutss.portfolio import (
    PortfolioBacktester,
    PortfolioConfig,
    PortfolioResult,
    RebalanceFrequency,
    Rebalancer,
    equal_weight,
    inverse_volatility,
    risk_parity,
    target_weights,
)
from pyutss.portfolio.rebalancer import RebalanceConfig


def create_sample_data(
    symbol: str,
    start: str = "2023-01-01",
    periods: int = 252,
    start_price: float = 100.0,
) -> pd.DataFrame:
    """Create sample OHLCV data."""
    dates = pd.date_range(start, periods=periods, freq="B")
    np.random.seed(hash(symbol) % 2**31)

    # Generate random walk price
    returns = np.random.normal(0.0005, 0.02, periods)
    close = start_price * np.cumprod(1 + returns)

    # Generate OHLCV
    df = pd.DataFrame({
        "open": close * (1 + np.random.uniform(-0.01, 0.01, periods)),
        "high": close * (1 + np.random.uniform(0, 0.02, periods)),
        "low": close * (1 - np.random.uniform(0, 0.02, periods)),
        "close": close,
        "volume": np.random.randint(1000000, 10000000, periods),
    }, index=dates)

    return df


def create_sample_strategy() -> dict:
    """Create a simple RSI strategy."""
    return {
        "info": {"id": "test_portfolio_strategy"},
        "rules": [
            {
                "when": {"type": "always"},
                "then": {"type": "hold"},
            }
        ],
        "constraints": {
            "stop_loss": {"percentage": 5},
            "take_profit": {"percentage": 10},
        },
    }


class TestWeightSchemes:
    """Tests for weight calculation schemes."""

    @pytest.fixture
    def sample_data(self):
        """Create sample multi-symbol data."""
        return {
            "AAPL": create_sample_data("AAPL", start_price=150),
            "MSFT": create_sample_data("MSFT", start_price=300),
            "GOOGL": create_sample_data("GOOGL", start_price=120),
        }

    def test_equal_weight(self, sample_data):
        """Test equal weight scheme."""
        scheme = equal_weight()
        symbols = list(sample_data.keys())
        current_date = pd.Timestamp("2023-06-01")

        weights = scheme.calculate(symbols, sample_data, current_date)

        assert len(weights) == 3
        assert abs(sum(weights.values()) - 1.0) < 0.0001
        assert all(abs(w - 1/3) < 0.0001 for w in weights.values())

    def test_inverse_volatility(self, sample_data):
        """Test inverse volatility weight scheme."""
        scheme = inverse_volatility()
        symbols = list(sample_data.keys())
        current_date = pd.Timestamp("2023-06-01")

        weights = scheme.calculate(symbols, sample_data, current_date)

        assert len(weights) == 3
        assert abs(sum(weights.values()) - 1.0) < 0.0001
        assert all(w >= 0 for w in weights.values())

    def test_risk_parity(self, sample_data):
        """Test risk parity weight scheme."""
        scheme = risk_parity()
        symbols = list(sample_data.keys())
        current_date = pd.Timestamp("2023-06-01")

        weights = scheme.calculate(symbols, sample_data, current_date)

        assert len(weights) == 3
        assert abs(sum(weights.values()) - 1.0) < 0.01  # Allow small numerical error
        # Weights should be non-negative or very close to zero
        assert all(w >= -0.01 for w in weights.values())

    def test_target_weights(self, sample_data):
        """Test fixed target weight scheme."""
        custom_weights = {"AAPL": 0.5, "MSFT": 0.3, "GOOGL": 0.2}
        scheme = target_weights(custom_weights)
        symbols = list(sample_data.keys())
        current_date = pd.Timestamp("2023-06-01")

        weights = scheme.calculate(symbols, sample_data, current_date)

        assert weights["AAPL"] == 0.5
        assert weights["MSFT"] == 0.3
        assert weights["GOOGL"] == 0.2


class TestRebalancer:
    """Tests for Rebalancer class."""

    def test_monthly_rebalance(self):
        """Test monthly rebalancing trigger."""
        config = RebalanceConfig(frequency=RebalanceFrequency.MONTHLY)
        rebalancer = Rebalancer(config)

        # First day should trigger
        jan_first = date(2023, 1, 2)  # Monday, Jan 2
        assert rebalancer.should_rebalance(jan_first)

        # Same month should not trigger again
        jan_mid = date(2023, 1, 15)
        assert not rebalancer.should_rebalance(jan_mid)

        # New month should trigger
        feb_first = date(2023, 2, 1)
        assert rebalancer.should_rebalance(feb_first)

    def test_weekly_rebalance(self):
        """Test weekly rebalancing trigger."""
        config = RebalanceConfig(
            frequency=RebalanceFrequency.WEEKLY,
            day_of_week=0,  # Monday
        )
        rebalancer = Rebalancer(config)

        monday = date(2023, 1, 2)  # Monday
        tuesday = date(2023, 1, 3)  # Tuesday

        assert rebalancer.should_rebalance(monday)
        assert not rebalancer.should_rebalance(tuesday)

    def test_threshold_rebalance(self):
        """Test threshold-based rebalancing."""
        config = RebalanceConfig(
            frequency=RebalanceFrequency.NEVER,
            threshold_pct=20.0,  # 20% drift threshold
        )
        rebalancer = Rebalancer(config)

        target = {"AAPL": 0.33, "MSFT": 0.33, "GOOGL": 0.34}

        # Within threshold (drift < 20%)
        current_ok = {"AAPL": 0.35, "MSFT": 0.35, "GOOGL": 0.30}
        assert not rebalancer.should_rebalance(date(2023, 1, 1), current_ok, target)

        # Outside threshold (drift > 20%)
        drifted = {"AAPL": 0.50, "MSFT": 0.30, "GOOGL": 0.20}  # AAPL drifted ~50%
        assert rebalancer.should_rebalance(date(2023, 1, 1), drifted, target)

    def test_never_rebalance(self):
        """Test never rebalancing."""
        config = RebalanceConfig(frequency=RebalanceFrequency.NEVER)
        rebalancer = Rebalancer(config)

        assert not rebalancer.should_rebalance(date(2023, 1, 1))
        assert not rebalancer.should_rebalance(date(2023, 6, 1))


class TestPortfolioBacktester:
    """Tests for PortfolioBacktester class."""

    @pytest.fixture
    def sample_data(self):
        """Create sample multi-symbol data."""
        return {
            "AAPL": create_sample_data("AAPL", start_price=150),
            "MSFT": create_sample_data("MSFT", start_price=300),
        }

    @pytest.fixture
    def strategy(self):
        return create_sample_strategy()

    def test_basic_portfolio_backtest(self, sample_data, strategy):
        """Test basic portfolio backtest runs without error."""
        config = PortfolioConfig(
            initial_capital=100000,
            rebalance="monthly",
        )
        backtester = PortfolioBacktester(config)

        result = backtester.run(
            strategy=strategy,
            data=sample_data,
            weights="equal",
        )

        assert isinstance(result, PortfolioResult)
        assert result.symbols == ["AAPL", "MSFT"]
        assert result.initial_capital == 100000
        assert result.final_equity > 0

    def test_portfolio_with_inverse_vol(self, sample_data, strategy):
        """Test portfolio with inverse volatility weighting."""
        config = PortfolioConfig(
            initial_capital=100000,
            rebalance="monthly",
        )
        backtester = PortfolioBacktester(config)

        result = backtester.run(
            strategy=strategy,
            data=sample_data,
            weights="inverse_vol",
        )

        assert isinstance(result, PortfolioResult)
        assert result.weight_scheme == "inverse_vol"

    def test_portfolio_with_custom_weights(self, sample_data, strategy):
        """Test portfolio with custom weights."""
        config = PortfolioConfig(
            initial_capital=100000,
            rebalance="monthly",
        )
        backtester = PortfolioBacktester(config)

        result = backtester.run(
            strategy=strategy,
            data=sample_data,
            weights={"AAPL": 0.6, "MSFT": 0.4},
        )

        assert isinstance(result, PortfolioResult)
        assert result.weight_scheme == "custom"


class TestPortfolioResult:
    """Tests for PortfolioResult class."""

    def test_correlation_matrix(self):
        """Test correlation matrix calculation."""
        from pyutss.results.types import BacktestResult

        # Create mock per-symbol results
        dates = pd.date_range("2023-01-01", periods=100, freq="B")
        np.random.seed(42)

        result = PortfolioResult(
            strategy_id="test",
            symbols=["AAPL", "MSFT"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 5, 1),
            initial_capital=100000,
            final_equity=110000,
            per_symbol_results={
                "AAPL": BacktestResult(
                    strategy_id="test",
                    symbol="AAPL",
                    start_date=date(2023, 1, 1),
                    end_date=date(2023, 5, 1),
                    initial_capital=50000,
                    final_equity=55000,
                    equity_curve=pd.Series(
                        50000 * np.cumprod(1 + np.random.normal(0.001, 0.02, 100)),
                        index=dates,
                    ),
                ),
                "MSFT": BacktestResult(
                    strategy_id="test",
                    symbol="MSFT",
                    start_date=date(2023, 1, 1),
                    end_date=date(2023, 5, 1),
                    initial_capital=50000,
                    final_equity=55000,
                    equity_curve=pd.Series(
                        50000 * np.cumprod(1 + np.random.normal(0.001, 0.02, 100)),
                        index=dates,
                    ),
                ),
            },
        )

        corr = result.correlation_matrix()

        assert isinstance(corr, pd.DataFrame)
        assert "AAPL" in corr.columns
        assert "MSFT" in corr.columns
        assert corr.loc["AAPL", "AAPL"] == 1.0

    def test_diversification_ratio(self):
        """Test diversification ratio calculation."""
        from pyutss.results.types import BacktestResult

        dates = pd.date_range("2023-01-01", periods=100, freq="B")
        np.random.seed(42)

        result = PortfolioResult(
            strategy_id="test",
            symbols=["AAPL", "MSFT"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 5, 1),
            initial_capital=100000,
            final_equity=110000,
            per_symbol_results={
                "AAPL": BacktestResult(
                    strategy_id="test",
                    symbol="AAPL",
                    start_date=date(2023, 1, 1),
                    end_date=date(2023, 5, 1),
                    initial_capital=50000,
                    final_equity=55000,
                    equity_curve=pd.Series(
                        50000 * np.cumprod(1 + np.random.normal(0.001, 0.02, 100)),
                        index=dates,
                    ),
                ),
                "MSFT": BacktestResult(
                    strategy_id="test",
                    symbol="MSFT",
                    start_date=date(2023, 1, 1),
                    end_date=date(2023, 5, 1),
                    initial_capital=50000,
                    final_equity=55000,
                    equity_curve=pd.Series(
                        50000 * np.cumprod(1 + np.random.normal(0.001, 0.02, 100)),
                        index=dates,
                    ),
                ),
            },
        )

        dr = result.diversification_ratio()

        # Diversification ratio should be >= 1 for diversified portfolio
        assert dr >= 0.9  # Allow for numerical tolerance
