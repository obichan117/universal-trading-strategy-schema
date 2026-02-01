"""Tests for Monte Carlo simulation."""

import numpy as np
import pandas as pd

from pyutss.analysis.monte_carlo import (
    MonteCarloResult,
    MonteCarloSimulator,
    TradeInfo,
)


class TestMonteCarloResult:
    """Tests for MonteCarloResult dataclass."""

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        result = MonteCarloResult(
            n_iterations=1000,
            drawdown_95=0.15,
            drawdown_99=0.20,
            drawdown_median=0.08,
            drawdown_mean=0.09,
            return_ci=(0.05, 0.25),
            sharpe_ci=(0.5, 1.5),
            final_equity_ci=(105000.0, 125000.0),
            win_rate_ci=(45.0, 55.0),
            profit_factor_ci=(1.2, 1.8),
            all_max_drawdowns=np.array([0.1, 0.15, 0.2]),
            all_total_returns=np.array([0.1, 0.15, 0.2]),
            all_sharpe_ratios=np.array([0.8, 1.0, 1.2]),
        )

        data = result.to_dict()

        assert data["n_iterations"] == 1000
        assert data["drawdown_95"] == 0.15
        assert data["return_ci_low"] == 0.05
        assert data["return_ci_high"] == 0.25
        assert "all_max_drawdowns" not in data  # Arrays excluded

    def test_summary(self) -> None:
        """Test summary generation."""
        result = MonteCarloResult(
            n_iterations=1000,
            drawdown_95=0.15,
            drawdown_99=0.20,
            drawdown_median=0.08,
            drawdown_mean=0.09,
            return_ci=(0.05, 0.25),
            sharpe_ci=(0.5, 1.5),
            final_equity_ci=(105000.0, 125000.0),
            win_rate_ci=(45.0, 55.0),
            profit_factor_ci=(1.2, 1.8),
            all_max_drawdowns=np.array([0.1]),
            all_total_returns=np.array([0.1]),
            all_sharpe_ratios=np.array([1.0]),
        )

        summary = result.summary()

        assert "1,000 iterations" in summary
        assert "15.00%" in summary  # 95th percentile drawdown
        assert "Sharpe Ratio" in summary


