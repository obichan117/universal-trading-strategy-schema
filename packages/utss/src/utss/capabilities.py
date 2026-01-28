"""
UTSS Capabilities Export

This module exports all supported capabilities of the UTSS schema.
Used by engine implementations (like pyutss) to validate that they
implement all required features.
"""

from utss.models import (
    ArithmeticOperator,
    CalendarField,
    ChangeDirection,
    CommissionType,
    ComparisonOperator,
    CrossDirection,
    EventType,
    FundamentalMetric,
    IndicatorType,
    PortfolioField,
    PriceField,
    RebalanceMethod,
    SlippageType,
    TemporalModifier,
    TradeDirection,
)

# Schema version
SCHEMA_VERSION = "2.2.0"

# All supported indicator types
SUPPORTED_INDICATORS: list[str] = [e.value for e in IndicatorType]

# All supported fundamental metrics
SUPPORTED_FUNDAMENTALS: list[str] = [e.value for e in FundamentalMetric]

# All supported event types
SUPPORTED_EVENTS: list[str] = [e.value for e in EventType]

# All supported price fields
SUPPORTED_PRICE_FIELDS: list[str] = [e.value for e in PriceField]

# All supported calendar fields
SUPPORTED_CALENDAR_FIELDS: list[str] = [e.value for e in CalendarField]

# All supported portfolio fields
SUPPORTED_PORTFOLIO_FIELDS: list[str] = [e.value for e in PortfolioField]

# All supported comparison operators
SUPPORTED_COMPARISON_OPERATORS: list[str] = [e.value for e in ComparisonOperator]

# All supported arithmetic operators
SUPPORTED_ARITHMETIC_OPERATORS: list[str] = [e.value for e in ArithmeticOperator]

# All supported cross directions
SUPPORTED_CROSS_DIRECTIONS: list[str] = [e.value for e in CrossDirection]

# All supported temporal modifiers
SUPPORTED_TEMPORAL_MODIFIERS: list[str] = [e.value for e in TemporalModifier]

# All supported change directions
SUPPORTED_CHANGE_DIRECTIONS: list[str] = [e.value for e in ChangeDirection]

# All supported trade directions
SUPPORTED_TRADE_DIRECTIONS: list[str] = [e.value for e in TradeDirection]

# All supported rebalance methods
SUPPORTED_REBALANCE_METHODS: list[str] = [e.value for e in RebalanceMethod]

# Condition types that engines must support
SUPPORTED_CONDITION_TYPES: list[str] = [
    "comparison",
    "cross",
    "range",
    "and",
    "or",
    "not",
    "temporal",
    "sequence",
    "change",
    "always",
]

# Signal types that engines must support
SUPPORTED_SIGNAL_TYPES: list[str] = [
    "price",
    "indicator",
    "fundamental",
    "calendar",
    "event",
    "portfolio",
    "relative",
    "constant",
    "arithmetic",
    "expr",
    "external",
]

# Action types that engines must support
SUPPORTED_ACTION_TYPES: list[str] = [
    "trade",
    "rebalance",
    "alert",
    "hold",
]

# Sizing types that engines must support
SUPPORTED_SIZING_TYPES: list[str] = [
    "fixed_amount",
    "percent_of_equity",
    "percent_of_position",
    "risk_based",
    "kelly",
    "volatility_adjusted",
    "conditional",
]

# Universe types that engines must support
SUPPORTED_UNIVERSE_TYPES: list[str] = [
    "static",
    "index",
    "screener",
    "dual",
]

# Slippage model types
SUPPORTED_SLIPPAGE_TYPES: list[str] = [e.value for e in SlippageType]

# Commission model types
SUPPORTED_COMMISSION_TYPES: list[str] = [e.value for e in CommissionType]

__all__ = [
    "SCHEMA_VERSION",
    "SUPPORTED_INDICATORS",
    "SUPPORTED_FUNDAMENTALS",
    "SUPPORTED_EVENTS",
    "SUPPORTED_PRICE_FIELDS",
    "SUPPORTED_CALENDAR_FIELDS",
    "SUPPORTED_PORTFOLIO_FIELDS",
    "SUPPORTED_COMPARISON_OPERATORS",
    "SUPPORTED_ARITHMETIC_OPERATORS",
    "SUPPORTED_CROSS_DIRECTIONS",
    "SUPPORTED_TEMPORAL_MODIFIERS",
    "SUPPORTED_CHANGE_DIRECTIONS",
    "SUPPORTED_TRADE_DIRECTIONS",
    "SUPPORTED_REBALANCE_METHODS",
    "SUPPORTED_CONDITION_TYPES",
    "SUPPORTED_SIGNAL_TYPES",
    "SUPPORTED_ACTION_TYPES",
    "SUPPORTED_SIZING_TYPES",
    "SUPPORTED_UNIVERSE_TYPES",
    "SUPPORTED_SLIPPAGE_TYPES",
    "SUPPORTED_COMMISSION_TYPES",
]
