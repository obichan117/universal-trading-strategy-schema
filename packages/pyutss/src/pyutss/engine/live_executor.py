"""Live executor implementations for real and paper trading.

Provides broker-agnostic executor implementations that use the
same Executor protocol as BacktestExecutor, enabling seamless
transition from backtesting to live trading.

Supported Brokerages
--------------------
+------------------+----------+-------------+---------------------------+
| Executor         | Type     | Dependency  | Markets                   |
+------------------+----------+-------------+---------------------------+
| BacktestExecutor | Backtest | (built-in)  | Any (historical data)     |
| PaperExecutor    | Paper    | (built-in)  | Any (simulated fills)     |
| AlpacaExecutor   | Live     | alpaca-py   | US stocks (paper + live)  |
+------------------+----------+-------------+---------------------------+

BacktestExecutor lives in executor.py. PaperExecutor and AlpacaExecutor
live here. All satisfy the Executor protocol (execute(order) -> Fill).

AlpacaExecutor additionally satisfies the LiveExecutor protocol which
adds get_account(), get_price(), and cancel_all().

Adding a new brokerage
~~~~~~~~~~~~~~~~~~~~~~
1. Create a class with an ``execute(order: OrderRequest) -> Fill | None`` method.
2. Optionally implement get_account / get_price / cancel_all for LiveExecutor.
3. Lazy-import the broker SDK inside methods to keep it an optional dependency.
4. Pass the executor to ``Engine(executor=your_executor)``.

Usage:
    # Paper trading (simulates fills using live prices)
    executor = PaperExecutor(initial_cash=100000)
    fill = executor.execute(order)

    # Live trading via Alpaca (pip install alpaca-py)
    executor = AlpacaExecutor(api_key="...", secret_key="...", paper=True)
    fill = executor.execute(order)

    # Use with Engine
    engine = Engine(executor=executor)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable

from pyutss.engine.executor import Fill, OrderRequest

logger = logging.getLogger(__name__)


@dataclass
class BrokerConfig:
    """Configuration for a broker connection."""

    api_key: str = ""
    secret_key: str = ""
    base_url: str = ""
    paper: bool = True


@dataclass
class AccountInfo:
    """Broker account summary."""

    cash: float = 0.0
    equity: float = 0.0
    buying_power: float = 0.0
    positions: dict[str, float] = field(default_factory=dict)


@runtime_checkable
class LiveExecutor(Protocol):
    """Protocol for live trading executors.

    Extends the basic Executor protocol with broker-specific operations.
    Implementations satisfy this structurally (no inheritance needed).
    """

    def execute(self, order: OrderRequest) -> Fill | None:
        """Execute an order against the broker."""
        ...

    def get_account(self) -> AccountInfo:
        """Get current account information."""
        ...

    def get_price(self, symbol: str) -> float | None:
        """Get current market price for a symbol."""
        ...

    def cancel_all(self) -> int:
        """Cancel all open orders. Returns count cancelled."""
        ...


class PaperExecutor:
    """Paper trading executor that simulates fills locally.

    Tracks positions and cash in memory. Uses a price feed
    callback to get current prices for fill simulation.

    Works as a drop-in replacement for BacktestExecutor
    with the same Executor protocol.
    """

    def __init__(
        self,
        initial_cash: float = 100000.0,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        price_feed: callable | None = None,
    ) -> None:
        """Initialize paper executor.

        Args:
            initial_cash: Starting cash balance
            commission_rate: Commission as fraction of trade value
            slippage_rate: Slippage as fraction of price
            price_feed: Optional callback(symbol) -> float for live prices.
                If not provided, uses the price from the OrderRequest.
        """
        self.cash = initial_cash
        self.initial_cash = initial_cash
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.price_feed = price_feed
        self.positions: dict[str, float] = {}
        self.fills: list[Fill] = []
        self.order_log: list[dict] = []

    def execute(self, order: OrderRequest) -> Fill | None:
        """Execute an order with paper fills.

        Simulates fill at current price with commission/slippage.
        Validates sufficient cash for buys.
        """
        price = order.price
        if self.price_feed:
            live_price = self.price_feed(order.symbol)
            if live_price is not None:
                price = live_price

        quantity = max(0, int(order.quantity))
        if quantity <= 0:
            return None

        fill_price = self._apply_slippage(price, order.direction)
        trade_value = quantity * fill_price
        commission = trade_value * self.commission_rate

        # Validate sufficient cash for buys
        if order.direction in ("buy", "long", "cover"):
            total_cost = trade_value + commission
            if total_cost > self.cash:
                logger.warning(
                    f"Insufficient cash for {order.symbol}: "
                    f"need ${total_cost:.2f}, have ${self.cash:.2f}"
                )
                return None

        slippage = abs(fill_price - price) * quantity

        fill = Fill(
            symbol=order.symbol,
            direction=order.direction,
            quantity=quantity,
            fill_price=fill_price,
            commission=commission,
            slippage=slippage,
        )

        # Update paper positions and cash
        self._update_state(fill)
        self.fills.append(fill)
        self.order_log.append({
            "timestamp": datetime.now().isoformat(),
            "order": {
                "symbol": order.symbol,
                "direction": order.direction,
                "quantity": order.quantity,
                "price": order.price,
            },
            "fill": {
                "quantity": fill.quantity,
                "fill_price": fill.fill_price,
                "commission": fill.commission,
            },
        })

        return fill

    def _apply_slippage(self, price: float, direction: str) -> float:
        """Apply slippage to price."""
        if direction in ("buy", "long", "cover"):
            return price * (1 + self.slippage_rate)
        return price * (1 - self.slippage_rate)

    def _update_state(self, fill: Fill) -> None:
        """Update cash and positions after a fill."""
        cost = fill.quantity * fill.fill_price

        if fill.direction in ("buy", "long"):
            self.cash -= cost + fill.commission
            current = self.positions.get(fill.symbol, 0.0)
            self.positions[fill.symbol] = current + fill.quantity
        elif fill.direction in ("sell", "short"):
            self.cash += cost - fill.commission
            current = self.positions.get(fill.symbol, 0.0)
            self.positions[fill.symbol] = current - fill.quantity
            if self.positions[fill.symbol] <= 0:
                del self.positions[fill.symbol]
        elif fill.direction == "cover":
            self.cash -= cost + fill.commission
            current = self.positions.get(fill.symbol, 0.0)
            self.positions[fill.symbol] = current + fill.quantity
            if abs(self.positions[fill.symbol]) < 1e-10:
                del self.positions[fill.symbol]

    def get_account(self) -> AccountInfo:
        """Get paper account summary."""
        return AccountInfo(
            cash=self.cash,
            equity=self.cash,  # Simplified: doesn't mark-to-market
            buying_power=self.cash,
            positions=dict(self.positions),
        )

    def reset(self) -> None:
        """Reset paper account to initial state."""
        self.cash = self.initial_cash
        self.positions.clear()
        self.fills.clear()
        self.order_log.clear()


class AlpacaExecutor:
    """Alpaca broker executor (requires alpaca-py).

    Supports both paper and live trading via Alpaca's API.
    Install with: pip install alpaca-py

    Usage:
        executor = AlpacaExecutor(
            api_key="PKXXXXXXXX",
            secret_key="XXXXXXXX",
            paper=True,
        )
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        paper: bool = True,
    ) -> None:
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        self._client = None

    def _get_client(self):
        """Lazy-import and create Alpaca client."""
        if self._client is None:
            try:
                from alpaca.trading.client import TradingClient
                self._client = TradingClient(
                    self.api_key,
                    self.secret_key,
                    paper=self.paper,
                )
            except ImportError:
                raise ImportError(
                    "alpaca-py is required for AlpacaExecutor. "
                    "Install with: pip install alpaca-py"
                )
        return self._client

    def execute(self, order: OrderRequest) -> Fill | None:
        """Submit order to Alpaca and return fill."""
        try:
            from alpaca.trading.requests import MarketOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce

            client = self._get_client()

            side = OrderSide.BUY if order.direction in ("buy", "long", "cover") else OrderSide.SELL
            qty = int(order.quantity)
            if qty <= 0:
                return None

            req = MarketOrderRequest(
                symbol=order.symbol,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY,
            )

            result = client.submit_order(req)
            logger.info(f"Alpaca order submitted: {result.id} {order.symbol} {side} {qty}")

            # For market orders, approximate fill price
            fill_price = float(result.filled_avg_price) if result.filled_avg_price else order.price

            return Fill(
                symbol=order.symbol,
                direction=order.direction,
                quantity=float(result.filled_qty or qty),
                fill_price=fill_price,
                commission=0.0,  # Alpaca is commission-free
                slippage=abs(fill_price - order.price) * qty,
            )
        except Exception as e:
            logger.error(f"Alpaca execution failed: {e}")
            return None

    def get_account(self) -> AccountInfo:
        """Get Alpaca account info."""
        client = self._get_client()
        account = client.get_account()
        positions = client.get_all_positions()
        return AccountInfo(
            cash=float(account.cash),
            equity=float(account.equity),
            buying_power=float(account.buying_power),
            positions={p.symbol: float(p.qty) for p in positions},
        )

    def get_price(self, symbol: str) -> float | None:
        """Get latest price from Alpaca."""
        try:
            from alpaca.data.requests import StockLatestQuoteRequest
            from alpaca.data.historical import StockHistoricalDataClient

            data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
            req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote = data_client.get_stock_latest_quote(req)
            if symbol in quote:
                return float(quote[symbol].ask_price)
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
        return None

    def cancel_all(self) -> int:
        """Cancel all open orders."""
        client = self._get_client()
        statuses = client.cancel_orders()
        return len(statuses)
