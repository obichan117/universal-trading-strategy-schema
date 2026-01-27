"""Data providers for pyutss."""

from pyutss.data.providers.base import BaseDataProvider, DataProviderError

__all__ = [
    "BaseDataProvider",
    "DataProviderError",
]


def get_yahoo_provider():
    """Get Yahoo Finance provider (lazy import).

    Returns:
        YahooFinanceProvider instance

    Raises:
        ImportError: If yfinance is not installed
    """
    from pyutss.data.providers.yahoo import YahooFinanceProvider

    return YahooFinanceProvider()
