"""Moving average indicator functions."""

import numpy as np
import pandas as pd


def sma(data: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return data.rolling(window=period, min_periods=period).mean()


def ema(data: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return data.ewm(span=period, adjust=False, min_periods=period).mean()


def wma(data: pd.Series, period: int) -> pd.Series:
    """Weighted Moving Average."""
    weights = np.arange(1, period + 1)
    return data.rolling(window=period).apply(
        lambda x: np.dot(x, weights) / weights.sum(), raw=True
    )


def dema(data: pd.Series, period: int) -> pd.Series:
    """Double Exponential Moving Average."""
    ema1 = ema(data, period)
    ema2 = ema(ema1, period)
    return 2 * ema1 - ema2


def tema(data: pd.Series, period: int) -> pd.Series:
    """Triple Exponential Moving Average."""
    ema1 = ema(data, period)
    ema2 = ema(ema1, period)
    ema3 = ema(ema2, period)
    return 3 * ema1 - 3 * ema2 + ema3


def kama(
    data: pd.Series,
    period: int = 10,
    fast_period: int = 2,
    slow_period: int = 30,
) -> pd.Series:
    """Kaufman Adaptive Moving Average."""
    fast_sc = 2.0 / (fast_period + 1)
    slow_sc = 2.0 / (slow_period + 1)

    values = data.values.astype(float)
    n = len(values)
    kama_values = np.full(n, np.nan)

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


def hull(data: pd.Series, period: int = 9) -> pd.Series:
    """Hull Moving Average.

    HMA = WMA(2 * WMA(n/2) - WMA(n), sqrt(n))
    """
    half_period = max(int(period / 2), 1)
    sqrt_period = max(int(np.sqrt(period)), 1)

    wma_half = wma(data, half_period)
    wma_full = wma(data, period)
    diff = 2 * wma_half - wma_full
    return wma(diff, sqrt_period)


def vwma(
    close: pd.Series,
    volume: pd.Series,
    period: int = 20,
) -> pd.Series:
    """Volume Weighted Moving Average.

    VWMA = sum(close * volume, period) / sum(volume, period)
    """
    cv = close * volume
    return cv.rolling(window=period, min_periods=period).sum() / \
        volume.rolling(window=period, min_periods=period).sum()
