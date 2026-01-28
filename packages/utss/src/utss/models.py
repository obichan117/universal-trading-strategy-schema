"""
Universal Trading Strategy Schema (UTSS) v1.0 - Pydantic Models

A comprehensive, composable schema for expressing any trading strategy.
Follows the Signal -> Condition -> Rule -> Strategy hierarchy.

Extensibility: Core enum values are guaranteed portable. Prefixed values
(custom:, talib:, platform:, etc.) provide extensibility for user-defined
or platform-specific features.
"""

import re
from enum import Enum
from typing import Annotated, Any, Literal, Union

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

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


class Frequency(str, Enum):
    """Evaluation frequency (includes tick)."""

    TICK = "tick"
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


class CalendarField(str, Enum):
    """Calendar signal fields."""

    DAY_OF_WEEK = "day_of_week"
    DAY_OF_MONTH = "day_of_month"
    WEEK_OF_MONTH = "week_of_month"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    IS_MONTH_START = "is_month_start"
    IS_MONTH_END = "is_month_end"
    IS_QUARTER_START = "is_quarter_start"
    IS_QUARTER_END = "is_quarter_end"
    IS_YEAR_START = "is_year_start"
    IS_YEAR_END = "is_year_end"


class PortfolioField(str, Enum):
    """Portfolio signal fields."""

    POSITION_QTY = "position_qty"
    POSITION_VALUE = "position_value"
    POSITION_SIDE = "position_side"
    AVG_ENTRY_PRICE = "avg_entry_price"
    UNREALIZED_PNL = "unrealized_pnl"
    UNREALIZED_PNL_PCT = "unrealized_pnl_pct"
    REALIZED_PNL = "realized_pnl"
    DAYS_IN_POSITION = "days_in_position"
    BARS_IN_POSITION = "bars_in_position"
    EQUITY = "equity"
    CASH = "cash"
    BUYING_POWER = "buying_power"
    MARGIN_USED = "margin_used"
    DAILY_PNL = "daily_pnl"
    DAILY_PNL_PCT = "daily_pnl_pct"


class IndicatorType(str, Enum):
    """Technical indicator types."""

    # Moving Averages
    SMA = "SMA"
    EMA = "EMA"
    WMA = "WMA"
    DEMA = "DEMA"
    TEMA = "TEMA"
    KAMA = "KAMA"
    HULL = "HULL"
    VWMA = "VWMA"
    # Momentum
    RSI = "RSI"
    MACD = "MACD"
    MACD_SIGNAL = "MACD_SIGNAL"
    MACD_HIST = "MACD_HIST"
    STOCH_K = "STOCH_K"
    STOCH_D = "STOCH_D"
    STOCH_RSI = "STOCH_RSI"
    ROC = "ROC"
    MOMENTUM = "MOMENTUM"
    WILLIAMS_R = "WILLIAMS_R"
    CCI = "CCI"
    MFI = "MFI"
    CMO = "CMO"
    TSI = "TSI"
    # Trend
    ADX = "ADX"
    PLUS_DI = "PLUS_DI"
    MINUS_DI = "MINUS_DI"
    AROON_UP = "AROON_UP"
    AROON_DOWN = "AROON_DOWN"
    AROON_OSC = "AROON_OSC"
    SUPERTREND = "SUPERTREND"
    PSAR = "PSAR"
    # Volatility
    ATR = "ATR"
    STDDEV = "STDDEV"
    VARIANCE = "VARIANCE"
    BB_UPPER = "BB_UPPER"
    BB_MIDDLE = "BB_MIDDLE"
    BB_LOWER = "BB_LOWER"
    BB_WIDTH = "BB_WIDTH"
    BB_PERCENT = "BB_PERCENT"
    KC_UPPER = "KC_UPPER"
    KC_MIDDLE = "KC_MIDDLE"
    KC_LOWER = "KC_LOWER"
    DC_UPPER = "DC_UPPER"
    DC_MIDDLE = "DC_MIDDLE"
    DC_LOWER = "DC_LOWER"
    # Volume
    OBV = "OBV"
    VWAP = "VWAP"
    AD = "AD"
    CMF = "CMF"
    KLINGER = "KLINGER"
    # Statistical
    HIGHEST = "HIGHEST"
    LOWEST = "LOWEST"
    RETURN = "RETURN"
    DRAWDOWN = "DRAWDOWN"
    ZSCORE = "ZSCORE"
    PERCENTILE = "PERCENTILE"
    RANK = "RANK"
    CORRELATION = "CORRELATION"
    BETA = "BETA"
    # Ichimoku
    ICHIMOKU_TENKAN = "ICHIMOKU_TENKAN"
    ICHIMOKU_KIJUN = "ICHIMOKU_KIJUN"
    ICHIMOKU_SENKOU_A = "ICHIMOKU_SENKOU_A"
    ICHIMOKU_SENKOU_B = "ICHIMOKU_SENKOU_B"
    ICHIMOKU_CHIKOU = "ICHIMOKU_CHIKOU"


