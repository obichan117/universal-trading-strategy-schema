"""Tests for all 27 newly-added indicators.

Covers: AD, AROON_DOWN, AROON_OSC, AROON_UP, BETA, CMF, CMO,
CORRELATION, DC_LOWER, DC_MIDDLE, DC_UPPER, DRAWDOWN, HULL,
ICHIMOKU_CHIKOU, KC_LOWER, KC_MIDDLE, KC_UPPER, KLINGER, MINUS_DI,
PERCENTILE, PLUS_DI, RANK, RETURN, STOCH_RSI, TSI, VWMA, ZSCORE
"""

import numpy as np
import pandas as pd
import pytest

from pyutss.engine.indicators import IndicatorService
from pyutss.engine.evaluator import EvaluationContext, SignalEvaluator


def _make_data(n: int = 300) -> pd.DataFrame:
    """Generate synthetic OHLCV data for testing."""
    np.random.seed(42)
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    close = 100 + np.random.randn(n).cumsum()
    close = np.maximum(close, 10)
    high = close + abs(np.random.randn(n)) * 1.5
    low = close - abs(np.random.randn(n)) * 1.5
    low = np.maximum(low, 1)
    return pd.DataFrame(
        {
            "open": close + np.random.randn(n) * 0.5,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.random.randint(100_000, 1_000_000, n).astype(float),
        },
        index=dates,
    )


# ---------------------------------------------------------------------------
# Ichimoku Chikou
# ---------------------------------------------------------------------------


class TestIchimokuChikou:
    def test_basic(self):
        data = _make_data()
        result = IndicatorService.ichimoku_chikou(data["close"], 26)
        assert isinstance(result, pd.Series)
        assert len(result) == len(data)
        # First 26 values should be NaN (shifted back 26)
        assert result.iloc[:26].isna().all()

    def test_value_matches_shifted_close(self):
        data = _make_data()
        result = IndicatorService.ichimoku_chikou(data["close"], 26)
        # chikou at index i == close at index i - 26
        valid = result.dropna()
        for i in range(5):
            idx = valid.index[i]
            pos = data.index.get_loc(idx)
            assert result.iloc[pos] == data["close"].iloc[pos - 26]


# ---------------------------------------------------------------------------
# Hull MA
# ---------------------------------------------------------------------------


class TestHullMA:
    def test_basic(self):
        data = _make_data()
        result = IndicatorService.hull(data["close"], 9)
        assert isinstance(result, pd.Series)
        assert len(result) == len(data)
        assert result.dropna().shape[0] > 0

    def test_tracks_price(self):
        data = _make_data()
        result = IndicatorService.hull(data["close"], 16)
        valid = result.dropna()
        corr = valid.corr(data["close"].loc[valid.index])
        assert corr > 0.90


# ---------------------------------------------------------------------------
# Donchian Channel
# ---------------------------------------------------------------------------


class TestDonchianChannel:
    def test_components(self):
        data = _make_data()
        dc = IndicatorService.donchian_channel(data["high"], data["low"], 20)
        assert hasattr(dc, "upper")
        assert hasattr(dc, "middle")
        assert hasattr(dc, "lower")

    def test_ordering(self):
        data = _make_data()
        dc = IndicatorService.donchian_channel(data["high"], data["low"], 20)
        mask = ~dc.upper.isna()
        assert (dc.upper[mask] >= dc.middle[mask]).all()
        assert (dc.middle[mask] >= dc.lower[mask]).all()

    def test_upper_is_rolling_max(self):
        data = _make_data()
        dc = IndicatorService.donchian_channel(data["high"], data["low"], 20)
        expected_upper = data["high"].rolling(20, min_periods=20).max()
        pd.testing.assert_series_equal(dc.upper, expected_upper, check_names=False)


# ---------------------------------------------------------------------------
# Keltner Channel
# ---------------------------------------------------------------------------


