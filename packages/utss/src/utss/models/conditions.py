"""Condition types - produce boolean values."""

from typing import Literal, Union

from pydantic import Field

from utss.models.base import BaseSchema, Reference
from utss.models.enums import ComparisonOperator
from utss.models.signals import Signal


class ComparisonCondition(BaseSchema):
    """Compare a signal to a value or another signal."""

    type: Literal["comparison"]
    left: Signal
    operator: ComparisonOperator
    right: Signal


class AndCondition(BaseSchema):
    """All conditions must be true."""

    type: Literal["and"]
    conditions: list["Condition"] = Field(..., min_length=2)


class OrCondition(BaseSchema):
    """Any condition must be true."""

    type: Literal["or"]
    conditions: list["Condition"] = Field(..., min_length=2)


class NotCondition(BaseSchema):
    """Negate a condition."""

    type: Literal["not"]
    condition: "Condition"


class ExpressionCondition(BaseSchema):
    """Boolean expression for complex patterns.

    Use for crossovers, ranges, temporal conditions, sequences, etc.
    See patterns/ directory for reusable pattern formulas.

    Examples:
        - Cross above: "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"
        - Range: "RSI(14) > 20 and RSI(14) < 80"
        - Temporal: "all(RSI(14) < 30, bars=3)"
    """

    type: Literal["expr"]
    formula: str


class AlwaysCondition(BaseSchema):
    """Always true (for scheduled actions)."""

    type: Literal["always"]


# Condition union - minimal primitives + expr escape hatch
# Use primitives (comparison, and/or/not) for simple cases, expr for complex patterns
Condition = Union[
    ComparisonCondition,
    AndCondition,
    OrCondition,
    NotCondition,
    ExpressionCondition,
    AlwaysCondition,
    Reference,
]
