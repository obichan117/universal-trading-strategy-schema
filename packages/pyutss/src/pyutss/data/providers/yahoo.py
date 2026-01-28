"""Yahoo Finance data provider implementation."""

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


def _import_yfinance() -> Any:
    """Lazy import yfinance."""
    try:
        import yfinance as yf

        return yf
    except ImportError as e:
        raise ImportError(
            "yfinance is required for Yahoo Finance provider. "
            "Install it with: pip install pyutss[yahoo]"
        ) from e


class YahooFinanceProvider(BaseDataProvider):
    """Yahoo Finance data provider.

    Provides free access to stock data for both JP and US markets.
    Rate limits and data quality may vary.

    Example:
        provider = YahooFinanceProvider()
        ohlcv = await provider.get_ohlcv("AAPL", date(2024, 1, 1), date(2024, 12, 31))
    """

    def __init__(self) -> None:
        """Initialize Yahoo Finance provider."""
        self._yf: Any = None

    @property
    def yf(self) -> Any:
        """Lazy load yfinance."""
        if self._yf is None:
            self._yf = _import_yfinance()
        return self._yf

    @property
    def name(self) -> str:
        """Provider name."""
        return "yahoo_finance"

    @property
    def supported_markets(self) -> list[Market]:
        """Supported markets."""
        return [Market.JP, Market.US]

    def _normalize_symbol(self, symbol: str, market: Market | None = None) -> str:
        """Normalize symbol for Yahoo Finance.

        Args:
            symbol: Stock symbol
            market: Optional market hint

        Returns:
            Yahoo Finance compatible symbol
        """
        if "." in symbol:
            return symbol

        if market == Market.JP:
            return f"{symbol}.T"
        elif market == Market.US:
            return symbol

        if symbol.isdigit() and len(symbol) == 4:
            return f"{symbol}.T"

        return symbol

    async def get_ohlcv(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe: Timeframe = Timeframe.DAILY,
    ) -> list[OHLCV]:
        """Fetch OHLCV data from Yahoo Finance.

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe

        Returns:
            List of OHLCV data
        """
        interval_map = {
            Timeframe.DAILY: "1d",
            Timeframe.WEEKLY: "1wk",
            Timeframe.MONTHLY: "1mo",
        }
        interval = interval_map.get(timeframe, "1d")
        normalized_symbol = self._normalize_symbol(symbol)

        try:
            ticker = self.yf.Ticker(normalized_symbol)
            df = ticker.history(
                start=start_date.isoformat(),
                end=end_date.isoformat(),
                interval=interval,
                auto_adjust=False,
            )

            if df.empty:
                logger.warning(f"No data returned for {normalized_symbol}")
                return []

            result = []
            for idx, row in df.iterrows():
                try:
                    result.append(
                        OHLCV(
                            date=idx.date() if hasattr(idx, "date") else idx,
                            symbol=symbol,
                            open=float(row["Open"]),
                            high=float(row["High"]),
                            low=float(row["Low"]),
                            close=float(row["Close"]),
                            volume=int(row["Volume"]),
                            adjusted_close=float(row.get("Adj Close", row["Close"])),
                        )
                    )
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse row for {symbol}: {e}")
                    continue

            return result

        except Exception as e:
            raise DataProviderError(f"Yahoo Finance error for {symbol}: {e}") from e

    async def get_stock_info(self, symbol: str) -> StockMetadata | None:
        """Fetch stock information from Yahoo Finance.

        Args:
            symbol: Stock symbol

        Returns:
            Stock metadata or None
        """
        normalized_symbol = self._normalize_symbol(symbol)

        try:
            ticker = self.yf.Ticker(normalized_symbol)
            info = ticker.info

            if not info or "symbol" not in info:
                return None

            market = Market.US
            if ".T" in normalized_symbol or info.get("exchange", "").startswith("TSE"):
                market = Market.JP

            return StockMetadata(
                symbol=symbol,
                name=info.get("longName", info.get("shortName", symbol)),
                market=market,
                sector=info.get("sector"),
                industry=info.get("industry"),
                market_cap=info.get("marketCap"),
                currency=info.get("currency", "USD" if market == Market.US else "JPY"),
            )

        except Exception as e:
            logger.warning(f"Failed to get stock info for {symbol}: {e}")
            return None

    async def get_fundamentals(self, symbol: str) -> FundamentalMetrics | None:
        """Fetch fundamental metrics from Yahoo Finance.

        Args:
            symbol: Stock symbol

        Returns:
            Fundamental metrics or None
        """
        normalized_symbol = self._normalize_symbol(symbol)

        try:
            ticker = self.yf.Ticker(normalized_symbol)
            info = ticker.info

            if not info:
                return None

            return FundamentalMetrics(
                symbol=symbol,
                date=date.today(),
                pe_ratio=info.get("trailingPE") or info.get("forwardPE"),
                pb_ratio=info.get("priceToBook"),
                ps_ratio=info.get("priceToSalesTrailing12Months"),
                peg_ratio=info.get("pegRatio"),
                roe=info.get("returnOnEquity"),
                roa=info.get("returnOnAssets"),
                profit_margin=info.get("profitMargins"),
                operating_margin=info.get("operatingMargins"),
                dividend_yield=info.get("dividendYield"),
                payout_ratio=info.get("payoutRatio"),
                market_cap=info.get("marketCap"),
                revenue=info.get("totalRevenue"),
                net_income=info.get("netIncomeToCommon"),
                eps=info.get("trailingEps"),
                book_value_per_share=info.get("bookValue"),
            )

        except Exception as e:
            logger.warning(f"Failed to get fundamentals for {symbol}: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if Yahoo Finance is accessible."""
        try:
            ticker = self.yf.Ticker("AAPL")
            info = ticker.info
            return info is not None and "symbol" in info
        except Exception as e:
            logger.error(f"Yahoo Finance health check failed: {e}")
            return False
