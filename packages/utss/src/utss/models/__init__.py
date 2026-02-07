"""
Universal Trading Strategy Schema (UTSS) v1.0 - Pydantic Models

A comprehensive, composable schema for expressing any trading strategy.
Follows the Signal -> Condition -> Rule -> Strategy hierarchy.

Extensibility: Core enum values are guaranteed portable. Prefixed values
(custom:, talib:, platform:, etc.) provide extensibility for user-defined
or platform-specific features.
"""

# --- Enums ---
from utss.models.enums import (
    AlertChannel,
    AlertLevel,
    CalendarField,
    CommissionType,
    ComparisonOperator,
    DayOfWeek,
    EventType,
    ExternalSource,
    Frequency,
    FundamentalMetric,
    IndicatorType,
    OrderType,
    ParameterType,
    PortfolioField,
    PriceField,
    SlippageType,
    TimeInForce,
    Timeframe,
    TradeDirection,
    Visibility,
)

# --- Extensible Validators ---
from utss.models.validators import (
    EVENT_PREFIXES,
    FUNDAMENTAL_PREFIXES,
    INDICATOR_PREFIXES,
    ExtensibleEvent,
    ExtensibleFundamental,
    ExtensibleIndicator,
)

# --- Base ---
from utss.models.base import (
    BaseSchema,
    ParameterReference,
    Reference,
)

# --- Signals ---
from utss.models.signals import (
    CalendarSignal,
    ConstantSignal,
    EventSignal,
    ExpressionSignal,
    ExternalSignal,
    FundamentalSignal,
    IndicatorParams,
    IndicatorSignal,
    PortfolioSignal,
    PriceSignal,
    Signal,
)

# --- Conditions ---
from utss.models.conditions import (
    AlwaysCondition,
    AndCondition,
    ComparisonCondition,
    Condition,
    ExpressionCondition,
    NotCondition,
    OrCondition,
)

# --- Sizing ---
from utss.models.sizing import (
    FixedAmountSizing,
    FixedQuantitySizing,
    KellySizing,
    PercentCashSizing,
    PercentEquitySizing,
    PercentPositionSizing,
    RiskBasedSizing,
    Sizing,
    VolatilityAdjustedSizing,
)

# --- Actions ---
from utss.models.actions import (
    Action,
    AlertAction,
    HoldAction,
    TradeAction,
)

# --- Core (rules, universe, constraints, schedule, strategy) ---
from utss.models.core import (
    Author,
    CommissionModel,
    StrategyCommissionTier,
    Constraints,
    Execution,
    Info,
    Parameter,
    Rule,
    Schedule,
    ScreenerUniverse,
    SlippageModel,
    StrategySlippageTier,
    StaticUniverse,
    StopConfig,
    Strategy,
    TimeStop,
    TrailingStopConfig,
    Universe,
)

# --- Resolve forward references ---
# Must be called after all types are imported to handle recursive types
ComparisonCondition.model_rebuild()
AndCondition.model_rebuild()
OrCondition.model_rebuild()
NotCondition.model_rebuild()
ExpressionCondition.model_rebuild()
RiskBasedSizing.model_rebuild()
TradeAction.model_rebuild()
ScreenerUniverse.model_rebuild()
Strategy.model_rebuild()

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
    "SlippageType",
    "CommissionType",
    # Extensible validators
    "INDICATOR_PREFIXES",
    "FUNDAMENTAL_PREFIXES",
    "EVENT_PREFIXES",
    "ExtensibleIndicator",
    "ExtensibleFundamental",
    "ExtensibleEvent",
    # Base
    "BaseSchema",
    "ParameterReference",
    "Reference",
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
    "Signal",
    # Conditions
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
    # Execution
    "StrategySlippageTier",
    "SlippageModel",
    "StrategyCommissionTier",
    "CommissionModel",
    "Execution",
    # Info
    "Author",
    "Info",
    # Strategy
    "Strategy",
]
