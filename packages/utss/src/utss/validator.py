"""
UTSS Validation utilities
"""

from typing import Any

import yaml
from pydantic import ValidationError as PydanticValidationError

from utss.models import Strategy


class ValidationError(Exception):
    """Validation error with detailed error information."""

    def __init__(self, message: str, errors: list[dict[str, str]]) -> None:
        super().__init__(message)
        self.errors = errors


def validate_strategy(data: dict[str, Any]) -> Strategy:
    """
    Validate a strategy dictionary against the UTSS schema.

    Args:
        data: Strategy data as a dictionary

    Returns:
        Validated Strategy object

    Raises:
        ValidationError: If validation fails
    """
    try:
        return Strategy.model_validate(data)
    except PydanticValidationError as e:
        errors = [
            {"path": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
            for err in e.errors()
        ]
        raise ValidationError(f"Strategy validation failed with {len(errors)} error(s)", errors)


def validate_yaml(yaml_content: str) -> Strategy:
    """
    Parse and validate a YAML string.

    Args:
        yaml_content: YAML string containing strategy definition

    Returns:
        Validated Strategy object

    Raises:
        ValidationError: If parsing or validation fails
    """
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValidationError(f"YAML parse error: {e}", [{"path": "/", "message": str(e)}])

    if not isinstance(data, dict):
        raise ValidationError(
            "Invalid YAML: expected a mapping at root", [{"path": "/", "message": "Expected object"}]
        )

    return validate_strategy(data)