class TestKeltnerChannel:
    def test_components(self):
        data = _make_data()
        kc = IndicatorService.keltner_channel(
            data["high"], data["low"], data["close"]
        )
        assert hasattr(kc, "upper")
        assert hasattr(kc, "middle")
        assert hasattr(kc, "lower")

    def test_ordering(self):
        data = _make_data()
        kc = IndicatorService.keltner_channel(
            data["high"], data["low"], data["close"]
        )
        mask = ~kc.upper.isna()
        assert (kc.upper[mask] >= kc.middle[mask]).all()
        assert (kc.middle[mask] >= kc.lower[mask]).all()


# ---------------------------------------------------------------------------
# Aroon
# ---------------------------------------------------------------------------


class TestAroon:
    def test_components(self):
        data = _make_data()
        ar = IndicatorService.aroon(data["high"], data["low"], 25)
        assert hasattr(ar, "aroon_up")
        assert hasattr(ar, "aroon_down")
        assert hasattr(ar, "oscillator")

    def test_range(self):
        data = _make_data()
        ar = IndicatorService.aroon(data["high"], data["low"], 25)
        up = ar.aroon_up.dropna()
        down = ar.aroon_down.dropna()
        assert (up >= 0).all() and (up <= 100).all()
        assert (down >= 0).all() and (down <= 100).all()

    def test_oscillator_is_diff(self):
        data = _make_data()
        ar = IndicatorService.aroon(data["high"], data["low"], 25)
        mask = ~ar.oscillator.isna()
        expected = ar.aroon_up[mask] - ar.aroon_down[mask]
        pd.testing.assert_series_equal(
            ar.oscillator[mask], expected, check_names=False
        )


# ---------------------------------------------------------------------------
# CMF
# ---------------------------------------------------------------------------


class TestCMF:
    def test_basic(self):
        data = _make_data()
        result = IndicatorService.cmf(
            data["high"], data["low"], data["close"], data["volume"], 20
        )
        assert isinstance(result, pd.Series)
        valid = result.dropna()
        assert valid.shape[0] > 0
        # CMF is typically between -1 and 1
        assert (valid >= -1.01).all() and (valid <= 1.01).all()


# ---------------------------------------------------------------------------
# CMO
# ---------------------------------------------------------------------------


class TestCMO:
    def test_basic(self):
        data = _make_data()
        result = IndicatorService.cmo(data["close"], 14)
        assert isinstance(result, pd.Series)
        valid = result.dropna()
        assert valid.shape[0] > 0

    def test_range(self):
        data = _make_data()
        result = IndicatorService.cmo(data["close"], 14)
        valid = result.dropna()
        assert (valid >= -100).all() and (valid <= 100).all()


# ---------------------------------------------------------------------------
# TSI
# ---------------------------------------------------------------------------


class TestTSI:
    def test_basic(self):
        data = _make_data()
        result = IndicatorService.tsi(data["close"], 25, 13)
        assert isinstance(result, pd.Series)
        valid = result.dropna()
        assert valid.shape[0] > 0

    def test_range(self):
        data = _make_data()
        result = IndicatorService.tsi(data["close"], 25, 13)
        valid = result.dropna()
        # TSI is typically in -100 to 100 range
        assert (valid >= -100).all() and (valid <= 100).all()


# ---------------------------------------------------------------------------
# Stochastic RSI
# ---------------------------------------------------------------------------


class TestStochRSI:
    def test_basic(self):
        data = _make_data()
        result = IndicatorService.stoch_rsi(data["close"], 14, 14, 3)
        assert isinstance(result, pd.Series)
        valid = result.dropna()
        assert valid.shape[0] > 0

    def test_range(self):
        data = _make_data()
        result = IndicatorService.stoch_rsi(data["close"], 14, 14, 3)
        valid = result.dropna()
        assert (valid >= -0.01).all() and (valid <= 100.01).all()


# ---------------------------------------------------------------------------
# Klinger
# ---------------------------------------------------------------------------


