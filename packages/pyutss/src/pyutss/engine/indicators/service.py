"""IndicatorService class — delegates to category modules."""

import pandas as pd

from pyutss.engine.indicators import (
    momentum,
    moving_averages,
    statistical,
    trend,
    volatility,
)
from pyutss.engine.indicators import volume as volume_mod
from pyutss.engine.indicators.results import (
    AroonResult,
    BollingerBandsResult,
    DonchianChannelResult,
    KeltnerChannelResult,
    MACDResult,
    StochasticResult,
)


class IndicatorService:
    """Technical indicator calculation service.

    Implements all UTSS-supported indicators with optimized calculations
    using pandas and numpy.

    Example:
        rsi = IndicatorService.rsi(close_prices, period=14)

        macd = IndicatorService.macd(close_prices)
        print(macd.macd_line, macd.signal_line)
    """

    # --- Moving Averages ---

    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average."""
        return moving_averages.sma(data, period)

    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average."""
        return moving_averages.ema(data, period)

    @staticmethod
    def wma(data: pd.Series, period: int) -> pd.Series:
        """Weighted Moving Average."""
        return moving_averages.wma(data, period)

    @staticmethod
    def dema(data: pd.Series, period: int) -> pd.Series:
        """Double Exponential Moving Average."""
        return moving_averages.dema(data, period)

    @staticmethod
    def tema(data: pd.Series, period: int) -> pd.Series:
        """Triple Exponential Moving Average."""
        return moving_averages.tema(data, period)

    @staticmethod
    def kama(
        data: pd.Series,
        period: int = 10,
        fast_period: int = 2,
        slow_period: int = 30,
    ) -> pd.Series:
        """Kaufman Adaptive Moving Average."""
        return moving_averages.kama(data, period, fast_period, slow_period)

    @staticmethod
    def hull(data: pd.Series, period: int = 9) -> pd.Series:
        """Hull Moving Average."""
        return moving_averages.hull(data, period)

    @staticmethod
    def vwma(
        close: pd.Series,
        volume: pd.Series,
        period: int = 20,
    ) -> pd.Series:
        """Volume Weighted Moving Average."""
        return moving_averages.vwma(close, volume, period)

    # --- Momentum ---

    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index."""
        return momentum.rsi(data, period)

    @staticmethod
    def macd(
        data: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> MACDResult:
        """Moving Average Convergence Divergence."""
        return momentum.macd(data, fast_period, slow_period, signal_period)

    @staticmethod
    def stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3,
    ) -> StochasticResult:
        """Stochastic Oscillator."""
        return momentum.stochastic(high, low, close, k_period, d_period)

    @staticmethod
    def williams_r(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Williams %R."""
        return momentum.williams_r(high, low, close, period)

    @staticmethod
    def cci(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 20,
    ) -> pd.Series:
        """Commodity Channel Index."""
        return momentum.cci(high, low, close, period)

    @staticmethod
    def mfi(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Money Flow Index."""
        return momentum.mfi(high, low, close, volume, period)

    @staticmethod
    def cmo(data: pd.Series, period: int = 14) -> pd.Series:
        """Chande Momentum Oscillator."""
        return momentum.cmo(data, period)

    @staticmethod
    def tsi(
        data: pd.Series,
        long_period: int = 25,
        short_period: int = 13,
    ) -> pd.Series:
        """True Strength Index."""
        return momentum.tsi(data, long_period, short_period)

    @staticmethod
    def stoch_rsi(
        data: pd.Series,
        rsi_period: int = 14,
        stoch_period: int = 14,
        k_period: int = 3,
    ) -> pd.Series:
        """Stochastic RSI."""
        return momentum.stoch_rsi(data, rsi_period, stoch_period, k_period)

    @staticmethod
    def roc(data: pd.Series, period: int = 12) -> pd.Series:
        """Rate of Change."""
        return momentum.roc(data, period)

    @staticmethod
    def momentum(data: pd.Series, period: int = 10) -> pd.Series:
        """Momentum indicator."""
        return momentum.momentum(data, period)

    @staticmethod
    def detect_crosses(fast: pd.Series, slow: pd.Series) -> tuple[pd.Series, pd.Series]:
        """Detect cross events between two series."""
        return momentum.detect_crosses(fast, slow)

    # --- Volatility ---

    @staticmethod
    def atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Average True Range."""
        return volatility.atr(high, low, close, period)

    @staticmethod
    def stddev(data: pd.Series, period: int = 20) -> pd.Series:
        """Rolling Standard Deviation."""
        return volatility.stddev(data, period)

    @staticmethod
    def variance(data: pd.Series, period: int = 20) -> pd.Series:
        """Rolling Variance."""
        return volatility.variance(data, period)

    @staticmethod
    def bollinger_bands(
        data: pd.Series,
        period: int = 20,
        std_dev: float = 2.0,
    ) -> BollingerBandsResult:
        """Bollinger Bands."""
        return volatility.bollinger_bands(data, period, std_dev)

    # --- Trend ---

    @staticmethod
    def adx(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Average Directional Index."""
        return trend.adx(high, low, close, period)

    @staticmethod
    def plus_di(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Plus Directional Indicator (+DI)."""
        return trend.plus_di(high, low, close, period)

    @staticmethod
    def minus_di(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Minus Directional Indicator (-DI)."""
        return trend.minus_di(high, low, close, period)

    @staticmethod
    def supertrend(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 10,
        multiplier: float = 3.0,
    ) -> pd.Series:
        """Supertrend indicator."""
        return trend.supertrend(high, low, close, period, multiplier)

    @staticmethod
    def psar(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        af_start: float = 0.02,
        af_increment: float = 0.02,
        af_max: float = 0.2,
    ) -> pd.Series:
        """Parabolic SAR."""
        return trend.psar(high, low, close, af_start, af_increment, af_max)

    @staticmethod
    def aroon(
        high: pd.Series,
        low: pd.Series,
        period: int = 25,
    ) -> AroonResult:
        """Aroon Indicator."""
        return trend.aroon(high, low, period)

    @staticmethod
    def ichimoku_tenkan(
        high: pd.Series,
        low: pd.Series,
        period: int = 9,
    ) -> pd.Series:
        """Ichimoku Tenkan-sen (Conversion Line)."""
        return trend.ichimoku_tenkan(high, low, period)

    @staticmethod
    def ichimoku_kijun(
        high: pd.Series,
        low: pd.Series,
        period: int = 26,
    ) -> pd.Series:
        """Ichimoku Kijun-sen (Base Line)."""
        return trend.ichimoku_kijun(high, low, period)

    @staticmethod
    def ichimoku_senkou_a(
        high: pd.Series,
        low: pd.Series,
        tenkan_period: int = 9,
        kijun_period: int = 26,
    ) -> pd.Series:
        """Ichimoku Senkou Span A (Leading Span A)."""
        return trend.ichimoku_senkou_a(high, low, tenkan_period, kijun_period)

    @staticmethod
    def ichimoku_senkou_b(
        high: pd.Series,
        low: pd.Series,
        period: int = 52,
    ) -> pd.Series:
        """Ichimoku Senkou Span B (Leading Span B)."""
        return trend.ichimoku_senkou_b(high, low, period)

    @staticmethod
    def ichimoku_chikou(
        close: pd.Series,
        period: int = 26,
    ) -> pd.Series:
        """Ichimoku Chikou Span (Lagging Span)."""
        return trend.ichimoku_chikou(close, period)

    @staticmethod
    def donchian_channel(
        high: pd.Series,
        low: pd.Series,
        period: int = 20,
    ) -> DonchianChannelResult:
        """Donchian Channel."""
        return trend.donchian_channel(high, low, period)

    @staticmethod
    def keltner_channel(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        ema_period: int = 20,
        atr_period: int = 10,
        multiplier: float = 2.0,
    ) -> KeltnerChannelResult:
        """Keltner Channel."""
        return trend.keltner_channel(high, low, close, ema_period, atr_period, multiplier)

    # --- Volume ---

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume."""
        return volume_mod.obv(close, volume)

    @staticmethod
    def volume_ma(vol: pd.Series, period: int = 20) -> pd.Series:
        """Volume Moving Average."""
        return volume_mod.volume_ma(vol, period)

    @staticmethod
    def vwap(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        vol: pd.Series,
    ) -> pd.Series:
        """Volume Weighted Average Price."""
        return volume_mod.vwap(high, low, close, vol)

    @staticmethod
    def cmf(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        vol: pd.Series,
        period: int = 20,
    ) -> pd.Series:
        """Chaikin Money Flow."""
        return volume_mod.cmf(high, low, close, vol, period)

    @staticmethod
    def ad(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        vol: pd.Series,
    ) -> pd.Series:
        """Accumulation/Distribution Line."""
        return volume_mod.ad(high, low, close, vol)

    @staticmethod
    def klinger(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        vol: pd.Series,
        fast_period: int = 34,
        slow_period: int = 55,
    ) -> pd.Series:
        """Klinger Oscillator."""
        return volume_mod.klinger(high, low, close, vol, fast_period, slow_period)

    # --- Statistical ---

    @staticmethod
    def highest(data: pd.Series, period: int) -> pd.Series:
        """Rolling Maximum (highest value over period)."""
        return statistical.highest(data, period)

    @staticmethod
    def lowest(data: pd.Series, period: int) -> pd.Series:
        """Rolling Minimum (lowest value over period)."""
        return statistical.lowest(data, period)

    @staticmethod
    def simple_return(data: pd.Series, period: int = 1) -> pd.Series:
        """Simple Return over period."""
        return statistical.simple_return(data, period)

    @staticmethod
    def drawdown(data: pd.Series) -> pd.Series:
        """Drawdown from rolling maximum."""
        return statistical.drawdown(data)

    @staticmethod
    def zscore(data: pd.Series, period: int = 20) -> pd.Series:
        """Rolling Z-Score."""
        return statistical.zscore(data, period)

    @staticmethod
    def percentile(data: pd.Series, period: int = 252) -> pd.Series:
        """Rolling Percentile Rank."""
        return statistical.percentile(data, period)

    @staticmethod
    def rank(data: pd.Series, period: int = 252) -> pd.Series:
        """Rolling Rank."""
        return statistical.rank(data, period)

    @staticmethod
    def beta(
        data: pd.Series,
        benchmark: pd.Series | None = None,
        period: int = 252,
    ) -> pd.Series:
        """Rolling Beta against benchmark."""
        return statistical.beta(data, benchmark, period)

    @staticmethod
    def correlation(
        data: pd.Series,
        benchmark: pd.Series | None = None,
        period: int = 252,
    ) -> pd.Series:
        """Rolling Correlation against benchmark."""
        return statistical.correlation(data, benchmark, period)
