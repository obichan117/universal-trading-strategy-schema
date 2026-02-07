"""Momentum indicator functions."""

import numpy as np
import pandas as pd

from pyutss.engine.indicators.moving_averages import ema, sma
from pyutss.engine.indicators.results import MACDResult, StochasticResult


def rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = data.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi_val = 100 - (100 / (1 + rs))
    return rsi_val.replace([np.inf, -np.inf], np.nan)


def macd(
    data: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> MACDResult:
    """Moving Average Convergence Divergence."""
    fast_ema = ema(data, fast_period)
    slow_ema = ema(data, slow_period)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal_period)
    histogram = macd_line - signal_line

    return MACDResult(
        macd_line=macd_line,
        signal_line=signal_line,
        histogram=histogram,
    )


def stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3,
) -> StochasticResult:
    """Stochastic Oscillator."""
    lowest_low = low.rolling(window=k_period, min_periods=k_period).min()
    highest_high = high.rolling(window=k_period, min_periods=k_period).max()

    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period, min_periods=d_period).mean()

    return StochasticResult(k=k, d=d)


def williams_r(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Williams %R."""
    highest_high = high.rolling(window=period, min_periods=period).max()
    lowest_low = low.rolling(window=period, min_periods=period).min()
    return -100 * (highest_high - close) / (highest_high - lowest_low)


def cci(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 20,
) -> pd.Series:
    """Commodity Channel Index."""
    typical_price = (high + low + close) / 3
    sma_val = sma(typical_price, period)
    mean_deviation = typical_price.rolling(window=period).apply(
        lambda x: np.abs(x - x.mean()).mean(), raw=True
    )
    return (typical_price - sma_val) / (0.015 * mean_deviation)


def mfi(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Money Flow Index."""
    typical_price = (high + low + close) / 3
    raw_money_flow = typical_price * volume

    positive_flow = raw_money_flow.where(typical_price > typical_price.shift(1), 0)
    negative_flow = raw_money_flow.where(typical_price < typical_price.shift(1), 0)

    positive_mf = positive_flow.rolling(window=period).sum()
    negative_mf = negative_flow.rolling(window=period).sum()

    money_ratio = positive_mf / negative_mf
    return 100 - (100 / (1 + money_ratio))


def cmo(data: pd.Series, period: int = 14) -> pd.Series:
    """Chande Momentum Oscillator."""
    delta = data.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    up_sum = gain.rolling(window=period, min_periods=period).sum()
    down_sum = loss.rolling(window=period, min_periods=period).sum()

    total = up_sum + down_sum
    cmo_val = ((up_sum - down_sum) / total.replace(0, np.nan)) * 100
    return cmo_val


def tsi(
    data: pd.Series,
    long_period: int = 25,
    short_period: int = 13,
) -> pd.Series:
    """True Strength Index."""
    delta = data.diff()

    ema1 = delta.ewm(span=long_period, adjust=False, min_periods=long_period).mean()
    double_smoothed = ema1.ewm(span=short_period, adjust=False, min_periods=short_period).mean()

    abs_ema1 = delta.abs().ewm(span=long_period, adjust=False, min_periods=long_period).mean()
    abs_double_smoothed = abs_ema1.ewm(span=short_period, adjust=False, min_periods=short_period).mean()

    tsi_val = (double_smoothed / abs_double_smoothed.replace(0, np.nan)) * 100
    return tsi_val


def stoch_rsi(
    data: pd.Series,
    rsi_period: int = 14,
    stoch_period: int = 14,
    k_period: int = 3,
) -> pd.Series:
    """Stochastic RSI."""
    rsi_val = rsi(data, rsi_period)

    rsi_min = rsi_val.rolling(window=stoch_period, min_periods=stoch_period).min()
    rsi_max = rsi_val.rolling(window=stoch_period, min_periods=stoch_period).max()

    stoch_rsi_val = ((rsi_val - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan)) * 100
    return stoch_rsi_val.rolling(window=k_period, min_periods=k_period).mean()


def roc(data: pd.Series, period: int = 12) -> pd.Series:
    """Rate of Change."""
    shifted = data.shift(period)
    return (data - shifted) / shifted * 100


def momentum(data: pd.Series, period: int = 10) -> pd.Series:
    """Momentum indicator."""
    return data - data.shift(period)


def detect_crosses(fast: pd.Series, slow: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Detect cross events between two series.

    Returns:
        Tuple of (crosses_above, crosses_below) boolean series
    """
    prev_fast = fast.shift(1)
    prev_slow = slow.shift(1)

    crosses_above = (fast > slow) & (prev_fast <= prev_slow)
    crosses_below = (fast < slow) & (prev_fast >= prev_slow)

    return crosses_above, crosses_below
