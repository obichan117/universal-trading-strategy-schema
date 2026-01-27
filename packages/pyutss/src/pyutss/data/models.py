"""Data models for pyutss."""

from dataclasses import dataclass
from datetime import date
from enum import Enum


class Market(str, Enum):
    """Supported market identifiers."""

    JP = "JP"
    US = "US"


class Timeframe(str, Enum):
    """Data timeframe."""

    DAILY = "1d"
    WEEKLY = "1wk"
    MONTHLY = "1mo"


@dataclass
class OHLCV:
    """OHLCV (Open-High-Low-Close-Volume) price data."""

    date: date
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: float | None = None


@dataclass
class StockMetadata:
    """Stock metadata information."""

    symbol: str
    name: str
    market: Market
    sector: str | None = None
    industry: str | None = None
    market_cap: float | None = None
    currency: str = "USD"


@dataclass
class FundamentalMetrics:
    """Fundamental financial metrics."""

    symbol: str
    date: date
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    ps_ratio: float | None = None
    peg_ratio: float | None = None
    roe: float | None = None
    roa: float | None = None
    profit_margin: float | None = None
    operating_margin: float | None = None
    dividend_yield: float | None = None
    payout_ratio: float | None = None
    market_cap: float | None = None
    revenue: float | None = None
    net_income: float | None = None
    eps: float | None = None
    book_value_per_share: float | None = None
