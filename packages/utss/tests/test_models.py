"""Tests for UTSS models."""

import pytest
from utss import (
    SCHEMA_VERSION,
    SUPPORTED_CONDITION_TYPES,
    SUPPORTED_INDICATORS,
    ValidationError,
    validate_yaml,
)


def test_schema_version():
    """Test schema version is defined."""
    assert SCHEMA_VERSION == "1.0.0"


def test_supported_indicators():
    """Test supported indicators are exported."""
    assert "RSI" in SUPPORTED_INDICATORS
    assert "SMA" in SUPPORTED_INDICATORS
    assert "MACD" in SUPPORTED_INDICATORS
    assert len(SUPPORTED_INDICATORS) > 50  # Should have 50+ indicators


def test_supported_condition_types():
    """Test supported condition types are exported (v1.0 minimal primitives)."""
    assert "comparison" in SUPPORTED_CONDITION_TYPES
    assert "and" in SUPPORTED_CONDITION_TYPES
    assert "or" in SUPPORTED_CONDITION_TYPES
    assert "not" in SUPPORTED_CONDITION_TYPES
    assert "expr" in SUPPORTED_CONDITION_TYPES
    assert "always" in SUPPORTED_CONDITION_TYPES
    assert len(SUPPORTED_CONDITION_TYPES) == 6  # v1.0: comparison, and, or, not, expr, always


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


def test_execution_section():
    """Test strategy with execution section."""
    yaml_content = """
info:
  id: execution-test
  name: Execution Test
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

execution:
  slippage:
    type: percentage
    value: 0.001
  commission:
    type: per_trade
    value: 5
  min_capital: 50000
  min_history: 200
"""
    strategy = validate_yaml(yaml_content)
    assert strategy.execution is not None
    assert strategy.execution.slippage is not None
    assert strategy.execution.slippage.type == "percentage"
    assert strategy.execution.slippage.value == 0.001
    assert strategy.execution.commission is not None
    assert strategy.execution.commission.type == "per_trade"
    assert strategy.execution.commission.value == 5
    assert strategy.execution.min_capital == 50000
    assert strategy.execution.min_history == 200


def test_execution_tiered_slippage():
    """Test strategy with tiered slippage model."""
    yaml_content = """
info:
  id: tiered-slippage-test
  name: Tiered Slippage Test
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

execution:
  slippage:
    type: tiered
    tiers:
      - up_to: 10000
        value: 0.0005
      - up_to: 100000
        value: 0.001
      - up_to: 1000000
        value: 0.002
"""
    strategy = validate_yaml(yaml_content)
    assert strategy.execution is not None
    assert strategy.execution.slippage.type == "tiered"
    assert len(strategy.execution.slippage.tiers) == 3
    assert strategy.execution.slippage.tiers[0].up_to == 10000
    assert strategy.execution.slippage.tiers[0].value == 0.0005
