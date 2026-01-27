"""Technical indicator calculations.

Provides indicator implementations that match UTSS schema definitions.
All indicators are implemented as static methods for easy testing and reuse.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class MACDResult:
    """MACD calculation result."""

    macd_line: pd.Series
    signal_line: pd.Series
    histogram: pd.Series


@dataclass
class BollingerBandsResult:
    """Bollinger Bands calculation result."""

    upper: pd.Series
    middle: pd.Series
    lower: pd.Series
    bandwidth: pd.Series
    percent_b: pd.Series


@dataclass
class StochasticResult:
    """Stochastic oscillator result."""

    k: pd.Series
    d: pd.Series


class IndicatorService:
    """Technical indicator calculation service.

    Implements all UTSS-supported indicators with optimized calculations
    using pandas and numpy.

    Example:
        # Calculate RSI
        rsi = IndicatorService.rsi(close_prices, period=14)

        # Calculate MACD
        macd = IndicatorService.macd(close_prices)
        print(macd.macd_line, macd.signal_line)
    """

    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average.

        Args:
            data: Price series
            period: Lookback period

        Returns:
            SMA series
        """
        return data.rolling(window=period, min_periods=period).mean()

    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average.

        Args:
            data: Price series
            period: Lookback period

        Returns:
            EMA series
        """
        return data.ewm(span=period, adjust=False, min_periods=period).mean()

    @staticmethod
    def wma(data: pd.Series, period: int) -> pd.Series:
        """Weighted Moving Average.

        Args:
            data: Price series
            period: Lookback period

        Returns:
            WMA series
        """
        weights = np.arange(1, period + 1)
        return data.rolling(window=period).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )

    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index.

        Args:
            data: Price series
            period: Lookback period (default 14)

        Returns:
            RSI series (0-100)
        """
        delta = data.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.replace([np.inf, -np.inf], np.nan)

    @staticmethod
    def macd(
        data: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> MACDResult:
        """Moving Average Convergence Divergence.

        Args:
            data: Price series
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line period (default 9)

        Returns:
            MACDResult with macd_line, signal_line, histogram
        """
        fast_ema = IndicatorService.ema(data, fast_period)
        slow_ema = IndicatorService.ema(data, slow_period)
        macd_line = fast_ema - slow_ema
        signal_line = IndicatorService.ema(macd_line, signal_period)
        histogram = macd_line - signal_line

        return MACDResult(
            macd_line=macd_line,
            signal_line=signal_line,
            histogram=histogram,
        )

    @staticmethod
    def stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3,
    ) -> StochasticResult:
        """Stochastic Oscillator.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            k_period: %K period (default 14)
            d_period: %D period (default 3)

        Returns:
            StochasticResult with k and d lines
        """
        lowest_low = low.rolling(window=k_period, min_periods=k_period).min()
        highest_high = high.rolling(window=k_period, min_periods=k_period).max()

        k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(window=d_period, min_periods=d_period).mean()

        return StochasticResult(k=k, d=d)

    @staticmethod
    def bollinger_bands(
        data: pd.Series,
        period: int = 20,
        std_dev: float = 2.0,
    ) -> BollingerBandsResult:
        """Bollinger Bands.

        Args:
            data: Price series
            period: Moving average period (default 20)
            std_dev: Standard deviation multiplier (default 2.0)

        Returns:
            BollingerBandsResult with upper, middle, lower bands
        """
        middle = IndicatorService.sma(data, period)
        rolling_std = data.rolling(window=period, min_periods=period).std()

        upper = middle + (rolling_std * std_dev)
        lower = middle - (rolling_std * std_dev)

        bandwidth = (upper - lower) / middle * 100
        percent_b = (data - lower) / (upper - lower)

        return BollingerBandsResult(
            upper=upper,
            middle=middle,
            lower=lower,
            bandwidth=bandwidth,
            percent_b=percent_b,
        )

    @staticmethod
    def atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Average True Range.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Lookback period (default 14)

        Returns:
            ATR series
        """
        prev_close = close.shift(1)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

        return atr

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume.

        Args:
            close: Close prices
            volume: Volume data

        Returns:
            OBV series
        """
        price_change = close.diff()
        signed_volume = volume.copy()
        signed_volume[price_change < 0] = -volume[price_change < 0]
        signed_volume[price_change == 0] = 0
        return signed_volume.cumsum()

    @staticmethod
    def volume_ma(volume: pd.Series, period: int = 20) -> pd.Series:
        """Volume Moving Average.

        Args:
            volume: Volume data
            period: Lookback period (default 20)

        Returns:
            Volume MA series
        """
        return IndicatorService.sma(volume, period)

    @staticmethod
    def vwap(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
    ) -> pd.Series:
        """Volume Weighted Average Price.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume data

        Returns:
            VWAP series
        """
        typical_price = (high + low + close) / 3
        return (typical_price * volume).cumsum() / volume.cumsum()

    @staticmethod
    def adx(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Average Directional Index.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Lookback period (default 14)

        Returns:
            ADX series
        """
        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        plus_dm[(plus_dm < minus_dm)] = 0
        minus_dm[(minus_dm < plus_dm)] = 0

        atr = IndicatorService.atr(high, low, close, period)

        plus_di = 100 * (
            plus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr
        )
        minus_di = 100 * (
            minus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
            / atr
        )

        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx = dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

        return adx

    @staticmethod
    def cci(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 20,
    ) -> pd.Series:
        """Commodity Channel Index.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Lookback period (default 20)

        Returns:
            CCI series
        """
        typical_price = (high + low + close) / 3
        sma = IndicatorService.sma(typical_price, period)
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.abs(x - x.mean()).mean(), raw=True
        )
        return (typical_price - sma) / (0.015 * mean_deviation)

    @staticmethod
    def williams_r(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Williams %R.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Lookback period (default 14)

        Returns:
            Williams %R series (-100 to 0)
        """
        highest_high = high.rolling(window=period, min_periods=period).max()
        lowest_low = low.rolling(window=period, min_periods=period).min()
        return -100 * (highest_high - close) / (highest_high - lowest_low)

    @staticmethod
    def mfi(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Money Flow Index.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume data
            period: Lookback period (default 14)

        Returns:
            MFI series (0-100)
        """
        typical_price = (high + low + close) / 3
        raw_money_flow = typical_price * volume

        positive_flow = raw_money_flow.where(typical_price > typical_price.shift(1), 0)
        negative_flow = raw_money_flow.where(typical_price < typical_price.shift(1), 0)

        positive_mf = positive_flow.rolling(window=period).sum()
        negative_mf = negative_flow.rolling(window=period).sum()

        money_ratio = positive_mf / negative_mf
        return 100 - (100 / (1 + money_ratio))

    @staticmethod
    def detect_crosses(fast: pd.Series, slow: pd.Series) -> tuple[pd.Series, pd.Series]:
        """Detect cross events between two series.

        Args:
            fast: Fast series
            slow: Slow series

        Returns:
            Tuple of (crosses_above, crosses_below) boolean series
        """
        prev_fast = fast.shift(1)
        prev_slow = slow.shift(1)

        crosses_above = (fast > slow) & (prev_fast <= prev_slow)
        crosses_below = (fast < slow) & (prev_fast >= prev_slow)

        return crosses_above, crosses_below
