"""Tests for pyutss signal and condition evaluator using real market data."""

import pandas as pd
import pytest

from pyutss import (
    ConditionEvaluator,
    EvaluationContext,
    EvaluationError,
    SignalEvaluator,
)


# sample_data fixture is provided by conftest.py (real AAPL data)


@pytest.fixture
def context(sample_data):
    """Create evaluation context with real data."""
    return EvaluationContext(primary_data=sample_data)


class TestSignalEvaluator:
    """Tests for SignalEvaluator using real data."""

    def test_price_signal(self, context, sample_data):
        """Test price signal evaluation with real data."""
        evaluator = SignalEvaluator()
        signal = {"type": "price", "field": "close"}
        result = evaluator.evaluate_signal(signal, context)
        assert len(result) == len(sample_data)
        pd.testing.assert_series_equal(result, context.primary_data["close"])

    def test_price_signal_open(self, context, sample_data):
        """Test open price signal with real data."""
        evaluator = SignalEvaluator()
        signal = {"type": "price", "field": "open"}
        result = evaluator.evaluate_signal(signal, context)
        pd.testing.assert_series_equal(result, context.primary_data["open"])

    def test_price_signal_high_low(self, context, sample_data):
        """Test high/low price signals with real data."""
        evaluator = SignalEvaluator()

        high = evaluator.evaluate_signal({"type": "price", "field": "high"}, context)
        low = evaluator.evaluate_signal({"type": "price", "field": "low"}, context)

        # High should always be >= low
        assert (high >= low).all()

    def test_indicator_signal_sma(self, context, sample_data):
        """Test SMA indicator signal with real data."""
        evaluator = SignalEvaluator()
        signal = {"type": "indicator", "indicator": "SMA", "params": {"period": 10}}
        result = evaluator.evaluate_signal(signal, context)
        assert len(result) == len(sample_data)
        assert result.isna().sum() == 9  # First 9 values NaN

    def test_indicator_signal_rsi(self, context, sample_data):
        """Test RSI indicator signal with real data."""
        evaluator = SignalEvaluator()
        signal = {"type": "indicator", "indicator": "RSI", "params": {"period": 14}}
        result = evaluator.evaluate_signal(signal, context)
        valid = result.dropna()
        # RSI should be between 0 and 100
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_indicator_signal_ema(self, context, sample_data):
        """Test EMA indicator signal with real data."""
        evaluator = SignalEvaluator()
        signal = {"type": "indicator", "indicator": "EMA", "params": {"period": 20}}
        result = evaluator.evaluate_signal(signal, context)
        # EMA should closely track price
        correlation = result.dropna().corr(sample_data["close"].loc[result.dropna().index])
        assert correlation > 0.9

    def test_constant_signal(self, context, sample_data):
        """Test constant signal returns same value for all rows."""
        evaluator = SignalEvaluator()
        signal = {"type": "constant", "value": 50}
        result = evaluator.evaluate_signal(signal, context)
        assert len(result) == len(sample_data)
        assert (result == 50).all()

    def test_calendar_signal_day_of_week(self, context, sample_data):
        """Test calendar signal for day of week with real data."""
        evaluator = SignalEvaluator()
        signal = {"type": "calendar", "field": "day_of_week"}
        result = evaluator.evaluate_signal(signal, context)
        assert len(result) == len(sample_data)
        # Day of week should be 0-6 (pandas: Mon=0, Sun=6)
        assert result.min() >= 0 and result.max() <= 6
        # Real trading data should only have weekdays (0-4)
        assert result.max() <= 4

    def test_calendar_signal_month(self, context, sample_data):
        """Test calendar signal for month with real data."""
        evaluator = SignalEvaluator()
        signal = {"type": "calendar", "field": "month"}
        result = evaluator.evaluate_signal(signal, context)
        # Month should be 1-12
        assert result.min() >= 1 and result.max() <= 12

    def test_unsupported_signal_type(self, context):
        """Test error on unsupported signal type."""
        evaluator = SignalEvaluator()
        signal = {"type": "unknown_type"}
        with pytest.raises(EvaluationError):
            evaluator.evaluate_signal(signal, context)


