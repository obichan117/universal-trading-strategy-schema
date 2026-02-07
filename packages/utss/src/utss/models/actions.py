"""Action types - what to do when conditions are met."""

from typing import Annotated, Literal, Union

from pydantic import Field

from utss.models.base import BaseSchema
from utss.models.enums import (
    AlertChannel,
    AlertLevel,
    OrderType,
    TimeInForce,
    TradeDirection,
)
from utss.models.signals import Signal
from utss.models.sizing import Sizing


class TradeAction(BaseSchema):
    """Execute a trade."""

    type: Literal["trade"]
    direction: TradeDirection
    sizing: Sizing
    symbol: str | None = None
    order_type: OrderType = OrderType.MARKET
    limit_price: Signal | None = None
    stop_price: Signal | None = None
    time_in_force: TimeInForce = TimeInForce.DAY


class AlertAction(BaseSchema):
    """Send notification or log event."""

    type: Literal["alert"]
    message: str
    level: AlertLevel = AlertLevel.INFO
    channels: list[AlertChannel] = Field(default_factory=lambda: [AlertChannel.LOG])
    throttle_minutes: int | None = Field(None, ge=0)


class HoldAction(BaseSchema):
    """Explicitly do nothing."""

    type: Literal["hold"]
    reason: str | None = None


# Action discriminated union
Action = Annotated[
    Union[TradeAction, AlertAction, HoldAction],
    Field(discriminator="type"),
]