class TestKlinger:
    def test_basic(self):
        data = _make_data()
        result = IndicatorService.klinger(
            data["high"], data["low"], data["close"], data["volume"]
        )
        assert isinstance(result, pd.Series)
        assert len(result) == len(data)
        valid = result.dropna()
        assert valid.shape[0] > 0


# ---------------------------------------------------------------------------
# AD (Accumulation/Distribution)
# ---------------------------------------------------------------------------


class TestAD:
    def test_basic(self):
        data = _make_data()
        result = IndicatorService.ad(
            data["high"], data["low"], data["close"], data["volume"]
        )
        assert isinstance(result, pd.Series)
        assert len(result) == len(data)

    def test_cumulative(self):
        data = _make_data()
        result = IndicatorService.ad(
            data["high"], data["low"], data["close"], data["volume"]
        )
        # Should have variation (not all zero)
        assert result.std() > 0


# ---------------------------------------------------------------------------
# VWMA
# ---------------------------------------------------------------------------


class TestVWMA:
    def test_basic(self):
        data = _make_data()
        result = IndicatorService.vwma(data["close"], data["volume"], 20)
        assert isinstance(result, pd.Series)
        valid = result.dropna()
        assert valid.shape[0] > 0

    def test_within_price_range(self):
        data = _make_data()
        result = IndicatorService.vwma(data["close"], data["volume"], 20)
        valid = result.dropna()
        # VWMA should be in a reasonable range near close prices
        assert valid.min() > 0


# ---------------------------------------------------------------------------
# +DI / -DI
# ---------------------------------------------------------------------------


class TestDirectionalIndicators:
    def test_plus_di_basic(self):
        data = _make_data()
        result = IndicatorService.plus_di(
            data["high"], data["low"], data["close"], 14
        )
        assert isinstance(result, pd.Series)
        valid = result.dropna()
        assert valid.shape[0] > 0
        assert (valid >= 0).all()

    def test_minus_di_basic(self):
        data = _make_data()
        result = IndicatorService.minus_di(
            data["high"], data["low"], data["close"], 14
        )
        assert isinstance(result, pd.Series)
        valid = result.dropna()
        assert valid.shape[0] > 0
        assert (valid >= 0).all()


# ---------------------------------------------------------------------------
# Beta / Correlation
# ---------------------------------------------------------------------------


class TestBetaCorrelation:
    def test_beta_no_benchmark_returns_nan(self):
        data = _make_data()
        result = IndicatorService.beta(data["close"], benchmark=None, period=60)
        assert result.isna().all()

    def test_beta_with_benchmark(self):
        data = _make_data(300)
        np.random.seed(99)
        bench = pd.Series(
            100 + np.random.randn(300).cumsum(), index=data.index
        )
        result = IndicatorService.beta(data["close"], benchmark=bench, period=60)
        valid = result.dropna()
        assert valid.shape[0] > 0

    def test_correlation_no_benchmark_returns_nan(self):
        data = _make_data()
        result = IndicatorService.correlation(
            data["close"], benchmark=None, period=60
        )
        assert result.isna().all()

    def test_correlation_with_benchmark(self):
        data = _make_data(300)
        np.random.seed(99)
        bench = pd.Series(
            100 + np.random.randn(300).cumsum(), index=data.index
        )
        result = IndicatorService.correlation(
            data["close"], benchmark=bench, period=60
        )
        valid = result.dropna()
        assert valid.shape[0] > 0
        assert (valid >= -1.01).all() and (valid <= 1.01).all()


# ---------------------------------------------------------------------------
# Percentile / Rank / ZScore
# ---------------------------------------------------------------------------


class TestStatisticalMeasures:
    def test_percentile_basic(self):
        data = _make_data()
        result = IndicatorService.percentile(data["close"], 60)
        valid = result.dropna()
        assert valid.shape[0] > 0
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_rank_basic(self):
        data = _make_data()
        result = IndicatorService.rank(data["close"], 60)
        valid = result.dropna()
        assert valid.shape[0] > 0
        assert (valid >= 1).all() and (valid <= 60).all()

    def test_zscore_basic(self):
        data = _make_data()
        result = IndicatorService.zscore(data["close"], 20)
        valid = result.dropna()
        assert valid.shape[0] > 0
        # z-score should have mean near 0 over full window
        assert abs(valid.mean()) < 1.0


