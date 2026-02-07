"""Evaluation context and error types."""

from dataclasses import dataclass
from typing import Any

import pandas as pd


class EvaluationError(Exception):
    """Error during signal/condition evaluation."""

    pass


@dataclass
class EvaluationPortfolioState:
    """Current portfolio state for signal evaluation.

    Updated by the backtest engine on each bar.
    This is the evaluator's view of portfolio state, distinct from
    the engine's PortfolioManager which tracks actual positions.
    """

    cash: float = 0.0
    equity: float = 0.0
    positions: dict[str, Any] = None  # symbol -> Position
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

    def __post_init__(self):
        if self.positions is None:
            self.positions = {}


# Backward compatibility alias
PortfolioState = EvaluationPortfolioState


@dataclass
class EvaluationContext:
    """Context for evaluating signals and conditions.

    Contains all data needed to evaluate signals, including
    primary and optional secondary timeframe data, and portfolio state.
    """

    primary_data: pd.DataFrame
    secondary_data: pd.DataFrame | None = None
    signal_library: dict[str, Any] | None = None
    condition_library: dict[str, Any] | None = None
    parameters: dict[str, float] | None = None
    portfolio_state: PortfolioState | None = None
    current_bar_idx: int = 0  # Current bar index for portfolio lookups
    fundamental_data: dict[str, Any] | None = None  # {symbol: FundamentalMetrics}
    external_data: dict[str, pd.Series] | None = None  # {key: Series}
    event_data: dict[str, list] | None = None  # {"EARNINGS_RELEASE": [date1, ...]}

    def get_data(self, timeframe: str | None = None) -> pd.DataFrame:
        """Get data for specified timeframe."""
        if timeframe is None or self.secondary_data is None:
            return self.primary_data
        return self.secondary_data
