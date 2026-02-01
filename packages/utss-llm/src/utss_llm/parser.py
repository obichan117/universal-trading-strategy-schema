"""
Main strategy parser - converts natural language to UTSS strategies.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import yaml

from utss import Strategy, ValidationError, validate_yaml

from utss_llm.prompts import ADVANCED_TEMPLATE, BEGINNER_TEMPLATE, SYSTEM_PROMPT
from utss_llm.providers.base import LLMProvider


class ParseMode(str, Enum):
    """Parsing modes for strategy generation."""

    BEGINNER = "beginner"  # Interactive Q&A guided flow
    ADVANCED = "advanced"  # One-shot generation


@dataclass
class ParseResult:
    """Result of parsing natural language to strategy."""

    success: bool
    strategy: Strategy | None = None
    yaml_output: str | None = None
    errors: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    tokens_used: int = 0


# Few-shot examples for better LLM output
FEW_SHOT_EXAMPLES = """
## Example 1: RSI Reversal

User: "RSI reversal strategy for tech stocks. Buy when oversold, sell when overbought."

```yaml
info:
  id: rsi_reversal
  name: RSI Reversal Strategy
  version: "1.0"
  description: Mean-reversion strategy using RSI(14) thresholds.
  tags: [reversal, RSI, mean-reversion]

universe:
  type: static
  symbols: [AAPL, MSFT, GOOGL]

signals:
  rsi_14:
    type: indicator
    indicator: RSI
    params:
      period: 14

conditions:
  oversold:
    type: comparison
    left: { $ref: "#/signals/rsi_14" }
    operator: "<"
    right: { type: constant, value: 30 }
  overbought:
    type: comparison
    left: { $ref: "#/signals/rsi_14" }
    operator: ">"
    right: { type: constant, value: 70 }

rules:
  - name: Buy oversold
    when: { $ref: "#/conditions/oversold" }
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 10 }

  - name: Sell overbought
    when: { $ref: "#/conditions/overbought" }
    then:
      type: trade
      direction: sell
      sizing: { type: percent_of_position, percent: 100 }

constraints:
  max_positions: 5
  stop_loss: { percent: 5 }
  no_shorting: true
```

## Example 2: Golden Cross

User: "Moving average crossover strategy on SPY. Enter when 50-day crosses above 200-day."

```yaml
info:
  id: golden_cross
  name: Golden Cross Strategy
  version: "1.0"
  description: Trend-following strategy using SMA 50/200 crossover.
  tags: [trend, moving-average, crossover]

universe:
  type: static
  symbols: [SPY]

rules:
  - name: Golden Cross Entry
    when:
      type: expr
      formula: "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 100 }

  - name: Death Cross Exit
    when:
      type: expr
      formula: "SMA(50)[-1] >= SMA(200)[-1] and SMA(50) < SMA(200)"
    then:
      type: trade
      direction: sell
      sizing: { type: percent_of_position, percent: 100 }

constraints:
  trailing_stop: { percent: 10 }
```

## Example 3: Calendar Strategy

User: "Buy SPY every Monday, sell Friday."

```yaml
info:
  id: weekly_momentum
  name: Weekly Momentum Strategy
  version: "1.0"
  description: Calendar-based strategy trading the weekly cycle.
  tags: [calendar, momentum, weekly]

universe:
  type: static
  symbols: [SPY]

signals:
  day_of_week:
    type: calendar
    field: day_of_week

rules:
  - name: Monday Entry
    when:
      type: comparison
      left: { $ref: "#/signals/day_of_week" }
      operator: "="
      right: { type: constant, value: 0 }
    then:
      type: trade
      direction: buy
      sizing: { type: percent_of_equity, percent: 50 }

  - name: Friday Exit
    when:
      type: comparison
      left: { $ref: "#/signals/day_of_week" }
      operator: "="
      right: { type: constant, value: 4 }
    then:
      type: trade
      direction: sell
      sizing: { type: percent_of_position, percent: 100 }

constraints:
  no_shorting: true

schedule:
  frequency: daily
  trading_days: [monday, friday]
```
"""

# Enhanced system prompt with schema details
ENHANCED_SYSTEM_PROMPT = SYSTEM_PROMPT + """

