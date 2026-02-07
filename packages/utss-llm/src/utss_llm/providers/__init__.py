"""
LLM provider implementations.

Each provider wraps a specific LLM API (OpenAI, Anthropic, etc.)
and provides a consistent interface for strategy generation.
"""

from utss_llm.providers.base import LLMProvider, LLMResponse

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "get_openai_provider",
    "get_anthropic_provider",
    "get_gemini_provider",
    "get_local_provider",
]

# Lazy imports for optional dependencies


def get_openai_provider():
    """Get OpenAI provider (requires openai package)."""
    from utss_llm.providers.openai import OpenAIProvider

    return OpenAIProvider


def get_anthropic_provider():
    """Get Anthropic provider (requires anthropic package)."""
    from utss_llm.providers.anthropic import AnthropicProvider

    return AnthropicProvider


def get_gemini_provider():
    """Get Gemini provider (requires google-generativeai package)."""
    from utss_llm.providers.gemini import GeminiProvider

    return GeminiProvider


def get_local_provider():
    """Get local Ollama provider (requires ollama package)."""
    from utss_llm.providers.local import LocalProvider

    return LocalProvider
