"""
Local Ollama provider implementation.

Requires: pip install utss-llm[local]
"""

from typing import Any

from utss_llm.providers.base import LLMProvider, LLMResponse


class LocalProvider(LLMProvider):
    """
    Local Ollama provider for running models locally.

    Example:
        ```python
        provider = LocalProvider(model="llama3.1")
        response = await provider.generate("Create a trading strategy")
        ```
    """

    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
    ):
        """
        Initialize local Ollama provider.

        Args:
            model: Model to use (default: llama3.1)
            host: Ollama host URL (default: http://localhost:11434)
        """
        try:
            import ollama
        except ImportError:
            raise ImportError(
                "Ollama package not installed. "
                "Install with: pip install utss-llm[local]"
            )

        self._ollama = ollama
        self._model = model or self.default_model
        self._host = host

        if host:
            self._client = ollama.AsyncClient(host=host)
        else:
            self._client = ollama.AsyncClient()

    @property
    def name(self) -> str:
        return "local"

    @property
    def default_model(self) -> str:
        return "llama3.1"

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response using local Ollama."""
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat(
            model=kwargs.get("model", self._model),
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        )

        # Extract token counts if available
        tokens_input = response.get("prompt_eval_count", 0)
        tokens_output = response.get("eval_count", 0)

        return LLMResponse(
            content=response["message"]["content"],
            model=response.get("model", self._model),
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            finish_reason=response.get("done_reason"),
            raw_response=response,
        )
