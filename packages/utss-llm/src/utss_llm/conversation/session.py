"""Conversation session for interactive strategy building."""

import json
import re
import uuid
from dataclasses import dataclass, field

import yaml

from utss_llm.conversation.builder import StrategyBuilder
from utss_llm.conversation.state import (
    ConversationResponse,
    ConversationState,
    ResponseType,
)
from utss_llm.parser import ParseMode
from utss_llm.providers.base import LLMProvider


# Prompt for extracting strategy info from natural language
SMART_START_PROMPT = """Analyze this trading strategy description and extract key information.

Description: "{description}"

Extract the following if mentioned (return null if not specified):
1. strategy_type: One of "mean_reversion", "trend_following", "breakout", "calendar", or null
2. indicators: List of indicators mentioned (e.g., ["RSI", "SMA"])
3. entry_threshold: Numeric threshold for entry (e.g., 30 for RSI < 30)
4. exit_threshold: Numeric threshold for exit (e.g., 70 for RSI > 70)
5. symbols: List of stock symbols mentioned (e.g., ["AAPL", "MSFT"])
6. stop_loss: Stop loss percentage if mentioned
7. position_size: Position size percentage if mentioned

Return ONLY a JSON object with these fields, no explanation:
```json
{{
  "strategy_type": ...,
  "indicators": [...],
  "entry_threshold": ...,
  "exit_threshold": ...,
  "symbols": [...],
  "stop_loss": ...,
  "position_size": ...
}}
```"""

