"""Tests for UniverseResolver."""

import pytest

from pyutss.engine.universe import UniverseResolver, INDEX_CONSTITUENTS


class TestUniverseResolverStatic:
    """Test static universe resolution."""

    def test_static_returns_symbols(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({"type": "static", "symbols": ["AAPL", "MSFT"]})
        assert symbols == ["AAPL", "MSFT"]

    def test_static_empty_raises(self):
        resolver = UniverseResolver()
        with pytest.raises(ValueError, match="non-empty"):
            resolver.resolve({"type": "static", "symbols": []})

    def test_static_missing_symbols_raises(self):
        resolver = UniverseResolver()
        with pytest.raises(ValueError, match="non-empty"):
            resolver.resolve({"type": "static"})


class TestUniverseResolverIndexRemoved:
    """Test that index universe type is properly removed."""

    def test_index_type_raises_error(self):
        resolver = UniverseResolver()
        with pytest.raises(ValueError, match="removed"):
            resolver.resolve({"type": "index", "index": "DOW30"})

    def test_screener_replaces_index_dow30(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({"type": "screener", "base": "DOW30"})
        assert len(symbols) == 30
        assert "AAPL" in symbols
        assert "MSFT" in symbols

    def test_screener_replaces_index_nikkei225(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({"type": "screener", "base": "NIKKEI225"})
        assert len(symbols) == 20  # subset
        assert "7203.T" in symbols

    def test_screener_replaces_index_with_limit(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({"type": "screener", "base": "DOW30", "limit": 5})
        assert len(symbols) == 5

    def test_screener_custom_base(self):
        resolver = UniverseResolver(custom_indices={"MY_INDEX": ["A", "B", "C"]})
        symbols = resolver.resolve({"type": "screener", "base": "MY_INDEX"})
        assert symbols == ["A", "B", "C"]


class TestUniverseResolverScreener:
    """Test screener universe resolution."""

    def test_screener_with_known_base(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({"type": "screener", "base": "DOW30"})
        assert len(symbols) == 30

    def test_screener_with_limit(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({"type": "screener", "base": "DOW30", "limit": 10})
        assert len(symbols) == 10

    def test_screener_unknown_base_returns_empty(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({"type": "screener", "base": "UNKNOWN"})
        assert symbols == []

    def test_screener_no_base_returns_empty(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({"type": "screener"})
        assert symbols == []


class TestUniverseResolverMisc:
    """Test miscellaneous resolver features."""

    def test_unknown_type_raises(self):
        resolver = UniverseResolver()
        with pytest.raises(ValueError, match="Unknown universe type"):
            resolver.resolve({"type": "unknown"})

    def test_add_index(self):
        resolver = UniverseResolver()
        resolver.add_index("CUSTOM", ["X", "Y", "Z"])
        symbols = resolver.resolve({"type": "screener", "base": "CUSTOM"})
        assert symbols == ["X", "Y", "Z"]

    def test_default_type_is_static(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({"symbols": ["AAPL"]})
        assert symbols == ["AAPL"]

    def test_index_constituents_not_mutated(self):
        """Custom indices shouldn't mutate the module-level constant."""
        UniverseResolver(custom_indices={"NEW": ["A"]})
        assert "NEW" not in INDEX_CONSTITUENTS
