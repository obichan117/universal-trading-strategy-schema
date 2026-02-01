"""Tests for utss-llm parser."""

import pytest

from utss_llm import ParseMode, ParseResult, StrategyParser
from utss_llm.providers.base import LLMProvider, LLMResponse


# Sample valid YAML for testing
VALID_RSI_YAML = """```yaml
info:
  id: rsi_test
  name: RSI Test Strategy
  version: "1.0"

universe:
  type: static
  symbols: [AAPL]

rules:
  - name: Buy oversold
    when:
      type: comparison
      left:
        type: indicator
        indicator: RSI
        params:
          period: 14
      operator: "<"
      right:
        type: constant
        value: 30
    then:
      type: trade
      direction: buy
      sizing:
        type: percent_of_equity
        percent: 10
```"""

INVALID_YAML = """```yaml
info:
  id: test
  # Missing required fields
```"""


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


@pytest.mark.asyncio
async def test_parse_valid_yaml():
    """Test parsing with valid YAML response."""
    provider = MockProvider(response=VALID_RSI_YAML)
    parser = StrategyParser(provider=provider)

    result = await parser.parse("RSI strategy for AAPL")

    assert result.success is True
    assert result.strategy is not None
    assert result.strategy.info.id == "rsi_test"
    assert result.yaml_output is not None
    assert result.tokens_used == 30


@pytest.mark.asyncio
async def test_parse_invalid_yaml():
    """Test parsing with invalid YAML response."""
    provider = MockProvider(response=INVALID_YAML)
    parser = StrategyParser(provider=provider)

    result = await parser.parse("Some strategy")

    assert result.success is False
    assert result.strategy is None
    assert len(result.errors) > 0


@pytest.mark.asyncio
async def test_parse_no_yaml():
    """Test parsing when no YAML is found."""
    provider = MockProvider(response="I don't understand what you want.")
    parser = StrategyParser(provider=provider)

    result = await parser.parse("Some strategy")

    assert result.success is False
    assert "No valid YAML found" in result.errors[0]


@pytest.mark.asyncio
async def test_parse_with_context():
    """Test parsing with context."""
    provider = MockProvider(response=VALID_RSI_YAML)
    parser = StrategyParser(provider=provider)

    result = await parser.parse(
        "RSI strategy",
        context={"symbols": ["AAPL", "MSFT"], "market": "US"},
    )

    assert result.success is True


@pytest.mark.asyncio
async def test_parse_without_validation():
    """Test parsing without validation."""
    provider = MockProvider(response=VALID_RSI_YAML)
    parser = StrategyParser(provider=provider, validate=False)

    result = await parser.parse("RSI strategy")

    assert result.success is True
    assert result.yaml_output is not None


def test_parse_sync():
    """Test synchronous parse."""
    provider = MockProvider(response=VALID_RSI_YAML)
    parser = StrategyParser(provider=provider)

    result = parser.parse_sync("RSI strategy")

    assert result.success is True
    assert result.strategy is not None


def test_extract_yaml_from_code_block():
    """Test YAML extraction from code block."""
    provider = MockProvider()
    parser = StrategyParser(provider=provider)

    yaml_content = parser._extract_yaml(VALID_RSI_YAML)
    assert yaml_content is not None
    assert "info:" in yaml_content


def test_extract_yaml_without_code_block():
    """Test YAML extraction without code block."""
    provider = MockProvider()
    parser = StrategyParser(provider=provider)

    raw_yaml = """info:
  id: test
  name: Test
  version: "1.0"

universe:
  type: static
  symbols: [AAPL]"""

    yaml_content = parser._extract_yaml(raw_yaml)
    assert yaml_content is not None
    assert "info:" in yaml_content


def test_extract_assumptions():
    """Test assumption extraction."""
    provider = MockProvider()
    parser = StrategyParser(provider=provider)

    content = """Here's your strategy:
```yaml
info:
  id: test
```

Assumptions:
- Used default RSI period of 14
- Assumed US market hours
"""

    assumptions = parser._extract_assumptions(content)
    assert len(assumptions) >= 1


@pytest.mark.asyncio
async def test_parse_interactive_complete():
    """Test interactive parse when description is complete."""
    provider = MockProvider(response="COMPLETE")
    parser = StrategyParser(provider=provider, mode=ParseMode.BEGINNER)

    # First call should return COMPLETE, but we need mock to return YAML for parse
    class TwoResponseProvider(LLMProvider):
        def __init__(self):
            self._call_count = 0

        @property
        def name(self) -> str:
            return "mock"

        @property
        def default_model(self) -> str:
            return "mock-model"

        async def generate(self, prompt, **kwargs) -> LLMResponse:
            self._call_count += 1
            if self._call_count == 1:
                return LLMResponse(content="COMPLETE", model="mock", tokens_input=5, tokens_output=5)
            return LLMResponse(content=VALID_RSI_YAML, model="mock", tokens_input=10, tokens_output=20)

    parser = StrategyParser(provider=TwoResponseProvider(), mode=ParseMode.BEGINNER)
    result = await parser.parse_interactive("Buy AAPL when RSI is below 30")

    assert isinstance(result, ParseResult)
    assert result.success is True


@pytest.mark.asyncio
async def test_parse_interactive_needs_clarification():
    """Test interactive parse when clarification is needed."""
    questions_response = """Q: What symbols do you want to trade?
Q: What position size should we use?
Q: What's your risk tolerance?"""

    provider = MockProvider(response=questions_response)
    parser = StrategyParser(provider=provider, mode=ParseMode.BEGINNER)

    result = await parser.parse_interactive("A trading strategy")

    assert isinstance(result, list)
    assert len(result) <= 3
    assert any("symbol" in q.lower() for q in result)
