"""Conversation session for interactive strategy building."""

import uuid
from dataclasses import dataclass, field

import yaml

from utss_llm.conversation.builder import StrategyBuilder
from utss_llm.conversation.state import (
    ConversationResponse,
    ConversationState,
    Option,
    Question,
    ResponseType,
)
from utss_llm.parser import ParseMode
from utss_llm.providers.base import LLMProvider


@dataclass
class ConversationSession:
    """Stateful strategy building session.

    Manages the conversation flow for building UTSS strategies interactively.
    Can work in two modes:
    - Guided: Step-by-step questions with predefined options
    - LLM-assisted: Uses LLM to interpret free-form input and generate questions

    Example:
        session = ConversationSession(provider=anthropic_provider)

        # Start conversation
        response = await session.start("I want to buy tech stocks when oversold")

        # Answer questions
        while response.needs_input:
            print(response.message)
            if response.question:
                for opt in response.question.options:
                    print(f"  {opt.id}: {opt.label}")
            user_input = input("> ")
            response = await session.answer(user_input)

        # Get final strategy
        print(response.strategy_yaml)
    """

    provider: LLMProvider | None = None
    mode: ParseMode = ParseMode.BEGINNER
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: ConversationState = field(default_factory=ConversationState)
    builder: StrategyBuilder = field(default_factory=StrategyBuilder)
    use_llm: bool = False  # Whether to use LLM for question generation

    async def start(self, initial_prompt: str | None = None) -> ConversationResponse:
        """Start a new strategy building conversation.

        Args:
            initial_prompt: Optional initial description of desired strategy

        Returns:
            First question or confirmation response
        """
        self.state = ConversationState()
        self.state.current_step = "strategy_type"

        if initial_prompt:
            self.state.add_turn("user", initial_prompt)

            # If we have an LLM and want smart parsing, try to extract info
            if self.use_llm and self.provider:
                return await self._smart_start(initial_prompt)

        # Default: return first guided question
        response = self.builder.get_initial_question()
        self.state.add_turn("assistant", response.message, response.question)
        return response

    async def answer(self, user_answer: str) -> ConversationResponse:
        """Process user's answer and continue conversation.

        Args:
            user_answer: User's response (option id, number, or free text)

        Returns:
            Next question, preview, or completion response
        """
        self.state.add_turn("user", user_answer)

        # Resolve answer to option id if numeric
        resolved_answer = self._resolve_answer(user_answer)

        # Process through builder
        response = self.builder.process_answer(self.state, resolved_answer)

        self.state.add_turn("assistant", response.message, response.question)
        return response

    async def revise(self, instruction: str) -> ConversationResponse:
        """Revise the current strategy based on instruction.

        Args:
            instruction: What to change (e.g., "change RSI threshold to 25")

        Returns:
            Updated preview or question
        """
        self.state.add_turn("user", f"Revise: {instruction}")

        # Simple keyword-based revision for now
        instruction_lower = instruction.lower()

        if "rsi" in instruction_lower and any(
            c.isdigit() for c in instruction
        ):
            # Extract number
            numbers = [int(s) for s in instruction.split() if s.isdigit()]
            if numbers:
                if "entry" in instruction_lower or "oversold" in instruction_lower:
                    self.state.partial_strategy.entry_threshold = numbers[0]
                elif "exit" in instruction_lower or "overbought" in instruction_lower:
                    self.state.partial_strategy.exit_threshold = numbers[0]

        if "stop" in instruction_lower and "loss" in instruction_lower:
            numbers = [int(s) for s in instruction.split() if s.isdigit()]
            if numbers:
                self.state.partial_strategy.stop_loss_pct = numbers[0]

        # Generate updated preview
        strategy_dict = self.state.partial_strategy.to_utss_dict()
        preview = yaml.dump(strategy_dict, default_flow_style=False, sort_keys=False)

        response = ConversationResponse(
            type=ResponseType.PREVIEW,
            message="Strategy updated. Here's the revised version:",
            preview_yaml=preview,
            strategy_dict=strategy_dict,
        )
        self.state.add_turn("assistant", response.message)
        return response

    def export(self) -> str | None:
        """Export current strategy as UTSS YAML.

        Returns:
            YAML string if strategy is complete, None otherwise
        """
        if not self.state.is_complete:
            return None

        strategy_dict = self.state.partial_strategy.to_utss_dict()
        return yaml.dump(strategy_dict, default_flow_style=False, sort_keys=False)

    def export_dict(self) -> dict | None:
        """Export current strategy as dictionary.

        Returns:
            Strategy dict if complete, None otherwise
        """
        if not self.state.is_complete:
            return None
        return self.state.partial_strategy.to_utss_dict()

    def get_preview(self) -> str:
        """Get preview of current partial strategy.

        Returns:
            YAML string of current state
        """
        strategy_dict = self.state.partial_strategy.to_utss_dict()
        return yaml.dump(strategy_dict, default_flow_style=False, sort_keys=False)

    def _resolve_answer(self, answer: str) -> str:
        """Resolve user answer to option id.

        Handles:
        - Numeric selection (1, 2, 3...)
        - Option id directly
        - Free text
        """
        last_question = self.state.last_question
        if not last_question or not last_question.options:
            return answer

        # Try numeric selection
        try:
            idx = int(answer) - 1  # 1-indexed
            if 0 <= idx < len(last_question.options):
                return last_question.options[idx].id
        except ValueError:
            pass

        # Try matching option id or label
        answer_lower = answer.lower()
        for opt in last_question.options:
            if opt.id.lower() == answer_lower or opt.label.lower() == answer_lower:
                return opt.id

        # Return as-is for custom input
        return answer

    async def _smart_start(self, prompt: str) -> ConversationResponse:
        """Use LLM to extract strategy info from initial prompt.

        This is a placeholder for LLM-assisted parsing.
        """
        # For now, just start with guided flow
        # In the future, this would:
        # 1. Send prompt to LLM
        # 2. Extract strategy type, indicators, etc.
        # 3. Pre-fill partial strategy
        # 4. Skip to first unanswered question

        return self.builder.get_initial_question()


# Session storage for multi-turn conversations
_sessions: dict[str, ConversationSession] = {}


def get_session(session_id: str) -> ConversationSession | None:
    """Get an existing session by ID."""
    return _sessions.get(session_id)


def create_session(
    provider: LLMProvider | None = None,
    mode: ParseMode = ParseMode.BEGINNER,
) -> ConversationSession:
    """Create a new conversation session."""
    session = ConversationSession(provider=provider, mode=mode)
    _sessions[session.session_id] = session
    return session


def delete_session(session_id: str) -> bool:
    """Delete a session."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False
