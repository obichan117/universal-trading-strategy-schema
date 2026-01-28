"""J-Quants data provider implementation for Japanese stocks."""

import logging
from datetime import date, datetime
from typing import Any

from pyutss.data.models import (
    FundamentalMetrics,
    Market,
    OHLCV,
    StockMetadata,
    Timeframe,
)
from pyutss.data.providers.base import BaseDataProvider, DataProviderError

logger = logging.getLogger(__name__)


def _import_jquants() -> Any:
    """Lazy import jquantsapi."""
    try:
        import jquantsapi

        return jquantsapi
    except ImportError as e:
        raise ImportError(
            "jquants-api-client is required for J-Quants provider. "
            "Install it with: pip install pyutss[jquants]"
        ) from e


def _import_dateutil_tz() -> Any:
    """Lazy import dateutil.tz."""
    try:
        from dateutil import tz

        return tz
    except ImportError as e:
        raise ImportError(
            "python-dateutil is required for J-Quants provider. "
            "It should be installed with jquants-api-client."
        ) from e


class JQuantsProvider(BaseDataProvider):
    """J-Quants data provider for Japanese stocks.

    Provides access to historical stock data for Japanese equities via
    the J-Quants API. Requires an API key from J-Quants.

    Example:
        provider = JQuantsProvider(api_key="your_key")
        # Or use JQUANTS_API_KEY environment variable
        provider = JQuantsProvider()
        ohlcv = await provider.get_ohlcv("7203", date(2024, 1, 1), date(2024, 12, 31))
    """

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize J-Quants provider.

        Args:
            api_key: J-Quants API key. If None, uses JQUANTS_API_KEY env var.
        """
        self._api_key = api_key
        self._client: Any = None
        self._jquants: Any = None
        self._tz: Any = None

    @property
    def jquants(self) -> Any:
        """Lazy load jquantsapi module."""
        if self._jquants is None:
            self._jquants = _import_jquants()
        return self._jquants

    @property
    def tz(self) -> Any:
        """Lazy load dateutil.tz module."""
        if self._tz is None:
            self._tz = _import_dateutil_tz()
        return self._tz

    @property
    def client(self) -> Any:
        """Lazy load J-Quants client."""
        if self._client is None:
            if self._api_key:
                self._client = self.jquants.ClientV2(api_key=self._api_key)
            else:
                self._client = self.jquants.ClientV2()
        return self._client

    @property
    def name(self) -> str:
        """Provider name."""
        return "jquants"

    @property
    def supported_markets(self) -> list[Market]:
        """Supported markets."""
        return [Market.JP]

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for J-Quants API.

        J-Quants uses 4-digit stock codes without suffix.

        Args:
            symbol: Stock symbol (e.g., "7203", "7203.T")

        Returns:
            Normalized symbol (e.g., "7203")
        """
        if symbol.endswith(".T"):
            return symbol[:-2]
        return symbol

    async def get_ohlcv(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe: Timeframe = Timeframe.DAILY,
    ) -> list[OHLCV]:
        """Fetch OHLCV data from J-Quants.

        Args:
            symbol: Stock symbol (e.g., "7203" or "7203.T")
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe (only DAILY supported)

        Returns:
            List of OHLCV data

        Raises:
            DataProviderError: If data fetch fails
            ValueError: If unsupported timeframe requested
        """
        if timeframe != Timeframe.DAILY:
            raise ValueError(
                f"J-Quants provider only supports daily timeframe, got {timeframe}"
            )

        normalized_symbol = self._normalize_symbol(symbol)
        tokyo_tz = self.tz.gettz("Asia/Tokyo")

        try:
            start_dt = datetime(
                start_date.year, start_date.month, start_date.day, tzinfo=tokyo_tz
            )
            end_dt = datetime(
                end_date.year, end_date.month, end_date.day, tzinfo=tokyo_tz
            )

            df = self.client.get_prices_daily_quotes_range(
                start_dt=start_dt, end_dt=end_dt
            )

            if df is None or df.empty:
                logger.warning(f"No data returned from J-Quants for {normalized_symbol}")
                return []

            # Filter by symbol code
            df = df[df["Code"] == normalized_symbol]

            if df.empty:
                logger.warning(f"No data found for symbol {normalized_symbol}")
                return []

            result = []
            for _, row in df.iterrows():
                try:
                    row_date = row["Date"]
                    if isinstance(row_date, str):
                        row_date = datetime.strptime(row_date, "%Y-%m-%d").date()
                    elif hasattr(row_date, "date"):
                        row_date = row_date.date()

                    result.append(
                        OHLCV(
                            date=row_date,
                            symbol=symbol,
                            open=float(row["Open"]),
                            high=float(row["High"]),
                            low=float(row["Low"]),
                            close=float(row["Close"]),
                            volume=int(row["Volume"]),
                            adjusted_close=float(row.get("AdjustmentClose", row["Close"])),
                        )
                    )
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse row for {symbol}: {e}")
                    continue

            result.sort(key=lambda x: x.date)
            return result

        except Exception as e:
            raise DataProviderError(f"J-Quants error for {symbol}: {e}") from e

    async def get_stock_info(self, symbol: str) -> StockMetadata | None:
        """Fetch stock information from J-Quants.

        Args:
            symbol: Stock symbol

        Returns:
            Stock metadata or None
        """
        normalized_symbol = self._normalize_symbol(symbol)

        try:
            df = self.client.get_listed_info()

            if df is None or df.empty:
                return None

            stock_info = df[df["Code"] == normalized_symbol]

            if stock_info.empty:
                return None

            row = stock_info.iloc[0]

            return StockMetadata(
                symbol=symbol,
                name=row.get("CompanyName", symbol),
                market=Market.JP,
                sector=row.get("Sector17CodeName") or row.get("Sector33CodeName"),
                industry=row.get("Sector33CodeName"),
                market_cap=None,
                currency="JPY",
            )

        except Exception as e:
            logger.warning(f"Failed to get stock info for {symbol}: {e}")
            return None

    async def get_fundamentals(self, symbol: str) -> FundamentalMetrics | None:
        """Fetch fundamental metrics from J-Quants.

        Args:
            symbol: Stock symbol

        Returns:
            Fundamental metrics or None
        """
        normalized_symbol = self._normalize_symbol(symbol)

        try:
            df = self.client.get_fins_statements()

            if df is None or df.empty:
                return None

            # Filter by symbol and get latest
            stock_fins = df[df["LocalCode"] == normalized_symbol]

            if stock_fins.empty:
                return None

            # Get most recent statement
            stock_fins = stock_fins.sort_values("DisclosedDate", ascending=False)
            row = stock_fins.iloc[0]

            return FundamentalMetrics(
                symbol=symbol,
                date=date.today(),
                pe_ratio=row.get("EarningsPerShare"),
                pb_ratio=row.get("BookValuePerShare"),
                roe=row.get("ReturnOnEquity"),
                profit_margin=row.get("ProfitMargin"),
                revenue=row.get("NetSales"),
                net_income=row.get("Profit"),
                eps=row.get("EarningsPerShare"),
            )

        except Exception as e:
            logger.warning(f"Failed to get fundamentals for {symbol}: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if J-Quants API is accessible."""
        try:
            df = self.client.get_listed_info()
            return df is not None and not df.empty
        except Exception as e:
            logger.error(f"J-Quants health check failed: {e}")
            return False
