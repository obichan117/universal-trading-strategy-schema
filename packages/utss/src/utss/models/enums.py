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
