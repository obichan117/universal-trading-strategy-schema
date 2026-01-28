"""Data module for pyutss.

Simple, unified interface for fetching market data from multiple sources.
All sources share the same yfinance-style API.

Quick Start:
    from pyutss.data import fetch, Ticker

    # Fetch data (auto-detects source based on symbol)
    df = fetch("AAPL", "2024-01-01", "2024-12-31")      # US -> yahoo
    df = fetch("7203", "2024-01-01", "2024-12-31")      # JP -> jquants

    # Explicit source
    df = fetch("7203", "2024-01-01", "2024-12-31", source="yahoo")

    # Ticker-style (mirrors yfinance API)
    ticker = Ticker("AAPL")
    df = ticker.history(start="2024-01-01", end="2024-12-31")
    print(ticker.info)

    # Multiple symbols
    data = download(["AAPL", "MSFT"], "2024-01-01", "2024-12-31")

Available Sources:
    - "yahoo": Yahoo Finance (US, JP, global) - pip install pyutss[yahoo]
    - "jquants": J-Quants (JP only) - pip install pyutss[jquants]
"""

# Primary interface - simple and unified
# Configuration
from pyutss.data.config import (
    configure,
    get_api_key,
    set_api_key,
    show_config,
)

# Data models
from pyutss.data.models import (
    OHLCV,
    FundamentalMetrics,
    Market,
    StockMetadata,
    Timeframe,
)

# Legacy provider interface (for backward compatibility)
from pyutss.data.providers.base import BaseDataProvider, DataProviderError
from pyutss.data.providers.registry import (
    DataProviderRegistry,
    get_default_registry,
    get_registry,
)
from pyutss.data.sources import (
    DEFAULT_SOURCES,
    SOURCES,
    Ticker,
    available_sources,
    download,
    fetch,
)

__all__ = [
    # Primary interface
    "Ticker",
    "fetch",
    "download",
    "available_sources",
    "SOURCES",
    "DEFAULT_SOURCES",
    # Configuration
    "configure",
    "get_api_key",
    "set_api_key",
    "show_config",
    # Models
    "OHLCV",
    "StockMetadata",
    "FundamentalMetrics",
    "Market",
    "Timeframe",
    # Legacy (deprecated)
    "BaseDataProvider",
    "DataProviderError",
    "DataProviderRegistry",
    "get_default_registry",
    "get_registry",
]
