"""Result dataclasses for multi-output indicators."""

from dataclasses import dataclass

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
