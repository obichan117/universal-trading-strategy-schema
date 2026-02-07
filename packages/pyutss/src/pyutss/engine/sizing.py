"""Position sizing logic for UTSS strategies.

Extracted from BacktestEngine._calculate_size() to be reusable
across single-symbol and multi-symbol engines.

Supports all UTSS sizing types:
- fixed_amount: Fixed dollar amount
- fixed_quantity: Fixed number of shares
- percent_of_equity: % of total portfolio value
- percent_of_cash: % of available cash
- percent_of_position: % of existing position (for pyramiding)
- risk_based: Size based on stop loss distance
- kelly: Kelly criterion sizing
- volatility_adjusted: ATR-based sizing
"""

from __future__ import annotations

import logging
import math
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def calculate_size(
    sizing: dict[str, Any],
    price: float,
    equity: float,
    cash: float,
    positions: dict[str, Any] | None = None,
    trades: list[Any] | None = None,
    data: pd.DataFrame | None = None,
) -> float:
    """Calculate position size based on sizing configuration.

    Args:
        sizing: Sizing config dict from strategy rule action
        price: Current price of the asset
        equity: Current total portfolio equity
        cash: Available cash
        positions: Current positions dict (symbol -> Position or quantity)
        trades: Closed trade history (for Kelly sizing)
        data: OHLCV data (for volatility-adjusted sizing)

    Returns:
        Number of shares/units to trade (always >= 0)
    """
    sizing_type = sizing.get("type", "percent_of_equity")
    value = sizing.get("value") or sizing.get("percent", 10)
    amount = sizing.get("amount", value)

    if sizing_type == "fixed_amount":
        return amount / price if price > 0 else 0.0

    elif sizing_type == "fixed_quantity":
        return float(value)

    elif sizing_type == "percent_of_equity":
        target_value = equity * (value / 100)
        return target_value / price if price > 0 else 0.0

    elif sizing_type == "percent_of_cash":
        target_value = cash * (value / 100)
        return target_value / price if price > 0 else 0.0

    elif sizing_type == "percent_of_position":
        symbol = sizing.get("symbol")
        if positions and symbol and symbol in positions:
            pos = positions[symbol]
            existing_qty = pos.quantity if hasattr(pos, "quantity") else float(pos)
            return existing_qty * (value / 100)
        return 0.0

    elif sizing_type == "risk_based":
        return _calculate_risk_based(sizing, price, equity)

    elif sizing_type == "kelly":
        return _calculate_kelly(sizing, price, equity, trades)

    elif sizing_type == "volatility_adjusted":
        return _calculate_volatility_adjusted(sizing, price, equity, data)

    else:
        logger.debug(f"Unknown sizing type '{sizing_type}', using 10% of equity")
        return (equity * 0.10) / price if price > 0 else 0.0


def _calculate_risk_based(
    sizing: dict[str, Any], price: float, equity: float
) -> float:
    """Risk-based sizing: risk_percent of equity / stop_loss distance."""
    risk_percent = sizing.get("risk_percent", 1.0)
    stop_loss_pct = sizing.get("stop_loss_percent", 2.0)

    max_risk = equity * (risk_percent / 100)
    risk_per_share = price * (stop_loss_pct / 100)

    if risk_per_share > 0:
        return max_risk / risk_per_share
    return 0.0


def _calculate_kelly(
    sizing: dict[str, Any],
    price: float,
    equity: float,
    trades: list[Any] | None = None,
) -> float:
    """Kelly criterion sizing: f* = (bp - q) / b."""
    win_rate = sizing.get("win_rate", 0.5)
    avg_win = sizing.get("avg_win", 1.0)
    avg_loss = sizing.get("avg_loss", 1.0)

    # Calculate from trade history if available
    if trades:
        closed_trades = [t for t in trades if hasattr(t, "is_open") and not t.is_open]
        if len(closed_trades) >= 10:
            winners = [t for t in closed_trades if t.pnl > 0]
            losers = [t for t in closed_trades if t.pnl < 0]
            if winners and losers:
                win_rate = len(winners) / len(closed_trades)
                avg_win = sum(t.pnl for t in winners) / len(winners)
                avg_loss = abs(sum(t.pnl for t in losers) / len(losers))

    if avg_loss > 0:
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - p
        kelly_fraction = (b * p - q) / b

        kelly_multiplier = sizing.get("multiplier") or sizing.get("fraction", 0.5)
        kelly_fraction = max(0, kelly_fraction * kelly_multiplier)
        kelly_fraction = min(kelly_fraction, 0.25)  # Cap at 25%

        target_value = equity * kelly_fraction
        return target_value / price if price > 0 else 0.0

    return (equity * 0.02) / price if price > 0 else 0.0


def _calculate_volatility_adjusted(
    sizing: dict[str, Any],
    price: float,
    equity: float,
    data: pd.DataFrame | None = None,
) -> float:
    """Volatility-adjusted sizing using ATR."""
    target_risk = sizing.get("target_risk", equity * 0.01)
    atr_period = sizing.get("atr_period") or sizing.get("lookback", 14)

    if data is not None and len(data) >= atr_period:
        from pyutss.engine.indicators import IndicatorService

        atr = IndicatorService.atr(data["high"], data["low"], data["close"], atr_period)
        current_atr = atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else price * 0.02

        if current_atr > 0:
            return target_risk / current_atr

    # Fallback: assume 2% ATR
    fallback_atr = price * 0.02
    return target_risk / fallback_atr if fallback_atr > 0 else 0.0


def round_to_lot(quantity: float, lot_size: int = 1, fractional: bool = False) -> float:
    """Round quantity to valid lot size.

    Args:
        quantity: Desired quantity
        lot_size: Minimum lot size (e.g., 100 for Japanese stocks, 1 for US)
        fractional: Whether fractional shares are allowed

    Returns:
        Rounded quantity (may be 0 if less than one lot)
    """
    if fractional:
        return quantity

    if lot_size <= 1:
        return math.floor(quantity)

    # Round down to nearest lot
    lots = math.floor(quantity / lot_size)
    return float(lots * lot_size)
