"""Data providers for pyutss."""

from pyutss.data.providers.base import BaseDataProvider, DataProviderError
from pyutss.data.providers.registry import (
    DataProviderRegistry,
    get_default_registry,
    get_registry,
)

__all__ = [
    "BaseDataProvider",
    "DataProviderError",
    "DataProviderRegistry",
    "get_default_registry",
    "get_registry",
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


def get_jquants_provider():
    """Get J-Quants provider (lazy import).

    Returns:
        JQuantsProvider instance

    Raises:
        ImportError: If pyjquants is not installed
    """
    from pyutss.data.providers.jquants import JQuantsProvider

    return JQuantsProvider()
