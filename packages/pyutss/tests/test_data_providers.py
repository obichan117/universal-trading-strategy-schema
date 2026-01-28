"""Tests for data providers."""

from datetime import date

import pytest

from pyutss.data import (
    Market,
    Timeframe,
    OHLCV,
    BaseDataProvider,
    DataProviderError,
    DataProviderRegistry,
    get_default_registry,
    get_registry,
)


class TestDataModels:
    """Tests for data models."""

    def test_market_enum(self):
        """Market enum has expected values."""
        assert Market.US.value == "US"
        assert Market.JP.value == "JP"

    def test_timeframe_enum(self):
        """Timeframe enum has expected values."""
        assert Timeframe.DAILY.value == "1d"
        assert Timeframe.WEEKLY.value == "1wk"
        assert Timeframe.MONTHLY.value == "1mo"

    def test_ohlcv_creation(self):
        """OHLCV dataclass works correctly."""
        ohlcv = OHLCV(
            date=date(2024, 1, 1),
            symbol="AAPL",
            open=100.0,
            high=105.0,
            low=99.0,
            close=104.0,
            volume=1000000,
        )
        assert ohlcv.symbol == "AAPL"
        assert ohlcv.close == 104.0
        assert ohlcv.adjusted_close is None

    def test_ohlcv_with_adjusted_close(self):
        """OHLCV supports adjusted close."""
        ohlcv = OHLCV(
            date=date(2024, 1, 1),
            symbol="AAPL",
            open=100.0,
            high=105.0,
            low=99.0,
            close=104.0,
            volume=1000000,
            adjusted_close=103.5,
        )
        assert ohlcv.adjusted_close == 103.5


class TestDataProviderRegistry:
    """Tests for DataProviderRegistry."""

    def test_registry_creation(self):
        """Registry can be created."""
        registry = DataProviderRegistry()
        assert isinstance(registry, DataProviderRegistry)

    def test_registry_list_providers_empty(self):
        """Empty registry has no providers."""
        registry = DataProviderRegistry()
        assert registry.list_providers() == []

    def test_detect_market_us_symbol(self):
        """US symbols are detected correctly."""
        registry = DataProviderRegistry()
        assert registry._detect_market("AAPL") == Market.US
        assert registry._detect_market("MSFT") == Market.US
        assert registry._detect_market("GOOGL") == Market.US

    def test_detect_market_jp_symbol_with_suffix(self):
        """Japanese symbols with .T suffix are detected."""
        registry = DataProviderRegistry()
        assert registry._detect_market("7203.T") == Market.JP
        assert registry._detect_market("6758.T") == Market.JP

    def test_detect_market_jp_symbol_numeric(self):
        """4-digit numeric symbols are detected as Japanese."""
        registry = DataProviderRegistry()
        assert registry._detect_market("7203") == Market.JP
        assert registry._detect_market("6758") == Market.JP
        assert registry._detect_market("9984") == Market.JP

    def test_detect_market_mixed(self):
        """Mixed symbols default to US."""
        registry = DataProviderRegistry()
        # 5-digit numeric is not standard JP
        assert registry._detect_market("12345") == Market.US


class TestDefaultRegistry:
    """Tests for default registry."""

    def test_get_default_registry(self):
        """Default registry can be created."""
        registry = get_default_registry()
        assert isinstance(registry, DataProviderRegistry)

    def test_get_registry_singleton(self):
        """get_registry returns same instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2


class TestYahooProviderImport:
    """Tests for Yahoo provider import."""

    def test_yahoo_provider_available(self):
        """Yahoo provider can be imported if yfinance is installed."""
        try:
            from pyutss.data.providers import get_yahoo_provider
            provider = get_yahoo_provider()
            assert provider.name == "yahoo_finance"
            assert Market.US in provider.supported_markets
            assert Market.JP in provider.supported_markets
        except ImportError:
            pytest.skip("yfinance not installed")


class TestJQuantsProviderImport:
    """Tests for J-Quants provider import."""

    def test_jquants_provider_import_error(self):
        """J-Quants provider raises ImportError if not installed."""
        try:
            from pyutss.data.providers import get_jquants_provider
            # If we get here, jquants is installed
            provider = get_jquants_provider()
            assert provider.name == "jquants"
            assert Market.JP in provider.supported_markets
        except ImportError as e:
            assert "jquants-api-client" in str(e)


class TestYahooProviderNormalization:
    """Tests for Yahoo provider symbol normalization."""

    def test_normalize_jp_symbol(self):
        """Japanese symbols are normalized correctly."""
        try:
            from pyutss.data.providers.yahoo import YahooFinanceProvider
            provider = YahooFinanceProvider()

            assert provider._normalize_symbol("7203", Market.JP) == "7203.T"
            assert provider._normalize_symbol("7203.T") == "7203.T"
            assert provider._normalize_symbol("7203") == "7203.T"  # Auto-detect
        except ImportError:
            pytest.skip("yfinance not installed")

    def test_normalize_us_symbol(self):
        """US symbols are unchanged."""
        try:
            from pyutss.data.providers.yahoo import YahooFinanceProvider
            provider = YahooFinanceProvider()

            assert provider._normalize_symbol("AAPL", Market.US) == "AAPL"
            assert provider._normalize_symbol("AAPL") == "AAPL"
        except ImportError:
            pytest.skip("yfinance not installed")


class TestJQuantsProviderNormalization:
    """Tests for J-Quants provider symbol normalization."""

    def test_normalize_removes_suffix(self):
        """J-Quants provider removes .T suffix."""
        try:
            from pyutss.data.providers.jquants import JQuantsProvider
            provider = JQuantsProvider(api_key="dummy")

            assert provider._normalize_symbol("7203.T") == "7203"
            assert provider._normalize_symbol("7203") == "7203"
        except ImportError:
            pytest.skip("jquants-api-client not installed")
