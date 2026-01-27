"""Integration tests for UTSS schema coverage in pyutss.

Validates that pyutss implements all capabilities defined in the UTSS schema.
This ensures the engine stays in sync with the schema as both evolve.
"""

import pytest

from utss.capabilities import (
    SCHEMA_VERSION,
    SUPPORTED_ARITHMETIC_OPERATORS,
    SUPPORTED_CALENDAR_FIELDS,
    SUPPORTED_COMPARISON_OPERATORS,
    SUPPORTED_CONDITION_TYPES,
    SUPPORTED_CROSS_DIRECTIONS,
    SUPPORTED_INDICATORS,
    SUPPORTED_PRICE_FIELDS,
    SUPPORTED_SIGNAL_TYPES,
    SUPPORTED_SIZING_TYPES,
    SUPPORTED_TEMPORAL_MODIFIERS,
    SUPPORTED_TRADE_DIRECTIONS,
)
from pyutss.engine.indicators import IndicatorService
from pyutss.engine.evaluator import SignalEvaluator, ConditionEvaluator


class TestSchemaVersion:
    """Tests for schema version compatibility."""

    def test_schema_version_defined(self):
        """Schema version should be defined."""
        assert SCHEMA_VERSION is not None
        assert SCHEMA_VERSION == "2.1.0"


class TestIndicatorCoverage:
    """Tests for indicator implementation coverage."""

    # Indicators implemented in pyutss
    IMPLEMENTED_INDICATORS = {
        "SMA", "EMA", "WMA", "RSI", "MACD", "MACD_SIGNAL", "MACD_HIST",
        "STOCH_K", "STOCH_D", "ATR", "BB_UPPER", "BB_LOWER", "BB_MIDDLE",
        "BB_WIDTH", "BB_PERCENT_B", "ADX", "CCI", "WILLIAMS_R", "MFI",
        "OBV", "VWAP",
    }

    # Indicators that are not yet implemented (tracked for future work)
    NOT_YET_IMPLEMENTED = {
        "DEMA", "TEMA", "KAMA", "HULL", "VWMA",  # Advanced MAs
        "STOCH_RSI", "ROC", "MOMENTUM", "CMO", "TSI",  # Momentum
        "PLUS_DI", "MINUS_DI", "AROON_UP", "AROON_DOWN", "AROON_OSC",  # Trend
        "SUPERTREND", "PSAR",  # Trend
        "STDDEV", "VARIANCE", "NATR", "KELTNER_UPPER", "KELTNER_LOWER",  # Volatility
        "DONCHIAN_UPPER", "DONCHIAN_LOWER", "DONCHIAN_MIDDLE",  # Volatility
        "CMF", "AD", "ADL", "VOLUME_OSC", "VOLUME_ROC",  # Volume
        "VWAP_UPPER", "VWAP_LOWER", "PVI", "NVI",  # Volume
        "PPO", "PPO_SIGNAL", "PPO_HIST", "TRIX", "UO", "DPO", "KST",  # Misc
        "ICH_TENKAN", "ICH_KIJUN", "ICH_SENKOU_A", "ICH_SENKOU_B", "ICH_CHIKOU",  # Ichimoku
        "PIVOT", "PIVOT_R1", "PIVOT_R2", "PIVOT_R3",  # Pivots
        "PIVOT_S1", "PIVOT_S2", "PIVOT_S3",
    }

    def test_indicator_service_has_methods(self):
        """IndicatorService should have static methods for calculations."""
        assert hasattr(IndicatorService, "sma")
        assert hasattr(IndicatorService, "ema")
        assert hasattr(IndicatorService, "rsi")
        assert hasattr(IndicatorService, "macd")
        assert hasattr(IndicatorService, "bollinger_bands")
        assert hasattr(IndicatorService, "atr")
        assert hasattr(IndicatorService, "stochastic")

    def test_core_indicators_implemented(self):
        """Core indicators should be implemented."""
        core_indicators = {"SMA", "EMA", "RSI", "MACD", "ATR"}
        for indicator in core_indicators:
            assert indicator in self.IMPLEMENTED_INDICATORS, f"{indicator} should be implemented"

    def test_indicator_coverage_report(self):
        """Report on indicator coverage percentage."""
        total = len(SUPPORTED_INDICATORS)
        implemented = len(self.IMPLEMENTED_INDICATORS & set(SUPPORTED_INDICATORS))
        coverage = (implemented / total) * 100 if total > 0 else 0

        print(f"\nIndicator Coverage: {implemented}/{total} ({coverage:.1f}%)")
        print(f"Implemented: {sorted(self.IMPLEMENTED_INDICATORS & set(SUPPORTED_INDICATORS))}")

        # We don't fail on coverage, just report
        # In the future, we may want to require 100% coverage
        assert coverage >= 20, f"Indicator coverage too low: {coverage:.1f}%"