class TestConditionEvaluator:
    """Tests for ConditionEvaluator using real data."""

    def test_comparison_lt(self, context, sample_data):
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
        assert len(result) == len(sample_data)
        assert result.all()  # 30 < 50 is always true

    def test_comparison_gt(self, context, sample_data):
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

    def test_comparison_eq(self, context, sample_data):
        """Test equality comparison."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)

        condition = {
            "type": "comparison",
            "left": {"type": "constant", "value": 50},
            "operator": "=",
            "right": {"type": "constant", "value": 50},
        }
        result = cond_eval.evaluate_condition(condition, context)
        assert result.all()  # 50 = 50 is always true

    def test_comparison_with_rsi(self, context, sample_data):
        """Test comparison using RSI indicator with real data."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)

        # RSI < 100 (should always be true for valid RSI values)
        condition = {
            "type": "comparison",
            "left": {"type": "indicator", "indicator": "RSI", "params": {"period": 14}},
            "operator": "<",
            "right": {"type": "constant", "value": 100},
        }
        result = cond_eval.evaluate_condition(condition, context)
        # Result is boolean series - True where condition met, False where NaN
        # Check that non-False values (True) exist after warmup period
        assert result.iloc[14:].any()  # After RSI warmup, some should be True

    def test_comparison_with_price(self, context, sample_data):
        """Test comparison using price with real data."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)

        # high >= low should always be true
        condition = {
            "type": "comparison",
            "left": {"type": "price", "field": "high"},
            "operator": ">=",
            "right": {"type": "price", "field": "low"},
        }
        result = cond_eval.evaluate_condition(condition, context)
        assert result.all()

    def test_and_condition(self, context, sample_data):
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

    def test_and_condition_with_false(self, context, sample_data):
        """Test AND condition with one false."""
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
                },  # True
                {
                    "type": "comparison",
                    "left": {"type": "constant", "value": 30},
                    "operator": ">",
                    "right": {"type": "constant", "value": 50},
                },  # False
            ],
        }
        result = cond_eval.evaluate_condition(condition, context)
        assert not result.any()  # False because one is false

    def test_or_condition(self, context, sample_data):
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

    def test_not_condition(self, context, sample_data):
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

    def test_always_condition(self, context, sample_data):
        """Test always true condition."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)

        condition = {"type": "always"}
        result = cond_eval.evaluate_condition(condition, context)
        assert len(result) == len(sample_data)
        assert result.all()

    def test_ref_condition(self, sample_data):
        """Test $ref condition resolution with strategy context."""
        # Set up signals and conditions for $ref resolution
        signal_library = {
            "rsi_14": {"type": "indicator", "indicator": "RSI", "params": {"period": 14}}
        }
        condition_library = {
            "overbought": {
                "type": "comparison",
                "left": {"$ref": "#/signals/rsi_14"},
                "operator": ">",
                "right": {"type": "constant", "value": 70},
            }
        }

        # Create context with signal and condition libraries
        ctx = EvaluationContext(
            primary_data=sample_data,
            signal_library=signal_library,
            condition_library=condition_library,
        )
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)

        # Test $ref to condition
        condition = {"$ref": "#/conditions/overbought"}
        result = cond_eval.evaluate_condition(condition, ctx)

        # Should return boolean series
        assert len(result) == len(sample_data)
        assert result.dtype == bool

    # Note: range, cross, temporal conditions removed in v1.0
    # Use expr formulas for complex patterns instead


class TestConditionWithRealMarketBehavior:
    """Test conditions that verify real market data behavior."""

    def test_high_always_gte_low(self, context, sample_data):
        """High should always be >= low in real market data."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)

        condition = {
            "type": "comparison",
            "left": {"type": "price", "field": "high"},
            "operator": ">=",
            "right": {"type": "price", "field": "low"},
        }
        result = cond_eval.evaluate_condition(condition, context)
        assert result.all()

    def test_close_within_high_low(self, context, sample_data):
        """Close should be between high and low."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)

        # close <= high
        cond1 = {
            "type": "comparison",
            "left": {"type": "price", "field": "close"},
            "operator": "<=",
            "right": {"type": "price", "field": "high"},
        }
        # close >= low
        cond2 = {
            "type": "comparison",
            "left": {"type": "price", "field": "close"},
            "operator": ">=",
            "right": {"type": "price", "field": "low"},
        }

        result1 = cond_eval.evaluate_condition(cond1, context)
        result2 = cond_eval.evaluate_condition(cond2, context)

        assert result1.all()
        assert result2.all()

    def test_volume_positive(self, context, sample_data):
        """Volume should always be positive in real market data."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)

        condition = {
            "type": "comparison",
            "left": {"type": "price", "field": "volume"},
            "operator": ">",
            "right": {"type": "constant", "value": 0},
        }
        result = cond_eval.evaluate_condition(condition, context)
        assert result.all()

    def test_rsi_within_bounds(self, context, sample_data):
        """RSI should always be between 0 and 100."""
        signal_eval = SignalEvaluator()

        # Evaluate RSI directly and check bounds
        rsi_signal = {"type": "indicator", "indicator": "RSI", "params": {"period": 14}}
        rsi = signal_eval.evaluate_signal(rsi_signal, context)

        # Check RSI is within valid range where it's computed
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all(), "RSI should be >= 0"
        assert (valid_rsi <= 100).all(), "RSI should be <= 100"
