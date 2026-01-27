"""
OpenAI provider implementation.

Requires: pip install utss-llm[openai]
"""

from typing import Any

from utss_llm.providers.base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """
    OpenAI API provider (GPT-4, GPT-3.5, etc.).

    Example:
        ```python
        provider = OpenAIProvider(api_key="sk-...")
        response = await provider.generate("Create a trading strategy")
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        organization: str | None = None,
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4o)
            organization: Optional organization ID
        """
        try:
            import openai
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. "
                "Install with: pip install utss-llm[openai]"
            )

        self._client = openai.AsyncOpenAI(
            api_key=api_key,
            organization=organization,
        )
        self._model = model or self.default_model

    @property
    def name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return "gpt-4o"

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response using OpenAI API."""
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=kwargs.get("model", self._model),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **{k: v for k, v in kwargs.items() if k != "model"},
        )

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            tokens_input=usage.prompt_tokens if usage else 0,
            tokens_output=usage.completion_tokens if usage else 0,
            finish_reason=choice.finish_reason,
            raw_response=response,
        )