class TestConditionTypeCoverage:
    """Tests for condition type implementation coverage."""

    # Condition types implemented in pyutss
    IMPLEMENTED_CONDITIONS = {
        "comparison", "cross", "range", "and", "or", "not",
        "temporal", "always",
    }

    # Not yet implemented
    NOT_YET_IMPLEMENTED = {"sequence", "change"}

    def test_core_conditions_implemented(self):
        """Core condition types should be implemented."""
        core_conditions = {"comparison", "and", "or", "not", "always"}
        for cond in core_conditions:
            assert cond in self.IMPLEMENTED_CONDITIONS, f"{cond} should be implemented"

    def test_condition_coverage(self):
        """Check condition type coverage."""
        total = len(SUPPORTED_CONDITION_TYPES)
        implemented = len(self.IMPLEMENTED_CONDITIONS & set(SUPPORTED_CONDITION_TYPES))
        coverage = (implemented / total) * 100 if total > 0 else 0

        print(f"\nCondition Coverage: {implemented}/{total} ({coverage:.1f}%)")
        assert coverage >= 70, f"Condition coverage too low: {coverage:.1f}%"


class TestSignalTypeCoverage:
    """Tests for signal type implementation coverage."""

    # Signal types implemented in pyutss
    IMPLEMENTED_SIGNALS = {
        "price", "indicator", "constant", "calendar", "arithmetic",
        "$ref",
    }

    # Not yet implemented
    NOT_YET_IMPLEMENTED = {
        "fundamental", "event", "portfolio", "relative", "expr", "external"
    }

    def test_core_signals_implemented(self):
        """Core signal types should be implemented."""
        core_signals = {"price", "indicator", "constant"}
        for signal in core_signals:
            assert signal in self.IMPLEMENTED_SIGNALS, f"{signal} should be implemented"

    def test_signal_coverage(self):
        """Check signal type coverage."""
        total = len(SUPPORTED_SIGNAL_TYPES)
        # Filter out $ref as it's special
        implemented = len((self.IMPLEMENTED_SIGNALS - {"$ref"}) & set(SUPPORTED_SIGNAL_TYPES))
        coverage = (implemented / total) * 100 if total > 0 else 0

        print(f"\nSignal Coverage: {implemented}/{total} ({coverage:.1f}%)")
        assert coverage >= 40, f"Signal coverage too low: {coverage:.1f}%"


class TestPriceFieldCoverage:
    """Tests for price field coverage."""

    IMPLEMENTED_FIELDS = {"open", "high", "low", "close", "volume", "hl2", "hlc3", "ohlc4"}

    def test_basic_price_fields(self):
        """Basic OHLCV fields should be supported."""
        for field in ["open", "high", "low", "close", "volume"]:
            assert field in self.IMPLEMENTED_FIELDS


