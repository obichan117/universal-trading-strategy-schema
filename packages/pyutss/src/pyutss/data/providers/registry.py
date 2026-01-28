"""Data provider registry for automatic provider selection."""

import logging
from datetime import date

import pandas as pd

from pyutss.data.models import OHLCV, Market, Timeframe
from pyutss.data.providers.base import BaseDataProvider, DataProviderError

logger = logging.getLogger(__name__)


class DataProviderRegistry:
    """Registry for data providers with automatic selection based on symbol.

    Provides a unified interface for fetching data across multiple providers.
    Automatically selects the appropriate provider based on symbol format.

    Symbol format rules:
    - Japanese stocks: 4-digit code or ending with .T (e.g., "7203", "7203.T")
    - US stocks: Alphabetic symbols (e.g., "AAPL", "MSFT")

    Example:
        registry = DataProviderRegistry()

        # Automatic provider selection
        data = await registry.get_ohlcv("AAPL", start, end)  # Uses Yahoo
        data = await registry.get_ohlcv("7203.T", start, end)  # Uses J-Quants if available, else Yahoo

        # Register custom provider
        registry.register(MyCustomProvider())
    """

    def __init__(self) -> None:
        """Initialize the registry with default providers."""
        self._providers: dict[str, BaseDataProvider] = {}
        self._market_providers: dict[Market, list[str]] = {
            Market.US: [],
            Market.JP: [],
        }

    def register(self, provider: BaseDataProvider, priority: int = 0) -> None:
        """Register a data provider.

        Args:
            provider: Data provider instance
            priority: Higher priority providers are tried first (default: 0)
        """
        self._providers[provider.name] = provider

        for market in provider.supported_markets:
            if market not in self._market_providers:
                self._market_providers[market] = []

            # Insert based on priority (higher first)
            providers = self._market_providers[market]
            inserted = False
            for i, name in enumerate(providers):
                if name not in self._providers:
                    providers[i] = provider.name
                    inserted = True
                    break
            if not inserted:
                providers.insert(0, provider.name)

        logger.info(f"Registered provider: {provider.name} for markets {provider.supported_markets}")

    def get_provider(self, name: str) -> BaseDataProvider | None:
        """Get a specific provider by name.

        Args:
            name: Provider name

        Returns:
            Provider instance or None if not found
        """
        return self._providers.get(name)

    def _detect_market(self, symbol: str) -> Market:
        """Detect market from symbol format.

        Args:
            symbol: Stock symbol

        Returns:
            Detected market
        """
        # Japanese stock detection
        if symbol.endswith(".T"):
            return Market.JP

        # 4-digit numeric code is typically Japanese
        clean_symbol = symbol.split(".")[0]
        if clean_symbol.isdigit() and len(clean_symbol) == 4:
            return Market.JP

        # Default to US
        return Market.US

    def _get_providers_for_symbol(self, symbol: str) -> list[BaseDataProvider]:
        """Get ordered list of providers for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            List of providers to try (in order)
        """
        market = self._detect_market(symbol)
        provider_names = self._market_providers.get(market, [])

        providers = []
        for name in provider_names:
            if name in self._providers:
                providers.append(self._providers[name])

        return providers

    async def get_ohlcv(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe: Timeframe = Timeframe.DAILY,
        provider: str | None = None,
    ) -> list[OHLCV]:
        """Fetch OHLCV data using the appropriate provider.

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe
            provider: Specific provider name (None for auto-select)

        Returns:
            List of OHLCV data

        Raises:
            DataProviderError: If all providers fail
            ValueError: If no providers available
        """
        if provider:
            p = self._providers.get(provider)
            if not p:
                raise ValueError(f"Provider not found: {provider}")
            return await p.get_ohlcv(symbol, start_date, end_date, timeframe)

        providers = self._get_providers_for_symbol(symbol)
        if not providers:
            raise ValueError(f"No providers available for symbol: {symbol}")

        errors = []
        for p in providers:
            try:
                data = await p.get_ohlcv(symbol, start_date, end_date, timeframe)
                if data:
                    return data
            except Exception as e:
                logger.warning(f"Provider {p.name} failed for {symbol}: {e}")
                errors.append((p.name, str(e)))
                continue

        error_details = "; ".join(f"{n}: {e}" for n, e in errors)
        raise DataProviderError(f"All providers failed for {symbol}: {error_details}")

    async def get_ohlcv_dataframe(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe: Timeframe = Timeframe.DAILY,
        provider: str | None = None,
    ) -> pd.DataFrame:
        """Fetch OHLCV data as a pandas DataFrame.

        Convenience method that returns data in DataFrame format
        with DatetimeIndex, suitable for backtesting.

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe
            provider: Specific provider name (None for auto-select)

        Returns:
            DataFrame with columns: open, high, low, close, volume
            Index: DatetimeIndex
        """
        data = await self.get_ohlcv(symbol, start_date, end_date, timeframe, provider)

        if not data:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        df = pd.DataFrame([
            {
                "date": d.date,
                "open": d.open,
                "high": d.high,
                "low": d.low,
                "close": d.close,
                "volume": d.volume,
            }
            for d in data
        ])

        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        df = df.sort_index()

        return df

    def list_providers(self) -> list[str]:
        """List all registered providers.

        Returns:
            List of provider names
        """
        return list(self._providers.keys())


def get_default_registry() -> DataProviderRegistry:
    """Get the default registry with standard providers.

    Registers Yahoo Finance provider (available by default).
    J-Quants provider is registered if jquants-api-client is installed.

    Returns:
        Configured registry
    """
    registry = DataProviderRegistry()

    # Try to register Yahoo Finance (most common)
    try:
        from pyutss.data.providers.yahoo import YahooFinanceProvider
        registry.register(YahooFinanceProvider(), priority=10)
    except ImportError:
        logger.debug("Yahoo Finance provider not available (yfinance not installed)")

    # Try to register J-Quants for Japanese stocks (higher priority for JP)
    try:
        from pyutss.data.providers.jquants import JQuantsProvider
        registry.register(JQuantsProvider(), priority=20)
    except ImportError:
        logger.debug("J-Quants provider not available (jquants-api-client not installed)")

    return registry


# Module-level default instance
_default_registry: DataProviderRegistry | None = None


def get_registry() -> DataProviderRegistry:
    """Get the shared default registry instance.

    Returns:
        The default registry (creates one if needed)
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = get_default_registry()
    return _default_registry