# Prompt for interpreting revision instructions
REVISION_PROMPT = """Given the current strategy and a revision instruction, determine what changes to make.

Current Strategy Summary:
- Entry indicator: {entry_indicator}
- Entry threshold: {entry_threshold}
- Exit indicator: {exit_indicator}
- Exit threshold: {exit_threshold}
- Stop loss: {stop_loss}%
- Position size: {position_size}%

Revision instruction: "{instruction}"

Identify what field(s) to update and their new value(s).
Return ONLY a JSON object with the fields to change:
```json
{{
  "entry_threshold": ...,
  "exit_threshold": ...,
  "stop_loss_pct": ...,
  "sizing_value": ...,
  "entry_indicator": ...,
  "exit_indicator": ...
}}
```
Only include fields that need to change. Use null for unchanged fields."""


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

        # Try LLM-powered revision if available
        if self.use_llm and self.provider:
            await self._llm_revise(instruction)
        else:
            # Fall back to keyword-based revision
            self._keyword_revise(instruction)

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

    def _keyword_revise(self, instruction: str) -> None:
        """Apply keyword-based revision (fallback when no LLM)."""
        instruction_lower = instruction.lower()
        strategy = self.state.partial_strategy

        # Extract all numbers from instruction
        numbers = [int(s) for s in re.findall(r'\d+', instruction)]

        if "rsi" in instruction_lower and numbers:
            if "entry" in instruction_lower or "oversold" in instruction_lower:
                strategy.entry_threshold = numbers[0]
            elif "exit" in instruction_lower or "overbought" in instruction_lower:
                strategy.exit_threshold = numbers[0]
            else:
                # If RSI mentioned but not entry/exit, update entry by default
                strategy.entry_threshold = numbers[0]

        if "stop" in instruction_lower and "loss" in instruction_lower and numbers:
            strategy.stop_loss_pct = numbers[0]

        if "take" in instruction_lower and "profit" in instruction_lower and numbers:
            strategy.take_profit_pct = numbers[0]

        if "position" in instruction_lower and "size" in instruction_lower and numbers:
            strategy.sizing_value = numbers[0]

        if "max" in instruction_lower and "position" in instruction_lower and numbers:
            strategy.max_positions = numbers[0]

    async def _llm_revise(self, instruction: str) -> None:
        """Use LLM to interpret and apply revision instruction."""
        if not self.provider:
            return

        strategy = self.state.partial_strategy

        prompt = REVISION_PROMPT.format(
            entry_indicator=strategy.entry_indicator or "N/A",
            entry_threshold=strategy.entry_threshold or "N/A",
            exit_indicator=strategy.exit_indicator or "N/A",
            exit_threshold=strategy.exit_threshold or "N/A",
            stop_loss=strategy.stop_loss_pct or "N/A",
            position_size=strategy.sizing_value or "N/A",
            instruction=instruction,
        )

        try:
            response = await self.provider.generate(
                prompt=prompt,
                system="You are a trading strategy assistant. Return only valid JSON.",
                temperature=0.1,
                max_tokens=256,
            )

            updates = self._extract_json(response.content)
            if updates:
                self._apply_updates(updates)
        except Exception:
            # Fall back to keyword-based if LLM fails
            self._keyword_revise(instruction)

    def _apply_updates(self, updates: dict) -> None:
        """Apply extracted updates to the partial strategy."""
        strategy = self.state.partial_strategy

        if updates.get("entry_threshold") is not None:
            strategy.entry_threshold = float(updates["entry_threshold"])

        if updates.get("exit_threshold") is not None:
            strategy.exit_threshold = float(updates["exit_threshold"])

        if updates.get("stop_loss_pct") is not None:
            strategy.stop_loss_pct = float(updates["stop_loss_pct"])

        if updates.get("sizing_value") is not None:
            strategy.sizing_value = float(updates["sizing_value"])

        if updates.get("entry_indicator") is not None:
            strategy.entry_indicator = str(updates["entry_indicator"]).upper()

        if updates.get("exit_indicator") is not None:
            strategy.exit_indicator = str(updates["exit_indicator"]).upper()

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

        Analyzes the user's description to pre-fill known values
        and skip to the first unanswered question.
        """
        if not self.provider:
            return self.builder.get_initial_question()

        extraction_prompt = SMART_START_PROMPT.format(description=prompt)

        try:
            response = await self.provider.generate(
                prompt=extraction_prompt,
                system="You are a trading strategy analyzer. Return only valid JSON.",
                temperature=0.1,
                max_tokens=512,
            )

            extracted = self._extract_json(response.content)
            if extracted:
                self._prefill_strategy(extracted)
                return self._skip_to_unanswered()

        except Exception:
            # Fall back to guided flow on any error
            pass

        return self.builder.get_initial_question()

    def _extract_json(self, content: str) -> dict | None:
        """Extract JSON from LLM response."""
        # Try to find JSON in code blocks
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)```", content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try parsing entire content as JSON
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass

        # Try to find JSON object pattern
        json_obj_match = re.search(r"\{[^{}]*\}", content, re.DOTALL)
        if json_obj_match:
            try:
                return json.loads(json_obj_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _prefill_strategy(self, extracted: dict) -> None:
        """Pre-fill partial strategy from extracted info."""
        strategy = self.state.partial_strategy

        # Strategy type
        strategy_type = extracted.get("strategy_type")
        if strategy_type:
            type_names = {
                "mean_reversion": ("Mean Reversion Strategy", "Buy when oversold, sell when overbought"),
                "trend_following": ("Trend Following Strategy", "Follow the direction of the market trend"),
                "breakout": ("Breakout Strategy", "Trade when price breaks key levels"),
                "calendar": ("Calendar Strategy", "Trade based on calendar patterns"),
            }
            if strategy_type in type_names:
                strategy.name, strategy.description = type_names[strategy_type]
                self.state.current_step = "universe_type"

        # Indicators
        indicators = extracted.get("indicators", [])
        if indicators and len(indicators) > 0:
            strategy.entry_indicator = indicators[0].upper()
            if len(indicators) > 1:
                strategy.exit_indicator = indicators[1].upper()
            else:
                strategy.exit_indicator = indicators[0].upper()

        # Thresholds
        if extracted.get("entry_threshold") is not None:
            strategy.entry_threshold = float(extracted["entry_threshold"])
            strategy.entry_operator = "<"  # Default for RSI-style

        if extracted.get("exit_threshold") is not None:
            strategy.exit_threshold = float(extracted["exit_threshold"])
            strategy.exit_operator = ">"

        # Symbols
        symbols = extracted.get("symbols", [])
        if symbols:
            strategy.universe_type = "static"
            strategy.symbols = [s.upper() for s in symbols]

        # Risk management
        if extracted.get("stop_loss") is not None:
            strategy.stop_loss_pct = float(extracted["stop_loss"])

        if extracted.get("position_size") is not None:
            strategy.sizing_type = "percent_of_equity"
            strategy.sizing_value = float(extracted["position_size"])

    def _skip_to_unanswered(self) -> ConversationResponse:
        """Find the first unanswered question and skip to it."""
        strategy = self.state.partial_strategy

        # Check what's filled and advance state accordingly
        if strategy.name is None:
            self.state.current_step = "strategy_type"
            return self.builder.get_initial_question()

        if strategy.universe_type is None:
            self.state.current_step = "universe_type"
            from utss_llm.conversation.questions import QUESTION_UNIVERSE_TYPE
            return ConversationResponse(
                type=ResponseType.QUESTION,
                message=f"I understand you want a {strategy.name}. Let's configure it.",
                question=QUESTION_UNIVERSE_TYPE,
            )

        if strategy.universe_type == "static" and not strategy.symbols:
            self.state.current_step = "universe_details"
            from utss_llm.conversation.questions import QUESTION_SYMBOLS
            return ConversationResponse(
                type=ResponseType.QUESTION,
                message="Which symbols would you like to trade?",
                question=QUESTION_SYMBOLS,
            )

        if strategy.entry_indicator is None:
            self.state.current_step = "entry_indicator"
            return ConversationResponse(
                type=ResponseType.QUESTION,
                message="Which indicator should trigger entries?",
                question=self.builder._get_entry_indicator_question(self.state),
            )

        if strategy.entry_threshold is None:
            self.state.current_step = "entry_params"
            return ConversationResponse(
                type=ResponseType.QUESTION,
                message=f"At what {strategy.entry_indicator} level should we enter?",
                question=self.builder._get_entry_params_question(strategy.entry_indicator),
            )

        if strategy.exit_threshold is None:
            self.state.current_step = "exit_params"
            return ConversationResponse(
                type=ResponseType.QUESTION,
                message=f"At what {strategy.exit_indicator} level should we exit?",
                question=self.builder._get_exit_params_question(strategy.exit_indicator),
            )

        if strategy.sizing_value is None:
            self.state.current_step = "position_size"
            from utss_llm.conversation.questions import QUESTION_POSITION_SIZE
            return ConversationResponse(
                type=ResponseType.QUESTION,
                message="How should we size positions?",
                question=QUESTION_POSITION_SIZE,
            )

        # If we have enough info, show preview
        self.state.current_step = "confirm"
        strategy_dict = strategy.to_utss_dict()
        preview = yaml.dump(strategy_dict, default_flow_style=False, sort_keys=False)

        from utss_llm.conversation.questions import QUESTION_CONFIRM
        return ConversationResponse(
            type=ResponseType.CONFIRMATION,
            message="I've extracted most of your strategy. Here's a preview:",
            question=QUESTION_CONFIRM,
            preview_yaml=preview,
            strategy_dict=strategy_dict,
        )


class SessionManager:
    """Manages conversation session lifecycle.

    Provides create/get/delete operations for ConversationSession instances.
    A default instance is used by the module-level convenience functions.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, ConversationSession] = {}

    def create(
        self,
        provider: LLMProvider | None = None,
        mode: ParseMode = ParseMode.BEGINNER,
    ) -> ConversationSession:
        """Create a new conversation session."""
        session = ConversationSession(provider=provider, mode=mode)
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> ConversationSession | None:
        """Get an existing session by ID."""
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def clear(self) -> None:
        """Remove all sessions."""
        self._sessions.clear()


# Default manager used by module-level convenience functions
_default_manager = SessionManager()


def get_session(session_id: str) -> ConversationSession | None:
    """Get an existing session by ID."""
    return _default_manager.get(session_id)


def create_session(
    provider: LLMProvider | None = None,
    mode: ParseMode = ParseMode.BEGINNER,
) -> ConversationSession:
    """Create a new conversation session."""
    return _default_manager.create(provider=provider, mode=mode)


def delete_session(session_id: str) -> bool:
    """Delete a session."""
    return _default_manager.delete(session_id)
