"""Sizing types - how to size positions."""

from typing import Annotated, Literal, Union

from pydantic import Field

from utss.models.base import BaseSchema, ParameterReference
from utss.models.signals import Signal


class FixedAmountSizing(BaseSchema):
    """Fixed dollar amount sizing."""

    type: Literal["fixed_amount"]
    amount: float = Field(..., ge=0)
    currency: str = "USD"


class FixedQuantitySizing(BaseSchema):
    """Fixed number of shares/contracts."""

    type: Literal["fixed_quantity"]
    quantity: float | ParameterReference = Field(..., ge=0)


class PercentEquitySizing(BaseSchema):
    """Percent of portfolio equity."""

    type: Literal["percent_of_equity"]
    percent: float | ParameterReference = Field(..., ge=0, le=100)


class PercentCashSizing(BaseSchema):
    """Percent of available cash."""

    type: Literal["percent_of_cash"]
    percent: float | ParameterReference = Field(..., ge=0, le=100)


class PercentPositionSizing(BaseSchema):
    """Percent of existing position."""

    type: Literal["percent_of_position"]
    percent: float = Field(..., ge=0, le=100)


class RiskBasedSizing(BaseSchema):
    """Size based on risk percent and stop distance."""

    type: Literal["risk_based"]
    risk_percent: float = Field(..., ge=0, le=100)
    stop_distance: Signal


class KellySizing(BaseSchema):
    """Kelly criterion sizing."""

    type: Literal["kelly"]
    fraction: float = Field(0.5, ge=0, le=1)
    lookback: int = 100


class VolatilityAdjustedSizing(BaseSchema):
    """Size based on target volatility."""

    type: Literal["volatility_adjusted"]
    target_volatility: float = Field(..., ge=0)
    lookback: int = 20


# Sizing discriminated union
Sizing = Annotated[
    Union[
        FixedAmountSizing,
        FixedQuantitySizing,
        PercentEquitySizing,
        PercentCashSizing,
        PercentPositionSizing,
        RiskBasedSizing,
        KellySizing,
        VolatilityAdjustedSizing,
    ],
    Field(discriminator="type"),
]
