"""Executor interface and backtest implementation.

Separates trade evaluation from trade execution via a protocol.
The Engine evaluates conditions and produces OrderRequests;
the Executor converts them into Fills (or rejects them).

This abstraction enables:
- BacktestExecutor: simulated fills with commission/slippage models
- LiveExecutor: real broker API fills (future)

Usage:
    executor = BacktestExecutor(commission_rate=0.001, slippage_rate=0.0005)
    fill = executor.execute(order)
    if fill:
        portfolio_manager.open_position(...)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)


@dataclass
class OrderRequest:
    """Request to execute a trade.

    Created by the Engine when a rule fires. Passed to an Executor
    for fill simulation or real execution.
    """

    symbol: str
    direction: str  # buy, sell, short, cover
    quantity: float
    price: float
    order_type: str = "market"


@dataclass
class Fill:
    """Result of executing an order.

    Returned by Executor.execute(). May differ from the request
    (e.g. lot rounding, slippage adjustment).
    """

    symbol: str
    direction: str
    quantity: float  # may differ from request (lot rounding)
    fill_price: float  # includes slippage
    commission: float
    slippage: float

    @property
    def total_cost(self) -> float:
        """Total cost of the fill (commission + slippage)."""
        return self.commission + self.slippage


class Executor(Protocol):
    """Protocol for trade execution.

    Implementations must convert an OrderRequest into a Fill or reject it.
    """

    def execute(self, order: OrderRequest) -> Fill | None:
        """Execute an order request.

        Args:
            order: The order to execute

        Returns:
            Fill if the order was executed, None if rejected
        """
        ...


class BacktestExecutor:
    """Simulated trade execution for backtesting.

    Handles:
    - Commission calculation (flat rate or tiered)
    - Slippage simulation (percentage-based)
    - Lot size rounding (for Japanese market support)
    - Price limit checks (future: exchange-specific)
    """

    def __init__(
        self,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        lot_size: int = 1,
        tiered_commission: list[dict] | None = None,
    ) -> None:
        """Initialize backtest executor.

        Args:
            commission_rate: Commission as fraction of trade value
            slippage_rate: Slippage as fraction of price
            lot_size: Minimum trade lot size (1 for US, 100 for Japan)
            tiered_commission: Optional tiered commission schedule.
                Each tier: {"up_to": value, "fee": amount} or
                {"above": value, "fee": amount}
        """
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.lot_size = lot_size
        self.tiered_commission = tiered_commission

    def execute(self, order: OrderRequest) -> Fill | None:
        """Execute an order with simulated fills.

        Applies lot rounding, slippage, and commission calculation.

        Args:
            order: The order to execute

        Returns:
            Fill with adjusted quantity and costs, or None if order
            would result in zero quantity after lot rounding
        """
        quantity = self._round_to_lot(order.quantity)
        if quantity <= 0:
            return None

        fill_price = self._apply_slippage(order.price, order.direction)
        trade_value = quantity * fill_price
        commission = self._calculate_commission(trade_value)
        slippage = abs(fill_price - order.price) * quantity

        return Fill(
            symbol=order.symbol,
            direction=order.direction,
            quantity=quantity,
            fill_price=fill_price,
            commission=commission,
            slippage=slippage,
        )

    def _round_to_lot(self, quantity: float) -> float:
        """Round quantity to lot size."""
        if self.lot_size <= 1:
            return max(0, int(quantity))
        return max(0, int(quantity / self.lot_size) * self.lot_size)

    def _apply_slippage(self, price: float, direction: str) -> float:
        """Apply slippage to price based on direction.

        Buys get worse (higher) prices, sells get worse (lower) prices.
        """
        if direction in ("buy", "long", "cover"):
            return price * (1 + self.slippage_rate)
        else:
            return price * (1 - self.slippage_rate)

    def _calculate_commission(self, trade_value: float) -> float:
        """Calculate commission for a trade.

        Uses tiered schedule if configured, otherwise flat rate.

        Args:
            trade_value: Absolute value of the trade

        Returns:
            Commission amount
        """
        if self.tiered_commission:
            return self._calculate_tiered_commission(trade_value)
        return trade_value * self.commission_rate

    def _calculate_tiered_commission(self, trade_value: float) -> float:
        """Calculate commission from tiered schedule.

        Finds the matching tier based on trade value. Tiers should have
        either 'up_to' (for ranges) or 'above' (for the final tier).

        Example Japanese broker tiers:
            [
                {"up_to": 50000, "fee": 55},
                {"up_to": 100000, "fee": 99},
                {"above": 100000, "fee": 115},
            ]
        """
        for tier in self.tiered_commission:
            if "up_to" in tier:
                if trade_value <= tier["up_to"]:
                    return tier["fee"]
            elif "above" in tier:
                if trade_value > tier["above"]:
                    return tier["fee"]

        # Fallback: use last tier's fee or flat rate
        if self.tiered_commission:
            return self.tiered_commission[-1].get("fee", trade_value * self.commission_rate)
        return trade_value * self.commission_rate
