"""Step handler functions for the guided strategy builder flow."""

import yaml

from utss_llm.conversation.questions import (
    MOMENTUM_INDICATORS,
    QUESTION_CONFIRM,
    QUESTION_ENTRY_INDICATOR,
    QUESTION_INDEX,
    QUESTION_MAX_POSITIONS,
    QUESTION_POSITION_SIZE,
    QUESTION_RSI_OVERBOUGHT,
    QUESTION_RSI_OVERSOLD,
    QUESTION_SMA_FAST_PERIOD,
    QUESTION_SMA_SLOW_PERIOD,
    QUESTION_STOP_LOSS,
    QUESTION_STRATEGY_TYPE,
    QUESTION_SYMBOLS,
    QUESTION_TAKE_PROFIT,
    QUESTION_UNIVERSE_TYPE,
    TREND_INDICATORS,
)
from utss_llm.conversation.state import (
    ConversationResponse,
    ConversationState,
    PartialStrategy,
    Question,
    ResponseType,
)

# Step order (shared with StrategyBuilder.STEPS)
STEPS = [
    "strategy_type",
    "universe_type",
    "universe_details",
    "entry_indicator",
    "entry_params",
    "exit_params",
    "position_size",
    "stop_loss",
    "take_profit",
    "max_positions",
    "confirm",
]


def advance_step(state: ConversationState) -> str:
    """Advance to the next step in the flow."""
    current_idx = STEPS.index(state.current_step)
    if current_idx < len(STEPS) - 1:
        state.current_step = STEPS[current_idx + 1]
    return state.current_step


def _get_entry_indicator_question(state: ConversationState) -> Question:
    """Get entry indicator question based on strategy type."""
    strategy_name = state.partial_strategy.name or ""

    if "Mean Reversion" in strategy_name:
        options = MOMENTUM_INDICATORS
    elif "Trend" in strategy_name:
        options = TREND_INDICATORS
    else:
        options = QUESTION_ENTRY_INDICATOR.options

    return Question(
        id="entry_indicator",
        text="Which indicator should trigger your entry?",
        options=options,
        allow_custom=True,
    )


def _get_entry_params_question(indicator: str) -> Question:
    """Get entry params question based on indicator."""
    if indicator == "RSI":
        return QUESTION_RSI_OVERSOLD
    elif indicator in ("SMA", "EMA"):
        return QUESTION_SMA_FAST_PERIOD
    else:
        return Question(
            id="entry_threshold",
            text=f"At what {indicator} level should we enter?",
            options=[],
            allow_custom=True,
        )


def _get_exit_params_question(indicator: str) -> Question:
    """Get exit params question based on indicator."""
    if indicator == "RSI":
        return QUESTION_RSI_OVERBOUGHT
    else:
        return Question(
            id="exit_threshold",
            text=f"At what {indicator} level should we exit?",
            options=[],
            allow_custom=True,
        )


def handle_strategy_type(
    state: ConversationState, answer: str
) -> ConversationResponse:
    """Handle strategy type selection."""
    strategy = state.partial_strategy

    if answer == "mean_reversion":
        strategy.name = "Mean Reversion Strategy"
        strategy.description = "Buy when oversold, sell when overbought"
    elif answer == "trend_following":
        strategy.name = "Trend Following Strategy"
        strategy.description = "Follow the direction of the market trend"
    elif answer == "breakout":
        strategy.name = "Breakout Strategy"
        strategy.description = "Trade when price breaks key levels"
    elif answer == "calendar":
        strategy.name = "Calendar Strategy"
        strategy.description = "Trade based on calendar patterns"
    else:
        strategy.name = answer
        strategy.description = f"Custom strategy: {answer}"

    advance_step(state)

    return ConversationResponse(
        type=ResponseType.QUESTION,
        message=f"Great! We'll build a {answer} strategy.",
        question=QUESTION_UNIVERSE_TYPE,
    )


def handle_universe_type(
    state: ConversationState, answer: str
) -> ConversationResponse:
    """Handle universe type selection."""
    state.partial_strategy.universe_type = answer
    advance_step(state)

    if answer == "static":
        return ConversationResponse(
            type=ResponseType.QUESTION,
            message="You've chosen to trade specific symbols.",
            question=QUESTION_SYMBOLS,
        )
    elif answer == "screener":
        return ConversationResponse(
            type=ResponseType.QUESTION,
            message="You've chosen to trade index members.",
            question=QUESTION_INDEX,
        )
    else:
        # Fallback — skip to entry_indicator
        state.current_step = "entry_indicator"
        return ConversationResponse(
            type=ResponseType.QUESTION,
            message="Universe selected. Now let's define entry conditions.",
            question=_get_entry_indicator_question(state),
        )


def handle_universe_details(
    state: ConversationState, answer: str
) -> ConversationResponse:
    """Handle universe details (symbols or index)."""
    strategy = state.partial_strategy

    if strategy.universe_type == "static":
        symbols = [s.strip().upper() for s in answer.split(",")]
        strategy.symbols = symbols
    elif strategy.universe_type == "screener":
        strategy.index = answer

    advance_step(state)

    return ConversationResponse(
        type=ResponseType.QUESTION,
        message="Universe configured. Now let's define entry conditions.",
        question=_get_entry_indicator_question(state),
    )


