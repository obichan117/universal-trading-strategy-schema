"""
Universal Trading Strategy Schema (UTSS) v2 - Pydantic Models

A comprehensive, composable schema for expressing any trading strategy.
Follows the Signal -> Condition -> Rule -> Strategy hierarchy.
"""

from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# ENUMS
# =============================================================================


class Timeframe(str, Enum):
    """Trading timeframes."""

    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class DayOfWeek(str, Enum):
    """Days of the week."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"


class PriceField(str, Enum):
    """Price data fields."""

    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    VOLUME = "volume"
    VWAP = "vwap"


class IndicatorType(str, Enum):
    """Technical indicator types."""

    # Moving Averages
    SMA = "SMA"
    EMA = "EMA"
    WMA = "WMA"
    DEMA = "DEMA"
    TEMA = "TEMA"
    # Momentum
    RSI = "RSI"
    MACD = "MACD"
    MACD_SIGNAL = "MACD_SIGNAL"
    MACD_HIST = "MACD_HIST"
    STOCH_K = "STOCH_K"
    STOCH_D = "STOCH_D"
    STOCH_RSI = "STOCH_RSI"
    # Volatility
    BB_UPPER = "BB_UPPER"
    BB_MIDDLE = "BB_MIDDLE"
    BB_LOWER = "BB_LOWER"
    BB_WIDTH = "BB_WIDTH"
    BB_PERCENT = "BB_PERCENT"
    ATR = "ATR"
    ADX = "ADX"
    PLUS_DI = "PLUS_DI"
    MINUS_DI = "MINUS_DI"
    # Volume & Other
    CCI = "CCI"
    MFI = "MFI"
    OBV = "OBV"
    VWAP = "VWAP"
    SUPERTREND = "SUPERTREND"
    ICHIMOKU_TENKAN = "ICHIMOKU_TENKAN"
    ICHIMOKU_KIJUN = "ICHIMOKU_KIJUN"
    ICHIMOKU_SENKOU_A = "ICHIMOKU_SENKOU_A"
    ICHIMOKU_SENKOU_B = "ICHIMOKU_SENKOU_B"


class FundamentalMetric(str, Enum):
    """Fundamental data metrics."""

    # Valuation
    PE_RATIO = "PE_RATIO"
    PB_RATIO = "PB_RATIO"
    PS_RATIO = "PS_RATIO"
    PEG_RATIO = "PEG_RATIO"
    EV_EBITDA = "EV_EBITDA"
    # Profitability
    ROE = "ROE"
    ROA = "ROA"
    ROIC = "ROIC"
    PROFIT_MARGIN = "PROFIT_MARGIN"
    OPERATING_MARGIN = "OPERATING_MARGIN"
    NET_MARGIN = "NET_MARGIN"
    # Dividend
    DIVIDEND_YIELD = "DIVIDEND_YIELD"
    PAYOUT_RATIO = "PAYOUT_RATIO"
    # Size & Growth
    MARKET_CAP = "MARKET_CAP"
    ENTERPRISE_VALUE = "ENTERPRISE_VALUE"
    REVENUE = "REVENUE"
    EBITDA = "EBITDA"
    NET_INCOME = "NET_INCOME"
    DEBT_TO_EQUITY = "DEBT_TO_EQUITY"
    CURRENT_RATIO = "CURRENT_RATIO"
    QUICK_RATIO = "QUICK_RATIO"
    EPS = "EPS"
    EPS_GROWTH = "EPS_GROWTH"
    REVENUE_GROWTH = "REVENUE_GROWTH"


class EventType(str, Enum):
    """Market event types."""

    EARNINGS_RELEASE = "EARNINGS_RELEASE"
    DIVIDEND_EX_DATE = "DIVIDEND_EX_DATE"
    DIVIDEND_PAY_DATE = "DIVIDEND_PAY_DATE"
    STOCK_SPLIT = "STOCK_SPLIT"
    IPO = "IPO"
    DELISTING = "DELISTING"
    FDA_APPROVAL = "FDA_APPROVAL"
    PRODUCT_LAUNCH = "PRODUCT_LAUNCH"
    INDEX_ADD = "INDEX_ADD"
    INDEX_REMOVE = "INDEX_REMOVE"
    INSIDER_BUY = "INSIDER_BUY"
    INSIDER_SELL = "INSIDER_SELL"
    ANALYST_UPGRADE = "ANALYST_UPGRADE"
    ANALYST_DOWNGRADE = "ANALYST_DOWNGRADE"


class RelativeMeasure(str, Enum):
    """Relative comparison measures."""

    RATIO = "ratio"
    DIFFERENCE = "difference"
    BETA = "beta"
    CORRELATION = "correlation"
    PERCENTILE = "percentile"
    Z_SCORE = "z_score"


class ArithmeticOperator(str, Enum):
    """Arithmetic operators."""

    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    MIN = "min"
    MAX = "max"
    AVG = "avg"


class ComparisonOperator(str, Enum):
    """Comparison operators."""

    LT = "<"
    LTE = "<="
    EQ = "="
    GTE = ">="
    GT = ">"
    NE = "!="


class CrossDirection(str, Enum):
    """Cross direction."""

    ABOVE = "above"
    BELOW = "below"


class TemporalModifier(str, Enum):
    """Temporal condition modifiers."""

    FOR_BARS = "for_bars"
    WITHIN_BARS = "within_bars"
    SINCE_BARS = "since_bars"
    FIRST_TIME = "first_time"
    NTH_TIME = "nth_time"


class TradeDirection(str, Enum):
    """Trade directions."""

    BUY = "buy"
    SELL = "sell"
    SHORT = "short"
    COVER = "cover"


class OrderType(str, Enum):
    """Order types."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class TimeInForce(str, Enum):
    """Time in force options."""

    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