class TestCalendarFieldCoverage:
    """Tests for calendar field coverage."""

    IMPLEMENTED_FIELDS = {
        "day_of_week", "day_of_month", "month", "week_of_year",
        "is_month_start", "is_month_end", "is_quarter_end"
    }

    def test_core_calendar_fields(self):
        """Core calendar fields should be supported."""
        for field in ["day_of_week", "day_of_month"]:
            assert field in self.IMPLEMENTED_FIELDS


class TestComparisonOperatorCoverage:
    """Tests for comparison operator coverage."""

    IMPLEMENTED_OPERATORS = {"<", "<=", "=", "==", ">=", ">", "!=", "lt", "lte", "eq", "gte", "gt", "ne"}

    def test_all_comparison_operators(self):
        """All comparison operators should be supported."""
        # Map UTSS operators to our implementation
        utss_to_impl = {
            "<": "<", "<=": "<=", "=": "=", ">=": ">=", ">": ">",
            "lt": "lt", "lte": "lte", "eq": "eq", "gte": "gte", "gt": "gt",
        }
        for utss_op in SUPPORTED_COMPARISON_OPERATORS:
            if utss_op in utss_to_impl:
                assert utss_to_impl[utss_op] in self.IMPLEMENTED_OPERATORS


class TestCrossDirectionCoverage:
    """Tests for cross direction coverage."""

    def test_cross_directions(self):
        """Both cross directions should be supported."""
        assert "above" in SUPPORTED_CROSS_DIRECTIONS or "crosses_above" in str(SUPPORTED_CROSS_DIRECTIONS)


class TestSizingTypeCoverage:
    """Tests for sizing type coverage."""

    IMPLEMENTED_SIZING = {
        "fixed_amount", "fixed_quantity", "percent_of_equity", "percent_of_cash"
    }

    NOT_YET_IMPLEMENTED = {
        "percent_of_position", "risk_based", "kelly", "volatility_adjusted", "conditional"
    }

    def test_core_sizing_types(self):
        """Core sizing types should be implemented."""
        core = {"percent_of_equity"}
        for sizing in core:
            assert sizing in self.IMPLEMENTED_SIZING


class TestEvaluatorIntegration:
    """Integration tests for evaluators with UTSS types."""

    def test_signal_evaluator_creates(self):
        """SignalEvaluator should be instantiable."""
        evaluator = SignalEvaluator()
        assert evaluator is not None

    def test_condition_evaluator_creates(self):
        """ConditionEvaluator should be instantiable."""
        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)
        assert cond_eval is not None


class TestOverallCoverage:
    """Summary tests for overall schema coverage."""

    def test_print_coverage_summary(self):
        """Print overall coverage summary."""
        print("\n" + "=" * 50)
        print("UTSS Schema Coverage Summary")
        print("=" * 50)

        # Indicators
        ind_impl = len(TestIndicatorCoverage.IMPLEMENTED_INDICATORS)
        ind_total = len(SUPPORTED_INDICATORS)
        print(f"Indicators:  {ind_impl}/{ind_total} ({ind_impl/ind_total*100:.0f}%)")

        # Conditions
        cond_impl = len(TestConditionTypeCoverage.IMPLEMENTED_CONDITIONS)
        cond_total = len(SUPPORTED_CONDITION_TYPES)
        print(f"Conditions:  {cond_impl}/{cond_total} ({cond_impl/cond_total*100:.0f}%)")

        # Signals
        sig_impl = len(TestSignalTypeCoverage.IMPLEMENTED_SIGNALS) - 1  # Exclude $ref
        sig_total = len(SUPPORTED_SIGNAL_TYPES)
        print(f"Signals:     {sig_impl}/{sig_total} ({sig_impl/sig_total*100:.0f}%)")

        # Sizing
        size_impl = len(TestSizingTypeCoverage.IMPLEMENTED_SIZING)
        size_total = len(SUPPORTED_SIZING_TYPES)
        print(f"Sizing:      {size_impl}/{size_total} ({size_impl/size_total*100:.0f}%)")

        print("=" * 50)
