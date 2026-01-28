"""Tests for pyutss indicator calculations."""

import numpy as np
import pandas as pd
import pytest
from pyutss import IndicatorService


@pytest.fixture
def sample_data():
    """Create sample price data for testing."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    close = pd.Series(100 + np.cumsum(np.random.randn(100)), index=dates)
    high = close + np.abs(np.random.randn(100))
    low = close - np.abs(np.random.randn(100))
    volume = pd.Series(np.random.randint(1000, 10000, 100), index=dates)
    return pd.DataFrame({"open": close.shift(1).fillna(100), "high": high, "low": low, "close": close, "volume": volume})


class TestSMA:
    """Tests for Simple Moving Average."""

    def test_sma_basic(self, sample_data):
        """Test basic SMA calculation."""
        sma = IndicatorService.sma(sample_data["close"], 20)
        assert len(sma) == 100
        assert sma.isna().sum() == 19  # First 19 values should be NaN

    def test_sma_value(self, sample_data):
        """Test SMA value calculation."""
        sma = IndicatorService.sma(sample_data["close"], 5)
        # Check that SMA is average of last 5 values
        expected = sample_data["close"].iloc[4:9].mean()
        assert abs(sma.iloc[8] - expected) < 0.0001


class TestEMA:
    """Tests for Exponential Moving Average."""

    def test_ema_basic(self, sample_data):
        """Test basic EMA calculation."""
        ema = IndicatorService.ema(sample_data["close"], 20)
        assert len(ema) == 100

    def test_ema_vs_sma(self, sample_data):
        """EMA should be closer to recent prices than SMA."""
        ema = IndicatorService.ema(sample_data["close"], 20)
        sma = IndicatorService.sma(sample_data["close"], 20)
        # Both should have values after warmup
        assert not ema.iloc[-1] == sma.iloc[-1]  # They should differ


class TestRSI:
    """Tests for Relative Strength Index."""

    def test_rsi_range(self, sample_data):
        """RSI should be between 0 and 100."""
        rsi = IndicatorService.rsi(sample_data["close"], 14)
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_rsi_length(self, sample_data):
        """Test RSI output length."""
        rsi = IndicatorService.rsi(sample_data["close"], 14)
        assert len(rsi) == 100


class TestMACD:
    """Tests for MACD."""

    def test_macd_components(self, sample_data):
        """Test MACD returns all components."""
        result = IndicatorService.macd(sample_data["close"])
        assert hasattr(result, "macd_line")
        assert hasattr(result, "signal_line")
        assert hasattr(result, "histogram")

    def test_macd_histogram(self, sample_data):
        """Histogram should equal MACD - Signal."""
        result = IndicatorService.macd(sample_data["close"])
        diff = result.macd_line - result.signal_line
        assert np.allclose(
            result.histogram.dropna().values,
            diff.dropna().values[-len(result.histogram.dropna()):],
            rtol=1e-10,
        )


class TestBollingerBands:
    """Tests for Bollinger Bands."""

    def test_bollinger_components(self, sample_data):
        """Test Bollinger Bands returns all components."""
        result = IndicatorService.bollinger_bands(sample_data["close"])
        assert hasattr(result, "upper")
        assert hasattr(result, "middle")
        assert hasattr(result, "lower")
        assert hasattr(result, "bandwidth")
        assert hasattr(result, "percent_b")

    def test_bollinger_ordering(self, sample_data):
        """Upper should be > middle > lower."""
        result = IndicatorService.bollinger_bands(sample_data["close"])
        valid_idx = ~(result.upper.isna() | result.lower.isna())
        assert (result.upper[valid_idx] >= result.middle[valid_idx]).all()
        assert (result.middle[valid_idx] >= result.lower[valid_idx]).all()


class TestATR:
    """Tests for Average True Range."""

    def test_atr_positive(self, sample_data):
        """ATR should always be positive."""
        atr = IndicatorService.atr(
            sample_data["high"], sample_data["low"], sample_data["close"]
        )
        valid_atr = atr.dropna()
        assert (valid_atr >= 0).all()


class TestStochastic:
    """Tests for Stochastic Oscillator."""

    def test_stochastic_range(self, sample_data):
        """Stochastic K and D should be between 0 and 100."""
        result = IndicatorService.stochastic(
            sample_data["high"], sample_data["low"], sample_data["close"]
        )
        valid_k = result.k.dropna()
        valid_d = result.d.dropna()
        assert (valid_k >= 0).all() and (valid_k <= 100).all()
        assert (valid_d >= 0).all() and (valid_d <= 100).all()


class TestOBV:
    """Tests for On-Balance Volume."""

    def test_obv_cumulative(self, sample_data):
        """OBV should be cumulative."""
        obv = IndicatorService.obv(sample_data["close"], sample_data["volume"])
        assert len(obv) == 100