class FundamentalMetric(str, Enum):
    """Fundamental data metrics."""

    # Valuation
    PE_RATIO = "PE_RATIO"
    PB_RATIO = "PB_RATIO"
    PS_RATIO = "PS_RATIO"
    PEG_RATIO = "PEG_RATIO"
    EV_EBITDA = "EV_EBITDA"
    EARNINGS_YIELD = "EARNINGS_YIELD"
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
    # Size & Financials
    MARKET_CAP = "MARKET_CAP"
    ENTERPRISE_VALUE = "ENTERPRISE_VALUE"
    REVENUE = "REVENUE"
    EBITDA = "EBITDA"
    NET_INCOME = "NET_INCOME"
    EPS = "EPS"
    EPS_GROWTH = "EPS_GROWTH"
    REVENUE_GROWTH = "REVENUE_GROWTH"
    # Solvency
    DEBT_TO_EQUITY = "DEBT_TO_EQUITY"
    CURRENT_RATIO = "CURRENT_RATIO"
    QUICK_RATIO = "QUICK_RATIO"
    INTEREST_COVERAGE = "INTEREST_COVERAGE"
    # Quality Scores
    F_SCORE = "F_SCORE"
    ALTMAN_Z = "ALTMAN_Z"
    # Market Data
    INDEX_WEIGHT = "INDEX_WEIGHT"
    FREE_FLOAT = "FREE_FLOAT"
    SHORT_INTEREST = "SHORT_INTEREST"
    ANALYST_RATING = "ANALYST_RATING"
    PRICE_TARGET = "PRICE_TARGET"
    EARNINGS_SURPRISE = "EARNINGS_SURPRISE"


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
    SEC_FILING_10K = "SEC_FILING_10K"
    SEC_FILING_10Q = "SEC_FILING_10Q"
    SEC_FILING_8K = "SEC_FILING_8K"


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
    ABS = "abs"
    POW = "pow"


class ComparisonOperator(str, Enum):
    """Comparison operators."""

    LT = "<"
    LTE = "<="
    EQ = "="
    GTE = ">="
    GT = ">"
    NE = "!="


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


class RebalanceMethod(str, Enum):
    """Rebalance methods."""

    EQUAL_WEIGHT = "equal_weight"
    MARKET_CAP_WEIGHT = "market_cap_weight"
    RISK_PARITY = "risk_parity"
    INVERSE_VOLATILITY = "inverse_volatility"
    TARGET_WEIGHTS = "target_weights"


