"""
Main strategy parser - converts natural language to UTSS strategies.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from utss import Strategy, validate_yaml, ValidationError

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

        result = parser.parse(
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
        # TODO: Implement actual parsing logic
        # 1. Build prompt with system message + examples
        # 2. Call LLM provider
        # 3. Extract YAML from response
        # 4. Validate against UTSS schema
        # 5. Return result

        raise NotImplementedError("Parser implementation coming soon")

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
        raise NotImplementedError("Interactive parsing coming soon")

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
