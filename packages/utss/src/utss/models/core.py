"""Core strategy types - rules, universe, constraints, schedule, strategy."""

from typing import Annotated, Any, Literal, Union

from pydantic import ConfigDict, Field

from utss.models.actions import Action
from utss.models.base import BaseSchema, ParameterReference
from utss.models.conditions import Condition
from utss.models.enums import (
    CommissionType,
    DayOfWeek,
    Frequency,
    ParameterType,
    SlippageType,
    Timeframe,
    Visibility,
)
from utss.models.signals import Signal
from utss.models.validators import ExtensibleIndex


# =============================================================================
# RULES - Condition + Action pairs
# =============================================================================


class Rule(BaseSchema):
    """A condition-action pair."""

    name: str
    description: str | None = None
    when: Condition
    then: Action
    priority: int = 0
    enabled: bool = True


# =============================================================================
# UNIVERSE - Which assets to trade
# =============================================================================


class StaticUniverse(BaseSchema):
    """Static list of symbols."""

    type: Literal["static"]
    symbols: list[str] = Field(..., min_length=1)


class IndexUniverse(BaseSchema):
    """Index-based universe.

    .. deprecated::
        Use ``ScreenerUniverse`` with ``base`` instead.
        Example: ``{type: screener, base: SP500}``

    Supports core indices (e.g., SP500, NIKKEI225) and extensions:
    - custom:MY_WATCHLIST - User-defined symbol lists
    - etf:SPY - ETF as universe source
    - sector:TECHNOLOGY - Sector-based universes
    """

    type: Literal["index"]
    index: ExtensibleIndex
    filters: list[Condition] | None = None
    rank_by: Signal | None = None
    order: Literal["asc", "desc"] = "desc"
    limit: int | ParameterReference | None = Field(None, ge=1)
    refresh: Literal["daily", "weekly", "monthly", "quarterly", "never"] | None = None


class ScreenerUniverse(BaseSchema):
    """Screener-based universe.

    The canonical universe type for filtered/index-based universes.
    Use ``base`` to specify a starting index (e.g., SP500, NIKKEI225).
    ``filters`` is optional -- omit for unfiltered index membership.
    """

    type: Literal["screener"]
    base: str | None = None
    filters: list[Condition] | None = None
    rank_by: Signal | None = None
    order: Literal["asc", "desc"] = "desc"
    limit: int | None = Field(None, ge=1)
    refresh: Literal["daily", "weekly", "monthly", "quarterly", "never"] | None = None


# Universe discriminated union
Universe = Annotated[
    Union[StaticUniverse, IndexUniverse, ScreenerUniverse],
    Field(discriminator="type"),
]


# =============================================================================
# CONSTRAINTS - Risk and position limits
# =============================================================================


class StopConfig(BaseSchema):
    """Stop loss/take profit configuration."""

    percent: float | None = Field(None, ge=0, le=100)
    atr_multiple: float | None = Field(None, ge=0)


class TrailingStopConfig(BaseSchema):
    """Trailing stop configuration."""

    percent: float | None = Field(None, ge=0, le=100)
    atr_multiple: float | None = Field(None, ge=0)
    activation_percent: float | None = Field(None, ge=0)


class TimeStop(BaseSchema):
    """Time-based exit."""

    bars: int = Field(..., ge=1)


class Constraints(BaseSchema):
    """Risk and position constraints."""

    max_positions: int | None = Field(None, ge=1)
    min_positions: int | None = Field(None, ge=0)
    max_position_size: float | None = Field(None, ge=0, le=100)
    max_sector_exposure: float | None = Field(None, ge=0, le=100)
    max_correlation: float | None = Field(None, ge=0, le=1)
    max_drawdown: float | None = Field(None, ge=0, le=100)
    daily_loss_limit: float | None = Field(None, ge=0, le=100)
    stop_loss: StopConfig | None = None
    take_profit: StopConfig | None = None
    trailing_stop: TrailingStopConfig | None = None
    time_stop: TimeStop | None = None
    max_daily_turnover: float | None = Field(None, ge=0, le=100)
    min_holding_bars: int | None = Field(None, ge=0)
    no_shorting: bool = False
    no_leverage: bool = True


# =============================================================================
# SCHEDULE - When to evaluate
# =============================================================================


