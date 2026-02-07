"""Universe resolution for UTSS strategies.

Resolves strategy universe definitions into concrete symbol lists.
Supports static, index, screener, and dual universe types.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Hardcoded core index constituents (subset for common indices)
# Full lists would come from a data provider at runtime
INDEX_CONSTITUENTS: dict[str, list[str]] = {
    # US - Small representative subsets
    "DOW30": [
        "AAPL", "AMGN", "AXP", "BA", "CAT", "CRM", "CSCO", "CVX", "DIS", "DOW",
        "GS", "HD", "HON", "IBM", "INTC", "JNJ", "JPM", "KO", "MCD", "MMM",
        "MRK", "MSFT", "NKE", "PG", "TRV", "UNH", "V", "VZ", "WBA", "WMT",
    ],
    # Japan (Yahoo Finance .T suffix format)
    "NIKKEI225": [
        "7203.T", "6758.T", "9984.T", "8306.T", "6861.T", "6501.T", "7267.T",
        "4502.T", "9432.T", "6902.T", "8035.T", "7751.T", "4503.T", "6367.T",
        "8316.T", "9433.T", "6954.T", "7974.T", "4063.T", "8411.T",
    ],
}


class UniverseResolver:
    """Resolves strategy universe definitions into symbol lists.

    Supports:
    - static: Returns symbols directly
    - index: Maps index name to constituent symbols
    - screener: Resolves base universe then applies filters
    - dual: Resolves long and short sides independently
    """

    def __init__(self, custom_indices: dict[str, list[str]] | None = None) -> None:
        """Initialize resolver.

        Args:
            custom_indices: Additional custom index definitions
        """
        self._indices = {**INDEX_CONSTITUENTS}
        if custom_indices:
            self._indices.update(custom_indices)

    def resolve(self, universe: dict[str, Any]) -> list[str]:
        """Resolve a universe definition to a list of symbols.

        Args:
            universe: Universe definition from strategy

        Returns:
            List of symbol strings

        Raises:
            ValueError: If universe type is invalid or cannot be resolved
        """
        utype = universe.get("type", "static")

        if utype == "static":
            return self._resolve_static(universe)
        elif utype == "index":
            return self._resolve_index(universe)
        elif utype == "screener":
            return self._resolve_screener(universe)
        elif utype == "dual":
            return self._resolve_dual(universe)
        else:
            raise ValueError(f"Unknown universe type: {utype}")

    def _resolve_static(self, universe: dict) -> list[str]:
        """Resolve static universe."""
        symbols = universe.get("symbols", [])
        if not symbols:
            raise ValueError("Static universe requires non-empty 'symbols' list")
        return list(symbols)

    def _resolve_index(self, universe: dict) -> list[str]:
        """Resolve index universe."""
        index_name = universe.get("index", "")
        symbols = self._get_index_symbols(index_name)

        limit = universe.get("limit")
        if limit and isinstance(limit, int):
            symbols = symbols[:limit]

        return symbols

    def _resolve_screener(self, universe: dict) -> list[str]:
        """Resolve screener universe.

        Note: Full filter evaluation requires data. Without data,
        returns the base universe symbols.
        """
        base = universe.get("base", "")
        if base and base in self._indices:
            symbols = list(self._indices[base])
        elif base:
            logger.warning(f"Unknown screener base '{base}', returning empty list")
            symbols = []
        else:
            symbols = []

        limit = universe.get("limit")
        if limit and isinstance(limit, int):
            symbols = symbols[:limit]

        return symbols

    def _resolve_dual(self, universe: dict) -> list[str]:
        """Resolve dual universe (long + short sides)."""
        symbols = set()

        long_side = universe.get("long", {})
        short_side = universe.get("short", {})

        if long_side:
            index_name = long_side.get("index", "")
            if index_name:
                long_symbols = self._get_index_symbols(index_name)
                limit = long_side.get("limit")
                if limit and isinstance(limit, int):
                    long_symbols = long_symbols[:limit]
                symbols.update(long_symbols)

        if short_side:
            index_name = short_side.get("index", "")
            if index_name:
                short_symbols = self._get_index_symbols(index_name)
                limit = short_side.get("limit")
                if limit and isinstance(limit, int):
                    short_symbols = short_symbols[:limit]
                symbols.update(short_symbols)

        return list(symbols)

    def _get_index_symbols(self, index_name: str) -> list[str]:
        """Get symbols for a named index."""
        if index_name in self._indices:
            return list(self._indices[index_name])

        logger.warning(
            f"Index '{index_name}' not found in local database. "
            f"Available: {list(self._indices.keys())}"
        )
        return []

    def add_index(self, name: str, symbols: list[str]) -> None:
        """Register a custom index.

        Args:
            name: Index name
            symbols: List of symbols
        """
        self._indices[name] = list(symbols)