class AlertLevel(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    """Alert notification channels."""

    LOG = "log"
    WEBHOOK = "webhook"
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"


class ExternalSource(str, Enum):
    """External signal sources."""

    WEBHOOK = "webhook"
    FILE = "file"
    PROVIDER = "provider"


class StockIndex(str, Enum):
    """Stock indices."""

    # Japan
    NIKKEI225 = "NIKKEI225"
    TOPIX = "TOPIX"
    TOPIX100 = "TOPIX100"
    TOPIX500 = "TOPIX500"
    JPXNIKKEI400 = "JPXNIKKEI400"
    TSE_PRIME = "TSE_PRIME"
    TSE_STANDARD = "TSE_STANDARD"
    TSE_GROWTH = "TSE_GROWTH"
    TOPIX_LARGE70 = "TOPIX_LARGE70"
    TOPIX_MID400 = "TOPIX_MID400"
    TOPIX_SMALL = "TOPIX_SMALL"
    MOTHERS = "MOTHERS"
    # US
    SP500 = "SP500"
    NASDAQ100 = "NASDAQ100"
    DOW30 = "DOW30"
    RUSSELL2000 = "RUSSELL2000"
    RUSSELL1000 = "RUSSELL1000"
    SP400 = "SP400"
    SP600 = "SP600"
    # Europe
    FTSE100 = "FTSE100"
    DAX40 = "DAX40"
    CAC40 = "CAC40"
    STOXX50 = "STOXX50"
    STOXX600 = "STOXX600"
    # Asia Pacific
    HANG_SENG = "HANG_SENG"
    SSE50 = "SSE50"
    CSI300 = "CSI300"
    KOSPI = "KOSPI"
    KOSDAQ = "KOSDAQ"
    TWSE = "TWSE"
    ASX200 = "ASX200"
    # Global
    MSCI_WORLD = "MSCI_WORLD"
    MSCI_EM = "MSCI_EM"
    MSCI_ACWI = "MSCI_ACWI"
    MSCI_EAFE = "MSCI_EAFE"


class Visibility(str, Enum):
    """Strategy visibility."""

    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"


class ParameterType(str, Enum):
    """Parameter types."""

    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    STRING = "string"


class SlippageType(str, Enum):
    """Slippage model types."""

    PERCENTAGE = "percentage"
    FIXED = "fixed"
    TIERED = "tiered"


class CommissionType(str, Enum):
    """Commission model types."""

    PER_TRADE = "per_trade"
    PER_SHARE = "per_share"
    PERCENTAGE = "percentage"
    TIERED = "tiered"


# =============================================================================
# EXTENSIBLE ENUM VALIDATORS
# =============================================================================
# These create validated string types that accept both core enum values
# and prefixed extension values (custom:, talib:, platform:, etc.)

# Prefix patterns for extensible enums
INDICATOR_PREFIXES = [
    r"^custom:[a-zA-Z0-9_]+$",
    r"^talib:[A-Z0-9_]+$",
    r"^platform:[a-z]+:[a-zA-Z0-9_]+$",
]

FUNDAMENTAL_PREFIXES = [
    r"^custom:[a-zA-Z0-9_]+$",
    r"^provider:[a-z]+:[a-zA-Z0-9_]+$",
]

EVENT_PREFIXES = [
    r"^custom:[a-zA-Z0-9_]+$",
    r"^calendar:[a-zA-Z0-9_]+$",
]

INDEX_PREFIXES = [
    r"^custom:[a-zA-Z0-9_]+$",
    r"^etf:[A-Z0-9]+$",
    r"^sector:[A-Z0-9_]+$",
]


def _make_extensible_validator(enum_class: type[Enum], prefixes: list[str]):
    """Create a validator that accepts enum values or prefixed extensions."""
    core_values = {e.value for e in enum_class}
    compiled_patterns = [re.compile(p) for p in prefixes]

    def validator(v: str) -> str:
        if v in core_values:
            return v
        for pattern in compiled_patterns:
            if pattern.match(v):
                return v
        valid_prefixes = ", ".join(p.split(":")[0].lstrip("^") + ":" for p in prefixes)
        raise ValueError(
            f"Invalid value '{v}'. Must be a core {enum_class.__name__} value "
            f"or use extension prefix ({valid_prefixes})"
        )

    return validator


# Extensible type aliases
ExtensibleIndicator = Annotated[
    str,
    AfterValidator(_make_extensible_validator(IndicatorType, INDICATOR_PREFIXES)),
    Field(description="Technical indicator (core or custom:, talib:, platform: prefixed)"),
]

ExtensibleFundamental = Annotated[
    str,
    AfterValidator(_make_extensible_validator(FundamentalMetric, FUNDAMENTAL_PREFIXES)),
    Field(description="Fundamental metric (core or custom:, provider: prefixed)"),
]

ExtensibleEvent = Annotated[
    str,
    AfterValidator(_make_extensible_validator(EventType, EVENT_PREFIXES)),
    Field(description="Event type (core or custom:, calendar: prefixed)"),
]

ExtensibleIndex = Annotated[
    str,
    AfterValidator(_make_extensible_validator(StockIndex, INDEX_PREFIXES)),
    Field(description="Stock index (core or custom:, etf:, sector: prefixed)"),
]


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
# PARAMETER REFERENCE
# =============================================================================


class ParameterReference(BaseSchema):
    """Reference to an optimizable parameter."""

    param: str = Field(..., alias="$param")


# =============================================================================
# SIGNALS - Produce numeric values
# =============================================================================


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
    operands: list["Signal"] = Field(..., min_length=1)


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
    ArithmeticSignal,
    ExpressionSignal,
    ExternalSignal,
    Reference,
    ParameterReference,
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


class ConditionalSizingCase(BaseSchema):
    """A case in conditional sizing."""

    when: "Condition"
    sizing: "Sizing"


class ConditionalSizing(BaseSchema):
    """Size based on conditions."""

    type: Literal["conditional"]
    cases: list[ConditionalSizingCase] = Field(..., min_length=1)
    default: "Sizing"


# Sizing discriminated union
Sizing = Annotated[
    Union[
        FixedAmountSizing,
        PercentEquitySizing,
        PercentPositionSizing,
        RiskBasedSizing,
        KellySizing,
        VolatilityAdjustedSizing,
        ConditionalSizing,
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
    symbol: str | None = None
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
    method: RebalanceMethod
    targets: list[RebalanceTarget] | None = None
    threshold: float = 0.05


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
    Union[TradeAction, RebalanceAction, AlertAction, HoldAction],
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
    """Index-based universe.

    Supports core indices (e.g., SP500, NIKKEI225) and extensions:
    - custom:MY_WATCHLIST - User-defined symbol lists
    - etf:SPY - ETF as universe source
    - sector:TECHNOLOGY - Sector-based universes
    """

    type: Literal["index"]
    index: ExtensibleIndex
    filters: list[Condition] | None = None
    rank_by: Signal | None = None
    order: Literal["asc", "desc"] = "desc"
    limit: int | ParameterReference | None = Field(None, ge=1)


class ScreenerUniverse(BaseSchema):
    """Screener-based universe."""

    type: Literal["screener"]
    base: str | None = None
    filters: list[Condition] = Field(..., min_length=1)
    rank_by: Signal | None = None
    order: Literal["asc", "desc"] = "desc"
    limit: int | None = Field(None, ge=1)


class DualUniverseSide(BaseSchema):
    """One side of a dual universe."""

    type: str | None = None
    index: ExtensibleIndex | None = None
    filters: list[Condition] | None = None
    rank_by: Signal | None = None
    order: Literal["asc", "desc"] | None = None
    limit: int | None = Field(None, ge=1)


class DualUniverse(BaseSchema):
    """Separate long and short universes."""

    type: Literal["dual"]
    long: DualUniverseSide
    short: DualUniverseSide


# Universe discriminated union
Universe = Annotated[
    Union[StaticUniverse, IndexUniverse, ScreenerUniverse, DualUniverse],
    Field(discriminator="type"),
]


# =============================================================================
# CONSTRAINTS - Risk and position limits
# =============================================================================


class StopConfig(BaseSchema):
    """Stop loss/take profit configuration."""

    percent: float | None = Field(None, ge=0, le=100)
    atr_multiple: float | None = Field(None, ge=0)


class TrailingStopConfig(BaseSchema):
    """Trailing stop configuration."""

    percent: float | None = Field(None, ge=0, le=100)
    atr_multiple: float | None = Field(None, ge=0)
    activation_percent: float | None = Field(None, ge=0)


class TimeStop(BaseSchema):
    """Time-based exit."""

    bars: int = Field(..., ge=1)


class Constraints(BaseSchema):
    """Risk and position constraints."""

    max_positions: int | None = Field(None, ge=1)
    min_positions: int | None = Field(None, ge=0)
    max_position_size: float | None = Field(None, ge=0, le=100)
    max_sector_exposure: float | None = Field(None, ge=0, le=100)
    max_correlation: float | None = Field(None, ge=0, le=1)
    max_drawdown: float | None = Field(None, ge=0, le=100)
    daily_loss_limit: float | None = Field(None, ge=0, le=100)
    stop_loss: StopConfig | None = None
    take_profit: StopConfig | None = None
    trailing_stop: TrailingStopConfig | None = None
    time_stop: TimeStop | None = None
    max_daily_turnover: float | None = Field(None, ge=0, le=100)
    min_holding_bars: int | None = Field(None, ge=0)
    no_shorting: bool = False
    no_leverage: bool = True


# =============================================================================
# SCHEDULE - When to evaluate
# =============================================================================


class Schedule(BaseSchema):
    """Evaluation schedule."""

    frequency: Frequency | None = None
    market_hours_only: bool = True
    timezone: str = "America/New_York"
    trading_days: list[DayOfWeek] | None = None
    evaluate_at: list[str] | None = None


# =============================================================================
# PARAMETERS - Optimizable values
# =============================================================================


class Parameter(BaseSchema):
    """Optimizable parameter definition."""

    type: ParameterType
    default: Any
    min: float | None = None
    max: float | None = None
    step: float | None = None
    choices: list[Any] | None = None
    description: str | None = None


# =============================================================================
# EXECUTION - Strategy execution assumptions
# =============================================================================


class SlippageTier(BaseSchema):
    """A tier in tiered slippage model."""

    up_to: float = Field(..., description="Order size threshold")
    value: float = Field(..., description="Slippage for this tier")


class SlippageModel(BaseSchema):
    """Expected slippage model.

    Slippage is a strategy design decision - the strategy author knows
    what slippage to expect based on the markets/instruments traded.
    """

    type: SlippageType
    value: float | None = Field(
        None, ge=0, description="Slippage value (percentage as decimal, e.g., 0.001 = 0.1%)"
    )
    tiers: list[SlippageTier] | None = Field(
        None, description="Tiered slippage based on order size"
    )


class CommissionTier(BaseSchema):
    """A tier in tiered commission model."""

    up_to: float = Field(..., description="Trade value threshold")
    value: float = Field(..., description="Commission for this tier")


class CommissionModel(BaseSchema):
    """Expected commission model.

    Commission is a strategy design decision - affects position sizing
    and profitability calculations.
    """

    type: CommissionType
    value: float | None = Field(None, ge=0, description="Commission value")
    min: float | None = Field(None, ge=0, description="Minimum commission per trade")
    max: float | None = Field(None, ge=0, description="Maximum commission per trade")
    tiers: list[CommissionTier] | None = Field(
        None, description="Tiered commission based on trade value"
    )


class Execution(BaseSchema):
    """Strategy execution assumptions.

    Defines the slippage, commission, and other execution parameters
    that the strategy was designed for. These are part of the strategy
    itself, not the backtest configuration.

    The only things external to the strategy are:
    - Data source (historical file vs real-time feed)
    - Date range (for backtest) or real-time mode
    - Actual capital amount
    """

    slippage: SlippageModel | None = None
    commission: CommissionModel | None = None
    min_capital: float | None = Field(
        None, ge=0, description="Minimum capital required for this strategy"
    )
    min_history: int | None = Field(
        None, ge=1, description="Minimum bars/days of history needed for indicator warmup"
    )
    timeframe: Timeframe | None = Field(
        None, description="Expected data timeframe for the strategy"
    )


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

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        extra="allow",  # Allow x-extensions
    )

    schema_: str | None = Field(None, alias="$schema")
    info: Info
    universe: Universe
    signals: dict[str, Signal] | None = None
    conditions: dict[str, Condition] | None = None
    rules: list[Rule] = Field(..., min_length=1)
    constraints: Constraints | None = None
    schedule: Schedule | None = None
    parameters: dict[str, Parameter] | None = None
    execution: Execution | None = None


# Update forward references
RelativeSignal.model_rebuild()
ArithmeticSignal.model_rebuild()
ComparisonCondition.model_rebuild()
AndCondition.model_rebuild()
OrCondition.model_rebuild()
NotCondition.model_rebuild()
ExpressionCondition.model_rebuild()
RiskBasedSizing.model_rebuild()
ConditionalSizingCase.model_rebuild()
ConditionalSizing.model_rebuild()
TradeAction.model_rebuild()
IndexUniverse.model_rebuild()
ScreenerUniverse.model_rebuild()
DualUniverseSide.model_rebuild()
DualUniverse.model_rebuild()
Strategy.model_rebuild()
