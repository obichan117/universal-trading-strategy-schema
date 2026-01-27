"""
Base LLM provider interface.

All provider implementations must inherit from LLMProvider.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    tokens_input: int = 0
    tokens_output: int = 0
    finish_reason: str | None = None
    raw_response: Any = None

    @property
    def tokens_total(self) -> int:
        """Total tokens used."""
        return self.tokens_input + self.tokens_output


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Implementations should handle:
    - Authentication
    - API calls
    - Response parsing
    - Error handling
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'openai', 'anthropic')."""
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model to use."""
        ...

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            prompt: User prompt/message
            system: Optional system message
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            **kwargs: Provider-specific arguments

        Returns:
            LLMResponse with generated content
        """
        ...

    def generate_sync(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Synchronous version of generate().
        """
        import asyncio

        return asyncio.run(
            self.generate(prompt, system, temperature, max_tokens, **kwargs)
        )
