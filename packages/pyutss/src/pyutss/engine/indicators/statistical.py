"""Statistical indicator functions."""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def highest(data: pd.Series, period: int) -> pd.Series:
    """Rolling Maximum (highest value over period)."""
    return data.rolling(window=period, min_periods=period).max()


def lowest(data: pd.Series, period: int) -> pd.Series:
    """Rolling Minimum (lowest value over period)."""
    return data.rolling(window=period, min_periods=period).min()


def simple_return(data: pd.Series, period: int = 1) -> pd.Series:
    """Simple Return over period."""
    shifted = data.shift(period)
    return (data - shifted) / shifted


def drawdown(data: pd.Series) -> pd.Series:
    """Drawdown from rolling maximum."""
    rolling_max = data.expanding(min_periods=1).max()
    return (data - rolling_max) / rolling_max


def zscore(data: pd.Series, period: int = 20) -> pd.Series:
    """Rolling Z-Score."""
    rolling_mean = data.rolling(window=period, min_periods=period).mean()
    rolling_std = data.rolling(window=period, min_periods=period).std()
    return (data - rolling_mean) / rolling_std.replace(0, np.nan)


def percentile(data: pd.Series, period: int = 252) -> pd.Series:
    """Rolling Percentile Rank."""
    return data.rolling(window=period, min_periods=period).apply(
        lambda x: (np.sum(x < x[-1]) / (len(x) - 1)) * 100 if len(x) > 1 else 50.0,
        raw=True,
    )


def rank(data: pd.Series, period: int = 252) -> pd.Series:
    """Rolling Rank."""
    return data.rolling(window=period, min_periods=period).apply(
        lambda x: np.sum(x <= x[-1]),
        raw=True,
    )


def beta(
    data: pd.Series,
    benchmark: pd.Series | None = None,
    period: int = 252,
) -> pd.Series:
    """Rolling Beta against benchmark."""
    if benchmark is None:
        logger.warning("BETA: No benchmark data provided, returning NaN")
        return pd.Series(np.nan, index=data.index)

    asset_returns = data.pct_change()
    bench_returns = benchmark.pct_change()

    cov = asset_returns.rolling(window=period, min_periods=period).cov(bench_returns)
    var = bench_returns.rolling(window=period, min_periods=period).var()

    return cov / var.replace(0, np.nan)


def correlation(
    data: pd.Series,
    benchmark: pd.Series | None = None,
    period: int = 252,
) -> pd.Series:
    """Rolling Correlation against benchmark."""
    if benchmark is None:
        logger.warning("CORRELATION: No benchmark data provided, returning NaN")
        return pd.Series(np.nan, index=data.index)

    asset_returns = data.pct_change()
    bench_returns = benchmark.pct_change()

    return asset_returns.rolling(window=period, min_periods=period).corr(bench_returns)
