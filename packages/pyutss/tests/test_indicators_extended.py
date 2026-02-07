"""Tests for extended indicators added in Phase 5."""

import numpy as np
import pandas as pd

from pyutss.engine.indicators import IndicatorService


def _make_data(n: int = 200) -> pd.DataFrame:
    """Generate synthetic OHLCV data for testing."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    close = 100 + np.random.randn(n).cumsum()
    close = np.maximum(close, 10)
    return pd.DataFrame({
        "open": close + np.random.randn(n) * 0.5,
        "high": close + abs(np.random.randn(n)),
        "low": close - abs(np.random.randn(n)),
        "close": close,
        "volume": np.random.randint(100000, 1000000, n),
    }, index=dates)


class TestMovingAverages:
    """Test new moving average indicators."""

    def test_dema(self):
        data = _make_data()
        result = IndicatorService.dema(data["close"], 20)
        assert isinstance(result, pd.Series)
        assert len(result) == len(data)
        # DEMA should have values after warmup
        assert result.dropna().shape[0] > 0

    def test_tema(self):
        data = _make_data()
        result = IndicatorService.tema(data["close"], 20)
        assert isinstance(result, pd.Series)
        assert result.dropna().shape[0] > 0

    def test_kama(self):
        data = _make_data()
        result = IndicatorService.kama(data["close"], period=10)
        assert isinstance(result, pd.Series)
        assert result.dropna().shape[0] > 0
        # KAMA should be within price range
        valid = result.dropna()
        assert valid.min() > 0


class TestMomentum:
    """Test momentum indicators."""

    def test_roc(self):
        data = _make_data()
        result = IndicatorService.roc(data["close"], 12)
        assert isinstance(result, pd.Series)
        # First 12 values should be NaN
        assert result.iloc[:12].isna().all()
        assert result.dropna().shape[0] > 0

    def test_momentum(self):
        data = _make_data()
        result = IndicatorService.momentum(data["close"], 10)
        assert isinstance(result, pd.Series)
        assert result.iloc[:10].isna().all()
        assert result.dropna().shape[0] > 0


class TestStatistical:
    """Test statistical indicators."""

    def test_stddev(self):
        data = _make_data()
        result = IndicatorService.stddev(data["close"], 20)
        assert isinstance(result, pd.Series)
        valid = result.dropna()
        assert valid.shape[0] > 0
        # Stddev should be non-negative
        assert (valid >= 0).all()

    def test_variance(self):
        data = _make_data()
        result = IndicatorService.variance(data["close"], 20)
        assert isinstance(result, pd.Series)
        valid = result.dropna()
        assert valid.shape[0] > 0
        assert (valid >= 0).all()

    def test_highest(self):
        data = _make_data()
        result = IndicatorService.highest(data["close"], 20)
        assert isinstance(result, pd.Series)
        # Highest should always be >= close
        mask = ~result.isna()
        assert (result[mask] >= data["close"][mask]).all()

    def test_lowest(self):
        data = _make_data()
        result = IndicatorService.lowest(data["close"], 20)
        assert isinstance(result, pd.Series)
        # Lowest should always be <= close
        mask = ~result.isna()
        assert (result[mask] <= data["close"][mask]).all()


class TestTrend:
    """Test trend indicators."""

    def test_psar(self):
        data = _make_data()
        result = IndicatorService.psar(data["high"], data["low"], data["close"])
        assert isinstance(result, pd.Series)
        assert len(result) == len(data)
        # PSAR should have values
        assert result.dropna().shape[0] > 0

    def test_supertrend(self):
        data = _make_data()
        result = IndicatorService.supertrend(
            data["high"], data["low"], data["close"], period=10, multiplier=3.0
        )
        assert isinstance(result, pd.Series)
        assert result.dropna().shape[0] > 0


class TestIchimoku:
    """Test Ichimoku indicators."""

    def test_tenkan(self):
        data = _make_data()
        result = IndicatorService.ichimoku_tenkan(data["high"], data["low"], 9)
        assert isinstance(result, pd.Series)
        assert result.dropna().shape[0] > 0

    def test_kijun(self):
        data = _make_data()
        result = IndicatorService.ichimoku_kijun(data["high"], data["low"], 26)
        assert isinstance(result, pd.Series)
        assert result.dropna().shape[0] > 0

    def test_senkou_a(self):
        data = _make_data()
        result = IndicatorService.ichimoku_senkou_a(data["high"], data["low"])
        assert isinstance(result, pd.Series)
        assert result.dropna().shape[0] > 0

    def test_senkou_b(self):
        data = _make_data()
        result = IndicatorService.ichimoku_senkou_b(data["high"], data["low"], 52)
        assert isinstance(result, pd.Series)
        assert result.dropna().shape[0] > 0


class TestCapabilities:
    """Test engine capability reporting."""

    def test_validate_engine_capabilities(self):
        from pyutss.engine.capabilities import validate_engine_capabilities
        report = validate_engine_capabilities()
        assert "indicators" in report
        assert "signal_types" in report
        assert "condition_types" in report
        assert "sizing_types" in report
        assert "universe_types" in report

    def test_indicators_coverage(self):
        from pyutss.engine.capabilities import validate_engine_capabilities
        report = validate_engine_capabilities()
        ind = report["indicators"]
        # Should have at least 30 of ~75 indicators
        implemented_count = len(ind["schema"] & ind["implemented"])
        assert implemented_count >= 30

    def test_condition_types_full_coverage(self):
        from pyutss.engine.capabilities import validate_engine_capabilities
        report = validate_engine_capabilities()
        assert report["condition_types"]["coverage"] == 100.0

    def test_universe_types_full_coverage(self):
        from pyutss.engine.capabilities import validate_engine_capabilities
        report = validate_engine_capabilities()
        assert report["universe_types"]["coverage"] == 100.0


class TestEvaluatorArithmetic:
    """Test extended arithmetic operators in evaluator."""

    def test_min_operator(self):
        from pyutss.engine.evaluator import SignalEvaluator, EvaluationContext
        data = _make_data(50)
        evaluator = SignalEvaluator()
        ctx = EvaluationContext(primary_data=data)
        signal = {
            "type": "arithmetic",
            "operator": "min",
            "operands": [
                {"type": "price", "field": "high"},
                {"type": "price", "field": "close"},
            ],
        }
        result = evaluator.evaluate_signal(signal, ctx)
        # min(high, close) should be <= high and <= close (approximately)
        assert len(result) == len(data)

    def test_max_operator(self):
        from pyutss.engine.evaluator import SignalEvaluator, EvaluationContext
        data = _make_data(50)
        evaluator = SignalEvaluator()
        ctx = EvaluationContext(primary_data=data)
        signal = {
            "type": "arithmetic",
            "operator": "max",
            "operands": [
                {"type": "price", "field": "low"},
                {"type": "price", "field": "close"},
            ],
        }
        result = evaluator.evaluate_signal(signal, ctx)
        assert len(result) == len(data)

    def test_abs_operator(self):
        from pyutss.engine.evaluator import SignalEvaluator, EvaluationContext
        data = _make_data(50)
        evaluator = SignalEvaluator()
        ctx = EvaluationContext(primary_data=data)
        signal = {
            "type": "arithmetic",
            "operator": "abs",
            "operands": [
                {
                    "type": "arithmetic",
                    "operator": "-",
                    "operands": [
                        {"type": "price", "field": "close"},
                        {"type": "price", "field": "open"},
                    ],
                },
            ],
        }
        result = evaluator.evaluate_signal(signal, ctx)
        assert (result >= 0).all()

    def test_pow_operator(self):
        from pyutss.engine.evaluator import SignalEvaluator, EvaluationContext
        data = _make_data(50)
        evaluator = SignalEvaluator()
        ctx = EvaluationContext(primary_data=data)
        signal = {
            "type": "arithmetic",
            "operator": "pow",
            "operands": [
                {"type": "constant", "value": 2},
                {"type": "constant", "value": 3},
            ],
        }
        result = evaluator.evaluate_signal(signal, ctx)
        assert (result == 8).all()

    def test_word_operators(self):
        """add, subtract, multiply, divide should work as operator values."""
        from pyutss.engine.evaluator import SignalEvaluator, EvaluationContext
        data = _make_data(50)
        evaluator = SignalEvaluator()
        ctx = EvaluationContext(primary_data=data)
        for op in ("add", "subtract", "multiply", "divide"):
            signal = {
                "type": "arithmetic",
                "operator": op,
                "operands": [
                    {"type": "constant", "value": 10},
                    {"type": "constant", "value": 2},
                ],
            }
            result = evaluator.evaluate_signal(signal, ctx)
            assert len(result) == len(data)


class TestEvaluatorNewIndicators:
    """Test new indicator evaluation through the evaluator."""

    def test_highest_indicator(self):
        from pyutss.engine.evaluator import SignalEvaluator, EvaluationContext
        data = _make_data(100)
        evaluator = SignalEvaluator()
        ctx = EvaluationContext(primary_data=data)
        signal = {"type": "indicator", "indicator": "HIGHEST", "params": {"period": 20}}
        result = evaluator.evaluate_signal(signal, ctx)
        assert result.dropna().shape[0] > 0

    def test_lowest_indicator(self):
        from pyutss.engine.evaluator import SignalEvaluator, EvaluationContext
        data = _make_data(100)
        evaluator = SignalEvaluator()
        ctx = EvaluationContext(primary_data=data)
        signal = {"type": "indicator", "indicator": "LOWEST", "params": {"period": 20}}
        result = evaluator.evaluate_signal(signal, ctx)
        assert result.dropna().shape[0] > 0

    def test_dema_through_evaluator(self):
        from pyutss.engine.evaluator import SignalEvaluator, EvaluationContext
        data = _make_data(100)
        evaluator = SignalEvaluator()
        ctx = EvaluationContext(primary_data=data)
        signal = {"type": "indicator", "indicator": "DEMA", "params": {"period": 20}}
        result = evaluator.evaluate_signal(signal, ctx)
        assert result.dropna().shape[0] > 0

    def test_supertrend_through_evaluator(self):
        from pyutss.engine.evaluator import SignalEvaluator, EvaluationContext
        data = _make_data(100)
        evaluator = SignalEvaluator()
        ctx = EvaluationContext(primary_data=data)
        signal = {"type": "indicator", "indicator": "SUPERTREND", "params": {"period": 10, "multiplier": 3.0}}
        result = evaluator.evaluate_signal(signal, ctx)
        assert result.dropna().shape[0] > 0

    def test_ichimoku_tenkan_through_evaluator(self):
        from pyutss.engine.evaluator import SignalEvaluator, EvaluationContext
        data = _make_data(100)
        evaluator = SignalEvaluator()
        ctx = EvaluationContext(primary_data=data)
        signal = {"type": "indicator", "indicator": "ICHIMOKU_TENKAN", "params": {"period": 9}}
        result = evaluator.evaluate_signal(signal, ctx)
        assert result.dropna().shape[0] > 0
