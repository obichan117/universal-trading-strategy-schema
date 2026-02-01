"""Portfolio backtesting module for multi-symbol strategies.

Provides portfolio-level backtesting with shared capital pool,
rebalancing, and various weight schemes.

Example:
    from pyutss.portfolio import PortfolioBacktester, PortfolioConfig

    config = PortfolioConfig(initial_capital=100000, rebalance="monthly")
    backtester = PortfolioBacktester(config)

    result = backtester.run(
        strategy=strategy,
        data={"AAPL": aapl_df, "MSFT": msft_df, "GOOGL": googl_df},
        start_date=date(2020, 1, 1),
        end_date=date(2024, 1, 1),
        weights="equal",
    )

    print(f"Portfolio return: {result.total_return_pct:.2f}%")
"""

from pyutss.portfolio.backtester import PortfolioBacktester, PortfolioConfig
from pyutss.portfolio.rebalancer import RebalanceFrequency, Rebalancer
from pyutss.portfolio.result import PortfolioResult
from pyutss.portfolio.weights import (
    WeightScheme,
    equal_weight,
    inverse_volatility,
    risk_parity,
    target_weights,
)

__all__ = [
    "PortfolioBacktester",
    "PortfolioConfig",
    "PortfolioResult",
    "Rebalancer",
    "RebalanceFrequency",
    "WeightScheme",
    "equal_weight",
    "inverse_volatility",
    "risk_parity",
    "target_weights",
]
