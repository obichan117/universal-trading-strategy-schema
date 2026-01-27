# utss-llm - LLM Strategy Parser

Convert natural language descriptions into validated [UTSS](https://github.com/obichan117/utss) trading strategies.

## Installation

```bash
# Core package
pip install utss-llm

# With specific provider
pip install utss-llm[openai]      # OpenAI (GPT-4)
pip install utss-llm[anthropic]   # Anthropic (Claude)
pip install utss-llm[gemini]      # Google (Gemini)
pip install utss-llm[local]       # Ollama (local models)

# All providers
pip install utss-llm[all]
```

## Quick Start

```python
from utss_llm import StrategyParser
from utss_llm.providers import get_anthropic_provider

# Initialize provider
AnthropicProvider = get_anthropic_provider()
provider = AnthropicProvider(api_key="sk-ant-...")

# Create parser
parser = StrategyParser(provider=provider)

# Parse natural language to strategy
result = parser.parse_sync(
    "RSI reversal strategy for AAPL. "
    "Buy when RSI drops below 30, sell when above 70. "
    "Use 10% of equity per trade with 5% stop loss."
)

if result.success:
    print(f"Strategy: {result.strategy.info.name}")
    print(f"YAML:\n{result.yaml_output}")
else:
    print(f"Errors: {result.errors}")
```

## Providers

### OpenAI

```python
from utss_llm.providers import get_openai_provider

OpenAIProvider = get_openai_provider()
provider = OpenAIProvider(
    api_key="sk-...",  # or set OPENAI_API_KEY env var
    model="gpt-4o",    # default
)
```

### Anthropic

```python
from utss_llm.providers import get_anthropic_provider

AnthropicProvider = get_anthropic_provider()
provider = AnthropicProvider(
    api_key="sk-ant-...",  # or set ANTHROPIC_API_KEY env var
    model="claude-sonnet-4-20250514",  # default
)
```

### Google Gemini

```python
from utss_llm.providers import get_gemini_provider

GeminiProvider = get_gemini_provider()
provider = GeminiProvider(
    api_key="...",  # or set GOOGLE_API_KEY env var
    model="gemini-1.5-flash",  # default
)
```

### Local (Ollama)

```python
from utss_llm.providers import get_local_provider

LocalProvider = get_local_provider()
provider = LocalProvider(
    model="llama3.1",  # default
    host="http://localhost:11434",  # default
)
```

## Parsing Modes

### Advanced Mode (Default)

One-shot generation - the LLM generates the complete strategy immediately.

```python
parser = StrategyParser(provider=provider, mode=ParseMode.ADVANCED)
result = parser.parse_sync("Buy AAPL when RSI < 30")
```

### Beginner Mode

Interactive Q&A - the parser asks clarifying questions before generating.

```python
parser = StrategyParser(provider=provider, mode=ParseMode.BEGINNER)

# First call may return questions
result = parser.parse_sync("Create a momentum strategy")
if isinstance(result, list):
    print("Questions:", result)
    # Answer questions and call again
    result = parser.parse_sync("Create a momentum strategy", answers={...})
```

## Async Usage

```python
import asyncio
from utss_llm import StrategyParser

async def main():
    parser = StrategyParser(provider=provider)
    result = await parser.parse("Buy when RSI < 30")
    print(result.strategy)

asyncio.run(main())
```

## ParseResult

```python
@dataclass
class ParseResult:
    success: bool                    # Whether parsing succeeded
    strategy: Strategy | None        # Validated UTSS Strategy object
    yaml_output: str | None          # Generated YAML string
    errors: list[str]                # Validation or generation errors
    assumptions: list[str]           # Assumptions made by the LLM
    suggestions: list[str]           # Suggestions for improvement
    tokens_used: int                 # Total tokens consumed
```

## License

MIT
