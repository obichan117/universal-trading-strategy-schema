"""UTSS Enum definitions.

All enumerations used across the UTSS schema.
"""

from enum import Enum


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
    """Technical indicator types.

    Indicators fall into three categories:

    - **Primitive**: Computed directly from OHLCV data via a dedicated
      calculation method (e.g. SMA, RSI, ATR). Each primitive has its own
      entry in the engine's INDICATOR_REGISTRY.

    - **Component**: A specific output line of a multi-output primitive.
      In the engine, these are resolved via _COMPONENT_SHORTCUTS to their
      parent indicator + component selector (e.g. MACD_SIGNAL → MACD
      with line=signal, BB_UPPER → Bollinger Bands with band=upper).

    - **Derived**: Computed by chaining or transforming primitives
      (e.g. STOCH_RSI applies Stochastic to RSI output).

    This classification matters when extending the engine: primitives
    need a new IndicatorService method, components just need a shortcut
    entry, and derived indicators compose existing methods.
    """

    # Moving Averages
    SMA = "SMA"  # Primitive
    EMA = "EMA"  # Primitive
    WMA = "WMA"  # Primitive
    DEMA = "DEMA"  # Primitive
    TEMA = "TEMA"  # Primitive
    KAMA = "KAMA"  # Primitive
    HULL = "HULL"  # Primitive
    VWMA = "VWMA"  # Primitive
    # Momentum
    RSI = "RSI"  # Primitive
    MACD = "MACD"  # Primitive (multi-output)
    MACD_SIGNAL = "MACD_SIGNAL"  # Component (MACD → signal line)
    MACD_HIST = "MACD_HIST"  # Component (MACD → histogram)
    STOCH_K = "STOCH_K"  # Component (Stochastic → %K)
    STOCH_D = "STOCH_D"  # Component (Stochastic → %D)
    STOCH_RSI = "STOCH_RSI"  # Derived (Stochastic applied to RSI)
    ROC = "ROC"  # Primitive
    MOMENTUM = "MOMENTUM"  # Primitive
    WILLIAMS_R = "WILLIAMS_R"  # Primitive
    CCI = "CCI"  # Primitive
    MFI = "MFI"  # Primitive
    CMO = "CMO"  # Primitive
    TSI = "TSI"  # Primitive
    # Trend
    ADX = "ADX"  # Primitive
    PLUS_DI = "PLUS_DI"  # Primitive
    MINUS_DI = "MINUS_DI"  # Primitive
    AROON_UP = "AROON_UP"  # Component (Aroon → up)
    AROON_DOWN = "AROON_DOWN"  # Component (Aroon → down)
    AROON_OSC = "AROON_OSC"  # Component (Aroon → oscillator)
    SUPERTREND = "SUPERTREND"  # Primitive
    PSAR = "PSAR"  # Primitive
    # Volatility
    ATR = "ATR"  # Primitive
    STDDEV = "STDDEV"  # Primitive
    VARIANCE = "VARIANCE"  # Primitive
    BB_UPPER = "BB_UPPER"  # Component (Bollinger Bands → upper)
    BB_MIDDLE = "BB_MIDDLE"  # Component (Bollinger Bands → middle)
    BB_LOWER = "BB_LOWER"  # Component (Bollinger Bands → lower)
    BB_WIDTH = "BB_WIDTH"  # Component (Bollinger Bands → bandwidth)
    BB_PERCENT = "BB_PERCENT"  # Component (Bollinger Bands → %B)
    KC_UPPER = "KC_UPPER"  # Component (Keltner Channel → upper)
    KC_MIDDLE = "KC_MIDDLE"  # Component (Keltner Channel → middle)
    KC_LOWER = "KC_LOWER"  # Component (Keltner Channel → lower)
    DC_UPPER = "DC_UPPER"  # Component (Donchian Channel → upper)
    DC_MIDDLE = "DC_MIDDLE"  # Component (Donchian Channel → middle)
    DC_LOWER = "DC_LOWER"  # Component (Donchian Channel → lower)
    # Volume
    OBV = "OBV"  # Primitive
    VWAP = "VWAP"  # Primitive
    AD = "AD"  # Primitive
    CMF = "CMF"  # Primitive
    KLINGER = "KLINGER"  # Primitive
    # Statistical
    HIGHEST = "HIGHEST"  # Primitive
    LOWEST = "LOWEST"  # Primitive
    RETURN = "RETURN"  # Primitive
    DRAWDOWN = "DRAWDOWN"  # Primitive
    ZSCORE = "ZSCORE"  # Primitive
    PERCENTILE = "PERCENTILE"  # Primitive
    RANK = "RANK"  # Primitive
    CORRELATION = "CORRELATION"  # Primitive
    BETA = "BETA"  # Primitive
    # Ichimoku
    ICHIMOKU_TENKAN = "ICHIMOKU_TENKAN"  # Primitive
    ICHIMOKU_KIJUN = "ICHIMOKU_KIJUN"  # Primitive
    ICHIMOKU_SENKOU_A = "ICHIMOKU_SENKOU_A"  # Primitive
    ICHIMOKU_SENKOU_B = "ICHIMOKU_SENKOU_B"  # Primitive
    ICHIMOKU_CHIKOU = "ICHIMOKU_CHIKOU"  # Primitive


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