## UTSS v1.0 Condition Types (IMPORTANT - only use these):
- comparison: { type: comparison, left: signal, operator: "<|<=|=|>=|>|!=", right: signal }
- and: { type: and, conditions: [...] }
- or: { type: or, conditions: [...] }
- not: { type: not, condition: {...} }
- expr: { type: expr, formula: "..." } - For crossovers, ranges, complex patterns
- always: { type: always } - For unconditional rules

## Signal Types:
- price: { type: price, field: close|open|high|low|volume }
- indicator: { type: indicator, indicator: SMA|EMA|RSI|MACD|BB|ATR|..., params: {...} }
- calendar: { type: calendar, field: day_of_week|is_month_end|... }
- constant: { type: constant, value: number }
- $ref: Reference to defined signals/conditions

## Common expr formulas:
- Crossover: "SMA(50)[-1] <= SMA(200)[-1] and SMA(50) > SMA(200)"
- RSI range: "RSI(14) >= 40 and RSI(14) <= 60"
- Breakout: "close > BB(20, 2).upper"

## Sizing Types:
- percent_of_equity: { type: percent_of_equity, percent: 10 }
- percent_of_position: { type: percent_of_position, percent: 100 }
- fixed_amount: { type: fixed_amount, amount: 10000 }

## Required fields:
- info.id (lowercase with underscores)
- info.name
- info.version (e.g., "1.0")
- universe.type and universe.symbols (for static)
- At least one rule with when and then

""" + FEW_SHOT_EXAMPLES


class StrategyParser:
    """
    Parse natural language descriptions into UTSS strategies.

    Example:
        ```python
        from utss_llm import StrategyParser
        from utss_llm.providers import AnthropicProvider

        parser = StrategyParser(
            provider=AnthropicProvider(api_key="...")
        )

        result = await parser.parse(
            "RSI reversal strategy for AAPL. "
            "Buy when RSI drops below 30, sell when above 70."
        )

        if result.success:
            print(result.strategy.info.name)
        ```
    """

    def __init__(
        self,
        provider: LLMProvider,
        mode: ParseMode = ParseMode.ADVANCED,
        validate: bool = True,
    ):
        """
        Initialize the parser.

        Args:
            provider: LLM provider to use for generation
            mode: Parsing mode (beginner or advanced)
            validate: Whether to validate generated strategies
        """
        self.provider = provider
        self.mode = mode
        self.validate = validate

    async def parse(
        self,
        description: str,
        context: dict[str, Any] | None = None,
    ) -> ParseResult:
        """
        Parse a natural language description into a UTSS strategy.

        Args:
            description: Natural language strategy description
            context: Optional context (market, symbols, etc.)

        Returns:
            ParseResult with strategy or errors
        """
        # Build context string
        context_str = ""
        if context:
            context_parts = []
            if "symbols" in context:
                context_parts.append(f"Symbols: {', '.join(context['symbols'])}")
            if "market" in context:
                context_parts.append(f"Market: {context['market']}")
            if "timeframe" in context:
                context_parts.append(f"Timeframe: {context['timeframe']}")
            if context_parts:
                context_str = "Context:\n" + "\n".join(context_parts)

        # Build prompt
        prompt = ADVANCED_TEMPLATE.format(
            description=description,
            context=context_str,
        )

        # Call LLM
        try:
            response = await self.provider.generate(
                prompt=prompt,
                system=ENHANCED_SYSTEM_PROMPT,
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=4096,
            )
        except Exception as e:
            return ParseResult(
                success=False,
                errors=[f"LLM provider error: {str(e)}"],
                tokens_used=0,
            )

        # Extract YAML from response
        yaml_content = self._extract_yaml(response.content)
        if not yaml_content:
            return ParseResult(
                success=False,
                errors=["No valid YAML found in LLM response"],
                tokens_used=response.tokens_total,
            )

        # Parse and validate
        if self.validate:
            try:
                strategy = validate_yaml(yaml_content)
                return ParseResult(
                    success=True,
                    strategy=strategy,
                    yaml_output=yaml_content,
                    assumptions=self._extract_assumptions(response.content),
                    tokens_used=response.tokens_total,
                )
            except ValidationError as e:
                return ParseResult(
                    success=False,
                    yaml_output=yaml_content,
                    errors=[err["message"] for err in e.errors],
                    tokens_used=response.tokens_total,
                )
            except yaml.YAMLError as e:
                return ParseResult(
                    success=False,
                    yaml_output=yaml_content,
                    errors=[f"YAML parse error: {str(e)}"],
                    tokens_used=response.tokens_total,
                )
        else:
            # Return without validation
            try:
                data = yaml.safe_load(yaml_content)
                strategy = Strategy.model_validate(data) if data else None
            except Exception:
                strategy = None

            return ParseResult(
                success=True,
                strategy=strategy,
                yaml_output=yaml_content,
                tokens_used=response.tokens_total,
            )

    async def parse_interactive(
        self,
        description: str,
        answers: dict[str, str] | None = None,
    ) -> ParseResult | list[str]:
        """
        Parse with interactive Q&A (beginner mode).

        If clarification is needed, returns list of questions.
        If complete, returns ParseResult.

        Args:
            description: Natural language strategy description
            answers: Answers to previous questions (if any)

        Returns:
            ParseResult if complete, or list of questions
        """
        # Build prompt with answers if provided
        if answers:
            answers_str = "\n".join(f"- {k}: {v}" for k, v in answers.items())
            enhanced_description = f"{description}\n\nAdditional details:\n{answers_str}"
        else:
            enhanced_description = description

        # First, check if we need clarification
        clarification_prompt = f"""Analyze this trading strategy description and determine if you need clarification:

