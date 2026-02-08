"""Strategy builder with guided flow logic."""

from utss_llm.conversation.questions import QUESTION_STRATEGY_TYPE
from utss_llm.conversation.state import (
    ConversationResponse,
    ConversationState,
    ResponseType,
)
from utss_llm.conversation.steps import (
    handle_confirm,
    handle_entry_indicator,
    handle_entry_params,
    handle_exit_params,
    handle_max_positions,
    handle_position_size,
    handle_stop_loss,
    handle_strategy_type,
    handle_take_profit,
    handle_universe_details,
    handle_universe_type,
)


class StrategyBuilder:
    """Guided strategy building flow.

    Manages the flow of questions and builds a strategy incrementally
    based on user responses.
    """

    def __init__(self) -> None:
        """Initialize the strategy builder."""
        self._step_handlers = {
            "strategy_type": handle_strategy_type,
            "universe_type": handle_universe_type,
            "universe_details": handle_universe_details,
            "entry_indicator": handle_entry_indicator,
            "entry_params": handle_entry_params,
            "exit_params": handle_exit_params,
            "position_size": handle_position_size,
            "stop_loss": handle_stop_loss,
            "take_profit": handle_take_profit,
            "max_positions": handle_max_positions,
            "confirm": handle_confirm,
        }

    def get_initial_question(self) -> ConversationResponse:
        """Get the first question to start the flow."""
        return ConversationResponse(
            type=ResponseType.QUESTION,
            message="Let's build your trading strategy step by step.",
            question=QUESTION_STRATEGY_TYPE,
        )

    def process_answer(
        self,
        state: ConversationState,
        answer: str,
    ) -> ConversationResponse:
        """Process user's answer and return next question or completion.

        Args:
            state: Current conversation state
            answer: User's answer (option id or free text)

        Returns:
            Next question, preview, or completion response
        """
        current_step = state.current_step
        handler = self._step_handlers.get(current_step)

        if not handler:
            return ConversationResponse(
                type=ResponseType.ERROR,
                message=f"Unknown step: {current_step}",
            )

        return handler(state, answer)