def handle_entry_indicator(
    state: ConversationState, answer: str
) -> ConversationResponse:
    """Handle entry indicator selection."""
    state.partial_strategy.entry_indicator = answer.upper()
    advance_step(state)

    question = _get_entry_params_question(answer.upper())

    return ConversationResponse(
        type=ResponseType.QUESTION,
        message=f"Using {answer} for entry signals.",
        question=question,
    )


def handle_entry_params(
    state: ConversationState, answer: str
) -> ConversationResponse:
    """Handle entry parameters."""
    strategy = state.partial_strategy
    indicator = strategy.entry_indicator

    try:
        threshold = float(answer)
    except ValueError:
        threshold = 30  # Default

    strategy.entry_threshold = threshold
    strategy.entry_operator = "<" if indicator == "RSI" else ">"

    # For MA crossover, ask for slow period
    if indicator in ("SMA", "EMA"):
        strategy.entry_params = {"period": int(threshold)}
        advance_step(state)
        return ConversationResponse(
            type=ResponseType.QUESTION,
            message=f"Fast {indicator} period set to {int(threshold)}.",
            question=QUESTION_SMA_SLOW_PERIOD,
        )

    advance_step(state)

    # Set up exit indicator (same as entry for mean reversion)
    strategy.exit_indicator = indicator
    strategy.exit_params = strategy.entry_params.copy() if strategy.entry_params else {}

    return ConversationResponse(
        type=ResponseType.QUESTION,
        message=f"Entry at {indicator} < {threshold}. Now let's set exit conditions.",
        question=_get_exit_params_question(indicator),
    )


def handle_exit_params(
    state: ConversationState, answer: str
) -> ConversationResponse:
    """Handle exit parameters."""
    strategy = state.partial_strategy

    try:
        threshold = float(answer)
    except ValueError:
        threshold = 70  # Default

    strategy.exit_threshold = threshold
    strategy.exit_operator = ">"

    advance_step(state)

    return ConversationResponse(
        type=ResponseType.QUESTION,
        message=f"Exit at {strategy.exit_indicator} > {threshold}. Now let's configure position sizing.",
        question=QUESTION_POSITION_SIZE,
    )


def handle_position_size(
    state: ConversationState, answer: str
) -> ConversationResponse:
    """Handle position size."""
    try:
        size = float(answer)
    except ValueError:
        size = 10

    state.partial_strategy.sizing_type = "percent_of_equity"
    state.partial_strategy.sizing_value = size

    advance_step(state)

    return ConversationResponse(
        type=ResponseType.QUESTION,
        message=f"Position size set to {size}% of portfolio.",
        question=QUESTION_STOP_LOSS,
    )


def handle_stop_loss(
    state: ConversationState, answer: str
) -> ConversationResponse:
    """Handle stop loss setting."""
    if answer != "none":
        try:
            state.partial_strategy.stop_loss_pct = float(answer)
        except ValueError:
            pass

    advance_step(state)

    return ConversationResponse(
        type=ResponseType.QUESTION,
        message="Stop loss configured." if answer != "none" else "No stop loss.",
        question=QUESTION_TAKE_PROFIT,
    )


def handle_take_profit(
    state: ConversationState, answer: str
) -> ConversationResponse:
    """Handle take profit setting."""
    if answer != "none":
        try:
            state.partial_strategy.take_profit_pct = float(answer)
        except ValueError:
            pass

    advance_step(state)

    return ConversationResponse(
        type=ResponseType.QUESTION,
        message="Take profit configured." if answer != "none" else "No take profit target.",
        question=QUESTION_MAX_POSITIONS,
    )


def handle_max_positions(
    state: ConversationState, answer: str
) -> ConversationResponse:
    """Handle max positions setting."""
    try:
        state.partial_strategy.max_positions = int(answer)
    except ValueError:
        state.partial_strategy.max_positions = 10

    advance_step(state)

    # Generate preview
    strategy_dict = state.partial_strategy.to_utss_dict()
    preview = yaml.dump(strategy_dict, default_flow_style=False, sort_keys=False)

    return ConversationResponse(
        type=ResponseType.CONFIRMATION,
        message="Here's a preview of your strategy:",
        question=QUESTION_CONFIRM,
        preview_yaml=preview,
        strategy_dict=strategy_dict,
    )


def handle_confirm(
    state: ConversationState, answer: str
) -> ConversationResponse:
    """Handle final confirmation."""
    if answer.lower() in ("yes", "y", "true", "1"):
        state.is_complete = True
        strategy_dict = state.partial_strategy.to_utss_dict()
        strategy_yaml = yaml.dump(
            strategy_dict, default_flow_style=False, sort_keys=False
        )

        return ConversationResponse(
            type=ResponseType.COMPLETE,
            message="Strategy created successfully!",
            strategy_yaml=strategy_yaml,
            strategy_dict=strategy_dict,
        )
    else:
        # Reset partial strategy and go back to start
        state.partial_strategy = PartialStrategy()
        state.current_step = "strategy_type"
        return ConversationResponse(
            type=ResponseType.QUESTION,
            message="Let's start over. What type of strategy would you like?",
            question=QUESTION_STRATEGY_TYPE,
        )
