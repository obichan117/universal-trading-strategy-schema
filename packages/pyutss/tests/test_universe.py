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


class TestUniverseResolverIndex:
    """Test index universe resolution."""

    def test_dow30(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({"type": "index", "index": "DOW30"})
        assert len(symbols) == 30
        assert "AAPL" in symbols
        assert "MSFT" in symbols

    def test_nikkei225(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({"type": "index", "index": "NIKKEI225"})
        assert len(symbols) == 20  # subset
        assert "7203.T" in symbols

    def test_index_with_limit(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({"type": "index", "index": "DOW30", "limit": 5})
        assert len(symbols) == 5

    def test_unknown_index_returns_empty(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({"type": "index", "index": "UNKNOWN"})
        assert symbols == []

    def test_custom_index(self):
        resolver = UniverseResolver(custom_indices={"MY_INDEX": ["A", "B", "C"]})
        symbols = resolver.resolve({"type": "index", "index": "MY_INDEX"})
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


class TestUniverseResolverDual:
    """Test dual universe resolution."""

    def test_dual_long_and_short(self):
        resolver = UniverseResolver(custom_indices={
            "LONG_IDX": ["A", "B", "C"],
            "SHORT_IDX": ["D", "E"],
        })
        symbols = resolver.resolve({
            "type": "dual",
            "long": {"index": "LONG_IDX"},
            "short": {"index": "SHORT_IDX"},
        })
        assert set(symbols) == {"A", "B", "C", "D", "E"}

    def test_dual_overlapping_symbols(self):
        resolver = UniverseResolver(custom_indices={
            "IDX1": ["A", "B"],
            "IDX2": ["B", "C"],
        })
        symbols = resolver.resolve({
            "type": "dual",
            "long": {"index": "IDX1"},
            "short": {"index": "IDX2"},
        })
        assert set(symbols) == {"A", "B", "C"}

    def test_dual_with_limit(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({
            "type": "dual",
            "long": {"index": "DOW30", "limit": 3},
            "short": {"index": "NIKKEI225", "limit": 2},
        })
        assert len(symbols) == 5

    def test_dual_long_only(self):
        resolver = UniverseResolver(custom_indices={"IDX": ["X", "Y"]})
        symbols = resolver.resolve({
            "type": "dual",
            "long": {"index": "IDX"},
        })
        assert set(symbols) == {"X", "Y"}

    def test_dual_empty(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({"type": "dual"})
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
        symbols = resolver.resolve({"type": "index", "index": "CUSTOM"})
        assert symbols == ["X", "Y", "Z"]

    def test_default_type_is_static(self):
        resolver = UniverseResolver()
        symbols = resolver.resolve({"symbols": ["AAPL"]})
        assert symbols == ["AAPL"]

    def test_index_constituents_not_mutated(self):
        """Custom indices shouldn't mutate the module-level constant."""
        UniverseResolver(custom_indices={"NEW": ["A"]})
        assert "NEW" not in INDEX_CONSTITUENTS
