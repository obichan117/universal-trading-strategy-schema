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


@dataclass
class DonchianChannelResult:
    """Donchian Channel calculation result."""

    upper: pd.Series
    middle: pd.Series
    lower: pd.Series


@dataclass
class KeltnerChannelResult:
    """Keltner Channel calculation result."""

    upper: pd.Series
    middle: pd.Series
    lower: pd.Series


@dataclass
class AroonResult:
    """Aroon indicator calculation result."""

    aroon_up: pd.Series
    aroon_down: pd.Series
    oscillator: pd.Series


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

    @staticmethod
    def ichimoku_chikou(
        close: pd.Series,
        period: int = 26,
    ) -> pd.Series:
        """Ichimoku Chikou Span (Lagging Span).

        Close price shifted back by the specified period.

        Args:
            close: Close prices
            period: Shift period (default 26)

        Returns:
            Chikou Span series (close shifted back)
        """
        return close.shift(period)

    @staticmethod
    def hull(data: pd.Series, period: int = 9) -> pd.Series:
        """Hull Moving Average.

        HMA = WMA(2 * WMA(n/2) - WMA(n), sqrt(n))

        Args:
            data: Price series
            period: Lookback period (default 9)

        Returns:
            Hull MA series
        """
        half_period = max(int(period / 2), 1)
        sqrt_period = max(int(np.sqrt(period)), 1)

        wma_half = IndicatorService.wma(data, half_period)
        wma_full = IndicatorService.wma(data, period)
        diff = 2 * wma_half - wma_full
        return IndicatorService.wma(diff, sqrt_period)

    @staticmethod
    def donchian_channel(
        high: pd.Series,
        low: pd.Series,
        period: int = 20,
    ) -> DonchianChannelResult:
        """Donchian Channel.

        Upper = rolling max of high, Lower = rolling min of low.

        Args:
            high: High prices
            low: Low prices
            period: Lookback period (default 20)

        Returns:
            DonchianChannelResult with upper, middle, lower
        """
        upper = high.rolling(window=period, min_periods=period).max()
        lower = low.rolling(window=period, min_periods=period).min()
        middle = (upper + lower) / 2
        return DonchianChannelResult(upper=upper, middle=middle, lower=lower)

    @staticmethod
    def keltner_channel(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        ema_period: int = 20,
        atr_period: int = 10,
        multiplier: float = 2.0,
    ) -> KeltnerChannelResult:
        """Keltner Channel.

        Middle = EMA(close), Upper/Lower = EMA +/- multiplier * ATR.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            ema_period: EMA period (default 20)
            atr_period: ATR period (default 10)
            multiplier: ATR multiplier (default 2.0)

        Returns:
            KeltnerChannelResult with upper, middle, lower
        """
        middle = IndicatorService.ema(close, ema_period)
        atr = IndicatorService.atr(high, low, close, atr_period)
        upper = middle + multiplier * atr
        lower = middle - multiplier * atr
        return KeltnerChannelResult(upper=upper, middle=middle, lower=lower)

    @staticmethod
    def aroon(
        high: pd.Series,
        low: pd.Series,
        period: int = 25,
    ) -> AroonResult:
        """Aroon Indicator.

        Aroon Up = ((period - bars since highest high) / period) * 100
        Aroon Down = ((period - bars since lowest low) / period) * 100

        Args:
            high: High prices
            low: Low prices
            period: Lookback period (default 25)

        Returns:
            AroonResult with aroon_up, aroon_down, oscillator
        """
        aroon_up = high.rolling(window=period + 1, min_periods=period + 1).apply(
            lambda x: ((period - (period - np.argmax(x))) / period) * 100,
            raw=True,
        )
        aroon_down = low.rolling(window=period + 1, min_periods=period + 1).apply(
            lambda x: ((period - (period - np.argmin(x))) / period) * 100,
            raw=True,
        )
        oscillator = aroon_up - aroon_down
        return AroonResult(aroon_up=aroon_up, aroon_down=aroon_down, oscillator=oscillator)

    @staticmethod
    def cmf(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        period: int = 20,
    ) -> pd.Series:
        """Chaikin Money Flow.

        CMF = sum(MFV * volume, period) / sum(volume, period)
        where MFV = ((close - low) - (high - close)) / (high - low)

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume data
            period: Lookback period (default 20)

        Returns:
            CMF series (-1 to 1)
        """
        hl_range = high - low
        # Avoid division by zero
        mfv = ((close - low) - (high - close)) / hl_range.replace(0, np.nan)
        mf_volume = mfv * volume

        return mf_volume.rolling(window=period, min_periods=period).sum() / \
            volume.rolling(window=period, min_periods=period).sum()

    @staticmethod
    def cmo(data: pd.Series, period: int = 14) -> pd.Series:
        """Chande Momentum Oscillator.

        CMO = (up_sum - down_sum) / (up_sum + down_sum) * 100

        Args:
            data: Price series
            period: Lookback period (default 14)

        Returns:
            CMO series (-100 to 100)
        """
        delta = data.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        up_sum = gain.rolling(window=period, min_periods=period).sum()
        down_sum = loss.rolling(window=period, min_periods=period).sum()

        total = up_sum + down_sum
        cmo = ((up_sum - down_sum) / total.replace(0, np.nan)) * 100
        return cmo

    @staticmethod
    def tsi(
        data: pd.Series,
        long_period: int = 25,
        short_period: int = 13,
    ) -> pd.Series:
        """True Strength Index.

        Double-smoothed EMA of price change / double-smoothed EMA of abs change.

        Args:
            data: Price series
            long_period: Long EMA period (default 25)
            short_period: Short EMA period (default 13)

        Returns:
            TSI series
        """
        delta = data.diff()

        # Double-smoothed price change
        ema1 = delta.ewm(span=long_period, adjust=False, min_periods=long_period).mean()
        double_smoothed = ema1.ewm(span=short_period, adjust=False, min_periods=short_period).mean()

        # Double-smoothed absolute price change
        abs_ema1 = delta.abs().ewm(span=long_period, adjust=False, min_periods=long_period).mean()
        abs_double_smoothed = abs_ema1.ewm(span=short_period, adjust=False, min_periods=short_period).mean()

        tsi = (double_smoothed / abs_double_smoothed.replace(0, np.nan)) * 100
        return tsi

    @staticmethod
    def stoch_rsi(
        data: pd.Series,
        rsi_period: int = 14,
        stoch_period: int = 14,
        k_period: int = 3,
    ) -> pd.Series:
        """Stochastic RSI.

        Applies Stochastic formula to RSI values.

        Args:
            data: Price series
            rsi_period: RSI calculation period (default 14)
            stoch_period: Stochastic lookback period (default 14)
            k_period: Smoothing period for %K (default 3)

        Returns:
            Stochastic RSI series (0-100)
        """
        rsi = IndicatorService.rsi(data, rsi_period)

        rsi_min = rsi.rolling(window=stoch_period, min_periods=stoch_period).min()
        rsi_max = rsi.rolling(window=stoch_period, min_periods=stoch_period).max()

        stoch_rsi = ((rsi - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan)) * 100
        # Apply smoothing
        return stoch_rsi.rolling(window=k_period, min_periods=k_period).mean()

    @staticmethod
    def klinger(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        fast_period: int = 34,
        slow_period: int = 55,
    ) -> pd.Series:
        """Klinger Oscillator.

        KO = EMA(fast, volume_force) - EMA(slow, volume_force)

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume data
            fast_period: Fast EMA period (default 34)
            slow_period: Slow EMA period (default 55)

        Returns:
            Klinger Oscillator series
        """
        hlc = high + low + close
        trend = np.where(hlc > hlc.shift(1), 1, -1)

        dm = high - low
        cm = pd.Series(np.zeros(len(close)), index=close.index)
        cm.iloc[0] = dm.iloc[0]
        for i in range(1, len(close)):
            if trend[i] == trend[i - 1]:
                cm.iloc[i] = cm.iloc[i - 1] + dm.iloc[i]
            else:
                cm.iloc[i] = dm.iloc[i]

        # Volume force
        vf = volume * abs(2 * (dm / cm.replace(0, np.nan)) - 1) * np.sign(trend) * 100

        fast_ema = vf.ewm(span=fast_period, adjust=False, min_periods=fast_period).mean()
        slow_ema = vf.ewm(span=slow_period, adjust=False, min_periods=slow_period).mean()

        return fast_ema - slow_ema

    @staticmethod
    def ad(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
    ) -> pd.Series:
        """Accumulation/Distribution Line.

        AD = cumsum(((close - low) - (high - close)) / (high - low) * volume)

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            volume: Volume data

        Returns:
            A/D line series
        """
        hl_range = high - low
        clv = ((close - low) - (high - close)) / hl_range.replace(0, np.nan)
        clv = clv.fillna(0)
        return (clv * volume).cumsum()

    @staticmethod
    def vwma(
        close: pd.Series,
        volume: pd.Series,
        period: int = 20,
    ) -> pd.Series:
        """Volume Weighted Moving Average.

        VWMA = sum(close * volume, period) / sum(volume, period)

        Args:
            close: Close prices
            volume: Volume data
            period: Lookback period (default 20)

        Returns:
            VWMA series
        """
        cv = close * volume
        return cv.rolling(window=period, min_periods=period).sum() / \
            volume.rolling(window=period, min_periods=period).sum()

    @staticmethod
    def plus_di(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Plus Directional Indicator (+DI).

        Extracted from ADX calculation.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Lookback period (default 14)

        Returns:
            +DI series
        """
        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        plus_dm[(plus_dm < minus_dm)] = 0
        minus_dm[(minus_dm < plus_dm)] = 0

        atr = IndicatorService.atr(high, low, close, period)

        return 100 * (
            plus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr
        )

    @staticmethod
    def minus_di(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Minus Directional Indicator (-DI).

        Extracted from ADX calculation.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Lookback period (default 14)

        Returns:
            -DI series
        """
        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        plus_dm[(plus_dm < minus_dm)] = 0
        minus_dm[(minus_dm < plus_dm)] = 0

        atr = IndicatorService.atr(high, low, close, period)

        return 100 * (
            minus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
            / atr
        )

    @staticmethod
    def beta(
        data: pd.Series,
        benchmark: pd.Series | None = None,
        period: int = 252,
    ) -> pd.Series:
        """Rolling Beta against benchmark.

        If no benchmark provided, returns NaN series with a warning.

        Args:
            data: Price series
            benchmark: Benchmark price series (optional)
            period: Rolling window (default 252)

        Returns:
            Beta series
        """
        import logging
        logger = logging.getLogger(__name__)

        if benchmark is None:
            logger.warning("BETA: No benchmark data provided, returning NaN")
            return pd.Series(np.nan, index=data.index)

        asset_returns = data.pct_change()
        bench_returns = benchmark.pct_change()

        cov = asset_returns.rolling(window=period, min_periods=period).cov(bench_returns)
        var = bench_returns.rolling(window=period, min_periods=period).var()

        return cov / var.replace(0, np.nan)

    @staticmethod
    def correlation(
        data: pd.Series,
        benchmark: pd.Series | None = None,
        period: int = 252,
    ) -> pd.Series:
        """Rolling Correlation against benchmark.

        If no benchmark provided, returns NaN series with a warning.

        Args:
            data: Price series
            benchmark: Benchmark price series (optional)
            period: Rolling window (default 252)

        Returns:
            Correlation series (-1 to 1)
        """
        import logging
        logger = logging.getLogger(__name__)

        if benchmark is None:
            logger.warning("CORRELATION: No benchmark data provided, returning NaN")
            return pd.Series(np.nan, index=data.index)

        asset_returns = data.pct_change()
        bench_returns = benchmark.pct_change()

        return asset_returns.rolling(window=period, min_periods=period).corr(bench_returns)

    @staticmethod
    def percentile(data: pd.Series, period: int = 252) -> pd.Series:
        """Rolling Percentile Rank.

        Current value's percentile rank within the rolling window.

        Args:
            data: Price series
            period: Rolling window (default 252)

        Returns:
            Percentile series (0-100)
        """
        return data.rolling(window=period, min_periods=period).apply(
            lambda x: (np.sum(x < x[-1]) / (len(x) - 1)) * 100 if len(x) > 1 else 50.0,
            raw=True,
        )

    @staticmethod
    def rank(data: pd.Series, period: int = 252) -> pd.Series:
        """Rolling Rank.

        Rank of current value within the rolling window (1 = lowest).

        Args:
            data: Price series
            period: Rolling window (default 252)

        Returns:
            Rank series (1 to period)
        """
        return data.rolling(window=period, min_periods=period).apply(
            lambda x: np.sum(x <= x[-1]),
            raw=True,
        )

    @staticmethod
    def zscore(data: pd.Series, period: int = 20) -> pd.Series:
        """Rolling Z-Score.

        (value - rolling_mean) / rolling_std

        Args:
            data: Price series
            period: Rolling window (default 20)

        Returns:
            Z-score series
        """
        rolling_mean = data.rolling(window=period, min_periods=period).mean()
        rolling_std = data.rolling(window=period, min_periods=period).std()
        return (data - rolling_mean) / rolling_std.replace(0, np.nan)

    @staticmethod
    def simple_return(data: pd.Series, period: int = 1) -> pd.Series:
        """Simple Return over period.

        return = (current - previous) / previous

        Args:
            data: Price series
            period: Lookback period (default 1)

        Returns:
            Return series (as decimal, e.g. 0.05 = 5%)
        """
        shifted = data.shift(period)
        return (data - shifted) / shifted

    @staticmethod
    def drawdown(data: pd.Series) -> pd.Series:
        """Drawdown from rolling maximum.

        drawdown = (current - rolling_max) / rolling_max

        Args:
            data: Price series

        Returns:
            Drawdown series (negative values, 0 at peaks)
        """
        rolling_max = data.expanding(min_periods=1).max()
        return (data - rolling_max) / rolling_max
