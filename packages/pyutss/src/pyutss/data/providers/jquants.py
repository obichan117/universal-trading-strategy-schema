"""J-Quants data provider implementation using pyjquants."""

import logging
from datetime import date
from typing import Any

from pyutss.data.models import (
    OHLCV,
    FundamentalMetrics,
    Market,
    StockMetadata,
    Timeframe,
)
from pyutss.data.providers.base import BaseDataProvider, DataProviderError

logger = logging.getLogger(__name__)


def _import_pyjquants() -> Any:
    """Lazy import pyjquants."""
    try:
        import pyjquants as pjq

        return pjq
    except ImportError as e:
        raise ImportError(
            "pyjquants is required for J-Quants provider. "
            "Install it with: pip install pyutss[jquants]"
        ) from e


class JQuantsProvider(BaseDataProvider):
    """J-Quants data provider for Japanese stocks using pyjquants.

    Provides access to historical stock data for Japanese equities via
    the pyjquants library (yfinance-style interface for J-Quants API).

    Example:
        provider = JQuantsProvider()
        ohlcv = await provider.get_ohlcv("7203", date(2024, 1, 1), date(2024, 12, 31))
    """

    def __init__(self) -> None:
        """Initialize J-Quants provider."""
        self._pjq: Any = None

    @property
    def pjq(self) -> Any:
        """Lazy load pyjquants module."""
        if self._pjq is None:
            self._pjq = _import_pyjquants()
        return self._pjq

    @property
    def name(self) -> str:
        """Provider name."""
        return "jquants"

    @property
    def supported_markets(self) -> list[Market]:
        """Supported markets."""
        return [Market.JP]

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol for pyjquants.

        pyjquants uses 4-digit stock codes without suffix.

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
        """Fetch OHLCV data from J-Quants via pyjquants.

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

        try:
            ticker = self.pjq.Ticker(normalized_symbol)
            df = ticker.history(start=start_date, end=end_date)

            if df is None or df.empty:
                logger.warning(f"No data returned from pyjquants for {normalized_symbol}")
                return []

            result = []
            for idx, row in df.iterrows():
                try:
                    row_date = idx.date() if hasattr(idx, "date") else idx

                    result.append(
                        OHLCV(
                            date=row_date,
                            symbol=symbol,
                            open=float(row["Open"]),
                            high=float(row["High"]),
                            low=float(row["Low"]),
                            close=float(row["Close"]),
                            volume=int(row["Volume"]),
                            adjusted_close=float(row.get("AdjustmentClose", row["Close"]))
                            if "AdjustmentClose" in row
                            else None,
                        )
                    )
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse row for {symbol}: {e}")
                    continue

            result.sort(key=lambda x: x.date)
            return result

        except Exception as e:
            raise DataProviderError(f"pyjquants error for {symbol}: {e}") from e

    async def get_stock_info(self, symbol: str) -> StockMetadata | None:
        """Fetch stock information from J-Quants via pyjquants.

        Args:
            symbol: Stock symbol

        Returns:
            Stock metadata or None
        """
        normalized_symbol = self._normalize_symbol(symbol)

        try:
            ticker = self.pjq.Ticker(normalized_symbol)
            info = ticker.info

            if info is None:
                return None

            return StockMetadata(
                symbol=symbol,
                name=getattr(info, "name", None) or getattr(info, "name_english", symbol),
                market=Market.JP,
                sector=getattr(info, "sector", None),
                industry=getattr(info, "industry", None),
                market_cap=getattr(info, "market_cap", None),
                currency="JPY",
            )

        except Exception as e:
            logger.warning(f"Failed to get stock info for {symbol}: {e}")
            return None

    async def get_fundamentals(self, symbol: str) -> FundamentalMetrics | None:
        """Fetch fundamental metrics from J-Quants via pyjquants.

        Args:
            symbol: Stock symbol

        Returns:
            Fundamental metrics or None
        """
        normalized_symbol = self._normalize_symbol(symbol)

        try:
            ticker = self.pjq.Ticker(normalized_symbol)
            info = ticker.info

            if info is None:
                return None

            return FundamentalMetrics(
                symbol=symbol,
                date=date.today(),
                pe_ratio=getattr(info, "pe_ratio", None),
                pb_ratio=getattr(info, "pb_ratio", None),
                roe=getattr(info, "roe", None),
                dividend_yield=getattr(info, "dividend_yield", None),
                market_cap=getattr(info, "market_cap", None),
                eps=getattr(info, "eps", None),
            )

        except Exception as e:
            logger.warning(f"Failed to get fundamentals for {symbol}: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if pyjquants/J-Quants API is accessible."""
        try:
            # Try to get Toyota as a health check
            ticker = self.pjq.Ticker("7203")
            info = ticker.info
            return info is not None
        except Exception as e:
            logger.error(f"J-Quants health check failed: {e}")
            return False
