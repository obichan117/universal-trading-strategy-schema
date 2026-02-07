"""LLM integration for conversation-based strategy building.

Handles smart start (extracting info from natural language prompts),
LLM-powered revision, and JSON extraction from LLM responses.
"""

import json
import re

import yaml

from utss_llm.conversation.state import (
    ConversationResponse,
    ConversationState,
    PartialStrategy,
    ResponseType,
)
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


def extract_json(content: str) -> dict | None:
    """Extract JSON from LLM response.

    Tries multiple strategies:
    1. JSON in code blocks (```json ... ```)
    2. Entire content as JSON
    3. First JSON object pattern in content
    """
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


async def smart_start(
    provider: LLMProvider,
    prompt: str,
    state: ConversationState,
    builder: "StrategyBuilder",  # noqa: F821
) -> ConversationResponse:
    """Use LLM to extract strategy info from initial prompt.

    Analyzes the user's description to pre-fill known values
    and skip to the first unanswered question.
    """
    extraction_prompt = SMART_START_PROMPT.format(description=prompt)

    try:
        response = await provider.generate(
            prompt=extraction_prompt,
            system="You are a trading strategy analyzer. Return only valid JSON.",
            temperature=0.1,
            max_tokens=512,
        )

        extracted = extract_json(response.content)
        if extracted:
            prefill_strategy(state.partial_strategy, extracted)
            return skip_to_unanswered(state, builder)

    except Exception:
        # Fall back to guided flow on any error
        pass

    return builder.get_initial_question()


async def llm_revise(
    provider: LLMProvider,
    instruction: str,
    strategy: PartialStrategy,
    keyword_revise_fn: callable,
) -> None:
    """Use LLM to interpret and apply revision instruction.

    Falls back to keyword_revise_fn on any LLM error.
    """
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
        response = await provider.generate(
            prompt=prompt,
            system="You are a trading strategy assistant. Return only valid JSON.",
            temperature=0.1,
            max_tokens=256,
        )

        updates = extract_json(response.content)
        if updates:
            apply_updates(strategy, updates)
            return
    except Exception:
        pass

    # Fall back to keyword-based if LLM fails
    keyword_revise_fn(instruction)


def apply_updates(strategy: PartialStrategy, updates: dict) -> None:
    """Apply extracted updates to the partial strategy."""
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


def prefill_strategy(strategy: PartialStrategy, extracted: dict) -> None:
    """Pre-fill partial strategy from extracted info."""
    # Strategy type
    strategy_type = extracted.get("strategy_type")
    if strategy_type:
        type_names = {
            "mean_reversion": ("Mean Reversion Strategy", "Buy when oversold, sell when overbought"),
            "trend_following": (
                "Trend Following Strategy",
                "Follow the direction of the market trend",
            ),
            "breakout": ("Breakout Strategy", "Trade when price breaks key levels"),
            "calendar": ("Calendar Strategy", "Trade based on calendar patterns"),
        }
        if strategy_type in type_names:
            strategy.name, strategy.description = type_names[strategy_type]

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


def skip_to_unanswered(
    state: ConversationState,
    builder: "StrategyBuilder",  # noqa: F821
) -> ConversationResponse:
    """Find the first unanswered question and skip to it."""
    strategy = state.partial_strategy

    # Check what's filled and advance state accordingly
    if strategy.name is None:
        state.current_step = "strategy_type"
        return builder.get_initial_question()

    if strategy.universe_type is None:
        state.current_step = "universe_type"
        from utss_llm.conversation.questions import QUESTION_UNIVERSE_TYPE

        return ConversationResponse(
            type=ResponseType.QUESTION,
            message=f"I understand you want a {strategy.name}. Let's configure it.",
            question=QUESTION_UNIVERSE_TYPE,
        )

    if strategy.universe_type == "static" and not strategy.symbols:
        state.current_step = "universe_details"
        from utss_llm.conversation.questions import QUESTION_SYMBOLS

        return ConversationResponse(
            type=ResponseType.QUESTION,
            message="Which symbols would you like to trade?",
            question=QUESTION_SYMBOLS,
        )

    if strategy.entry_indicator is None:
        state.current_step = "entry_indicator"
        return ConversationResponse(
            type=ResponseType.QUESTION,
            message="Which indicator should trigger entries?",
            question=builder._get_entry_indicator_question(state),
        )

    if strategy.entry_threshold is None:
        state.current_step = "entry_params"
        return ConversationResponse(
            type=ResponseType.QUESTION,
            message=f"At what {strategy.entry_indicator} level should we enter?",
            question=builder._get_entry_params_question(strategy.entry_indicator),
        )

    if strategy.exit_threshold is None:
        state.current_step = "exit_params"
        return ConversationResponse(
            type=ResponseType.QUESTION,
            message=f"At what {strategy.exit_indicator} level should we exit?",
            question=builder._get_exit_params_question(strategy.exit_indicator),
        )

    if strategy.sizing_value is None:
        state.current_step = "position_size"
        from utss_llm.conversation.questions import QUESTION_POSITION_SIZE

        return ConversationResponse(
            type=ResponseType.QUESTION,
            message="How should we size positions?",
            question=QUESTION_POSITION_SIZE,
        )

    # If we have enough info, show preview
    state.current_step = "confirm"
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
