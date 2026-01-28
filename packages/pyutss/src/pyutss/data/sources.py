"""Unified data source interface.

All data sources share the yfinance-style interface:
- Ticker(symbol).history(start, end) -> DataFrame
- Ticker(symbol).info -> stock info

Usage:
    from pyutss.data import Ticker, fetch

    # Auto-detect source based on symbol
    df = fetch("AAPL", "2024-01-01", "2024-12-31")
    df = fetch("7203", "2024-01-01", "2024-12-31")

    # Explicit source
    df = fetch("7203", "2024-01-01", "2024-12-31", source="jquants")

    # Ticker-style (mirrors yfinance API)
    ticker = Ticker("AAPL")
    df = ticker.history(start="2024-01-01", end="2024-12-31")
    print(ticker.info)
"""

import os
from datetime import date
from typing import Any

import pandas as pd

# Available data sources and their import paths
SOURCES = {
    "yahoo": ("yfinance", "yf"),
    "jquants": ("pyjquants", "pjq"),
}

# Default source for each market
DEFAULT_SOURCES = {
    "US": "yahoo",
    "JP": "jquants",
}

# Fallback source when preferred is unavailable
FALLBACK_SOURCE = "yahoo"


def _import_source(source: str) -> Any:
    """Import and return a data source module.

    Args:
        source: Source name ("yahoo", "jquants", etc.)

    Returns:
        The imported module

    Raises:
        ValueError: If source is unknown
        ImportError: If source library is not installed
    """
    if source not in SOURCES:
        available = ", ".join(SOURCES.keys())
        raise ValueError(f"Unknown source: {source}. Available: {available}")

    package_name, _ = SOURCES[source]

    try:
        if source == "yahoo":
            import yfinance as module
        elif source == "jquants":
            import pyjquants as module
        else:
            raise ValueError(f"Source {source} not implemented")
        return module
    except ImportError as e:
        raise ImportError(
            f"Source '{source}' requires {package_name}. "
            f"Install with: pip install pyutss[{source}]"
        ) from e


def _detect_market(symbol: str) -> str:
    """Detect market from symbol format.

    Args:
        symbol: Stock symbol

    Returns:
        Market code ("US" or "JP")
    """
    # Japanese: 4-digit code or .T suffix
    if symbol.endswith(".T"):
        return "JP"
    clean = symbol.split(".")[0]
    if clean.isdigit() and len(clean) == 4:
        return "JP"
    return "US"


def _check_api_key(source: str, prompt: bool = True) -> bool:
    """Check if API key is available for a source.

    Args:
        source: Source name
        prompt: Whether to prompt for key if missing

    Returns:
        True if API key is available
    """
    if source == "jquants":
        from pyutss.data.config import get_api_key
        key = get_api_key("jquants", prompt_if_missing=prompt)
        if key:
            # Set environment variable for pyjquants
            os.environ["JQUANTS_API_KEY"] = key
            return True
        return False
    # Yahoo doesn't need API key
    return True


def _get_source_for_symbol(symbol: str, prompt_for_key: bool = True) -> str:
    """Get the best available source for a symbol.

    Args:
        symbol: Stock symbol
        prompt_for_key: Whether to prompt for API key if missing

    Returns:
        Source name
    """
    market = _detect_market(symbol)
    preferred = DEFAULT_SOURCES.get(market, FALLBACK_SOURCE)

    # Try preferred source first
    try:
        _import_source(preferred)
        # Check if API key is configured (may prompt user)
        if _check_api_key(preferred, prompt=prompt_for_key):
            return preferred
    except (ImportError, Exception):
        pass

    # Fall back if preferred unavailable
    if preferred != FALLBACK_SOURCE:
        try:
            _import_source(FALLBACK_SOURCE)
            return FALLBACK_SOURCE
        except ImportError:
            pass

    raise ImportError(
        f"No data source available for {symbol}. "
        f"Install with: pip install pyutss[yahoo] or pyutss[jquants]"
    )


class Ticker:
    """Unified Ticker interface for all data sources.

    Wraps the underlying data source's Ticker class with a consistent interface.
    Auto-detects the appropriate source based on symbol format.

    Example:
        ticker = Ticker("AAPL")           # US stock -> yahoo
        ticker = Ticker("7203")           # JP stock -> jquants
        ticker = Ticker("7203", "yahoo")  # Explicit source

        df = ticker.history(start="2024-01-01", end="2024-12-31")
        print(ticker.info)
    """

    def __init__(self, symbol: str, source: str | None = None):
        """Initialize Ticker.

        Args:
            symbol: Stock symbol (e.g., "AAPL", "7203", "7203.T")
            source: Data source name. If None, auto-detects based on symbol.
        """
        self.symbol = symbol
        self.source = source or _get_source_for_symbol(symbol)
        self._module = _import_source(self.source)
        self._ticker = self._module.Ticker(self._normalize_symbol())

    def _normalize_symbol(self) -> str:
        """Normalize symbol for the data source."""
        if self.source == "jquants":
            # pyjquants uses 4-digit codes without .T suffix
            if self.symbol.endswith(".T"):
                return self.symbol[:-2]
        elif self.source == "yahoo":
            # yfinance uses .T suffix for Japanese stocks
            if self.symbol.isdigit() and len(self.symbol) == 4:
                return f"{self.symbol}.T"
        return self.symbol

    def history(
        self,
        period: str | None = None,
        start: str | date | None = None,
        end: str | date | None = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data.

        Args:
            period: Time period (e.g., "1d", "5d", "1mo", "1y", "max")
            start: Start date (string "YYYY-MM-DD" or date object)
            end: End date (string "YYYY-MM-DD" or date object)
            **kwargs: Additional arguments passed to underlying library

        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume
        """
        if period:
            return self._ticker.history(period=period, **kwargs)
        return self._ticker.history(start=start, end=end, **kwargs)

    @property
    def info(self) -> Any:
        """Get stock information."""
        return self._ticker.info

    def __repr__(self) -> str:
        return f"Ticker({self.symbol!r}, source={self.source!r})"


def fetch(
    symbol: str,
    start: str | date,
    end: str | date,
    source: str | None = None,
) -> pd.DataFrame:
    """Fetch OHLCV data for a symbol.

    Simple function interface for fetching historical data.

    Args:
        symbol: Stock symbol (e.g., "AAPL", "7203")
        start: Start date (string "YYYY-MM-DD" or date object)
        end: End date (string "YYYY-MM-DD" or date object)
        source: Data source name. If None, auto-detects based on symbol.

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume

    Example:
        df = fetch("AAPL", "2024-01-01", "2024-12-31")
        df = fetch("7203", "2024-01-01", "2024-12-31", source="jquants")
    """
    ticker = Ticker(symbol, source=source)
    return ticker.history(start=start, end=end)


def download(
    symbols: list[str],
    start: str | date,
    end: str | date,
    source: str | None = None,
) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV data for multiple symbols.

    Args:
        symbols: List of stock symbols
        start: Start date
        end: End date
        source: Data source name (applied to all symbols if specified)

    Returns:
        Dict mapping symbol to DataFrame

    Example:
        data = download(["AAPL", "MSFT", "GOOGL"], "2024-01-01", "2024-12-31")
    """
    return {sym: fetch(sym, start, end, source) for sym in symbols}


def available_sources() -> list[str]:
    """List available data sources.

    Returns:
        List of source names that are installed and available.
    """
    available = []
    for source in SOURCES:
        try:
            _import_source(source)
            available.append(source)
        except ImportError:
            pass
    return available
