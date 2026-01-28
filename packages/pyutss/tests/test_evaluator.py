"""Tests for pyutss signal and condition evaluator."""

import numpy as np
import pandas as pd
import pytest

from pyutss import (
    ConditionEvaluator,
    EvaluationContext,
    EvaluationError,
    SignalEvaluator,
)


@pytest.fixture
def sample_data():
    """Create sample OHLCV data."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=50, freq="D")
    close = pd.Series(100 + np.cumsum(np.random.randn(50) * 0.5), index=dates)
    return pd.DataFrame({
        "open": close.shift(1).fillna(100),
        "high": close + np.abs(np.random.randn(50)),
        "low": close - np.abs(np.random.randn(50)),
        "close": close,
        "volume": np.random.randint(1000, 10000, 50),
    })


@pytest.fixture
def context(sample_data):
    """Create evaluation context."""
    return EvaluationContext(primary_data=sample_data)


class TestSignalEvaluator:
    """Tests for SignalEvaluator."""

    def test_price_signal(self, context):
        """Test price signal evaluation."""
        evaluator = SignalEvaluator()
        signal = {"type": "price", "field": "close"}
        result = evaluator.evaluate_signal(signal, context)
        assert len(result) == 50
        pd.testing.assert_series_equal(result, context.primary_data["close"])

    def test_indicator_signal_sma(self, context):
        """Test SMA indicator signal."""
        evaluator = SignalEvaluator()
        signal = {"type": "indicator", "indicator": "SMA", "params": {"period": 10}}
        result = evaluator.evaluate_signal(signal, context)
        assert len(result) == 50
        assert result.isna().sum() == 9  # First 9 values NaN

    def test_indicator_signal_rsi(self, context):
        """Test RSI indicator signal."""
        evaluator = SignalEvaluator()
        signal = {"type": "indicator", "indicator": "RSI", "params": {"period": 14}}
        result = evaluator.evaluate_signal(signal, context)
        valid = result.dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_constant_signal(self, context):
        """Test constant signal."""
        evaluator = SignalEvaluator()
        signal = {"type": "constant", "value": 50}
        result = evaluator.evaluate_signal(signal, context)
        assert (result == 50).all()

    def test_calendar_signal_day_of_week(self, context):
        """Test calendar signal for day of week."""
        evaluator = SignalEvaluator()
        signal = {"type": "calendar", "field": "day_of_week"}
        result = evaluator.evaluate_signal(signal, context)
        assert len(result) == 50
        assert result.min() >= 0 and result.max() <= 6

    def test_unsupported_signal_type(self, context):
        """Test error on unsupported signal type."""
        evaluator = SignalEvaluator()
        signal = {"type": "unknown_type"}
        with pytest.raises(EvaluationError):
            evaluator.evaluate_signal(signal, context)


class TestConditionEvaluator:
    """Tests for ConditionEvaluator."""

    def test_comparison_lt(self, context):
        """Test less than comparison."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)

        condition = {
            "type": "comparison",
            "left": {"type": "constant", "value": 30},
            "operator": "<",
            "right": {"type": "constant", "value": 50},
        }
        result = cond_eval.evaluate_condition(condition, context)
        assert result.all()  # 30 < 50 is always true

    def test_comparison_gt(self, context):
        """Test greater than comparison."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)

        condition = {
            "type": "comparison",
            "left": {"type": "constant", "value": 70},
            "operator": ">",
            "right": {"type": "constant", "value": 50},
        }
        result = cond_eval.evaluate_condition(condition, context)
        assert result.all()  # 70 > 50 is always true

    def test_and_condition(self, context):
        """Test AND condition."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)

        condition = {
            "type": "and",
            "conditions": [
                {
                    "type": "comparison",
                    "left": {"type": "constant", "value": 30},
                    "operator": "<",
                    "right": {"type": "constant", "value": 50},
                },
                {
                    "type": "comparison",
                    "left": {"type": "constant", "value": 70},
                    "operator": ">",
                    "right": {"type": "constant", "value": 50},
                },
            ],
        }
        result = cond_eval.evaluate_condition(condition, context)
        assert result.all()  # Both true

    def test_or_condition(self, context):
        """Test OR condition."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)

        condition = {
            "type": "or",
            "conditions": [
                {
                    "type": "comparison",
                    "left": {"type": "constant", "value": 70},
                    "operator": "<",
                    "right": {"type": "constant", "value": 50},
                },  # False
                {
                    "type": "comparison",
                    "left": {"type": "constant", "value": 70},
                    "operator": ">",
                    "right": {"type": "constant", "value": 50},
                },  # True
            ],
        }
        result = cond_eval.evaluate_condition(condition, context)
        assert result.all()  # One true is enough

    def test_not_condition(self, context):
        """Test NOT condition."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)

        condition = {
            "type": "not",
            "condition": {
                "type": "comparison",
                "left": {"type": "constant", "value": 70},
                "operator": "<",
                "right": {"type": "constant", "value": 50},
            },
        }
        result = cond_eval.evaluate_condition(condition, context)
        assert result.all()  # NOT (70 < 50) = NOT False = True

    def test_always_condition(self, context):
        """Test always true condition."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)

        condition = {"type": "always"}
        result = cond_eval.evaluate_condition(condition, context)
        assert result.all()

    # Note: range, cross, temporal conditions removed in v1.0
    # Use expr formulas for complex patterns instead