class StockIndex(str, Enum):
    """Stock indices."""

    # US
    SP500 = "SP500"
    NASDAQ100 = "NASDAQ100"
    DOW30 = "DOW30"
    RUSSELL2000 = "RUSSELL2000"
    RUSSELL1000 = "RUSSELL1000"
    # Japan
    NIKKEI225 = "NIKKEI225"
    TOPIX = "TOPIX"
    TOPIX100 = "TOPIX100"
    TOPIX500 = "TOPIX500"
    JPXNIKKEI400 = "JPXNIKKEI400"


class Visibility(str, Enum):
    """Strategy visibility."""

    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


# =============================================================================
# BASE SCHEMA
# =============================================================================


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        extra="forbid",
    )


# =============================================================================
# SIGNALS - Produce numeric values
# =============================================================================


class IndicatorParams(BaseSchema):
    """Indicator parameters."""

    period: int | None = Field(None, ge=1)
    fast_period: int | None = Field(None, ge=1)
    slow_period: int | None = Field(None, ge=1)
    signal_period: int | None = Field(None, ge=1)
    std_dev: float | None = Field(None, ge=0)
    source: Literal["open", "high", "low", "close", "hl2", "hlc3", "ohlc4"] | None = None


class PriceSignal(BaseSchema):
    """Raw price data signal."""

    type: Literal["price"]
    field: PriceField
    offset: int = 0
    timeframe: Timeframe | None = None


class IndicatorSignal(BaseSchema):
    """Technical indicator signal."""

    type: Literal["indicator"]
    indicator: IndicatorType
    params: IndicatorParams | None = None
    offset: int = 0
    timeframe: Timeframe | None = None


class FundamentalSignal(BaseSchema):
    """Fundamental data signal."""

    type: Literal["fundamental"]
    metric: FundamentalMetric


class CalendarSignal(BaseSchema):
    """Calendar/date pattern signal."""

    type: Literal["calendar"]
    day_of_week: DayOfWeek | None = None
    day_of_month: int | None = Field(None, ge=-31, le=31)
    week_of_month: int | None = Field(None, ge=-5, le=5)
    month: int | None = Field(None, ge=1, le=12)
    price: Literal["open", "close"] = "close"


class EventSignal(BaseSchema):
    """Event-driven signal."""

    type: Literal["event"]
    event: EventType
    days_before: int | None = Field(None, ge=0)
    days_after: int | None = Field(None, ge=0)


class ConstantSignal(BaseSchema):
    """A constant numeric value."""

    type: Literal["constant"]
    value: float


class Reference(BaseSchema):
    """Reference to a reusable component."""

    ref: str = Field(..., alias="$ref")


# Forward references for recursive types
class RelativeSignal(BaseSchema):
    """Signal relative to a benchmark."""

    type: Literal["relative"]
    signal: "Signal"
    benchmark: str
    measure: RelativeMeasure
    lookback: int | None = Field(None, ge=1)


class ArithmeticSignal(BaseSchema):
    """Arithmetic operation on signals."""

    type: Literal["arithmetic"]
    operator: ArithmeticOperator
    operands: list["Signal"] = Field(..., min_length=2)


# Signal discriminated union
Signal = Annotated[
    Union[
        PriceSignal,
        IndicatorSignal,
        FundamentalSignal,
        CalendarSignal,
        EventSignal,
        RelativeSignal,
        ConstantSignal,
        ArithmeticSignal,
        Reference,
    ],
    Field(discriminator="type"),
]


# =============================================================================
# CONDITIONS - Produce boolean values
# =============================================================================


class ComparisonCondition(BaseSchema):
    """Compare a signal to a value or another signal."""

    type: Literal["comparison"]
    left: Signal
    operator: ComparisonOperator
    right: Signal


class CrossCondition(BaseSchema):
    """Detect when one signal crosses another."""

    type: Literal["cross"]
    signal: Signal
    threshold: Signal
    direction: CrossDirection


class RangeCondition(BaseSchema):
    """Check if signal is within a range."""

    type: Literal["range"]
    signal: Signal
    min: Signal
    max: Signal
    inclusive: bool = True


class NotCondition(BaseSchema):
    """Negate a condition."""

    type: Literal["not"]
    condition: "Condition"


