"""
Anthropic provider implementation.

Requires: pip install utss-llm[anthropic]
"""

from typing import Any

from utss_llm.providers.base import LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    """
    Anthropic API provider (Claude models).

    Example:
        ```python
        provider = AnthropicProvider(api_key="sk-ant-...")
        response = await provider.generate("Create a trading strategy")
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            model: Model to use (default: claude-sonnet-4-20250514)
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "Anthropic package not installed. "
                "Install with: pip install utss-llm[anthropic]"
            )

        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model or self.default_model

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def default_model(self) -> str:
        return "claude-sonnet-4-20250514"

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response using Anthropic API."""
        response = await self._client.messages.create(
            model=kwargs.get("model", self._model),
            max_tokens=max_tokens,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            **{k: v for k, v in kwargs.items() if k != "model"},
        )

        content = ""
        if response.content:
            content = response.content[0].text

        return LLMResponse(
            content=content,
            model=response.model,
            tokens_input=response.usage.input_tokens,
            tokens_output=response.usage.output_tokens,
            finish_reason=response.stop_reason,
            raw_response=response,
        )
