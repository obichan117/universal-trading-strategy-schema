"""Base data provider interface."""

from abc import ABC, abstractmethod
from datetime import date

from pyutss.data.models import (
    OHLCV,
    FundamentalMetrics,
    Market,
    StockMetadata,
    Timeframe,
)


class DataProviderError(Exception):
    """Error from data provider."""

    pass


class BaseDataProvider(ABC):
    """Abstract base class for data providers.

    Implementations should provide access to OHLCV data, stock metadata,
    and fundamental metrics for supported markets.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        ...

    @property
    @abstractmethod
    def supported_markets(self) -> list[Market]:
        """List of supported markets."""
        ...

    @abstractmethod
    async def get_ohlcv(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe: Timeframe = Timeframe.DAILY,
    ) -> list[OHLCV]:
        """Fetch OHLCV data for a symbol.

        Args:
            symbol: Stock symbol
            start_date: Start date for data
            end_date: End date for data
            timeframe: Data timeframe (daily, weekly, monthly)

        Returns:
            List of OHLCV data points
        """
        ...

    @abstractmethod
    async def get_stock_info(self, symbol: str) -> StockMetadata | None:
        """Fetch stock metadata.

        Args:
            symbol: Stock symbol

        Returns:
            Stock metadata or None if not found
        """
        ...

    @abstractmethod
    async def get_fundamentals(self, symbol: str) -> FundamentalMetrics | None:
        """Fetch fundamental metrics.

        Args:
            symbol: Stock symbol

        Returns:
            Fundamental metrics or None if not found
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy and accessible.

        Returns:
            True if provider is working
        """
        ...
