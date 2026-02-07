"""Extensible enum validators.

These create validated string types that accept both core enum values
and prefixed extension values (custom:, talib:, platform:, etc.)
"""

import re
from enum import Enum
from typing import Annotated

from pydantic import AfterValidator, Field

from utss.models.enums import (
    EventType,
    FundamentalMetric,
    IndicatorType,
)

# Prefix patterns for extensible enums
INDICATOR_PREFIXES = [
    r"^custom:[a-zA-Z0-9_]+$",
    r"^talib:[A-Z0-9_]+$",
    r"^platform:[a-z]+:[a-zA-Z0-9_]+$",
]

FUNDAMENTAL_PREFIXES = [
    r"^custom:[a-zA-Z0-9_]+$",
    r"^provider:[a-z]+:[a-zA-Z0-9_]+$",
]

EVENT_PREFIXES = [
    r"^custom:[a-zA-Z0-9_]+$",
    r"^calendar:[a-zA-Z0-9_]+$",
]

def _make_extensible_validator(enum_class: type[Enum], prefixes: list[str]):
    """Create a validator that accepts enum values or prefixed extensions."""
    core_values = {e.value for e in enum_class}
    compiled_patterns = [re.compile(p) for p in prefixes]

    def validator(v: str) -> str:
        if v in core_values:
            return v
        for pattern in compiled_patterns:
            if pattern.match(v):
                return v
        valid_prefixes = ", ".join(p.split(":")[0].lstrip("^") + ":" for p in prefixes)
        raise ValueError(
            f"Invalid value '{v}'. Must be a core {enum_class.__name__} value "
            f"or use extension prefix ({valid_prefixes})"
        )

    return validator


# Extensible type aliases
ExtensibleIndicator = Annotated[
    str,
    AfterValidator(_make_extensible_validator(IndicatorType, INDICATOR_PREFIXES)),
    Field(description="Technical indicator (core or custom:, talib:, platform: prefixed)"),
]

ExtensibleFundamental = Annotated[
    str,
    AfterValidator(_make_extensible_validator(FundamentalMetric, FUNDAMENTAL_PREFIXES)),
    Field(description="Fundamental metric (core or custom:, provider: prefixed)"),
]

ExtensibleEvent = Annotated[
    str,
    AfterValidator(_make_extensible_validator(EventType, EVENT_PREFIXES)),
    Field(description="Event type (core or custom:, calendar: prefixed)"),
]

