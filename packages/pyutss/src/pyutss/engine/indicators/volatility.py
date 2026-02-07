"""Volatility indicator functions."""

import pandas as pd

from pyutss.engine.indicators.moving_averages import sma
from pyutss.engine.indicators.results import BollingerBandsResult


def atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Average True Range."""
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr_val = true_range.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    return atr_val


def stddev(data: pd.Series, period: int = 20) -> pd.Series:
    """Rolling Standard Deviation."""
    return data.rolling(window=period, min_periods=period).std()


def variance(data: pd.Series, period: int = 20) -> pd.Series:
    """Rolling Variance."""
    return data.rolling(window=period, min_periods=period).var()


def bollinger_bands(
    data: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> BollingerBandsResult:
    """Bollinger Bands."""
    middle = sma(data, period)
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
