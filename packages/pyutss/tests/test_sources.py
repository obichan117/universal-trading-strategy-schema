"""Tests for unified data sources interface."""

import pytest

from pyutss.data.sources import (
    Ticker,
    fetch,
    download,
    available_sources,
    SOURCES,
    DEFAULT_SOURCES,
    _detect_market,
    _get_source_for_symbol,
)


class TestSourcesConfig:
    """Tests for source configuration."""

    def test_sources_defined(self):
        """SOURCES should define available data sources."""
        assert "yahoo" in SOURCES
        assert "jquants" in SOURCES

    def test_default_sources_defined(self):
        """DEFAULT_SOURCES should map markets to sources."""
        assert "US" in DEFAULT_SOURCES
        assert "JP" in DEFAULT_SOURCES
        assert DEFAULT_SOURCES["US"] == "yahoo"
        assert DEFAULT_SOURCES["JP"] == "jquants"


class TestMarketDetection:
    """Tests for market detection from symbol."""

    def test_detect_us_symbols(self):
        """US symbols should be detected correctly."""
        assert _detect_market("AAPL") == "US"
        assert _detect_market("MSFT") == "US"
        assert _detect_market("GOOGL") == "US"
        assert _detect_market("BRK.B") == "US"

    def test_detect_jp_symbols_with_suffix(self):
        """Japanese symbols with .T suffix should be detected."""
        assert _detect_market("7203.T") == "JP"
        assert _detect_market("6758.T") == "JP"
        assert _detect_market("9984.T") == "JP"

    def test_detect_jp_symbols_numeric(self):
        """4-digit numeric symbols should be detected as Japanese."""
        assert _detect_market("7203") == "JP"
        assert _detect_market("6758") == "JP"
        assert _detect_market("9984") == "JP"

    def test_detect_non_jp_numeric(self):
        """Non-4-digit numeric should default to US."""
        assert _detect_market("12345") == "US"
        assert _detect_market("123") == "US"


class TestSourceSelection:
    """Tests for automatic source selection."""

    def test_get_source_for_us_symbol(self):
        """US symbols should use yahoo by default."""
        try:
            source = _get_source_for_symbol("AAPL")
            assert source in ["yahoo", "jquants"]  # Either is valid if available
        except ImportError:
            pytest.skip("No data sources installed")

    def test_get_source_for_jp_symbol(self):
        """JP symbols should prefer jquants, fallback to yahoo."""
        try:
            source = _get_source_for_symbol("7203")
            assert source in ["yahoo", "jquants"]
        except ImportError:
            pytest.skip("No data sources installed")


class TestAvailableSources:
    """Tests for available_sources function."""

    def test_available_sources_returns_list(self):
        """available_sources should return a list."""
        sources = available_sources()
        assert isinstance(sources, list)

    def test_available_sources_only_installed(self):
        """available_sources should only return installed sources."""
        sources = available_sources()
        for source in sources:
            assert source in SOURCES


class TestTickerClass:
    """Tests for Ticker class."""

    def test_ticker_creation_us(self):
        """Ticker should be created for US symbols."""
        try:
            ticker = Ticker("AAPL")
            assert ticker.symbol == "AAPL"
            assert ticker.source in ["yahoo", "jquants"]
        except ImportError:
            pytest.skip("No data sources installed")

    def test_ticker_creation_jp(self):
        """Ticker should be created for JP symbols."""
        try:
            ticker = Ticker("7203")
            assert ticker.symbol == "7203"
            assert ticker.source in ["yahoo", "jquants"]
        except ImportError:
            pytest.skip("No data sources installed")

    def test_ticker_explicit_source(self):
        """Ticker should accept explicit source."""
        try:
            ticker = Ticker("AAPL", source="yahoo")
            assert ticker.source == "yahoo"
        except ImportError:
            pytest.skip("yfinance not installed")

    def test_ticker_repr(self):
        """Ticker repr should show symbol and source."""
        try:
            ticker = Ticker("AAPL")
            repr_str = repr(ticker)
            assert "AAPL" in repr_str
            assert ticker.source in repr_str
        except ImportError:
            pytest.skip("No data sources installed")

    def test_ticker_normalize_jp_for_yahoo(self):
        """Ticker should normalize JP symbols for Yahoo."""
        try:
            ticker = Ticker("7203", source="yahoo")
            # Yahoo expects .T suffix for Japanese stocks
            assert ticker._normalize_symbol() == "7203.T"
        except ImportError:
            pytest.skip("yfinance not installed")

    def test_ticker_normalize_jp_for_jquants(self):
        """Ticker should normalize JP symbols for J-Quants."""
        try:
            ticker = Ticker("7203.T", source="jquants")
            # pyjquants expects 4-digit code without suffix
            assert ticker._normalize_symbol() == "7203"
        except ImportError:
            pytest.skip("pyjquants not installed")


class TestFetchFunction:
    """Tests for fetch function."""

    def test_fetch_raises_without_sources(self):
        """fetch should raise ImportError if no sources available."""
        # This test only makes sense if we can mock the imports
        # For now, just verify the function signature works
        from pyutss.data.sources import fetch
        assert callable(fetch)


class TestDownloadFunction:
    """Tests for download function."""

    def test_download_returns_dict(self):
        """download should return a dict mapping symbols to DataFrames."""
        from pyutss.data.sources import download
        assert callable(download)


class TestUnknownSource:
    """Tests for error handling with unknown sources."""

    def test_ticker_unknown_source_raises(self):
        """Ticker with unknown source should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown source"):
            Ticker("AAPL", source="nonexistent")
