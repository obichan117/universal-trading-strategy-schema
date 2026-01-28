"""
Prompt templates for strategy generation.

Contains system prompts, few-shot examples, and templates
for different parsing modes.
"""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt template by name."""
    path = _PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {name}")
    return path.read_text()


# System prompt for strategy generation
SYSTEM_PROMPT = """You are a trading strategy expert that converts natural language descriptions into UTSS (Universal Trading Strategy Schema) YAML format.

UTSS is a composable schema for expressing trading strategies with:
- Signals: Numeric values (price, indicators, fundamentals)
- Conditions: Boolean expressions (comparison, and/or/not, expr)
- Rules: When (condition) → Then (action)
- Sizing: Position sizing methods

Always output valid YAML that conforms to the UTSS v1.0 schema.
Be specific about indicator parameters and use sensible defaults when not specified.
"""

# Template for advanced (one-shot) mode
ADVANCED_TEMPLATE = """Convert this trading strategy description to UTSS YAML format:

{description}

{context}

Output only the YAML, no explanations. Start with:
```yaml
info:
  id: ..."""

# Template for beginner (guided) mode
BEGINNER_TEMPLATE = """I'll help you create a trading strategy. Based on your description:

"{description}"

I need to clarify a few things:

{questions}

Please answer these questions so I can generate the complete strategy."""


__all__ = [
    "load_prompt",
    "SYSTEM_PROMPT",
    "ADVANCED_TEMPLATE",
    "BEGINNER_TEMPLATE",
]