"{enhanced_description}"

If the description is complete enough to generate a UTSS strategy, respond with:
COMPLETE

If you need clarification, respond with up to 3 specific questions, one per line, starting with "Q:".
Focus on: symbols, entry/exit conditions, position sizing, risk management.

Only ask questions if truly necessary. Most strategies can use sensible defaults."""

        try:
            response = await self.provider.generate(
                prompt=clarification_prompt,
                system="You are a trading strategy assistant. Be concise.",
                temperature=0.3,
                max_tokens=500,
            )
        except Exception as e:
            return ParseResult(
                success=False,
                errors=[f"LLM provider error: {str(e)}"],
            )

        content = response.content.strip()

        # Check if complete or needs questions
        if "COMPLETE" in content.upper() or answers:
            # Generate the strategy
            return await self.parse(enhanced_description)
        else:
            # Extract questions
            questions = []
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("Q:"):
                    questions.append(line[2:].strip())
                elif line.startswith("-") or line.startswith("•"):
                    questions.append(line[1:].strip())
                elif "?" in line and len(line) > 10:
                    questions.append(line)

            if not questions:
                # No questions, just generate
                return await self.parse(enhanced_description)

            return questions[:3]  # Max 3 questions

    def parse_sync(
        self,
        description: str,
        context: dict[str, Any] | None = None,
    ) -> ParseResult:
        """
        Synchronous version of parse().

        Args:
            description: Natural language strategy description
            context: Optional context

        Returns:
            ParseResult with strategy or errors
        """
        import asyncio

        return asyncio.run(self.parse(description, context))

    def _extract_yaml(self, content: str) -> str | None:
        """Extract YAML content from LLM response."""
        # Try to find YAML in code blocks
        yaml_pattern = r"```(?:yaml|yml)?\s*\n(.*?)```"
        matches = re.findall(yaml_pattern, content, re.DOTALL)

        if matches:
            # Return the longest match (most complete)
            return max(matches, key=len).strip()

        # Try to find YAML starting with common keys
        lines = content.split("\n")
        yaml_start = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(("info:", "$schema:", "---")):
                yaml_start = i
                break

        if yaml_start >= 0:
            # Extract from start to end or next non-YAML content
            yaml_lines = []
            for line in lines[yaml_start:]:
                # Stop at obvious non-YAML content
                if line.strip().startswith(("Note:", "Assumptions:", "---")) and yaml_lines:
                    break
                yaml_lines.append(line)

            return "\n".join(yaml_lines).strip()

        return None

    def _extract_assumptions(self, content: str) -> list[str]:
        """Extract any assumptions mentioned by the LLM."""
        assumptions = []

        # Look for assumptions section
        assumption_patterns = [
            r"Assumptions?:\s*\n((?:[-•*]\s*.+\n?)+)",
            r"I (?:assumed|am assuming)(.+?)(?:\.|$)",
            r"Default(?:s|ing to)?:?\s*(.+?)(?:\.|$)",
        ]

        for pattern in assumption_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, str):
                    # Clean up and split by bullets
                    for line in match.split("\n"):
                        line = re.sub(r"^[-•*]\s*", "", line.strip())
                        if line and len(line) > 5:
                            assumptions.append(line)

        return assumptions[:5]  # Max 5 assumptions