# ---------------------------------------------------------------------------
# Return
# ---------------------------------------------------------------------------


class TestReturn:
    def test_basic(self):
        data = _make_data()
        result = IndicatorService.simple_return(data["close"], 1)
        assert isinstance(result, pd.Series)
        assert len(result) == len(data)
        # First value should be NaN
        assert pd.isna(result.iloc[0])

    def test_value(self):
        data = _make_data()
        result = IndicatorService.simple_return(data["close"], 1)
        # Check manual calculation for one point
        idx = 10
        expected = (data["close"].iloc[idx] - data["close"].iloc[idx - 1]) / data["close"].iloc[idx - 1]
        assert abs(result.iloc[idx] - expected) < 1e-10


# ---------------------------------------------------------------------------
# Drawdown
# ---------------------------------------------------------------------------


class TestDrawdown:
    def test_basic(self):
        data = _make_data()
        result = IndicatorService.drawdown(data["close"])
        assert isinstance(result, pd.Series)
        assert len(result) == len(data)

    def test_non_positive(self):
        data = _make_data()
        result = IndicatorService.drawdown(data["close"])
        # Drawdown should always be <= 0
        assert (result <= 1e-10).all()

    def test_zero_at_new_high(self):
        # Create data that starts low and goes high
        prices = pd.Series([10, 20, 30, 25, 35], index=pd.date_range("2023-01-01", periods=5))
        result = IndicatorService.drawdown(prices)
        # At index 0, 1, 2, 4 the price is at a new high, so drawdown = 0
        assert result.iloc[0] == 0.0
        assert result.iloc[1] == 0.0
        assert result.iloc[2] == 0.0
        assert result.iloc[4] == pytest.approx(0.0)
        # At index 3, drawdown = (25 - 30) / 30
        assert result.iloc[3] == pytest.approx(-5 / 30)


# ---------------------------------------------------------------------------
# Evaluator integration tests (through SignalEvaluator)
# ---------------------------------------------------------------------------


