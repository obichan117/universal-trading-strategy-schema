"""Tests for utss-llm parser."""

import pytest
from utss_llm import StrategyParser, ParseResult, ParseMode
from utss_llm.providers.base import LLMProvider, LLMResponse


class MockProvider(LLMProvider):
    """Mock provider for testing."""

    def __init__(self, response: str = ""):
        self._response = response

    @property
    def name(self) -> str:
        return "mock"

    @property
    def default_model(self) -> str:
        return "mock-model"

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        return LLMResponse(
            content=self._response,
            model="mock-model",
            tokens_input=10,
            tokens_output=20,
        )


def test_parse_mode_enum():
    """Test ParseMode enum values."""
    assert ParseMode.BEGINNER == "beginner"
    assert ParseMode.ADVANCED == "advanced"


def test_parse_result_dataclass():
    """Test ParseResult dataclass."""
    result = ParseResult(success=True)
    assert result.success is True
    assert result.strategy is None
    assert result.errors == []


def test_parser_initialization():
    """Test StrategyParser initialization."""
    provider = MockProvider()
    parser = StrategyParser(provider=provider)

    assert parser.provider == provider
    assert parser.mode == ParseMode.ADVANCED
    assert parser.validate is True


def test_parser_with_beginner_mode():
    """Test parser with beginner mode."""
    provider = MockProvider()
    parser = StrategyParser(provider=provider, mode=ParseMode.BEGINNER)

    assert parser.mode == ParseMode.BEGINNER


def test_llm_response_tokens():
    """Test LLMResponse token counting."""
    response = LLMResponse(
        content="test",
        model="test-model",
        tokens_input=100,
        tokens_output=50,
    )

    assert response.tokens_total == 150
