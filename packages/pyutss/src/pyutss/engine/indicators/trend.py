"""Trend indicator functions."""

import numpy as np
import pandas as pd

from pyutss.engine.indicators.moving_averages import ema
from pyutss.engine.indicators.results import (
    AroonResult,
    DonchianChannelResult,
    KeltnerChannelResult,
)
from pyutss.engine.indicators.volatility import atr


def adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Average Directional Index."""
    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    plus_dm[(plus_dm < minus_dm)] = 0
    minus_dm[(minus_dm < plus_dm)] = 0

    atr_val = atr(high, low, close, period)

    plus_di = 100 * (
        plus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr_val
    )
    minus_di = 100 * (
        minus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        / atr_val
    )

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx_val = dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    return adx_val


def plus_di(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Plus Directional Indicator (+DI)."""
    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    plus_dm[(plus_dm < minus_dm)] = 0
    minus_dm[(minus_dm < plus_dm)] = 0

    atr_val = atr(high, low, close, period)

    return 100 * (
        plus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr_val
    )


def minus_di(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Minus Directional Indicator (-DI)."""
    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0

    plus_dm[(plus_dm < minus_dm)] = 0
    minus_dm[(minus_dm < plus_dm)] = 0

    atr_val = atr(high, low, close, period)

    return 100 * (
        minus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        / atr_val
    )


def supertrend(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 10,
    multiplier: float = 3.0,
) -> pd.Series:
    """Supertrend indicator."""
    atr_val = atr(high, low, close, period)
    hl2 = (high + low) / 2

    upper_band = (hl2 + multiplier * atr_val).values.astype(float)
    lower_band = (hl2 - multiplier * atr_val).values.astype(float)
    close_vals = close.values.astype(float)
    n = len(close_vals)

    supertrend_vals = np.full(n, np.nan)
    direction = np.zeros(n)

    first_valid = None
    for i in range(n):
        if not np.isnan(upper_band[i]) and not np.isnan(lower_band[i]):
            first_valid = i
            break

    if first_valid is None:
        return pd.Series(supertrend_vals, index=close.index)

    supertrend_vals[first_valid] = upper_band[first_valid]
    direction[first_valid] = -1

    for i in range(first_valid + 1, n):
        if lower_band[i] > lower_band[i - 1] or close_vals[i - 1] < lower_band[i - 1]:
            pass
        else:
            lower_band[i] = lower_band[i - 1]

        if upper_band[i] < upper_band[i - 1] or close_vals[i - 1] > upper_band[i - 1]:
            pass
        else:
            upper_band[i] = upper_band[i - 1]

        if direction[i - 1] == -1:
            if close_vals[i] > upper_band[i - 1]:
                direction[i] = 1
            else:
                direction[i] = -1
        else:
            if close_vals[i] < lower_band[i - 1]:
                direction[i] = -1
            else:
                direction[i] = 1

        if direction[i] == 1:
            supertrend_vals[i] = lower_band[i]
        else:
            supertrend_vals[i] = upper_band[i]

    return pd.Series(supertrend_vals, index=close.index)


def psar(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    af_start: float = 0.02,
    af_increment: float = 0.02,
    af_max: float = 0.2,
) -> pd.Series:
    """Parabolic SAR."""
    high_vals = high.values.astype(float)
    low_vals = low.values.astype(float)
    close_vals = close.values.astype(float)
    n = len(close_vals)
    sar = np.full(n, np.nan)

    if n < 2:
        return pd.Series(sar, index=close.index)

    first_valid = 0
    while first_valid < n and (
        np.isnan(high_vals[first_valid])
        or np.isnan(low_vals[first_valid])
        or np.isnan(close_vals[first_valid])
    ):
        first_valid += 1

    if first_valid >= n - 1:
        return pd.Series(sar, index=close.index)

    if close_vals[first_valid + 1] >= close_vals[first_valid]:
        trend = 1
        sar[first_valid] = low_vals[first_valid]
        ep = high_vals[first_valid]
    else:
        trend = -1
        sar[first_valid] = high_vals[first_valid]
        ep = low_vals[first_valid]

    af = af_start

    for i in range(first_valid + 1, n):
        prev_sar = sar[i - 1]

        if trend == 1:
            sar[i] = prev_sar + af * (ep - prev_sar)
            sar[i] = min(sar[i], low_vals[i - 1])
            if i >= first_valid + 2:
                sar[i] = min(sar[i], low_vals[i - 2])

            if low_vals[i] < sar[i]:
                trend = -1
                sar[i] = ep
                ep = low_vals[i]
                af = af_start
            else:
                if high_vals[i] > ep:
                    ep = high_vals[i]
                    af = min(af + af_increment, af_max)
        else:
            sar[i] = prev_sar + af * (ep - prev_sar)
            sar[i] = max(sar[i], high_vals[i - 1])
            if i >= first_valid + 2:
                sar[i] = max(sar[i], high_vals[i - 2])

            if high_vals[i] > sar[i]:
                trend = 1
                sar[i] = ep
                ep = high_vals[i]
                af = af_start
            else:
                if low_vals[i] < ep:
                    ep = low_vals[i]
                    af = min(af + af_increment, af_max)

    return pd.Series(sar, index=close.index)


def aroon(
    high: pd.Series,
    low: pd.Series,
    period: int = 25,
) -> AroonResult:
    """Aroon Indicator."""
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


def ichimoku_tenkan(
    high: pd.Series,
    low: pd.Series,
    period: int = 9,
) -> pd.Series:
    """Ichimoku Tenkan-sen (Conversion Line)."""
    highest_high = high.rolling(window=period, min_periods=period).max()
    lowest_low = low.rolling(window=period, min_periods=period).min()
    return (highest_high + lowest_low) / 2


def ichimoku_kijun(
    high: pd.Series,
    low: pd.Series,
    period: int = 26,
) -> pd.Series:
    """Ichimoku Kijun-sen (Base Line)."""
    highest_high = high.rolling(window=period, min_periods=period).max()
    lowest_low = low.rolling(window=period, min_periods=period).min()
    return (highest_high + lowest_low) / 2


def ichimoku_senkou_a(
    high: pd.Series,
    low: pd.Series,
    tenkan_period: int = 9,
    kijun_period: int = 26,
) -> pd.Series:
    """Ichimoku Senkou Span A (Leading Span A)."""
    tenkan = ichimoku_tenkan(high, low, tenkan_period)
    kijun = ichimoku_kijun(high, low, kijun_period)
    return ((tenkan + kijun) / 2).shift(kijun_period)


def ichimoku_senkou_b(
    high: pd.Series,
    low: pd.Series,
    period: int = 52,
) -> pd.Series:
    """Ichimoku Senkou Span B (Leading Span B)."""
    highest_high = high.rolling(window=period, min_periods=period).max()
    lowest_low = low.rolling(window=period, min_periods=period).min()
    return ((highest_high + lowest_low) / 2).shift(26)


def ichimoku_chikou(
    close: pd.Series,
    period: int = 26,
) -> pd.Series:
    """Ichimoku Chikou Span (Lagging Span)."""
    return close.shift(period)


def donchian_channel(
    high: pd.Series,
    low: pd.Series,
    period: int = 20,
) -> DonchianChannelResult:
    """Donchian Channel."""
    upper = high.rolling(window=period, min_periods=period).max()
    lower = low.rolling(window=period, min_periods=period).min()
    middle = (upper + lower) / 2
    return DonchianChannelResult(upper=upper, middle=middle, lower=lower)


def keltner_channel(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    ema_period: int = 20,
    atr_period: int = 10,
    multiplier: float = 2.0,
) -> KeltnerChannelResult:
    """Keltner Channel."""
    middle = ema(close, ema_period)
    atr_val = atr(high, low, close, atr_period)
    upper = middle + multiplier * atr_val
    lower = middle - multiplier * atr_val
    return KeltnerChannelResult(upper=upper, middle=middle, lower=lower)
