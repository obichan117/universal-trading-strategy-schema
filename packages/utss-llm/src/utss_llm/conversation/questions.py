"""Predefined questions and option templates for strategy building."""

from utss_llm.conversation.state import Option, Question


# =============================================================================
# Indicator Options
# =============================================================================

MOMENTUM_INDICATORS = [
    Option(id="RSI", label="RSI", description="Relative Strength Index (0-100)", value="RSI"),
    Option(id="STOCH", label="Stochastic", description="Stochastic Oscillator", value="STOCH_K"),
    Option(id="WILLIAMS_R", label="Williams %R", description="Williams Percent Range", value="WILLIAMS_R"),
    Option(id="MFI", label="MFI", description="Money Flow Index", value="MFI"),
    Option(id="CCI", label="CCI", description="Commodity Channel Index", value="CCI"),
]

TREND_INDICATORS = [
    Option(id="SMA", label="SMA", description="Simple Moving Average", value="SMA"),
    Option(id="EMA", label="EMA", description="Exponential Moving Average", value="EMA"),
    Option(id="MACD", label="MACD", description="Moving Average Convergence Divergence", value="MACD"),
    Option(id="ADX", label="ADX", description="Average Directional Index", value="ADX"),
]

VOLATILITY_INDICATORS = [
    Option(id="BB", label="Bollinger Bands", description="Bollinger Bands %B", value="BB"),
    Option(id="ATR", label="ATR", description="Average True Range", value="ATR"),
]

ALL_INDICATORS = MOMENTUM_INDICATORS + TREND_INDICATORS + VOLATILITY_INDICATORS


# =============================================================================
# Strategy Type Questions
# =============================================================================

QUESTION_STRATEGY_TYPE = Question(
    id="strategy_type",
    text="What type of strategy would you like to build?",
    options=[
        Option(
            id="mean_reversion",
            label="Mean Reversion",
            description="Buy oversold, sell overbought",
        ),
        Option(
            id="trend_following",
            label="Trend Following",
            description="Follow the direction of the market",
        ),
        Option(
            id="breakout",
            label="Breakout",
            description="Trade when price breaks key levels",
        ),
        Option(
            id="calendar",
            label="Calendar-based",
            description="Trade based on day/week/month patterns",
        ),
    ],
    allow_custom=True,
)


# =============================================================================
# Universe Questions
# =============================================================================

QUESTION_UNIVERSE_TYPE = Question(
    id="universe_type",
    text="How would you like to select stocks to trade?",
    options=[
        Option(
            id="static",
            label="Specific symbols",
            description="Enter specific stock tickers",
        ),
        Option(
            id="index",
            label="Index members",
            description="Trade all stocks in an index (S&P 500, Nikkei 225, etc.)",
        ),
        Option(
            id="screener",
            label="Dynamic screener",
            description="Filter stocks by criteria (market cap, sector, etc.)",
        ),
    ],
)

QUESTION_INDEX = Question(
    id="index",
    text="Which index would you like to trade?",
    options=[
        Option(id="SP500", label="S&P 500", description="US large cap", value="SP500"),
        Option(id="NASDAQ100", label="NASDAQ 100", description="US tech-heavy", value="NASDAQ100"),
        Option(id="NIKKEI225", label="Nikkei 225", description="Japan large cap", value="NIKKEI225"),
        Option(id="TOPIX", label="TOPIX", description="All Tokyo Stock Exchange", value="TOPIX"),
    ],
    allow_custom=True,
)

QUESTION_SYMBOLS = Question(
    id="symbols",
    text="Enter the stock symbols you want to trade (comma-separated):",
    options=[],  # Free-form input
    allow_custom=True,
)


# =============================================================================
# Entry Condition Questions
# =============================================================================

QUESTION_ENTRY_INDICATOR = Question(
    id="entry_indicator",
    text="Which indicator should trigger your entry?",
    options=ALL_INDICATORS,
    allow_custom=True,
)

