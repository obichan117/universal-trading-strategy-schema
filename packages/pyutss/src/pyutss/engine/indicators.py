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


@dataclass
class IchimokuResult:
    """Ichimoku Cloud calculation result."""

    tenkan: pd.Series
    kijun: pd.Series
    senkou_a: pd.Series
    senkou_b: pd.Series


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

    @staticmethod
    def dema(data: pd.Series, period: int) -> pd.Series:
        """Double Exponential Moving Average.

        Args:
            data: Price series
            period: Lookback period

        Returns:
            DEMA series
        """
        ema1 = IndicatorService.ema(data, period)
        ema2 = IndicatorService.ema(ema1, period)
        return 2 * ema1 - ema2

    @staticmethod
    def tema(data: pd.Series, period: int) -> pd.Series:
        """Triple Exponential Moving Average.

        Args:
            data: Price series
            period: Lookback period

        Returns:
            TEMA series
        """
        ema1 = IndicatorService.ema(data, period)
        ema2 = IndicatorService.ema(ema1, period)
        ema3 = IndicatorService.ema(ema2, period)
        return 3 * ema1 - 3 * ema2 + ema3

    @staticmethod
    def kama(
        data: pd.Series,
        period: int = 10,
        fast_period: int = 2,
        slow_period: int = 30,
    ) -> pd.Series:
        """Kaufman Adaptive Moving Average.

        Args:
            data: Price series
            period: Efficiency ratio lookback period (default 10)
            fast_period: Fast smoothing constant period (default 2)
            slow_period: Slow smoothing constant period (default 30)

        Returns:
            KAMA series
        """
        fast_sc = 2.0 / (fast_period + 1)
        slow_sc = 2.0 / (slow_period + 1)

        values = data.values.astype(float)
        n = len(values)
        kama_values = np.full(n, np.nan)

        # Start KAMA with SMA over the first `period` values
        first_valid = 0
        while first_valid < n and np.isnan(values[first_valid]):
            first_valid += 1

        start_idx = first_valid + period - 1
        if start_idx >= n:
            return pd.Series(kama_values, index=data.index)

        kama_values[start_idx] = np.mean(values[first_valid : start_idx + 1])

        for i in range(start_idx + 1, n):
            direction = abs(values[i] - values[i - period])
            volatility = np.nansum(np.abs(np.diff(values[i - period : i + 1])))
            if volatility == 0:
                er = 0.0
            else:
                er = direction / volatility
            sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
            kama_values[i] = kama_values[i - 1] + sc * (values[i] - kama_values[i - 1])

        return pd.Series(kama_values, index=data.index)

    @staticmethod
    def roc(data: pd.Series, period: int = 12) -> pd.Series:
        """Rate of Change.

        Args:
            data: Price series
            period: Lookback period (default 12)

        Returns:
            ROC series (percentage)
        """
        shifted = data.shift(period)
        return (data - shifted) / shifted * 100

    @staticmethod
    def momentum(data: pd.Series, period: int = 10) -> pd.Series:
        """Momentum indicator.

        Args:
            data: Price series
            period: Lookback period (default 10)

        Returns:
            Momentum series
        """
        return data - data.shift(period)

    @staticmethod
    def stddev(data: pd.Series, period: int = 20) -> pd.Series:
        """Rolling Standard Deviation.

        Args:
            data: Price series
            period: Lookback period (default 20)

        Returns:
            Standard deviation series
        """
        return data.rolling(window=period, min_periods=period).std()

    @staticmethod
    def variance(data: pd.Series, period: int = 20) -> pd.Series:
        """Rolling Variance.

        Args:
            data: Price series
            period: Lookback period (default 20)

        Returns:
            Variance series
        """
        return data.rolling(window=period, min_periods=period).var()

    @staticmethod
    def highest(data: pd.Series, period: int) -> pd.Series:
        """Rolling Maximum (highest value over period).

        Args:
            data: Price series
            period: Lookback period

        Returns:
            Rolling maximum series
        """
        return data.rolling(window=period, min_periods=period).max()

    @staticmethod
    def lowest(data: pd.Series, period: int) -> pd.Series:
        """Rolling Minimum (lowest value over period).

        Args:
            data: Price series
            period: Lookback period

        Returns:
            Rolling minimum series
        """
        return data.rolling(window=period, min_periods=period).min()

    @staticmethod
    def psar(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        af_start: float = 0.02,
        af_increment: float = 0.02,
        af_max: float = 0.2,
    ) -> pd.Series:
        """Parabolic SAR.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            af_start: Initial acceleration factor (default 0.02)
            af_increment: AF increment on new extreme (default 0.02)
            af_max: Maximum acceleration factor (default 0.2)

        Returns:
            Parabolic SAR series
        """
        high_vals = high.values.astype(float)
        low_vals = low.values.astype(float)
        close_vals = close.values.astype(float)
        n = len(close_vals)
        sar = np.full(n, np.nan)

        if n < 2:
            return pd.Series(sar, index=close.index)

        # Find first valid index
        first_valid = 0
        while first_valid < n and (
            np.isnan(high_vals[first_valid])
            or np.isnan(low_vals[first_valid])
            or np.isnan(close_vals[first_valid])
        ):
            first_valid += 1

        if first_valid >= n - 1:
            return pd.Series(sar, index=close.index)

        # Initialize: assume uptrend if second close > first close
        if close_vals[first_valid + 1] >= close_vals[first_valid]:
            trend = 1  # uptrend
            sar[first_valid] = low_vals[first_valid]
            ep = high_vals[first_valid]
        else:
            trend = -1  # downtrend
            sar[first_valid] = high_vals[first_valid]
            ep = low_vals[first_valid]

        af = af_start

        for i in range(first_valid + 1, n):
            prev_sar = sar[i - 1]

            if trend == 1:  # uptrend
                sar[i] = prev_sar + af * (ep - prev_sar)
                # SAR must not be above the prior two lows
                sar[i] = min(sar[i], low_vals[i - 1])
                if i >= first_valid + 2:
                    sar[i] = min(sar[i], low_vals[i - 2])

                if low_vals[i] < sar[i]:
                    # Reversal to downtrend
                    trend = -1
                    sar[i] = ep
                    ep = low_vals[i]
                    af = af_start
                else:
                    if high_vals[i] > ep:
                        ep = high_vals[i]
                        af = min(af + af_increment, af_max)
            else:  # downtrend
                sar[i] = prev_sar + af * (ep - prev_sar)
                # SAR must not be below the prior two highs
                sar[i] = max(sar[i], high_vals[i - 1])
                if i >= first_valid + 2:
                    sar[i] = max(sar[i], high_vals[i - 2])

                if high_vals[i] > sar[i]:
                    # Reversal to uptrend
                    trend = 1
                    sar[i] = ep
                    ep = high_vals[i]
                    af = af_start
                else:
                    if low_vals[i] < ep:
                        ep = low_vals[i]
                        af = min(af + af_increment, af_max)

        return pd.Series(sar, index=close.index)

    @staticmethod
    def supertrend(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 10,
        multiplier: float = 3.0,
    ) -> pd.Series:
        """Supertrend indicator.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period (default 10)
            multiplier: ATR multiplier (default 3.0)

        Returns:
            Supertrend series
        """
        atr = IndicatorService.atr(high, low, close, period)
        hl2 = (high + low) / 2

        upper_band = (hl2 + multiplier * atr).values.astype(float)
        lower_band = (hl2 - multiplier * atr).values.astype(float)
        close_vals = close.values.astype(float)
        n = len(close_vals)

        supertrend_vals = np.full(n, np.nan)
        direction = np.zeros(n)  # 1 = uptrend, -1 = downtrend

        # Find the first valid index (where ATR is available)
        first_valid = None
        for i in range(n):
            if not np.isnan(upper_band[i]) and not np.isnan(lower_band[i]):
                first_valid = i
                break

        if first_valid is None:
            return pd.Series(supertrend_vals, index=close.index)

        # Initialize
        supertrend_vals[first_valid] = upper_band[first_valid]
        direction[first_valid] = -1

        for i in range(first_valid + 1, n):
            # Adjust bands based on previous bands
            if lower_band[i] > lower_band[i - 1] or close_vals[i - 1] < lower_band[i - 1]:
                pass  # keep current lower_band
            else:
                lower_band[i] = lower_band[i - 1]

            if upper_band[i] < upper_band[i - 1] or close_vals[i - 1] > upper_band[i - 1]:
                pass  # keep current upper_band
            else:
                upper_band[i] = upper_band[i - 1]

            # Determine direction
            if direction[i - 1] == -1:  # previous downtrend
                if close_vals[i] > upper_band[i - 1]:
                    direction[i] = 1  # switch to uptrend
                else:
                    direction[i] = -1
            else:  # previous uptrend
                if close_vals[i] < lower_band[i - 1]:
                    direction[i] = -1  # switch to downtrend
                else:
                    direction[i] = 1

            if direction[i] == 1:
                supertrend_vals[i] = lower_band[i]
            else:
                supertrend_vals[i] = upper_band[i]

        return pd.Series(supertrend_vals, index=close.index)

    @staticmethod
    def ichimoku_tenkan(
        high: pd.Series,
        low: pd.Series,
        period: int = 9,
    ) -> pd.Series:
        """Ichimoku Tenkan-sen (Conversion Line).

        Args:
            high: High prices
            low: Low prices
            period: Lookback period (default 9)

        Returns:
            Tenkan-sen series
        """
        highest_high = high.rolling(window=period, min_periods=period).max()
        lowest_low = low.rolling(window=period, min_periods=period).min()
        return (highest_high + lowest_low) / 2

    @staticmethod
    def ichimoku_kijun(
        high: pd.Series,
        low: pd.Series,
        period: int = 26,
    ) -> pd.Series:
        """Ichimoku Kijun-sen (Base Line).

        Args:
            high: High prices
            low: Low prices
            period: Lookback period (default 26)

        Returns:
            Kijun-sen series
        """
        highest_high = high.rolling(window=period, min_periods=period).max()
        lowest_low = low.rolling(window=period, min_periods=period).min()
        return (highest_high + lowest_low) / 2

    @staticmethod
    def ichimoku_senkou_a(
        high: pd.Series,
        low: pd.Series,
        tenkan_period: int = 9,
        kijun_period: int = 26,
    ) -> pd.Series:
        """Ichimoku Senkou Span A (Leading Span A).

        Args:
            high: High prices
            low: Low prices
            tenkan_period: Tenkan-sen period (default 9)
            kijun_period: Kijun-sen period (default 26)

        Returns:
            Senkou Span A series (shifted forward 26 periods)
        """
        tenkan = IndicatorService.ichimoku_tenkan(high, low, tenkan_period)
        kijun = IndicatorService.ichimoku_kijun(high, low, kijun_period)
        return ((tenkan + kijun) / 2).shift(kijun_period)

    @staticmethod
    def ichimoku_senkou_b(
        high: pd.Series,
        low: pd.Series,
        period: int = 52,
    ) -> pd.Series:
        """Ichimoku Senkou Span B (Leading Span B).

        Args:
            high: High prices
            low: Low prices
            period: Lookback period (default 52)

        Returns:
            Senkou Span B series (shifted forward 26 periods)
        """
        highest_high = high.rolling(window=period, min_periods=period).max()
        lowest_low = low.rolling(window=period, min_periods=period).min()
        return ((highest_high + lowest_low) / 2).shift(26)
