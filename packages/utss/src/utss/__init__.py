"""
Universal Trading Strategy Schema (UTSS) v1.0

A comprehensive, composable schema for expressing any trading strategy.
Follows the Signal -> Condition -> Rule -> Strategy hierarchy.

Design:
- Minimal condition types: comparison, and/or/not, expr, always
- Complex patterns via expr formulas (see patterns/ library)
- Extensible via x-extensions
"""

from utss.capabilities import (
    SCHEMA_VERSION,
    SUPPORTED_ACTION_TYPES,
    SUPPORTED_ARITHMETIC_OPERATORS,
    SUPPORTED_CALENDAR_FIELDS,
    SUPPORTED_COMPARISON_OPERATORS,
    SUPPORTED_CONDITION_TYPES,
    SUPPORTED_EVENTS,
    SUPPORTED_FUNDAMENTALS,
    SUPPORTED_INDICATORS,
    SUPPORTED_PORTFOLIO_FIELDS,
    SUPPORTED_PRICE_FIELDS,
    SUPPORTED_REBALANCE_METHODS,
    SUPPORTED_SIGNAL_TYPES,
    SUPPORTED_SIZING_TYPES,
    SUPPORTED_TRADE_DIRECTIONS,
    SUPPORTED_UNIVERSE_TYPES,
)
from utss.models import (
    Action,
    AlertAction,
    AlertChannel,
    AlertLevel,
    AlwaysCondition,
    AndCondition,
    ArithmeticOperator,
    ArithmeticSignal,
    # Info
    Author,
    CalendarField,
    CalendarSignal,
    # Conditions (minimal primitives + expr)
    ComparisonCondition,
    ComparisonOperator,
    Condition,
    ConditionalSizing,
    ConditionalSizingCase,
    ConstantSignal,
    Constraints,
    DayOfWeek,
    DualUniverse,
    DualUniverseSide,
    EventSignal,
    EventType,
    ExpressionCondition,
    ExpressionSignal,
    ExternalSignal,
    ExternalSource,
    # Sizing
    FixedAmountSizing,
    Frequency,
    FundamentalMetric,
    FundamentalSignal,
    HoldAction,
    IndexUniverse,
    # Signals
    IndicatorParams,
    IndicatorSignal,
    IndicatorType,
    Info,
    KellySizing,
    NotCondition,
    OrCondition,
    OrderType,
    # Parameters
    Parameter,
    # Parameter Reference
    ParameterReference,
    ParameterType,
    PercentEquitySizing,
    PercentPositionSizing,
    PortfolioField,
    PortfolioSignal,
    PriceField,
    PriceSignal,
    RebalanceAction,
    RebalanceMethod,
    RebalanceTarget,
    Reference,
    RelativeMeasure,
    RelativeSignal,
    RiskBasedSizing,
    # Rules
    Rule,
    # Schedule
    Schedule,
    ScreenerUniverse,
    Signal,
    Sizing,
    # Universe
    StaticUniverse,
    StockIndex,
    # Constraints
    StopConfig,
    # Strategy
    Strategy,
    # Enums
    Timeframe,
    TimeInForce,
    TimeStop,
    # Actions
    TradeAction,
    TradeDirection,
    TrailingStopConfig,
    Universe,
    Visibility,
    VolatilityAdjustedSizing,
)
from utss.validator import ValidationError, validate_strategy, validate_yaml

__version__ = "1.0.0"
__all__ = [
    # Enums
    "Timeframe",
    "Frequency",
    "DayOfWeek",
    "PriceField",
    "CalendarField",
    "PortfolioField",
    "IndicatorType",
    "FundamentalMetric",
    "EventType",
    "RelativeMeasure",
    "ArithmeticOperator",
    "ComparisonOperator",
    "TradeDirection",
    "OrderType",
    "TimeInForce",
    "RebalanceMethod",
    "AlertLevel",
    "AlertChannel",
    "ExternalSource",
    "StockIndex",
    "Visibility",
    "ParameterType",
    # Parameter Reference
    "ParameterReference",
    # Signals
    "IndicatorParams",
    "PriceSignal",
    "IndicatorSignal",
    "FundamentalSignal",
    "CalendarSignal",
    "EventSignal",
    "PortfolioSignal",
    "RelativeSignal",
    "ConstantSignal",
    "ArithmeticSignal",
    "ExpressionSignal",
    "ExternalSignal",
    "Reference",
    "Signal",
    # Conditions (minimal primitives + expr)
    "ComparisonCondition",
    "AndCondition",
    "OrCondition",
    "NotCondition",
    "ExpressionCondition",
    "AlwaysCondition",
    "Condition",
    # Sizing
    "FixedAmountSizing",
    "PercentEquitySizing",
    "PercentPositionSizing",
    "RiskBasedSizing",
    "KellySizing",
    "VolatilityAdjustedSizing",
    "ConditionalSizingCase",
    "ConditionalSizing",
    "Sizing",
    # Actions
    "TradeAction",
    "RebalanceTarget",
    "RebalanceAction",
    "AlertAction",
    "HoldAction",
    "Action",
    # Rules
    "Rule",
    # Universe
    "StaticUniverse",
    "IndexUniverse",
    "ScreenerUniverse",
    "DualUniverseSide",
    "DualUniverse",
    "Universe",
    # Constraints
    "StopConfig",
    "TrailingStopConfig",
    "TimeStop",
    "Constraints",
    # Schedule
    "Schedule",
    # Parameters
    "Parameter",
    # Info
    "Author",
    "Info",
    # Strategy
    "Strategy",
    # Validation
    "validate_strategy",
    "validate_yaml",
    "ValidationError",
    # Capabilities (for engine sync validation)
    "SCHEMA_VERSION",
    "SUPPORTED_INDICATORS",
    "SUPPORTED_FUNDAMENTALS",
    "SUPPORTED_EVENTS",
    "SUPPORTED_PRICE_FIELDS",
    "SUPPORTED_CALENDAR_FIELDS",
    "SUPPORTED_PORTFOLIO_FIELDS",
    "SUPPORTED_COMPARISON_OPERATORS",
    "SUPPORTED_ARITHMETIC_OPERATORS",
    "SUPPORTED_TRADE_DIRECTIONS",
    "SUPPORTED_REBALANCE_METHODS",
    "SUPPORTED_CONDITION_TYPES",
    "SUPPORTED_SIGNAL_TYPES",
    "SUPPORTED_ACTION_TYPES",
    "SUPPORTED_SIZING_TYPES",
    "SUPPORTED_UNIVERSE_TYPES",
]