QUESTION_RSI_OVERSOLD = Question(
    id="rsi_oversold",
    text="At what RSI level is the stock considered oversold (entry)?",
    options=[
        Option(id="20", label="20", description="Very aggressive", value=20),
        Option(id="25", label="25", description="Aggressive", value=25),
        Option(id="30", label="30", description="Standard (recommended)", value=30),
        Option(id="35", label="35", description="Conservative", value=35),
    ],
    default="30",
    allow_custom=True,
)

QUESTION_RSI_OVERBOUGHT = Question(
    id="rsi_overbought",
    text="At what RSI level is the stock considered overbought (exit)?",
    options=[
        Option(id="65", label="65", description="Conservative", value=65),
        Option(id="70", label="70", description="Standard (recommended)", value=70),
        Option(id="75", label="75", description="Aggressive", value=75),
        Option(id="80", label="80", description="Very aggressive", value=80),
    ],
    default="70",
    allow_custom=True,
)

QUESTION_SMA_FAST_PERIOD = Question(
    id="sma_fast_period",
    text="What period for the fast moving average?",
    options=[
        Option(id="10", label="10 days", value=10),
        Option(id="20", label="20 days", value=20),
        Option(id="50", label="50 days (recommended)", value=50),
    ],
    default="50",
    allow_custom=True,
)

QUESTION_SMA_SLOW_PERIOD = Question(
    id="sma_slow_period",
    text="What period for the slow moving average?",
    options=[
        Option(id="100", label="100 days", value=100),
        Option(id="150", label="150 days", value=150),
        Option(id="200", label="200 days (recommended)", value=200),
    ],
    default="200",
    allow_custom=True,
)


# =============================================================================
# Sizing Questions
# =============================================================================

QUESTION_POSITION_SIZE = Question(
    id="position_size",
    text="How much of your portfolio to invest per trade?",
    options=[
        Option(id="5", label="5%", description="Conservative", value=5),
        Option(id="10", label="10%", description="Moderate (recommended)", value=10),
        Option(id="20", label="20%", description="Aggressive", value=20),
        Option(id="25", label="25%", description="Very aggressive", value=25),
    ],
    default="10",
    allow_custom=True,
)


# =============================================================================
# Risk Management Questions
# =============================================================================

QUESTION_STOP_LOSS = Question(
    id="stop_loss",
    text="Would you like to set a stop loss?",
    options=[
        Option(id="none", label="No stop loss", value=None),
        Option(id="3", label="3%", description="Tight", value=3),
        Option(id="5", label="5%", description="Standard (recommended)", value=5),
        Option(id="10", label="10%", description="Wide", value=10),
    ],
    default="5",
    allow_custom=True,
)

QUESTION_TAKE_PROFIT = Question(
    id="take_profit",
    text="Would you like to set a take profit target?",
    options=[
        Option(id="none", label="No take profit", value=None),
        Option(id="10", label="10%", value=10),
        Option(id="15", label="15% (recommended)", value=15),
        Option(id="20", label="20%", value=20),
        Option(id="25", label="25%", value=25),
    ],
    default="15",
    allow_custom=True,
)

QUESTION_MAX_POSITIONS = Question(
    id="max_positions",
    text="Maximum number of positions to hold at once?",
    options=[
        Option(id="1", label="1", description="Single position only", value=1),
        Option(id="5", label="5", description="Moderate diversification", value=5),
        Option(id="10", label="10", description="Well diversified (recommended)", value=10),
        Option(id="20", label="20", description="Highly diversified", value=20),
    ],
    default="10",
    allow_custom=True,
)


# =============================================================================
# Confirmation
# =============================================================================

QUESTION_CONFIRM = Question(
    id="confirm",
    text="Does this strategy look correct?",
    options=[
        Option(id="yes", label="Yes, create the strategy", value=True),
        Option(id="no", label="No, let me make changes", value=False),
    ],
    allow_custom=False,
)


# =============================================================================
# Question Flow Mapping
# =============================================================================

# Maps strategy type to relevant entry indicators
STRATEGY_TYPE_INDICATORS = {
    "mean_reversion": MOMENTUM_INDICATORS,
    "trend_following": TREND_INDICATORS,
    "breakout": VOLATILITY_INDICATORS + TREND_INDICATORS,
    "calendar": [],  # Calendar doesn't use indicators
}