class AndCondition(BaseSchema):
    """All conditions must be true."""

    type: Literal["and"]
    conditions: list["Condition"] = Field(..., min_length=2)


class OrCondition(BaseSchema):
    """Any condition must be true."""

    type: Literal["or"]
    conditions: list["Condition"] = Field(..., min_length=2)


class TemporalCondition(BaseSchema):
    """Time-based condition modifiers."""

    type: Literal["temporal"]
    condition: "Condition"
    modifier: TemporalModifier
    bars: int | None = Field(None, ge=1)
    n: int | None = Field(None, ge=1)


# Condition discriminated union
Condition = Annotated[
    Union[
        ComparisonCondition,
        CrossCondition,
        RangeCondition,
        AndCondition,
        OrCondition,
        NotCondition,
        TemporalCondition,
        Reference,
    ],
    Field(discriminator="type"),
]


# =============================================================================
# SIZING - How to size positions
# =============================================================================


class FixedAmountSizing(BaseSchema):
    """Fixed dollar amount sizing."""

    type: Literal["fixed_amount"]
    amount: float = Field(..., ge=0)
    currency: str = "USD"


class PercentEquitySizing(BaseSchema):
    """Percent of portfolio equity."""

    type: Literal["percent_of_equity"]
    percent: float = Field(..., ge=0, le=100)


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
        PercentEquitySizing,
        PercentPositionSizing,
        RiskBasedSizing,
        KellySizing,
        VolatilityAdjustedSizing,
    ],
    Field(discriminator="type"),
]


# =============================================================================
# ACTIONS - What to do when conditions are met
# =============================================================================


class TradeAction(BaseSchema):
    """Execute a trade."""

    type: Literal["trade"]
    direction: TradeDirection
    sizing: Sizing
    order_type: OrderType = OrderType.MARKET
    limit_price: Signal | None = None
    stop_price: Signal | None = None
    time_in_force: TimeInForce = TimeInForce.DAY


class RebalanceTarget(BaseSchema):
    """Target weight for rebalancing."""

    symbol: str
    weight: float = Field(..., ge=0, le=1)


class RebalanceAction(BaseSchema):
    """Rebalance to target weights."""

    type: Literal["rebalance"]
    targets: list[RebalanceTarget]
    threshold: float = 0.05


class HoldAction(BaseSchema):
    """Explicitly do nothing."""

    type: Literal["hold"]
    reason: str | None = None


# Action discriminated union
Action = Annotated[
    Union[TradeAction, RebalanceAction, HoldAction],
    Field(discriminator="type"),
]


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
    """Index-based universe."""

    type: Literal["index"]
    index: StockIndex
    filters: list[Condition] | None = None


class ScreenerUniverse(BaseSchema):
    """Screener-based universe."""

    type: Literal["screener"]
    base: str | None = None
    filters: list[Condition] = Field(..., min_length=1)
    limit: int | None = Field(None, ge=1)
    sort_by: Signal | None = None
    sort_order: Literal["asc", "desc"] = "desc"


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


class Constraints(BaseSchema):
    """Risk and position constraints."""

    max_positions: int | None = Field(None, ge=1)
    max_position_size: float | None = Field(None, ge=0, le=100)
    max_sector_exposure: float | None = Field(None, ge=0, le=100)
    max_drawdown: float | None = Field(None, ge=0, le=100)
    daily_loss_limit: float | None = Field(None, ge=0, le=100)
    stop_loss: StopConfig | None = None
    take_profit: StopConfig | None = None
    trailing_stop: StopConfig | None = None
    no_shorting: bool = False
    no_leverage: bool = True


# =============================================================================
# SCHEDULE - When to evaluate
# =============================================================================


class Schedule(BaseSchema):
    """Evaluation schedule."""

    frequency: Timeframe | Literal["tick"] | None = None
    market_hours_only: bool = True
    timezone: str = "America/New_York"
    trading_days: list[DayOfWeek] | None = None


# =============================================================================
# COMPONENTS - Reusable named components
# =============================================================================


class Components(BaseSchema):
    """Reusable named components."""

    signals: dict[str, Signal] | None = None
    conditions: dict[str, Condition] | None = None
    actions: dict[str, Action] | None = None


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

    schema_: str | None = Field(None, alias="$schema")
    info: Info
    universe: Universe
    rules: list[Rule] = Field(..., min_length=1)
    constraints: Constraints | None = None
    schedule: Schedule | None = None
    components: Components | None = None


# Update forward references
RelativeSignal.model_rebuild()
ArithmeticSignal.model_rebuild()
ComparisonCondition.model_rebuild()
CrossCondition.model_rebuild()
RangeCondition.model_rebuild()
AndCondition.model_rebuild()
OrCondition.model_rebuild()
NotCondition.model_rebuild()
TemporalCondition.model_rebuild()
RiskBasedSizing.model_rebuild()
TradeAction.model_rebuild()
IndexUniverse.model_rebuild()
ScreenerUniverse.model_rebuild()
Components.model_rebuild()
Strategy.model_rebuild()
