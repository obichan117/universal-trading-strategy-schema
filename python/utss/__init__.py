"""
Universal Trading Strategy Schema (UTSS) v2

A comprehensive, composable schema for expressing any trading strategy.
Follows the Signal -> Condition -> Rule -> Strategy hierarchy.
"""

from utss.models import (
    # Enums
    Timeframe,
    DayOfWeek,
    PriceField,
    IndicatorType,
    FundamentalMetric,
    EventType,
    RelativeMeasure,
    ArithmeticOperator,
    ComparisonOperator,
    CrossDirection,
    TemporalModifier,
    TradeDirection,
    OrderType,
    TimeInForce,
    StockIndex,
    Visibility,
    # Signals
    IndicatorParams,
    PriceSignal,
    IndicatorSignal,
    FundamentalSignal,
    CalendarSignal,
    EventSignal,
    RelativeSignal,
    ConstantSignal,
    ArithmeticSignal,
    Reference,
    Signal,
    # Conditions
    ComparisonCondition,
    CrossCondition,
    RangeCondition,
    AndCondition,
    OrCondition,
    NotCondition,
    TemporalCondition,
    Condition,
    # Sizing
    FixedAmountSizing,
    PercentEquitySizing,
    PercentPositionSizing,
    RiskBasedSizing,
    KellySizing,
    VolatilityAdjustedSizing,
    Sizing,
    # Actions
    TradeAction,
    RebalanceTarget,
    RebalanceAction,
    HoldAction,
    Action,
    # Rules
    Rule,
    # Universe
    StaticUniverse,
    IndexUniverse,
    ScreenerUniverse,
    Universe,
    # Constraints
    StopConfig,
    Constraints,
    # Schedule
    Schedule,
    # Components
    Components,
    # Info
    Author,
    Info,
    # Strategy
    Strategy,
)
from utss.validator import validate_strategy, validate_yaml, ValidationError

__version__ = "2.0.0"
__all__ = [
    # Enums
    "Timeframe",
    "DayOfWeek",
    "PriceField",
    "IndicatorType",
    "FundamentalMetric",
    "EventType",
    "RelativeMeasure",
    "ArithmeticOperator",
    "ComparisonOperator",
    "CrossDirection",
    "TemporalModifier",
    "TradeDirection",
    "OrderType",
    "TimeInForce",
    "StockIndex",
    "Visibility",
    # Signals
    "IndicatorParams",
    "PriceSignal",
    "IndicatorSignal",
    "FundamentalSignal",
    "CalendarSignal",
    "EventSignal",
    "RelativeSignal",
    "ConstantSignal",
    "ArithmeticSignal",
    "Reference",
    "Signal",
    # Conditions
    "ComparisonCondition",
    "CrossCondition",
    "RangeCondition",
    "AndCondition",
    "OrCondition",
    "NotCondition",
    "TemporalCondition",
    "Condition",
    # Sizing
    "FixedAmountSizing",
    "PercentEquitySizing",
    "PercentPositionSizing",
    "RiskBasedSizing",
    "KellySizing",
    "VolatilityAdjustedSizing",
    "Sizing",
    # Actions
    "TradeAction",
    "RebalanceTarget",
    "RebalanceAction",
    "HoldAction",
    "Action",
    # Rules
    "Rule",
    # Universe
    "StaticUniverse",
    "IndexUniverse",
    "ScreenerUniverse",
    "Universe",
    # Constraints
    "StopConfig",
    "Constraints",
    # Schedule
    "Schedule",
    # Components
    "Components",
    # Info
    "Author",
    "Info",
    # Strategy
    "Strategy",
    # Validation
    "validate_strategy",
    "validate_yaml",
    "ValidationError",
]