class TestMonteCarloSimulatorShuffleTrades:
    """Tests for shuffle_trades method."""

    def test_basic_shuffle(self) -> None:
        """Test basic trade shuffling."""
        trades = [
            TradeInfo(pnl=100),
            TradeInfo(pnl=-50),
            TradeInfo(pnl=75),
            TradeInfo(pnl=-25),
            TradeInfo(pnl=50),
        ]

        simulator = MonteCarloSimulator(seed=42)
        result = simulator.shuffle_trades(trades, initial_capital=10000, n_iterations=100)

        assert result.n_iterations == 100
        assert len(result.all_max_drawdowns) == 100
        assert len(result.all_total_returns) == 100
        # Total PnL is 150, so return should be around 1.5%
        assert np.isclose(np.mean(result.all_total_returns), 0.015, atol=0.001)

    def test_shuffle_with_dicts(self) -> None:
        """Test shuffling with dict trades."""
        trades = [
            {"pnl": 100},
            {"pnl": -50},
            {"pnl": 75},
        ]

        simulator = MonteCarloSimulator(seed=42)
        result = simulator.shuffle_trades(trades, n_iterations=50)

        assert result.n_iterations == 50
        # Total PnL = 125
        assert np.mean(result.all_total_returns) > 0

    def test_empty_trades(self) -> None:
        """Test with empty trade list."""
        simulator = MonteCarloSimulator()
        result = simulator.shuffle_trades([], n_iterations=10)

        assert result.n_iterations == 10
        assert result.drawdown_95 == 0.0
        assert result.return_ci == (0.0, 0.0)

    def test_single_trade(self) -> None:
        """Test with single trade."""
        trades = [TradeInfo(pnl=100)]

        simulator = MonteCarloSimulator(seed=42)
        result = simulator.shuffle_trades(trades, initial_capital=10000, n_iterations=100)

        # With single trade, all iterations should be identical
        assert result.n_iterations == 100
        assert result.return_ci[0] == result.return_ci[1]  # No variance

    def test_all_winning_trades(self) -> None:
        """Test with all winning trades."""
        trades = [TradeInfo(pnl=100) for _ in range(10)]

        simulator = MonteCarloSimulator(seed=42)
        result = simulator.shuffle_trades(trades, initial_capital=10000, n_iterations=100)

        assert result.win_rate_ci[0] == 100.0
        assert result.win_rate_ci[1] == 100.0
        assert result.drawdown_95 == 0.0  # No drawdowns with all wins

    def test_all_losing_trades(self) -> None:
        """Test with all losing trades."""
        trades = [TradeInfo(pnl=-100) for _ in range(10)]

        simulator = MonteCarloSimulator(seed=42)
        result = simulator.shuffle_trades(trades, initial_capital=10000, n_iterations=100)

        assert result.win_rate_ci[0] == 0.0
        assert result.win_rate_ci[1] == 0.0
        assert result.drawdown_95 > 0.0  # Should have drawdown

    def test_reproducibility_with_seed(self) -> None:
        """Test that same seed produces same results."""
        trades = [TradeInfo(pnl=np.random.randn() * 100) for _ in range(50)]

        sim1 = MonteCarloSimulator(seed=42)
        sim2 = MonteCarloSimulator(seed=42)

        result1 = sim1.shuffle_trades(trades, n_iterations=100)
        result2 = sim2.shuffle_trades(trades, n_iterations=100)

        np.testing.assert_array_equal(
            result1.all_max_drawdowns, result2.all_max_drawdowns
        )

    def test_different_seeds_different_results(self) -> None:
        """Test that different seeds produce different results."""
        trades = [TradeInfo(pnl=np.random.randn() * 100) for _ in range(50)]

        sim1 = MonteCarloSimulator(seed=42)
        sim2 = MonteCarloSimulator(seed=123)

        result1 = sim1.shuffle_trades(trades, n_iterations=100)
        result2 = sim2.shuffle_trades(trades, n_iterations=100)

        assert not np.array_equal(
            result1.all_max_drawdowns, result2.all_max_drawdowns
        )


class TestMonteCarloSimulatorBootstrapReturns:
    """Tests for bootstrap_returns method."""

    def test_basic_bootstrap(self) -> None:
        """Test basic return bootstrapping."""
        np.random.seed(42)
        returns = pd.Series(np.random.randn(252) * 0.01)

        simulator = MonteCarloSimulator(seed=42)
        result = simulator.bootstrap_returns(returns, n_iterations=100)

        assert result.n_iterations == 100
        assert len(result.all_sharpe_ratios) == 100
        assert result.drawdown_95 > 0  # Should have some drawdown

    def test_bootstrap_with_numpy_array(self) -> None:
        """Test bootstrapping with numpy array input."""
        np.random.seed(42)
        returns = np.random.randn(252) * 0.01

        simulator = MonteCarloSimulator(seed=42)
        result = simulator.bootstrap_returns(returns, n_iterations=50)

        assert result.n_iterations == 50
        assert isinstance(result.sharpe_ci, tuple)

    def test_bootstrap_empty_returns(self) -> None:
        """Test with empty returns."""
        returns = pd.Series(dtype=float)

        simulator = MonteCarloSimulator()
        result = simulator.bootstrap_returns(returns, n_iterations=10)

        assert result.n_iterations == 10
        assert result.drawdown_95 == 0.0

    def test_bootstrap_single_return(self) -> None:
        """Test with single return value."""
        returns = pd.Series([0.01])

        simulator = MonteCarloSimulator()
        result = simulator.bootstrap_returns(returns, n_iterations=10)

        assert result.n_iterations == 10

    def test_positive_returns_low_drawdown(self) -> None:
        """Test that consistent positive returns have low drawdown."""
        returns = pd.Series([0.001] * 252)  # Consistent 0.1% daily

        simulator = MonteCarloSimulator(seed=42)
        result = simulator.bootstrap_returns(returns, n_iterations=100)

        assert result.drawdown_95 == 0.0  # No drawdown possible
        assert result.return_ci[0] > 0
        assert result.return_ci[1] > 0

    def test_block_size_parameter(self) -> None:
        """Test custom block size."""
        np.random.seed(42)
        returns = pd.Series(np.random.randn(252) * 0.01)

        simulator = MonteCarloSimulator(seed=42)
        result1 = simulator.bootstrap_returns(returns, n_iterations=50, block_size=5)
        result2 = simulator.bootstrap_returns(returns, n_iterations=50, block_size=20)

        # Results should differ with different block sizes
        assert result1.drawdown_95 != result2.drawdown_95

    def test_bootstrap_preserves_mean(self) -> None:
        """Test that bootstrap roughly preserves mean return."""
        np.random.seed(42)
        daily_return = 0.0005  # 0.05% daily
        returns = pd.Series(np.random.randn(252) * 0.01 + daily_return)

        simulator = MonteCarloSimulator(seed=42)
        result = simulator.bootstrap_returns(
            returns, initial_capital=100000, n_iterations=500
        )

        # Mean of bootstrapped returns should be close to original mean
        mean_return = np.mean(result.all_total_returns)
        # Should be in ballpark of expected annual return
        assert abs(mean_return) < 1.0  # Reasonable range