class Schedule(BaseSchema):
    """Evaluation schedule."""

    frequency: Frequency | None = None
    market_hours_only: bool = True
    timezone: str = "America/New_York"
    trading_days: list[DayOfWeek] | None = None
    evaluate_at: list[str] | None = None


# =============================================================================
# PARAMETERS - Optimizable values
# =============================================================================


class Parameter(BaseSchema):
    """Optimizable parameter definition."""

    type: ParameterType
    default: Any
    min: float | None = None
    max: float | None = None
    step: float | None = None
    choices: list[Any] | None = None
    description: str | None = None


# =============================================================================
# EXECUTION - Strategy execution assumptions
# =============================================================================


class StrategySlippageTier(BaseSchema):
    """A tier in tiered slippage model (strategy-level design assumption)."""

    up_to: float = Field(..., description="Order size threshold")
    value: float = Field(..., description="Slippage for this tier")


class SlippageModel(BaseSchema):
    """Expected slippage model.

    Slippage is a strategy design decision - the strategy author knows
    what slippage to expect based on the markets/instruments traded.
    """

    type: SlippageType
    value: float | None = Field(
        None, ge=0, description="Slippage value (percentage as decimal, e.g., 0.001 = 0.1%)"
    )
    tiers: list[StrategySlippageTier] | None = Field(
        None, description="Tiered slippage based on order size"
    )


class StrategyCommissionTier(BaseSchema):
    """A tier in tiered commission model (strategy-level design assumption)."""

    up_to: float = Field(..., description="Trade value threshold")
    value: float = Field(..., description="Commission for this tier")


class CommissionModel(BaseSchema):
    """Expected commission model.

    Commission is a strategy design decision - affects position sizing
    and profitability calculations.
    """

    type: CommissionType
    value: float | None = Field(None, ge=0, description="Commission value")
    min: float | None = Field(None, ge=0, description="Minimum commission per trade")
    max: float | None = Field(None, ge=0, description="Maximum commission per trade")
    tiers: list[StrategyCommissionTier] | None = Field(
        None, description="Tiered commission based on trade value"
    )


class Execution(BaseSchema):
    """Strategy execution assumptions.

    .. deprecated::
        The execution section in the strategy is deprecated for backtest configuration.
        Use a separate backtest config file (BacktestSpec) for execution parameters
        like commission, slippage, and lot size. The strategy's execution section
        remains as "design assumptions" for documentation purposes, but the
        BacktestSpec.execution takes precedence during backtesting.

    Defines the slippage, commission, and other execution parameters
    that the strategy was designed for. These are part of the strategy
    itself, not the backtest configuration.

    The only things external to the strategy are:
    - Data source (historical file vs real-time feed)
    - Date range (for backtest) or real-time mode
    - Actual capital amount
    """

    slippage: SlippageModel | None = None
    commission: CommissionModel | None = None
    min_capital: float | None = Field(
        None, ge=0, description="Minimum capital required for this strategy"
    )
    min_history: int | None = Field(
        None, ge=1, description="Minimum bars/days of history needed for indicator warmup"
    )
    timeframe: Timeframe | None = Field(
        None, description="Expected data timeframe for the strategy"
    )


# =============================================================================
# INFO - Strategy metadata
# =============================================================================


class Author(BaseSchema):
    """Author information."""

    id: str
    name: str


class Info(BaseSchema):
    """Strategy metadata."""

    id: str = Field(..., pattern=r"^[a-z0-9_-]+$")
    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., pattern=r"^\d+\.\d+(\.\d+)?$")
    description: str | None = Field(None, max_length=2000)
    author: Author | None = None
    tags: list[str] | None = Field(None, max_length=10)
    created_at: str | None = None
    updated_at: str | None = None
    visibility: Visibility = Visibility.PRIVATE


# =============================================================================
# STRATEGY - The complete strategy definition
# =============================================================================


class Strategy(BaseSchema):
    """Complete strategy definition."""

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        extra="allow",  # Allow x-extensions
    )

    schema_: str | None = Field(None, alias="$schema")
    info: Info
    universe: Universe
    signals: dict[str, Signal] | None = None
    conditions: dict[str, Condition] | None = None
    rules: list[Rule] = Field(..., min_length=1)
    constraints: Constraints | None = None
    schedule: Schedule | None = None
    parameters: dict[str, Parameter] | None = None
    execution: Execution | None = None
