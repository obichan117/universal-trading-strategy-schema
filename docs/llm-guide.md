# LLM Integration Guide

`utss-llm` provides tools for building UTSS strategies using natural language and large language models.

## Installation

```bash
pip install utss-llm
```

For specific providers, install with extras:

```bash
pip install utss-llm[anthropic]  # Claude support
pip install utss-llm[openai]     # GPT support
pip install utss-llm[all]        # All providers
```

## Provider Setup

### Anthropic (Claude)

```python
from utss_llm.providers import AnthropicProvider

provider = AnthropicProvider(
    api_key="your-api-key",  # Or set ANTHROPIC_API_KEY env var
    model="claude-sonnet-4-20250514",  # Optional, defaults to latest
)
```

### OpenAI (GPT)

```python
from utss_llm.providers import OpenAIProvider

provider = OpenAIProvider(
    api_key="your-api-key",  # Or set OPENAI_API_KEY env var
    model="gpt-4",
)
```

### Google Gemini

```python
from utss_llm.providers import GeminiProvider

provider = GeminiProvider(
    api_key="your-api-key",  # Or set GOOGLE_API_KEY env var
    model="gemini-pro",
)
```

### Local Models (Ollama)

```python
from utss_llm.providers import LocalProvider

provider = LocalProvider(
    base_url="http://localhost:11434",
    model="llama2",
)
```

## StrategyParser (One-Shot Generation)

Generate complete UTSS strategies from natural language descriptions.

### Basic Usage

```python
from utss_llm import StrategyParser
from utss_llm.providers import AnthropicProvider

# Setup
provider = AnthropicProvider()
parser = StrategyParser(provider=provider)

# Parse natural language to strategy
result = await parser.parse(
    "RSI reversal strategy for AAPL. "
    "Buy when RSI drops below 30, sell when above 70."
)

if result.success:
    print(result.yaml_output)
    # info:
    #   id: rsi_reversal
    #   name: RSI Reversal Strategy
    #   ...
else:
    print(f"Errors: {result.errors}")
```

### With Context

Provide additional context for better results:

```python
result = await parser.parse(
    "Mean reversion strategy using Bollinger Bands",
    context={
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "market": "US",
        "timeframe": "daily",
    },
)
```

### Synchronous Usage

```python
# Use parse_sync for non-async contexts
result = parser.parse_sync("RSI strategy for tech stocks")
```

### ParseResult

The result object contains:

```python
@dataclass
class ParseResult:
    success: bool                # Whether parsing succeeded
    strategy: Strategy | None    # Validated UTSS Strategy object
    yaml_output: str | None      # Generated YAML
    errors: list[str]            # Any validation errors
    assumptions: list[str]       # Assumptions made by the LLM
    tokens_used: int             # Total tokens consumed
```

## ConversationSession (Guided Building)

Build strategies interactively with step-by-step guidance.

### Basic Flow

```python
from utss_llm.conversation import ConversationSession, create_session

# Create session
session = create_session(provider=provider)

# Start conversation
response = await session.start()

# Interactive loop
while response.needs_input:
    print(response.message)

    if response.question:
        for i, opt in enumerate(response.question.options, 1):
            print(f"  {i}. {opt.label}")

    user_input = input("> ")
    response = await session.answer(user_input)

# Get final strategy
if response.is_complete:
    print(response.strategy_yaml)
```

### Smart Start

When using an LLM provider, the session can extract information from an initial description:

```python
session = ConversationSession(provider=provider, use_llm=True)

# Provide initial description - LLM extracts what it can
response = await session.start(
    "I want an RSI mean reversion strategy for tech stocks, "
    "buy at 30, sell at 70, with 5% stop loss"
)

# Session skips to first unanswered question
# (e.g., position sizing if not mentioned)
```

### Revising Strategies

Modify strategies after building:

```python
# Change thresholds
response = await session.revise("change RSI entry to 25")

# Update stop loss
response = await session.revise("set stop loss to 7%")

# Adjust sizing
response = await session.revise("increase position size to 15%")
```

### Session Management

```python
from utss_llm.conversation import create_session, get_session, delete_session

# Create and store session
session = create_session(provider=provider)
session_id = session.session_id

# Later: retrieve session
session = get_session(session_id)
if session:
    response = await session.answer("RSI")

# Cleanup
delete_session(session_id)
```

### Response Types

```python
from utss_llm.conversation import ResponseType

# Question - needs user input
if response.type == ResponseType.QUESTION:
    print(response.question.text)
    for opt in response.question.options:
        print(f"  - {opt.label}: {opt.description}")

# Confirmation - showing preview for approval
if response.type == ResponseType.CONFIRMATION:
    print(response.preview_yaml)
    # User confirms or requests changes

# Complete - strategy is done
if response.type == ResponseType.COMPLETE:
    print(response.strategy_yaml)

# Preview - after revision
if response.type == ResponseType.PREVIEW:
    print(response.preview_yaml)
```

