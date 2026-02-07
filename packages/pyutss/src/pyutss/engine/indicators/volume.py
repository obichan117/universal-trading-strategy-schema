"""Volume indicator functions."""

import numpy as np
import pandas as pd

from pyutss.engine.indicators.moving_averages import sma


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume."""
    price_change = close.diff()
    signed_volume = volume.copy()
    signed_volume[price_change < 0] = -volume[price_change < 0]
    signed_volume[price_change == 0] = 0
    return signed_volume.cumsum()


def volume_ma(volume: pd.Series, period: int = 20) -> pd.Series:
    """Volume Moving Average."""
    return sma(volume, period)


def vwap(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
) -> pd.Series:
    """Volume Weighted Average Price."""
    typical_price = (high + low + close) / 3
    return (typical_price * volume).cumsum() / volume.cumsum()


def cmf(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    period: int = 20,
) -> pd.Series:
    """Chaikin Money Flow."""
    hl_range = high - low
    mfv = ((close - low) - (high - close)) / hl_range.replace(0, np.nan)
    mf_volume = mfv * volume

    return mf_volume.rolling(window=period, min_periods=period).sum() / \
        volume.rolling(window=period, min_periods=period).sum()


def ad(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
) -> pd.Series:
    """Accumulation/Distribution Line."""
    hl_range = high - low
    clv = ((close - low) - (high - close)) / hl_range.replace(0, np.nan)
    clv = clv.fillna(0)
    return (clv * volume).cumsum()


def klinger(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    fast_period: int = 34,
    slow_period: int = 55,
) -> pd.Series:
    """Klinger Oscillator."""
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

    vf = volume * abs(2 * (dm / cm.replace(0, np.nan)) - 1) * np.sign(trend) * 100

    fast_ema = vf.ewm(span=fast_period, adjust=False, min_periods=fast_period).mean()
    slow_ema = vf.ewm(span=slow_period, adjust=False, min_periods=slow_period).mean()

    return fast_ema - slow_ema
