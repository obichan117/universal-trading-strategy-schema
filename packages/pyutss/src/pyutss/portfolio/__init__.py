"""Portfolio module for weight schemes, rebalancing, and results.

Use :class:`pyutss.Engine` for multi-symbol portfolio backtesting.

Example:
    from pyutss import Engine

    engine = Engine(initial_capital=100000)
    result = engine.backtest(
        strategy,
        data={"AAPL": aapl_df, "MSFT": msft_df},
        weights="equal",
    )
"""

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
    "PortfolioResult",
    "Rebalancer",
    "RebalanceFrequency",
    "WeightScheme",
    "equal_weight",
    "inverse_volatility",
    "risk_parity",
    "target_weights",
]
