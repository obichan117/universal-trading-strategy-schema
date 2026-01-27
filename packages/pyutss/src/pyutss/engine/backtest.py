"""Backtesting engine for UTSS strategies."""

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import pandas as pd

from pyutss.engine.evaluator import (
    ConditionEvaluator,
    EvaluationContext,
    SignalEvaluator,
)
from pyutss.results.types import (
    BacktestConfig,
    BacktestResult,
    PortfolioSnapshot,
    Position,
    Trade,
)

logger = logging.getLogger(__name__)


@dataclass
class EngineState:
    """Internal state of the backtest engine."""

    cash: float
    positions: dict[str, Position] = field(default_factory=dict)
    trades: list[Trade] = field(default_factory=list)
    portfolio_history: list[PortfolioSnapshot] = field(default_factory=list)
    equity_curve: list[tuple[date, float]] = field(default_factory=list)
    peak_equity: float = 0.0


class BacktestEngine:
    """Event-driven backtesting engine for UTSS strategies.

    Executes UTSS strategy definitions against historical OHLCV data,
    simulating trades and tracking portfolio performance.

    Features:
    - Signal and condition evaluation per UTSS schema
    - Commission and slippage modeling
    - Position sizing support
    - Take profit / stop loss handling
    - Detailed trade logging

    Example:
        from pyutss import BacktestEngine, BacktestConfig

        engine = BacktestEngine(config=BacktestConfig(initial_capital=100000))

        # Load UTSS strategy
        strategy = load_strategy("my_strategy.yaml")

        # Run backtest
        result = engine.run(
            strategy=strategy,
            data=ohlcv_df,
            symbol="AAPL",
            start_date=date(2020, 1, 1),
            end_date=date(2024, 1, 1),
        )

        print(f"Total return: {result.total_return_pct:.2f}%")
    """

    def __init__(self, config: BacktestConfig | None = None) -> None:
        """Initialize backtest engine.

        Args:
            config: Backtest configuration
        """
        self.config = config or BacktestConfig()
        self.signal_evaluator = SignalEvaluator()
        self.condition_evaluator = ConditionEvaluator(self.signal_evaluator)
        self._state: EngineState | None = None

    def reset(self) -> None:
        """Reset engine state for new backtest."""
        self._state = None
        self.signal_evaluator.clear_cache()

    def run(
        self,
        strategy: dict[str, Any],
        data: pd.DataFrame,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
        parameters: dict[str, float] | None = None,
    ) -> BacktestResult:
        """Run backtest for a strategy.

        Args:
            strategy: UTSS strategy definition
            data: OHLCV DataFrame with DatetimeIndex
            symbol: Stock symbol
            start_date: Backtest start date (optional)
            end_date: Backtest end date (optional)
            parameters: Strategy parameters (optional)

        Returns:
            BacktestResult with performance data
        """
        self.reset()

        # Filter data by date range
        if start_date:
            data = data[data.index >= pd.Timestamp(start_date)]
        if end_date:
            data = data[data.index <= pd.Timestamp(end_date)]

        if data.empty:
            raise ValueError("No data in specified date range")

        # Ensure lowercase columns
        data.columns = data.columns.str.lower()

        # Initialize state
        self._state = EngineState(
            cash=self.config.initial_capital,
            peak_equity=self.config.initial_capital,
        )

        # Build evaluation context
        context = EvaluationContext(
            primary_data=data,
            signal_library=strategy.get("signals", {}),
            condition_library=strategy.get("conditions", {}),
            parameters=parameters or strategy.get("parameters", {}).get("defaults", {}),
        )

        # Extract rules from strategy
        rules = strategy.get("rules", [])
        constraints = strategy.get("constraints", {})

        # Pre-evaluate rule conditions
        rule_signals = self._precompute_rules(rules, context)

        # Simulate day by day
        for i, (idx, row) in enumerate(data.iterrows()):
            current_date = idx.date() if hasattr(idx, "date") else idx
            current_price = row["close"]

            # Update position values
            self._update_positions(symbol, current_price, current_date)

            # Check exit conditions (stop loss, take profit)
            self._check_exits(symbol, current_price, current_date, constraints, row)

            # Process rules in priority order
            for rule_idx, rule in enumerate(rules):
                if rule_signals[rule_idx].iloc[i]:
                    self._execute_rule(
                        rule, symbol, current_price, current_date, row, context
                    )

            # Record portfolio state
            self._record_snapshot(current_date, current_price, symbol)

        # Close any remaining positions at end
        if self._state.positions:
            final_price = data.iloc[-1]["close"]
            final_date = data.index[-1].date() if hasattr(data.index[-1], "date") else data.index[-1]
            for sym in list(self._state.positions.keys()):
                self._close_position(sym, final_price, final_date, "end_of_backtest")

        # Build result
        strategy_id = strategy.get("info", {}).get("id", "unknown")
        actual_start = data.index[0].date() if hasattr(data.index[0], "date") else data.index[0]
        actual_end = data.index[-1].date() if hasattr(data.index[-1], "date") else data.index[-1]

        equity_series = pd.Series(
            {d: eq for d, eq in self._state.equity_curve},
            name="equity",
        )

        return BacktestResult(
            strategy_id=strategy_id,
            symbol=symbol,
            start_date=actual_start,
            end_date=actual_end,
            initial_capital=self.config.initial_capital,
            final_equity=self._get_equity(data.iloc[-1]["close"] if not data.empty else 0, symbol),
            trades=self._state.trades,
            portfolio_history=self._state.portfolio_history,
            equity_curve=equity_series,
            parameters=parameters,
        )

    def _precompute_rules(
        self, rules: list[dict], context: EvaluationContext
    ) -> list[pd.Series]:
        """Pre-compute rule conditions for all bars."""
        signals = []
        for rule in rules:
            condition = rule.get("when", {"type": "always"})
            try:
                signal = self.condition_evaluator.evaluate_condition(condition, context)
                signals.append(signal)
            except Exception as e:
                logger.warning(f"Failed to evaluate rule condition: {e}")
                signals.append(pd.Series(False, index=context.primary_data.index))
        return signals

    def _execute_rule(
        self,
        rule: dict,
        symbol: str,
        price: float,
        current_date: date,
        row: pd.Series,
        context: EvaluationContext,
    ) -> None:
        """Execute a triggered rule."""
        action = rule.get("then", {})
        action_type = action.get("type", "trade")

        if action_type == "trade":
            self._execute_trade(action, symbol, price, current_date, row, context)
        elif action_type == "rebalance":
            logger.debug("Rebalance action not yet implemented")
        elif action_type == "alert":
            logger.info(f"Alert: {action.get('message', 'Signal triggered')}")
        elif action_type == "hold":
            pass  # Explicit no-op

    def _execute_trade(
        self,
        action: dict,
        symbol: str,
        price: float,
        current_date: date,
        row: pd.Series,
        context: EvaluationContext,
    ) -> None:
        """Execute a trade action."""
        direction = action.get("direction", "buy")
        sizing = action.get("sizing", {"type": "percent_of_equity", "value": 10})

        # Calculate position size
        quantity = self._calculate_size(sizing, price, direction, context)
        if quantity <= 0:
            return

        # Apply commission and slippage
        commission = price * quantity * self.config.commission_rate
        slippage = price * quantity * self.config.slippage_rate

        if direction in ["buy", "long"]:
            if symbol in self._state.positions:
                # Already have position
                return

            total_cost = price * quantity + commission + slippage
            if total_cost > self._state.cash:
                # Adjust size to available cash
                quantity = (self._state.cash - commission - slippage) / price
                if quantity <= 0:
                    return
                total_cost = price * quantity + commission + slippage

            self._state.cash -= total_cost
            self._state.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=price,
                direction="long",
                entry_date=current_date,
            )

            trade = Trade(
                symbol=symbol,
                direction="long",
                entry_date=current_date,
                entry_price=price,
                quantity=quantity,
                commission=commission,
                slippage=slippage,
                entry_reason=action.get("reason", "rule_triggered"),
            )
            self._state.trades.append(trade)

        elif direction in ["sell", "close"]:
            if symbol not in self._state.positions:
                return
            self._close_position(symbol, price, current_date, "sell_signal")

        elif direction == "short":
            logger.debug("Short selling not yet implemented")

    def _calculate_size(
        self,
        sizing: dict,
        price: float,
        direction: str,
        context: EvaluationContext,
    ) -> float:
        """Calculate position size based on sizing config."""
        sizing_type = sizing.get("type", "percent_of_equity")
        value = sizing.get("value", 10)

        if sizing_type == "fixed_amount":
            return value / price

        elif sizing_type == "fixed_quantity":
            return value

        elif sizing_type == "percent_of_equity":
            equity = self._state.cash
            for pos in self._state.positions.values():
                equity += pos.quantity * pos.avg_price  # Rough estimate
            target_value = equity * (value / 100)
            return target_value / price

        elif sizing_type == "percent_of_cash":
            target_value = self._state.cash * (value / 100)
            return target_value / price

        else:
            # Default to 10% of equity
            return (self._state.cash * 0.10) / price

    def _close_position(
        self, symbol: str, price: float, current_date: date, reason: str
    ) -> None:
        """Close an existing position."""
        if symbol not in self._state.positions:
            return

        position = self._state.positions.pop(symbol)
        commission = price * position.quantity * self.config.commission_rate
        slippage = price * position.quantity * self.config.slippage_rate

        # Find the open trade
        for trade in reversed(self._state.trades):
            if trade.symbol == symbol and trade.is_open:
                trade.close(
                    exit_date=current_date,
                    exit_price=price,
                    reason=reason,
                    commission=commission,
                    slippage=slippage,
                )
                break

        # Return cash
        self._state.cash += price * position.quantity - commission - slippage

    def _update_positions(
        self, symbol: str, price: float, current_date: date
    ) -> None:
        """Update position unrealized P&L."""
        for pos in self._state.positions.values():
            if pos.symbol == symbol:
                pos.update_unrealized(price, current_date)

    def _check_exits(
        self,
        symbol: str,
        price: float,
        current_date: date,
        constraints: dict,
        row: pd.Series,
    ) -> None:
        """Check stop loss and take profit conditions."""
        if symbol not in self._state.positions:
            return

        position = self._state.positions[symbol]
        entry_price = position.avg_price

        # Stop loss
        stop_loss = constraints.get("stop_loss", {})
        if stop_loss:
            sl_pct = stop_loss.get("percentage")
            if sl_pct:
                sl_price = entry_price * (1 - sl_pct / 100)
                if price <= sl_price:
                    self._close_position(symbol, price, current_date, "stop_loss")
                    return

        # Take profit
        take_profit = constraints.get("take_profit", {})
        if take_profit:
            tp_pct = take_profit.get("percentage")
            if tp_pct:
                tp_price = entry_price * (1 + tp_pct / 100)
                if price >= tp_price:
                    self._close_position(symbol, price, current_date, "take_profit")
                    return

        # Trailing stop
        trailing_stop = constraints.get("trailing_stop", {})
        if trailing_stop:
            ts_pct = trailing_stop.get("percentage")
            if ts_pct and position.unrealized_pnl > 0:
                # Calculate trailing stop from peak
                peak_price = entry_price + (position.unrealized_pnl / position.quantity)
                ts_price = peak_price * (1 - ts_pct / 100)
                if price <= ts_price:
                    self._close_position(symbol, price, current_date, "trailing_stop")
                    return

    def _get_equity(self, current_price: float, symbol: str) -> float:
        """Calculate current equity."""
        equity = self._state.cash
        for pos in self._state.positions.values():
            if pos.symbol == symbol:
                equity += pos.quantity * current_price
            else:
                equity += pos.quantity * pos.avg_price
        return equity

    def _record_snapshot(
        self, current_date: date, current_price: float, symbol: str
    ) -> None:
        """Record portfolio snapshot."""
        equity = self._get_equity(current_price, symbol)
        positions_value = equity - self._state.cash

        # Track peak for drawdown
        if equity > self._state.peak_equity:
            self._state.peak_equity = equity

        drawdown = self._state.peak_equity - equity
        drawdown_pct = (drawdown / self._state.peak_equity) * 100 if self._state.peak_equity > 0 else 0

        snapshot = PortfolioSnapshot(
            date=current_date,
            cash=self._state.cash,
            positions_value=positions_value,
            equity=equity,
            drawdown=drawdown,
            drawdown_pct=drawdown_pct,
        )
        self._state.portfolio_history.append(snapshot)
        self._state.equity_curve.append((current_date, equity))

    def run_batch(
        self,
        strategy: dict[str, Any],
        data: pd.DataFrame,
        symbols: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
        parameters: dict[str, float] | None = None,
    ) -> list[BacktestResult]:
        """Run backtest for multiple symbols.

        Args:
            strategy: UTSS strategy definition
            data: Dict mapping symbol to OHLCV DataFrame
            symbols: List of symbols to backtest
            start_date: Backtest start date
            end_date: Backtest end date
            parameters: Strategy parameters

        Returns:
            List of BacktestResults
        """
        results = []
        for symbol in symbols:
            try:
                result = self.run(
                    strategy=strategy,
                    data=data,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    parameters=parameters,
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Backtest failed for {symbol}: {e}")
        return results
