"""
Prompt templates for strategy generation.

Contains system prompts, few-shot examples, and templates
for different parsing modes.
"""

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

__all__ = [
    "SYSTEM_PROMPT",
    "ADVANCED_TEMPLATE",
]
