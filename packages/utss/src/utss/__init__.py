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
    SUPPORTED_CALENDAR_FIELDS,
    SUPPORTED_COMMISSION_TYPES,
    SUPPORTED_COMPARISON_OPERATORS,
    SUPPORTED_CONDITION_TYPES,
    SUPPORTED_EVENTS,
    SUPPORTED_FUNDAMENTALS,
    SUPPORTED_INDICATORS,
    SUPPORTED_PORTFOLIO_FIELDS,
    SUPPORTED_PRICE_FIELDS,
    SUPPORTED_SIGNAL_TYPES,
    SUPPORTED_SIZING_TYPES,
    SUPPORTED_SLIPPAGE_TYPES,
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
    # Info
    Author,
    CalendarField,
    CalendarSignal,
    # Conditions (minimal primitives + expr)
    ComparisonCondition,
    ComparisonOperator,
    Condition,
    ConstantSignal,
    Constraints,
    DayOfWeek,
    EventSignal,
    EventType,
    ExpressionCondition,
    ExpressionSignal,
    ExternalSignal,
    ExternalSource,
    # Sizing
    FixedAmountSizing,
    FixedQuantitySizing,
    Frequency,
    FundamentalMetric,
    FundamentalSignal,
    HoldAction,
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
    PercentCashSizing,
    PercentEquitySizing,
    PercentPositionSizing,
    PortfolioField,
    PortfolioSignal,
    PriceField,
    PriceSignal,
    Reference,
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
from utss.backtest_models import (
    BacktestSpec,
    Benchmark,
    CommissionConfig,
    CommissionTier,
    DataConfig,
    DataSource,
    ExecutionConfig,
    FractionalConfig,
    LotSizeConfig,
    LotSizeMatch,
    LotSizeRule,
    MarginConfig,
    MetricsConfig,
    PriceLimitsConfig,
    SlippageConfig,
    SlippageTier,
)
from utss.backtest_validator import validate_backtest, validate_backtest_yaml
from utss.validator import ValidationError, validate_strategy, validate_yaml

__version__ = "1.1.0"
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
    "ComparisonOperator",
    "TradeDirection",
    "OrderType",
    "TimeInForce",
    "AlertLevel",
    "AlertChannel",
    "ExternalSource",
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
    "ConstantSignal",
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
    "FixedQuantitySizing",
    "PercentEquitySizing",
    "PercentCashSizing",
    "PercentPositionSizing",
    "RiskBasedSizing",
    "KellySizing",
    "VolatilityAdjustedSizing",
    "Sizing",
    # Actions
    "TradeAction",
    "AlertAction",
    "HoldAction",
    "Action",
    # Rules
    "Rule",
    # Universe
    "StaticUniverse",
    "ScreenerUniverse",
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
    "SUPPORTED_TRADE_DIRECTIONS",
    "SUPPORTED_CONDITION_TYPES",
    "SUPPORTED_SIGNAL_TYPES",
    "SUPPORTED_ACTION_TYPES",
    "SUPPORTED_SIZING_TYPES",
    "SUPPORTED_UNIVERSE_TYPES",
    "SUPPORTED_SLIPPAGE_TYPES",
    "SUPPORTED_COMMISSION_TYPES",
    # Backtest configuration
    "BacktestSpec",
    "Benchmark",
    "CommissionConfig",
    "CommissionTier",
    "DataConfig",
    "DataSource",
    "ExecutionConfig",
    "FractionalConfig",
    "LotSizeConfig",
    "LotSizeMatch",
    "LotSizeRule",
    "MarginConfig",
    "MetricsConfig",
    "PriceLimitsConfig",
    "SlippageConfig",
    "SlippageTier",
    "validate_backtest",
    "validate_backtest_yaml",
]
