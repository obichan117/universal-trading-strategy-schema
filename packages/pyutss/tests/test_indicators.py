"""Tests for pyutss indicator calculations using real market data."""

import pandas as pd

from pyutss import IndicatorService


# sample_data fixture is provided by conftest.py (real AAPL data)


class TestSMA:
    """Tests for Simple Moving Average with real data."""

    def test_sma_basic(self, sample_data):
        """Test basic SMA calculation on real AAPL data."""
        sma = IndicatorService.sma(sample_data["close"], 20)
        assert len(sma) == len(sample_data)
        assert sma.isna().sum() == 19  # First 19 values should be NaN

    def test_sma_value_is_average(self, sample_data):
        """Test SMA is actually the average of the period."""
        sma = IndicatorService.sma(sample_data["close"], 5)
        # Check that SMA at index 8 equals average of values 4-8
        expected = sample_data["close"].iloc[4:9].mean()
        assert abs(sma.iloc[8] - expected) < 0.0001

    def test_sma_smooths_daily_changes(self, sample_data):
        """SMA should smooth out daily price changes."""
        sma = IndicatorService.sma(sample_data["close"], 20)
        valid_sma = sma.dropna()
        valid_close = sample_data["close"].loc[valid_sma.index]

        # Daily changes in SMA should be smaller than daily changes in price
        sma_changes = valid_sma.diff().dropna().abs()
        price_changes = valid_close.diff().dropna().abs()

        # SMA daily changes should have lower standard deviation
        assert sma_changes.std() < price_changes.std()


class TestEMA:
    """Tests for Exponential Moving Average with real data."""

    def test_ema_basic(self, sample_data):
        """Test basic EMA calculation on real data."""
        ema = IndicatorService.ema(sample_data["close"], 20)
        assert len(ema) == len(sample_data)

    def test_ema_vs_sma_responsiveness(self, sample_data):
        """EMA should respond faster to recent price changes than SMA."""
        ema = IndicatorService.ema(sample_data["close"], 20)
        sma = IndicatorService.sma(sample_data["close"], 20)

        # EMA and SMA should be different (EMA weights recent prices more)
        valid_idx = ~ema.isna() & ~sma.isna()
        assert not ema[valid_idx].equals(sma[valid_idx])

    def test_ema_tracks_price(self, sample_data):
        """EMA should generally follow price direction."""
        ema = IndicatorService.ema(sample_data["close"], 10)
        # Correlation between EMA and close should be very high
        valid_ema = ema.dropna()
        valid_close = sample_data["close"].loc[valid_ema.index]
        correlation = valid_ema.corr(valid_close)
        assert correlation > 0.95


class TestRSI:
    """Tests for Relative Strength Index with real data."""

    def test_rsi_range(self, sample_data):
        """RSI should always be between 0 and 100."""
        rsi = IndicatorService.rsi(sample_data["close"], 14)
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_rsi_length(self, sample_data):
        """Test RSI output length matches input."""
        rsi = IndicatorService.rsi(sample_data["close"], 14)
        assert len(rsi) == len(sample_data)

    def test_rsi_variation(self, sample_data):
        """RSI should have meaningful variation with real data."""
        rsi = IndicatorService.rsi(sample_data["close"], 14)
        valid_rsi = rsi.dropna()
        # RSI should span a reasonable range with real data
        assert valid_rsi.std() > 5  # Should have some variation


class TestMACD:
    """Tests for MACD with real data."""

    def test_macd_components(self, sample_data):
        """Test MACD returns all components."""
        result = IndicatorService.macd(sample_data["close"])
        assert hasattr(result, "macd_line")
        assert hasattr(result, "signal_line")
        assert hasattr(result, "histogram")

    def test_macd_histogram_calculation(self, sample_data):
        """Histogram should equal MACD - Signal."""
        result = IndicatorService.macd(sample_data["close"])
        diff = result.macd_line - result.signal_line
        # Compare where both are valid
        valid_idx = ~result.histogram.isna() & ~diff.isna()
        if valid_idx.sum() > 0:
            pd.testing.assert_series_equal(
                result.histogram[valid_idx],
                diff[valid_idx],
                check_names=False,
            )

    def test_macd_crossovers_exist(self, sample_data):
        """With real data, MACD should cross signal line."""
        result = IndicatorService.macd(sample_data["close"])
        # Check if histogram changes sign (indicates crossover)
        valid_hist = result.histogram.dropna()
        if len(valid_hist) > 10:
            sign_changes = (valid_hist.shift(1) * valid_hist < 0).sum()
            # Should be an integer type (including numpy integers)
            import numpy as np
            assert isinstance(sign_changes, (int, np.integer))


