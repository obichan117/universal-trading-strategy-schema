"""Signal types - produce numeric values."""

from typing import Literal, Union

from pydantic import ConfigDict, Field

from utss.models.base import BaseSchema, ParameterReference, Reference
from utss.models.enums import (
    CalendarField,
    ExternalSource,
    Frequency,
    PortfolioField,
    PriceField,
    RelativeMeasure,
    Timeframe,
)
from utss.models.validators import (
    ExtensibleEvent,
    ExtensibleFundamental,
    ExtensibleIndicator,
)


class IndicatorParams(BaseSchema):
    """Indicator parameters."""

    period: int | ParameterReference | None = Field(None, ge=1)
    fast_period: int | ParameterReference | None = Field(None, ge=1)
    slow_period: int | ParameterReference | None = Field(None, ge=1)
    signal_period: int | ParameterReference | None = Field(None, ge=1)
    std_dev: float | ParameterReference | None = Field(None, ge=0)
    source: Literal["open", "high", "low", "close", "hl2", "hlc3", "ohlc4"] | None = (
        None
    )

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        extra="allow",  # Allow additional indicator-specific params
    )


class PriceSignal(BaseSchema):
    """Raw price data signal."""

    type: Literal["price"]
    field: PriceField
    offset: int = 0
    timeframe: Timeframe | None = None
    symbol: str | None = None


class IndicatorSignal(BaseSchema):
    """Technical indicator signal.

    Supports core indicators (e.g., RSI, SMA) and extensions:
    - custom:MY_INDICATOR - User-defined indicators
    - talib:CDLHAMMER - TA-Lib indicators
    - platform:tradingview:SQUEEZE - Platform-specific
    """

    type: Literal["indicator"]
    indicator: ExtensibleIndicator
    params: IndicatorParams | None = None
    offset: int = 0
    timeframe: Timeframe | None = None
    symbol: str | None = None


class FundamentalSignal(BaseSchema):
    """Fundamental data signal.

    Supports core metrics (e.g., PE_RATIO) and extensions:
    - custom:MY_METRIC - User-defined metrics
    - provider:bloomberg:WACC - Provider-specific metrics
    """

    type: Literal["fundamental"]
    metric: ExtensibleFundamental
    symbol: str | None = None


class CalendarSignal(BaseSchema):
    """Calendar/date pattern signal."""

    type: Literal["calendar"]
    field: CalendarField


class EventSignal(BaseSchema):
    """Event-driven signal.

    Supports core events (e.g., EARNINGS_RELEASE) and extensions:
    - custom:MY_EVENT - User-defined events
    - calendar:FOMC_DECISION - Economic calendar events
    """

    type: Literal["event"]
    event: ExtensibleEvent
    days_before: int | None = Field(None, ge=0)
    days_after: int | None = Field(None, ge=0)


class PortfolioSignal(BaseSchema):
    """Portfolio and position state signal."""

    type: Literal["portfolio"]
    field: PortfolioField
    symbol: str | None = None


class ConstantSignal(BaseSchema):
    """A constant numeric value."""

    type: Literal["constant"]
    value: float | ParameterReference


# Forward references for recursive types
class RelativeSignal(BaseSchema):
    """Signal relative to a benchmark."""

    type: Literal["relative"]
    signal: "Signal"
    benchmark: str
    measure: RelativeMeasure
    lookback: int | None = Field(None, ge=1)


class ExpressionSignal(BaseSchema):
    """Custom formula expression signal."""

    type: Literal["expr"]
    formula: str


class ExternalSignal(BaseSchema):
    """Runtime-resolved external signal."""

    type: Literal["external"]
    source: ExternalSource
    url: str | None = None
    path: str | None = None
    provider: str | None = None
    refresh: Frequency | None = None
    default: float | None = None


# Signal union (no discriminator due to Reference and ParameterReference not having type field)
Signal = Union[
    PriceSignal,
    IndicatorSignal,
    FundamentalSignal,
    CalendarSignal,
    EventSignal,
    PortfolioSignal,
    RelativeSignal,
    ConstantSignal,
    ExpressionSignal,
    ExternalSignal,
    Reference,
    ParameterReference,
]
