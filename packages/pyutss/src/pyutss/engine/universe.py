"""Universe resolution for UTSS strategies.

Resolves strategy universe definitions into concrete symbol lists.
Supports static, index, screener, and dual universe types.

When data is provided, screener filters are evaluated to select
symbols that match the conditions.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

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

    def resolve(
        self,
        universe: dict[str, Any],
        data: dict[str, pd.DataFrame] | None = None,
    ) -> list[str]:
        """Resolve a universe definition to a list of symbols.

        Args:
            universe: Universe definition from strategy
            data: Optional dict of symbol -> OHLCV DataFrames for screener filtering

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
            return self._resolve_screener(universe, data)
        elif utype == "dual":
            return self._resolve_dual(universe, data)
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

    def _resolve_screener(
        self,
        universe: dict,
        data: dict[str, pd.DataFrame] | None = None,
    ) -> list[str]:
        """Resolve screener universe with optional filter evaluation.

        When data is provided, evaluates filter conditions against each
        symbol's data. Only symbols where ALL filters pass on the last bar
        are included.

        When no data is provided, returns the base universe symbols (unfiltered).
        """
        base = universe.get("base", "")
        if base and base in self._indices:
            candidates = list(self._indices[base])
        elif base:
            logger.warning(f"Unknown screener base '{base}', returning empty list")
            candidates = []
        else:
            candidates = []

        filters = universe.get("filters", [])

        # If we have data and filters, evaluate them
        if data and filters:
            candidates = self._apply_filters(candidates, filters, data)

        # Rank if specified
        rank_by = universe.get("rank_by")
        rank_order = universe.get("order", "desc")
        if rank_by and data:
            candidates = self._rank_symbols(candidates, rank_by, rank_order, data)

        limit = universe.get("limit")
        if limit and isinstance(limit, int):
            candidates = candidates[:limit]

        return candidates

    def _apply_filters(
        self,
        symbols: list[str],
        filters: list[dict],
        data: dict[str, pd.DataFrame],
    ) -> list[str]:
        """Apply filter conditions to candidate symbols.

        Each filter is evaluated against the symbol's last bar.
        A symbol passes only if ALL filters are True.
        """
        from pyutss.engine.evaluator import (
            ConditionEvaluator,
            EvaluationContext,
            SignalEvaluator,
        )

        signal_eval = SignalEvaluator()
        cond_eval = ConditionEvaluator(signal_eval)
        passed = []

        for sym in symbols:
            if sym not in data:
                continue

            df = data[sym]
            if df.empty:
                continue

            ctx = EvaluationContext(primary_data=df)
            ctx.current_bar_idx = len(df) - 1

            try:
                all_pass = True
                for filt in filters:
                    result = cond_eval.evaluate_condition(filt, ctx)
                    if not result.iloc[-1]:
                        all_pass = False
                        break
                if all_pass:
                    passed.append(sym)
            except Exception as e:
                logger.debug(f"Filter evaluation failed for {sym}: {e}")
                continue

        return passed

    def _rank_symbols(
        self,
        symbols: list[str],
        rank_by: dict,
        order: str,
        data: dict[str, pd.DataFrame],
    ) -> list[str]:
        """Rank symbols by a signal value.

        Evaluates the rank_by signal for each symbol's last bar and sorts.
        """
        from pyutss.engine.evaluator import (
            EvaluationContext,
            SignalEvaluator,
        )

        signal_eval = SignalEvaluator()
        scores: list[tuple[str, float]] = []

        for sym in symbols:
            if sym not in data:
                continue

            df = data[sym]
            if df.empty:
                continue

            ctx = EvaluationContext(primary_data=df)
            try:
                result = signal_eval.evaluate_signal(rank_by, ctx)
                value = result.iloc[-1]
                if pd.notna(value):
                    scores.append((sym, float(value)))
            except Exception as e:
                logger.debug(f"Rank evaluation failed for {sym}: {e}")
                continue

        reverse = order == "desc"
        scores.sort(key=lambda x: x[1], reverse=reverse)
        return [sym for sym, _ in scores]

    def _resolve_dual(
        self,
        universe: dict,
        data: dict[str, pd.DataFrame] | None = None,
    ) -> list[str]:
        """Resolve dual universe (long + short sides)."""
        symbols = set()

        long_side = universe.get("long", {})
        short_side = universe.get("short", {})

        if long_side:
            long_symbols = self._resolve_side(long_side, data)
            symbols.update(long_symbols)

        if short_side:
            short_symbols = self._resolve_side(short_side, data)
            symbols.update(short_symbols)

        return list(symbols)

    def _resolve_side(
        self,
        side: dict,
        data: dict[str, pd.DataFrame] | None = None,
    ) -> list[str]:
        """Resolve one side of a dual universe."""
        # Treat each side as its own sub-universe
        side_type = side.get("type", "")

        if side_type == "screener":
            return self._resolve_screener(side, data)
        elif side_type == "index" or "index" in side:
            return self._resolve_index(side)
        elif "symbols" in side:
            return self._resolve_static(side)
        else:
            # Legacy format: just an index field
            index_name = side.get("index", "")
            if index_name:
                syms = self._get_index_symbols(index_name)
                limit = side.get("limit")
                if limit and isinstance(limit, int):
                    syms = syms[:limit]
                return syms
            return []

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