## Parse Modes

### Beginner Mode (Default)

Step-by-step guided flow with predefined options:

```python
from utss_llm import ParseMode

session = ConversationSession(mode=ParseMode.BEGINNER)
```

### Advanced Mode

For experienced users - one-shot generation:

```python
parser = StrategyParser(mode=ParseMode.ADVANCED)
```

## Without LLM (Guided Only)

You can use the conversation builder without an LLM:

```python
# No provider - pure guided flow
session = ConversationSession(use_llm=False)

response = await session.start()
# Uses predefined questions and options only
```

## Customization

### Custom Prompts

Override default prompts:

```python
from utss_llm.prompts import SYSTEM_PROMPT, ADVANCED_TEMPLATE

# Modify prompts
custom_system = SYSTEM_PROMPT + "\nAlways include stop losses."

parser = StrategyParser(provider=provider)
# Pass custom prompts via provider.generate() kwargs
```

### Custom Questions

Extend the question flow:

```python
from utss_llm.conversation import Question, Option

custom_question = Question(
    id="custom_indicator",
    text="Which proprietary indicator should we use?",
    options=[
        Option(id="my_indicator", label="MyIndicator", description="Custom signal"),
    ],
    allow_custom=True,
)
```

## Error Handling

```python
from utss import ValidationError

try:
    result = await parser.parse(description)

    if not result.success:
        for error in result.errors:
            print(f"Validation error: {error}")
except Exception as e:
    print(f"Provider error: {e}")
```

## Best Practices

### 1. Be Specific

More detail = better strategies:

```python
# Less specific
"RSI strategy for stocks"

# More specific
"RSI mean reversion strategy for AAPL, MSFT, GOOGL. "
"Buy when RSI(14) < 30, sell when RSI(14) > 70. "
"Position size 10% of equity, 5% stop loss."
```

### 2. Validate Output

Always validate generated strategies:

```python
from utss import validate_yaml

result = await parser.parse(description)
if result.success:
    # Re-validate to be sure
    strategy = validate_yaml(result.yaml_output)
```

### 3. Use Conversation for Complex Strategies

For strategies with many parameters, the guided conversation often produces better results:

```python
# Better for complex strategies
session = create_session(provider=provider, use_llm=True)
response = await session.start(description)
# ...answer questions...

# vs one-shot for simple strategies
result = await parser.parse("Simple RSI strategy")
```

### 4. Handle Token Limits

Monitor token usage for cost control:

```python
result = await parser.parse(description)
print(f"Tokens used: {result.tokens_used}")

if result.tokens_used > 2000:
    print("Consider simplifying the description")
```

## Complete Example

```python
import asyncio
from utss_llm import StrategyParser
from utss_llm.conversation import create_session
from utss_llm.providers import AnthropicProvider
from pyutss import BacktestEngine, BacktestConfig
from utss import validate_yaml
import pandas as pd

async def main():
    # Setup provider
    provider = AnthropicProvider()

    # Method 1: One-shot parsing
    parser = StrategyParser(provider=provider)
    result = await parser.parse(
        "Golden cross strategy for SPY using 50 and 200 day SMAs"
    )

    if result.success:
        strategy = result.strategy
        print("Strategy generated successfully!")

        # Backtest it
        engine = BacktestEngine()
        data = pd.read_csv("SPY.csv", index_col="date", parse_dates=True)
        backtest_result = engine.run(strategy, data, "SPY")
        print(f"Return: {backtest_result.total_return_pct:.2f}%")

    # Method 2: Guided conversation
    session = create_session(provider=provider, use_llm=True)
    response = await session.start("I want a momentum strategy")

    # Simulate answering questions
    answers = ["trend_following", "static", "AAPL,MSFT", "SMA", "50", "200", "10", "5", "none", "5", "yes"]

    for answer in answers:
        if response.needs_input:
            response = await session.answer(answer)

    if response.is_complete:
        print(response.strategy_yaml)

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### StrategyParser

```python
class StrategyParser:
    def __init__(
        self,
        provider: LLMProvider,
        mode: ParseMode = ParseMode.ADVANCED,
        validate: bool = True,
    ): ...

    async def parse(
        self,
        description: str,
        context: dict | None = None,
    ) -> ParseResult: ...

    def parse_sync(
        self,
        description: str,
        context: dict | None = None,
    ) -> ParseResult: ...
```

### ConversationSession

```python
class ConversationSession:
    provider: LLMProvider | None
    mode: ParseMode
    session_id: str
    state: ConversationState
    use_llm: bool

    async def start(
        self,
        initial_prompt: str | None = None,
    ) -> ConversationResponse: ...

    async def answer(
        self,
        user_answer: str,
    ) -> ConversationResponse: ...

    async def revise(
        self,
        instruction: str,
    ) -> ConversationResponse: ...

    def export(self) -> str | None: ...
    def export_dict(self) -> dict | None: ...
    def get_preview(self) -> str: ...
```