class TestEvaluatorNewIndicators:
    """Test all 27 new indicators through the SignalEvaluator."""

    def _eval(self, indicator: str, params: dict | None = None) -> pd.Series:
        data = _make_data(300)
        evaluator = SignalEvaluator()
        ctx = EvaluationContext(primary_data=data)
        signal = {
            "type": "indicator",
            "indicator": indicator,
            "params": params or {},
        }
        return evaluator.evaluate_signal(signal, ctx)

    def test_hull(self):
        result = self._eval("HULL", {"period": 9})
        assert result.dropna().shape[0] > 0

    def test_ichimoku_chikou(self):
        result = self._eval("ICHIMOKU_CHIKOU", {"period": 26})
        assert result.dropna().shape[0] > 0

    def test_dc_upper(self):
        result = self._eval("DC_UPPER", {"period": 20})
        assert result.dropna().shape[0] > 0

    def test_dc_middle(self):
        result = self._eval("DC_MIDDLE", {"period": 20})
        assert result.dropna().shape[0] > 0

    def test_dc_lower(self):
        result = self._eval("DC_LOWER", {"period": 20})
        assert result.dropna().shape[0] > 0

    def test_kc_upper(self):
        result = self._eval("KC_UPPER", {"ema_period": 20, "atr_period": 10, "multiplier": 2.0})
        assert result.dropna().shape[0] > 0

    def test_kc_middle(self):
        result = self._eval("KC_MIDDLE", {"ema_period": 20})
        assert result.dropna().shape[0] > 0

    def test_kc_lower(self):
        result = self._eval("KC_LOWER", {"ema_period": 20})
        assert result.dropna().shape[0] > 0

    def test_aroon_up(self):
        result = self._eval("AROON_UP", {"period": 25})
        assert result.dropna().shape[0] > 0

    def test_aroon_down(self):
        result = self._eval("AROON_DOWN", {"period": 25})
        assert result.dropna().shape[0] > 0

    def test_aroon_osc(self):
        result = self._eval("AROON_OSC", {"period": 25})
        assert result.dropna().shape[0] > 0

    def test_cmf(self):
        result = self._eval("CMF", {"period": 20})
        assert result.dropna().shape[0] > 0

    def test_cmo(self):
        result = self._eval("CMO", {"period": 14})
        assert result.dropna().shape[0] > 0

    def test_tsi(self):
        result = self._eval("TSI", {"long_period": 25, "short_period": 13})
        assert result.dropna().shape[0] > 0

    def test_stoch_rsi(self):
        result = self._eval("STOCH_RSI", {"rsi_period": 14, "stoch_period": 14, "k_period": 3})
        assert result.dropna().shape[0] > 0

    def test_klinger(self):
        result = self._eval("KLINGER", {"fast_period": 34, "slow_period": 55})
        assert result.dropna().shape[0] > 0

    def test_ad(self):
        result = self._eval("AD")
        assert len(result) > 0

    def test_vwma(self):
        result = self._eval("VWMA", {"period": 20})
        assert result.dropna().shape[0] > 0

    def test_plus_di(self):
        result = self._eval("PLUS_DI", {"period": 14})
        assert result.dropna().shape[0] > 0

    def test_minus_di(self):
        result = self._eval("MINUS_DI", {"period": 14})
        assert result.dropna().shape[0] > 0

    def test_beta(self):
        # Without benchmark, should return NaN
        result = self._eval("BETA", {"period": 60})
        assert result.isna().all()

    def test_correlation(self):
        result = self._eval("CORRELATION", {"period": 60})
        assert result.isna().all()

    def test_percentile(self):
        result = self._eval("PERCENTILE", {"period": 60})
        assert result.dropna().shape[0] > 0

    def test_rank(self):
        result = self._eval("RANK", {"period": 60})
        assert result.dropna().shape[0] > 0

    def test_zscore(self):
        result = self._eval("ZSCORE", {"period": 20})
        assert result.dropna().shape[0] > 0

    def test_return(self):
        result = self._eval("RETURN", {"period": 1})
        assert result.dropna().shape[0] > 0

    def test_drawdown(self):
        result = self._eval("DRAWDOWN")
        assert len(result) > 0
        assert (result <= 1e-10).all()


# ---------------------------------------------------------------------------
# Capabilities check
# ---------------------------------------------------------------------------


class TestCapabilitiesUpdate:
    """Verify all 27 new indicators are in IMPLEMENTED_INDICATORS."""

    NEW_INDICATORS = [
        "AD", "AROON_DOWN", "AROON_OSC", "AROON_UP", "BETA", "CMF", "CMO",
        "CORRELATION", "DC_LOWER", "DC_MIDDLE", "DC_UPPER", "DRAWDOWN", "HULL",
        "ICHIMOKU_CHIKOU", "KC_LOWER", "KC_MIDDLE", "KC_UPPER", "KLINGER",
        "MINUS_DI", "PERCENTILE", "PLUS_DI", "RANK", "RETURN", "STOCH_RSI",
        "TSI", "VWMA", "ZSCORE",
    ]

    def test_all_new_indicators_in_capabilities(self):
        from pyutss.engine.capabilities import IMPLEMENTED_INDICATORS

        for ind in self.NEW_INDICATORS:
            assert ind in IMPLEMENTED_INDICATORS, f"{ind} missing from IMPLEMENTED_INDICATORS"

    def test_count(self):
        from pyutss.engine.capabilities import IMPLEMENTED_INDICATORS

        # Previously 33, now 33 + 27 = 60
        assert len(IMPLEMENTED_INDICATORS) >= 60