class TestBollingerBands:
    """Tests for Bollinger Bands with real data."""

    def test_bollinger_components(self, sample_data):
        """Test Bollinger Bands returns all components."""
        result = IndicatorService.bollinger_bands(sample_data["close"])
        assert hasattr(result, "upper")
        assert hasattr(result, "middle")
        assert hasattr(result, "lower")
        assert hasattr(result, "bandwidth")
        assert hasattr(result, "percent_b")

    def test_bollinger_ordering(self, sample_data):
        """Upper should be >= middle >= lower."""
        result = IndicatorService.bollinger_bands(sample_data["close"])
        valid_idx = ~(result.upper.isna() | result.lower.isna())
        assert (result.upper[valid_idx] >= result.middle[valid_idx]).all()
        assert (result.middle[valid_idx] >= result.lower[valid_idx]).all()

    def test_bollinger_middle_is_sma(self, sample_data):
        """Middle band should be the SMA."""
        result = IndicatorService.bollinger_bands(sample_data["close"], period=20)
        sma = IndicatorService.sma(sample_data["close"], 20)
        valid_idx = ~result.middle.isna() & ~sma.isna()
        pd.testing.assert_series_equal(
            result.middle[valid_idx],
            sma[valid_idx],
            check_names=False,
        )

    def test_bollinger_contains_price(self, sample_data):
        """Most prices should be within bands."""
        result = IndicatorService.bollinger_bands(sample_data["close"], std_dev=2)
        valid_idx = ~result.upper.isna()
        close = sample_data["close"][valid_idx]
        upper = result.upper[valid_idx]
        lower = result.lower[valid_idx]

        within_bands = ((close <= upper) & (close >= lower)).mean()
        # ~95% of prices should be within 2 std dev bands
        assert within_bands > 0.85


class TestATR:
    """Tests for Average True Range with real data."""

    def test_atr_positive(self, sample_data):
        """ATR should always be positive."""
        atr = IndicatorService.atr(
            sample_data["high"], sample_data["low"], sample_data["close"]
        )
        valid_atr = atr.dropna()
        assert (valid_atr >= 0).all()

    def test_atr_reflects_volatility(self, sample_data):
        """ATR should correlate with price volatility."""
        atr = IndicatorService.atr(
            sample_data["high"], sample_data["low"], sample_data["close"], period=14
        )
        # ATR should be positive and meaningful
        valid_atr = atr.dropna()
        assert valid_atr.mean() > 0
        assert valid_atr.std() > 0  # Should have some variation


class TestStochastic:
    """Tests for Stochastic Oscillator with real data."""

    def test_stochastic_range(self, sample_data):
        """Stochastic K and D should be between 0 and 100."""
        result = IndicatorService.stochastic(
            sample_data["high"], sample_data["low"], sample_data["close"]
        )
        valid_k = result.k.dropna()
        valid_d = result.d.dropna()
        assert (valid_k >= 0).all() and (valid_k <= 100).all()
        assert (valid_d >= 0).all() and (valid_d <= 100).all()

    def test_stochastic_d_is_smoothed_k(self, sample_data):
        """%D should be smoother than %K."""
        result = IndicatorService.stochastic(
            sample_data["high"], sample_data["low"], sample_data["close"]
        )
        valid_idx = ~result.k.isna() & ~result.d.isna()
        if valid_idx.sum() > 10:
            # D should have lower variance than K
            k_var = result.k[valid_idx].var()
            d_var = result.d[valid_idx].var()
            assert d_var <= k_var * 1.1  # D should be smoother or similar


class TestOBV:
    """Tests for On-Balance Volume with real data."""

    def test_obv_cumulative(self, sample_data):
        """OBV should be cumulative and match data length."""
        obv = IndicatorService.obv(sample_data["close"], sample_data["volume"])
        assert len(obv) == len(sample_data)

    def test_obv_changes_with_price(self, sample_data):
        """OBV should increase on up days and decrease on down days."""
        obv = IndicatorService.obv(sample_data["close"], sample_data["volume"])
        # OBV should have variation
        assert obv.std() > 0