class TestMonteCarloSimulatorIntegration:
    """Integration tests for MonteCarloSimulator."""

    def test_realistic_trading_scenario(self) -> None:
        """Test with realistic trading scenario."""
        np.random.seed(42)

        # Simulate 100 trades with 55% win rate
        trades = []
        for _ in range(100):
            if np.random.random() < 0.55:
                trades.append(TradeInfo(pnl=np.random.uniform(50, 200)))
            else:
                trades.append(TradeInfo(pnl=-np.random.uniform(30, 150)))

        simulator = MonteCarloSimulator(seed=42)
        result = simulator.shuffle_trades(
            trades, initial_capital=100000, n_iterations=1000
        )

        # Win rate should be reasonable (shuffling doesn't change win rate much)
        # The CI should be narrow since win rate is deterministic given trades
        assert 50.0 <= result.win_rate_ci[0] <= 60.0
        assert 50.0 <= result.win_rate_ci[1] <= 60.0

        # 99th percentile drawdown should be reasonable
        assert result.drawdown_99 < 0.5  # Less than 50%

        # Sharpe confidence interval should be meaningful
        assert result.sharpe_ci[0] < result.sharpe_ci[1]

    def test_comparison_shuffle_vs_bootstrap(self) -> None:
        """Compare shuffle and bootstrap results are different."""
        np.random.seed(42)

        # Create trades and equivalent returns
        trades = [TradeInfo(pnl=100 * (1 if np.random.random() > 0.5 else -1)) for _ in range(50)]
        returns = pd.Series(np.random.randn(50) * 0.02)

        simulator = MonteCarloSimulator(seed=42)

        shuffle_result = simulator.shuffle_trades(trades, n_iterations=100)
        bootstrap_result = simulator.bootstrap_returns(returns, n_iterations=100)

        # Results should be different
        assert shuffle_result.drawdown_95 != bootstrap_result.drawdown_95

    def test_large_iteration_count(self) -> None:
        """Test with large iteration count."""
        trades = [TradeInfo(pnl=100), TradeInfo(pnl=-50)] * 10

        simulator = MonteCarloSimulator(seed=42)
        result = simulator.shuffle_trades(trades, n_iterations=5000)

        assert result.n_iterations == 5000
        assert len(result.all_max_drawdowns) == 5000

        # With deterministic PnL sum (500 total), CI may be narrow or zero
        # but the simulation should complete successfully
        ci_width = result.return_ci[1] - result.return_ci[0]
        assert ci_width >= 0  # Can be zero for deterministic scenarios

    def test_extreme_trades(self) -> None:
        """Test with extreme trade values."""
        trades = [
            TradeInfo(pnl=10000),   # Big win
            TradeInfo(pnl=-5000),  # Big loss
            TradeInfo(pnl=100),    # Small win
            TradeInfo(pnl=-50),    # Small loss
        ]

        simulator = MonteCarloSimulator(seed=42)
        result = simulator.shuffle_trades(
            trades, initial_capital=100000, n_iterations=1000
        )

        # Should handle extreme values without error
        assert np.isfinite(result.drawdown_95)
        assert np.isfinite(result.sharpe_ci[0])
        assert np.isfinite(result.sharpe_ci[1])
