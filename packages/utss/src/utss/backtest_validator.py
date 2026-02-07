"""
UTSS Backtest Configuration Validation utilities
"""

from typing import Any

import yaml
from pydantic import ValidationError as PydanticValidationError

from utss.backtest_models import BacktestSpec
from utss.validator import ValidationError


def validate_backtest(data: dict[str, Any]) -> BacktestSpec:
    """
    Validate a backtest configuration dictionary.

    Args:
        data: Backtest config as a dictionary

    Returns:
        Validated BacktestSpec object

    Raises:
        ValidationError: If validation fails
    """
    try:
        return BacktestSpec.model_validate(data)
    except PydanticValidationError as e:
        errors = [
            {"path": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
            for err in e.errors()
        ]
        raise ValidationError(
            f"Backtest config validation failed with {len(errors)} error(s)", errors
        )


def validate_backtest_yaml(yaml_content: str) -> BacktestSpec:
    """
    Parse and validate a backtest configuration YAML string.

    Args:
        yaml_content: YAML string containing backtest configuration

    Returns:
        Validated BacktestSpec object

    Raises:
        ValidationError: If parsing or validation fails
    """
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValidationError(
            f"YAML parse error: {e}", [{"path": "/", "message": str(e)}]
        )

    if not isinstance(data, dict):
        raise ValidationError(
            "Invalid YAML: expected a mapping at root",
            [{"path": "/", "message": "Expected object"}],
        )

    return validate_backtest(data)
