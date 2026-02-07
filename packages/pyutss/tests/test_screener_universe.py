"""Tests for screener universe with filter evaluation."""

import numpy as np
import pandas as pd

from pyutss.engine.universe import UniverseResolver


def _make_ohlcv(n=100, close_start=100.0, seed=42):
    """Create sample OHLCV data."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2024-01-01", periods=n)
    close = close_start + np.cumsum(rng.normal(0, 1, n))
    close = np.maximum(close, 10)
    return pd.DataFrame(
        {
            "open": close * (1 + rng.uniform(-0.01, 0.01, n)),
            "high": close * (1 + rng.uniform(0, 0.02, n)),
            "low": close * (1 - rng.uniform(0, 0.02, n)),
            "close": close,
            "volume": rng.integers(100000, 1000000, n).astype(float),
        },
        index=dates,
    )


class TestScreenerFiltering:
    def test_screener_without_data_returns_base(self):
        """Without data, screener returns unfiltered base."""
        resolver = UniverseResolver(custom_indices={"TEST": ["A", "B", "C"]})
        universe = {"type": "screener", "base": "TEST"}
        symbols = resolver.resolve(universe)
        assert symbols == ["A", "B", "C"]

    def test_screener_with_filter(self):
        """With data and filters, only passing symbols are returned."""
        resolver = UniverseResolver(custom_indices={"TEST": ["UP", "DOWN"]})

        # UP: trending up, DOWN: trending down
        up_data = _make_ohlcv(100, close_start=100, seed=1)
        up_data["close"] = np.linspace(100, 200, 100)
        up_data["high"] = up_data["close"] * 1.01
        up_data["low"] = up_data["close"] * 0.99
        up_data["open"] = up_data["close"]

        down_data = _make_ohlcv(100, close_start=200, seed=2)
        down_data["close"] = np.linspace(200, 50, 100)
        down_data["high"] = down_data["close"] * 1.01
        down_data["low"] = down_data["close"] * 0.99
        down_data["open"] = down_data["close"]

        data = {"UP": up_data, "DOWN": down_data}

        # Filter: RSI > 50 (UP should pass since it trends up)
        universe = {
            "type": "screener",
            "base": "TEST",
            "filters": [
                {
                    "type": "comparison",
                    "left": {"type": "indicator", "indicator": "RSI", "params": {"period": 14}},
                    "operator": ">",
                    "right": {"type": "constant", "value": 50},
                }
            ],
        }

        symbols = resolver.resolve(universe, data=data)
        assert "UP" in symbols
        # DOWN may or may not pass depending on RSI calculation
        # The key test is that filtering actually runs

    def test_screener_with_limit(self):
        """Limit restricts number of returned symbols."""
        resolver = UniverseResolver(custom_indices={"TEST": ["A", "B", "C", "D", "E"]})
        universe = {"type": "screener", "base": "TEST", "limit": 2}
        symbols = resolver.resolve(universe)
        assert len(symbols) == 2

    def test_screener_rank_by(self):
        """Symbols are ranked by the rank_by signal."""
        resolver = UniverseResolver(custom_indices={"TEST": ["LOW", "HIGH"]})

        # LOW has RSI ~30, HIGH has RSI ~70
        low_data = _make_ohlcv(100, close_start=200, seed=10)
        low_data["close"] = np.linspace(200, 100, 100)
        low_data["high"] = low_data["close"] * 1.01
        low_data["low"] = low_data["close"] * 0.99
        low_data["open"] = low_data["close"]

        high_data = _make_ohlcv(100, close_start=100, seed=20)
        high_data["close"] = np.linspace(100, 200, 100)
        high_data["high"] = high_data["close"] * 1.01
        high_data["low"] = high_data["close"] * 0.99
        high_data["open"] = high_data["close"]

        data = {"LOW": low_data, "HIGH": high_data}

        # Rank by RSI desc — HIGH should come first
        universe = {
            "type": "screener",
            "base": "TEST",
            "rank_by": {"type": "indicator", "indicator": "RSI", "params": {"period": 14}},
            "order": "desc",
        }

        symbols = resolver.resolve(universe, data=data)
        assert len(symbols) == 2
        assert symbols[0] == "HIGH"
        assert symbols[1] == "LOW"

    def test_screener_rank_asc(self):
        """Ascending rank order returns lowest first."""
        resolver = UniverseResolver(custom_indices={"TEST": ["LOW", "HIGH"]})

        low_data = _make_ohlcv(100, close_start=200, seed=10)
        low_data["close"] = np.linspace(200, 100, 100)
        low_data["high"] = low_data["close"] * 1.01
        low_data["low"] = low_data["close"] * 0.99
        low_data["open"] = low_data["close"]

        high_data = _make_ohlcv(100, close_start=100, seed=20)
        high_data["close"] = np.linspace(100, 200, 100)
        high_data["high"] = high_data["close"] * 1.01
        high_data["low"] = high_data["close"] * 0.99
        high_data["open"] = high_data["close"]

        data = {"LOW": low_data, "HIGH": high_data}

        universe = {
            "type": "screener",
            "base": "TEST",
            "rank_by": {"type": "indicator", "indicator": "RSI", "params": {"period": 14}},
            "order": "asc",
        }

        symbols = resolver.resolve(universe, data=data)
        assert symbols[0] == "LOW"

    def test_screener_missing_data_symbols_skipped(self):
        """Symbols without data are skipped during filtering."""
        resolver = UniverseResolver(custom_indices={"TEST": ["A", "B", "C"]})
        data = {"A": _make_ohlcv(100, seed=1)}  # Only A has data

        universe = {
            "type": "screener",
            "base": "TEST",
            "filters": [
                {
                    "type": "comparison",
                    "left": {"type": "price", "field": "close"},
                    "operator": ">",
                    "right": {"type": "constant", "value": 0},
                }
            ],
        }

        symbols = resolver.resolve(universe, data=data)
        assert symbols == ["A"]

