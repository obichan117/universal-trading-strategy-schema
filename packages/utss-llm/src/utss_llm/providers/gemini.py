"""
Google Gemini provider implementation.

Requires: pip install utss-llm[gemini]
"""

from typing import Any

from utss_llm.providers.base import LLMProvider, LLMResponse


class GeminiProvider(LLMProvider):
    """
    Google Gemini API provider.

    Example:
        ```python
        provider = GeminiProvider(api_key="...")
        response = await provider.generate("Create a trading strategy")
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key (or set GOOGLE_API_KEY env var)
            model: Model to use (default: gemini-1.5-flash)
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "Google Generative AI package not installed. "
                "Install with: pip install utss-llm[gemini]"
            )

        if api_key:
            genai.configure(api_key=api_key)

        self._genai = genai
        self._model = model or self.default_model

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return "gemini-1.5-flash"

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate response using Gemini API."""
        model = self._genai.GenerativeModel(
            model_name=kwargs.get("model", self._model),
            system_instruction=system,
        )

        generation_config = self._genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = await model.generate_content_async(
            prompt,
            generation_config=generation_config,
        )

        # Extract token counts if available
        tokens_input = 0
        tokens_output = 0
        if hasattr(response, "usage_metadata"):
            tokens_input = getattr(response.usage_metadata, "prompt_token_count", 0)
            tokens_output = getattr(response.usage_metadata, "candidates_token_count", 0)

        return LLMResponse(
            content=response.text if response.text else "",
            model=self._model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            finish_reason=None,
            raw_response=response,
        )
