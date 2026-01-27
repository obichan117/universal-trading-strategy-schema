"""Tests for UTSS models."""

import pytest
from utss import (
    Strategy,
    validate_yaml,
    ValidationError,
    SUPPORTED_INDICATORS,
    SUPPORTED_CONDITION_TYPES,
    SCHEMA_VERSION,
)


def test_schema_version():
    """Test schema version is defined."""
    assert SCHEMA_VERSION == "2.1.0"


def test_supported_indicators():
    """Test supported indicators are exported."""
    assert "RSI" in SUPPORTED_INDICATORS
    assert "SMA" in SUPPORTED_INDICATORS
    assert "MACD" in SUPPORTED_INDICATORS
    assert len(SUPPORTED_INDICATORS) > 50  # Should have 50+ indicators


def test_supported_condition_types():
    """Test supported condition types are exported."""
    assert "comparison" in SUPPORTED_CONDITION_TYPES
    assert "cross" in SUPPORTED_CONDITION_TYPES
    assert "and" in SUPPORTED_CONDITION_TYPES
    assert len(SUPPORTED_CONDITION_TYPES) == 10


def test_validate_simple_strategy():
    """Test validating a simple strategy."""
    yaml_content = """
info:
  id: test-strategy
  name: Test Strategy
  version: "1.0"

universe:
  type: static
  symbols: ["AAPL"]

rules:
  - name: test-rule
    when:
      type: always
    then:
      type: hold
"""
    strategy = validate_yaml(yaml_content)
    assert strategy.info.id == "test-strategy"
    assert strategy.info.name == "Test Strategy"
    assert len(strategy.rules) == 1


def test_validate_rsi_strategy():
    """Test validating an RSI-based strategy."""
    yaml_content = """
info:
  id: rsi-test
  name: RSI Test
  version: "1.0"

universe:
  type: static
  symbols: ["AAPL"]

rules:
  - name: buy-oversold
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
"""
    strategy = validate_yaml(yaml_content)
    assert strategy.info.id == "rsi-test"
    assert strategy.rules[0].name == "buy-oversold"


def test_invalid_strategy_missing_info():
    """Test that missing info raises ValidationError."""
    yaml_content = """
universe:
  type: static
  symbols: ["AAPL"]

rules:
  - name: test-rule
    when:
      type: always
    then:
      type: hold
"""
    with pytest.raises(ValidationError):
        validate_yaml(yaml_content)


def test_extensible_indicator():
    """Test that custom indicators are accepted."""
    yaml_content = """
info:
  id: custom-indicator-test
  name: Custom Indicator Test
  version: "1.0"

universe:
  type: static
  symbols: ["AAPL"]

rules:
  - name: custom-signal
    when:
      type: comparison
      left:
        type: indicator
        indicator: "custom:MY_INDICATOR"
        params:
          period: 20
      operator: ">"
      right:
        type: constant
        value: 50
    then:
      type: hold
"""
    strategy = validate_yaml(yaml_content)
    assert strategy.info.id == "custom-indicator-test"


def test_invalid_extensible_indicator():
    """Test that invalid custom indicator prefix is rejected."""
    yaml_content = """
info:
  id: invalid-indicator-test
  name: Invalid Indicator Test
  version: "1.0"

universe:
  type: static
  symbols: ["AAPL"]

rules:
  - name: invalid-signal
    when:
      type: comparison
      left:
        type: indicator
        indicator: "invalid:MY_INDICATOR"
      operator: ">"
      right:
        type: constant
        value: 50
    then:
      type: hold
"""
    with pytest.raises(ValidationError):
        validate_yaml(yaml_content)
