"""Unified portfolio management for backtesting.

Single source of truth for position tracking, cash management,
equity calculation, and snapshot recording. Used by the unified Engine
for both single-symbol and multi-symbol backtests.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from pyutss.results.types import (
    PortfolioSnapshot,
    Position,
    Trade,
)

logger = logging.getLogger(__name__)


@dataclass
class PortfolioManager:
    """Manages positions, cash, and equity tracking.

    Consolidates duplicated logic from BacktestEngine and PortfolioBacktester
    into a single, consistent position management system.

    All positions are tracked as Position objects (not bare floats).
    Supports both long and short positions.
    """

    initial_capital: float = 100000.0
    cash: float = 0.0
    positions: dict[str, Position] = field(default_factory=dict)
    trades: list[Trade] = field(default_factory=list)
    portfolio_history: list[PortfolioSnapshot] = field(default_factory=list)
    equity_curve: list[tuple[date, float]] = field(default_factory=list)
    peak_equity: float = 0.0

    def __post_init__(self) -> None:
        if self.cash == 0.0:
            self.cash = self.initial_capital
        if self.peak_equity == 0.0:
            self.peak_equity = self.initial_capital

    def reset(self) -> None:
        """Reset to initial state."""
        self.cash = self.initial_capital
        self.positions.clear()
        self.trades.clear()
        self.portfolio_history.clear()
        self.equity_curve.clear()
        self.peak_equity = self.initial_capital

    # ─── Equity ──────────────────────────────────────────────

    def get_equity(
        self,
        prices: dict[str, float] | None = None,
    ) -> float:
        """Calculate current total equity (cash + positions value).

        Args:
            prices: Current prices for each symbol. If not provided,
                    uses avg_price from positions.
        """
        equity = self.cash
        for symbol, pos in self.positions.items():
            if prices and symbol in prices:
                price = prices[symbol]
            else:
                price = pos.avg_price
            equity += pos.quantity * price
        return equity

    def get_positions_value(
        self,
        prices: dict[str, float] | None = None,
    ) -> float:
        """Calculate total value of all positions."""
        return self.get_equity(prices) - self.cash

    # ─── Position Operations ─────────────────────────────────

    def open_position(
        self,
        symbol: str,
        quantity: float,
        price: float,
        direction: str,
        current_date: date,
        commission: float = 0.0,
        slippage: float = 0.0,
        reason: str = "rule_triggered",
    ) -> Trade | None:
        """Open a new position.

        Args:
            symbol: Symbol to trade
            quantity: Number of shares
            price: Entry price
            direction: "long" or "short"
            current_date: Entry date
            commission: Commission cost
            slippage: Slippage cost
            reason: Entry reason

        Returns:
            Trade object if position was opened, None otherwise
        """
        if symbol in self.positions:
            logger.debug(f"Already have position in {symbol}, skipping")
            return None

        if quantity <= 0:
            return None

        if direction in ("long", "buy"):
            total_cost = price * quantity + commission + slippage
            if total_cost > self.cash:
                # Adjust to available cash
                quantity = (self.cash - commission - slippage) / price
                if quantity <= 0:
                    return None
                total_cost = price * quantity + commission + slippage

            self.cash -= total_cost
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=price,
                direction="long",
                entry_date=current_date,
            )
        elif direction in ("short",):
            position_value = price * quantity
            margin_required = position_value * 0.5
            total_cost = margin_required + commission + slippage
            if total_cost > self.cash:
                available_margin = self.cash - commission - slippage
                quantity = (available_margin / 0.5) / price
                if quantity <= 0:
                    return None
                position_value = price * quantity
                margin_required = position_value * 0.5
                total_cost = margin_required + commission + slippage

            self.cash -= total_cost
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=price,
                direction="short",
                entry_date=current_date,
            )
        else:
            return None

        trade = Trade(
            symbol=symbol,
            direction="long" if direction in ("long", "buy") else "short",
            entry_date=current_date,
            entry_price=price,
            quantity=quantity,
            commission=commission,
            slippage=slippage,
            entry_reason=reason,
        )
        self.trades.append(trade)
        return trade

    def close_position(
        self,
        symbol: str,
        price: float,
        current_date: date,
        reason: str = "signal",
        commission: float = 0.0,
        slippage: float = 0.0,
    ) -> Trade | None:
        """Close an existing position.

        Args:
            symbol: Symbol to close
            price: Exit price
            current_date: Exit date
            reason: Exit reason
            commission: Commission cost
            slippage: Slippage cost

        Returns:
            The closed Trade object, or None if no position exists
        """
        if symbol not in self.positions:
            return None

        position = self.positions.pop(symbol)
        position_value = price * position.quantity

        # Find and close the open trade
        closed_trade = None
        for trade in reversed(self.trades):
            if trade.symbol == symbol and trade.is_open:
                trade.close(
                    exit_date=current_date,
                    exit_price=price,
                    reason=reason,
                    commission=commission,
                    slippage=slippage,
                )
                closed_trade = trade
                break

        if closed_trade is None:
            # Create synthetic trade
            closed_trade = Trade(
                symbol=symbol,
                direction=position.direction,
                entry_date=position.entry_date,
                entry_price=position.avg_price,
                quantity=position.quantity,
                exit_date=current_date,
                exit_price=price,
                commission=commission,
                slippage=slippage,
                is_open=False,
                exit_reason=reason,
            )
            if position.direction == "long":
                closed_trade.pnl = (price - position.avg_price) * position.quantity
            else:
                closed_trade.pnl = (position.avg_price - price) * position.quantity
            closed_trade.pnl -= commission + slippage
            self.trades.append(closed_trade)

        # Update cash
        if position.direction == "long":
            self.cash += position_value - commission - slippage
        else:
            entry_value = position.avg_price * position.quantity
            pnl = entry_value - position_value
            margin_returned = entry_value * 0.5
            self.cash += margin_returned + pnl - commission - slippage

        return closed_trade

    def update_positions(
        self,
        prices: dict[str, float],
        current_date: date,
    ) -> None:
        """Update unrealized P&L and days held for all positions.

        Args:
            prices: Current prices keyed by symbol
            current_date: Current date
        """
        for symbol, pos in self.positions.items():
            if symbol in prices:
                pos.update_unrealized(prices[symbol], current_date)

    # ─── Exit Checks ─────────────────────────────────────────

    def check_exits(
        self,
        prices: dict[str, float],
        current_date: date,
        constraints: dict,
        commission_rate: float = 0.0,
        slippage_rate: float = 0.0,
    ) -> list[Trade]:
        """Check stop loss, take profit, and trailing stop for all positions.

        Args:
            prices: Current prices keyed by symbol
            current_date: Current date
            constraints: Strategy constraints dict
            commission_rate: Commission rate for exit trades
            slippage_rate: Slippage rate for exit trades

        Returns:
            List of trades that were closed
        """
        closed_trades = []
        stop_loss = constraints.get("stop_loss", {})
        take_profit = constraints.get("take_profit", {})
        trailing_stop = constraints.get("trailing_stop", {})

        for symbol in list(self.positions.keys()):
            if symbol not in prices:
                continue

            price = prices[symbol]
            position = self.positions[symbol]
            entry_price = position.avg_price
            is_long = position.direction == "long"

            should_exit = False
            reason = ""

            # Stop loss
            sl_pct = stop_loss.get("percentage") or stop_loss.get("percent")
            if sl_pct:
                if is_long and price <= entry_price * (1 - sl_pct / 100):
                    should_exit = True
                    reason = "stop_loss"
                elif not is_long and price >= entry_price * (1 + sl_pct / 100):
                    should_exit = True
                    reason = "stop_loss"

            # Take profit
            if not should_exit:
                tp_pct = take_profit.get("percentage") or take_profit.get("percent")
                if tp_pct:
                    if is_long and price >= entry_price * (1 + tp_pct / 100):
                        should_exit = True
                        reason = "take_profit"
                    elif not is_long and price <= entry_price * (1 - tp_pct / 100):
                        should_exit = True
                        reason = "take_profit"

            # Trailing stop
            if not should_exit:
                ts_pct = trailing_stop.get("percentage") or trailing_stop.get("percent")
                if ts_pct and position.unrealized_pnl > 0:
                    if is_long:
                        peak_price = entry_price + (position.unrealized_pnl / position.quantity)
                        if price <= peak_price * (1 - ts_pct / 100):
                            should_exit = True
                            reason = "trailing_stop"
                    else:
                        trough_price = entry_price - (position.unrealized_pnl / position.quantity)
                        if price >= trough_price * (1 + ts_pct / 100):
                            should_exit = True
                            reason = "trailing_stop"

            if should_exit:
                position_value = price * position.quantity
                commission = position_value * commission_rate
                slippage_cost = position_value * slippage_rate
                trade = self.close_position(
                    symbol, price, current_date, reason, commission, slippage_cost
                )
                if trade:
                    closed_trades.append(trade)

        return closed_trades

    # ─── Snapshot Recording ──────────────────────────────────

    def record_snapshot(
        self,
        current_date: date,
        prices: dict[str, float] | None = None,
    ) -> PortfolioSnapshot:
        """Record current portfolio state.

        Args:
            current_date: Current date
            prices: Current prices for equity calculation

        Returns:
            The recorded snapshot
        """
        equity = self.get_equity(prices)
        positions_value = self.get_positions_value(prices)

        if equity > self.peak_equity:
            self.peak_equity = equity

        drawdown = self.peak_equity - equity
        drawdown_pct = (drawdown / self.peak_equity * 100) if self.peak_equity > 0 else 0

        snapshot = PortfolioSnapshot(
            date=current_date,
            cash=self.cash,
            positions_value=positions_value,
            equity=equity,
            drawdown=drawdown,
            drawdown_pct=drawdown_pct,
        )
        self.portfolio_history.append(snapshot)
        self.equity_curve.append((current_date, equity))
        return snapshot

    def build_equity_series(self) -> pd.Series:
        """Build equity curve as a pandas Series."""
        return pd.Series(
            {d: eq for d, eq in self.equity_curve},
            name="equity",
        )
