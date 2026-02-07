"""Data resolution and preparation for backtesting."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def resolve_data(
    strategy: dict[str, Any],
    data: pd.DataFrame | dict[str, pd.DataFrame] | None,
    symbol: str | None,
    start_date: date | str | None,
    end_date: date | str | None,
) -> tuple[list[str], dict[str, pd.DataFrame]]:
    """Resolve symbols and data from inputs.

    Returns (symbols, data_dict).
    """
    if isinstance(data, dict):
        symbols = list(data.keys())
        return symbols, data

    if data is not None and symbol is not None:
        return [symbol], {symbol: data}

    if data is not None:
        # Single DataFrame, try to get symbol from strategy
        universe = strategy.get("universe", {})
        if universe.get("type") == "static":
            syms = universe.get("symbols", [])
            if len(syms) == 1:
                return syms, {syms[0]: data}
        return ["UNKNOWN"], {"UNKNOWN": data}

    # No data provided - try auto-fetch
    symbols = resolve_universe_symbols(strategy)
    if not symbols:
        raise ValueError("No data provided and could not resolve symbols from strategy universe")

    data_dict = fetch_data(symbols, start_date, end_date)
    return symbols, data_dict


def resolve_universe_symbols(strategy: dict[str, Any]) -> list[str]:
    """Extract symbols from strategy universe."""
    from pyutss.engine.universe import UniverseResolver
    resolver = UniverseResolver()
    universe = strategy.get("universe", {})
    try:
        return resolver.resolve(universe)
    except (ValueError, Exception) as e:
        logger.warning(f"Failed to resolve universe: {e}")
        return []


def fetch_data(
    symbols: list[str],
    start_date: date | str | None,
    end_date: date | str | None,
) -> dict[str, pd.DataFrame]:
    """Fetch data for symbols using pyutss data sources."""
    if start_date is None or end_date is None:
        raise ValueError("start_date and end_date required when auto-fetching data")

    from pyutss.data.sources import download
    return download(symbols, start_date, end_date)


def prepare_data(
    data: pd.DataFrame,
    start_date: date | str | None,
    end_date: date | str | None,
) -> pd.DataFrame:
    """Prepare data: filter dates, ensure lowercase columns."""
    if data.empty:
        return data

    data = data.copy()

    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = pd.to_datetime(data.index)

    data.columns = data.columns.str.lower()

    if start_date:
        data = data[data.index >= pd.Timestamp(start_date)]
    if end_date:
        data = data[data.index <= pd.Timestamp(end_date)]

    return data
