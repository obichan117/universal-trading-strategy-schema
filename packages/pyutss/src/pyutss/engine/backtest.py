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
                        rule, symbol, current_price, current_date, row, context, constraints
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
        constraints: dict | None = None,
    ) -> None:
        """Execute a triggered rule."""
        action = rule.get("then", {})
        action_type = action.get("type", "trade")

        if action_type == "trade":
            self._execute_trade(action, symbol, price, current_date, row, context, constraints)
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
        constraints: dict | None = None,
    ) -> None:
        """Execute a trade action."""
        direction = action.get("direction", "buy")
        sizing = action.get("sizing", {"type": "percent_of_equity", "value": 10})
        constraints = constraints or {}

        # Check max_positions constraint before opening new position
        if direction in ["buy", "long", "short"]:
            max_positions = constraints.get("max_positions")
            if max_positions and len(self._state.positions) >= max_positions:
                logger.debug(f"Max positions ({max_positions}) reached, skipping trade")
                return

            # Check max_drawdown constraint
            max_dd = constraints.get("max_drawdown", {})
            max_dd_pct = max_dd.get("percent") or max_dd.get("percentage")
            if max_dd_pct and self._state.peak_equity > 0:
                equity = self._state.cash
                for pos in self._state.positions.values():
                    equity += pos.quantity * pos.avg_price
                current_dd_pct = ((self._state.peak_equity - equity) / self._state.peak_equity) * 100
                if current_dd_pct >= max_dd_pct:
                    logger.debug(f"Max drawdown ({max_dd_pct}%) reached, skipping trade")
                    return

            # Check no_shorting constraint
            if direction == "short" and constraints.get("no_shorting", False):
                logger.debug("Short selling disabled by no_shorting constraint")
                return

        # Handle sell/close first (doesn't need size calculation)
        if direction in ["sell", "close"]:
            if symbol not in self._state.positions:
                return
            self._close_position(symbol, price, current_date, "sell_signal")
            return

        if direction == "cover":
            # Cover a short position
            if symbol not in self._state.positions:
                return
            position = self._state.positions[symbol]
            if position.direction != "short":
                return
            self._close_position(symbol, price, current_date, "cover_signal")
            return

        # Calculate position size (only for buy/long/short)
        quantity = self._calculate_size(sizing, price, direction, context, row)
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

        elif direction == "short":
            if symbol in self._state.positions:
                # Already have a position (long or short)
                return

            # Calculate position value for margin requirement
            position_value = price * quantity
            commission = position_value * self.config.commission_rate
            slippage = position_value * self.config.slippage_rate

            # For short selling, we receive cash but need margin
            # Simplified: require 50% margin (position value / 2)
            margin_required = position_value * 0.5
            if margin_required + commission + slippage > self._state.cash:
                # Adjust size to available margin
                available_margin = self._state.cash - commission - slippage
                quantity = (available_margin / 0.5) / price
                if quantity <= 0:
                    return
                position_value = price * quantity
                margin_required = position_value * 0.5
                commission = position_value * self.config.commission_rate
                slippage = position_value * self.config.slippage_rate

            # Reserve margin
            self._state.cash -= margin_required + commission + slippage

            self._state.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=price,
                direction="short",
                entry_date=current_date,
            )

            trade = Trade(
                symbol=symbol,
                direction="short",
                entry_date=current_date,
                entry_price=price,
                quantity=quantity,
                commission=commission,
                slippage=slippage,
                entry_reason=action.get("reason", "rule_triggered"),
            )
            self._state.trades.append(trade)

    def _calculate_size(
        self,
        sizing: dict,
        price: float,
        direction: str,
        context: EvaluationContext,
        row: pd.Series | None = None,
    ) -> float:
        """Calculate position size based on sizing config.

        Supports:
        - fixed_amount: Fixed dollar amount
        - fixed_quantity: Fixed number of shares
        - percent_of_equity: % of total portfolio value
        - percent_of_cash: % of available cash
        - percent_of_position: % of existing position (for pyramiding)
        - risk_based: Size based on stop loss distance (risk per trade)
        - kelly: Kelly criterion sizing
        - volatility_adjusted: ATR-based sizing
        """
        sizing_type = sizing.get("type", "percent_of_equity")
        value = sizing.get("value") or sizing.get("percent", 10)

        # Calculate current equity
        equity = self._state.cash
        for pos in self._state.positions.values():
            equity += pos.quantity * pos.avg_price

        if sizing_type == "fixed_amount":
            return value / price

        elif sizing_type == "fixed_quantity":
            return value

        elif sizing_type == "percent_of_equity":
            target_value = equity * (value / 100)
            return target_value / price

        elif sizing_type == "percent_of_cash":
            target_value = self._state.cash * (value / 100)
            return target_value / price

        elif sizing_type == "percent_of_position":
            # Size as % of existing position (for adding to position)
            symbol = sizing.get("symbol")
            if symbol and symbol in self._state.positions:
                existing_qty = self._state.positions[symbol].quantity
                return existing_qty * (value / 100)
            return 0.0

        elif sizing_type == "risk_based":
            # Size based on max risk per trade
            # risk_percent: max % of equity to risk
            # stop_loss_pct: stop loss distance %
            risk_percent = sizing.get("risk_percent", 1.0)  # Risk 1% of equity
            stop_loss_pct = sizing.get("stop_loss_percent", 2.0)  # 2% stop loss

            max_risk = equity * (risk_percent / 100)
            risk_per_share = price * (stop_loss_pct / 100)

            if risk_per_share > 0:
                return max_risk / risk_per_share
            return 0.0

        elif sizing_type == "kelly":
            # Kelly Criterion: f* = (bp - q) / b
            # b = odds (avg_win / avg_loss)
            # p = probability of winning
            # q = probability of losing (1 - p)
            # Use historical trade data or defaults
            win_rate = sizing.get("win_rate", 0.5)  # Default 50%
            avg_win = sizing.get("avg_win", 1.0)
            avg_loss = sizing.get("avg_loss", 1.0)

            # Calculate from trade history if available
            closed_trades = [t for t in self._state.trades if not t.is_open]
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

                # Apply Kelly fraction with optional multiplier (half-Kelly common)
                kelly_multiplier = sizing.get("multiplier", 0.5)
                kelly_fraction = max(0, kelly_fraction * kelly_multiplier)
                kelly_fraction = min(kelly_fraction, 0.25)  # Cap at 25%

                target_value = equity * kelly_fraction
                return target_value / price

            return (equity * 0.02) / price  # Default 2%

        elif sizing_type == "volatility_adjusted":
            # Size inversely proportional to volatility (ATR)
            # Target a fixed dollar risk per unit of ATR
            target_risk = sizing.get("target_risk", equity * 0.01)  # 1% of equity
            atr_period = sizing.get("atr_period", 14)

            # Calculate ATR from context data
            data = context.get_data()
            if len(data) >= atr_period and row is not None:
                from pyutss.engine.indicators import IndicatorService

                atr = IndicatorService.atr(
                    data["high"], data["low"], data["close"], atr_period
                )
                current_atr = atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else price * 0.02

                if current_atr > 0:
                    return target_risk / current_atr

            # Fallback: assume 2% ATR
            return target_risk / (price * 0.02)

        else:
            # Default to 10% of equity
            logger.debug(f"Unknown sizing type '{sizing_type}', using 10% of equity")
            return (equity * 0.10) / price

    def _close_position(
        self, symbol: str, price: float, current_date: date, reason: str
    ) -> None:
        """Close an existing position (long or short)."""
        if symbol not in self._state.positions:
            return

        position = self._state.positions.pop(symbol)
        position_value = price * position.quantity
        commission = position_value * self.config.commission_rate
        slippage = position_value * self.config.slippage_rate

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

        if position.direction == "long":
            # Long position: receive sale proceeds
            self._state.cash += position_value - commission - slippage
        else:
            # Short position: return margin and calculate P&L
            # P&L = (entry_price - exit_price) * quantity
            entry_value = position.avg_price * position.quantity
            pnl = entry_value - position_value  # Profit if price went down
            margin_returned = entry_value * 0.5  # Return the margin
            self._state.cash += margin_returned + pnl - commission - slippage

    def _update_positions(
        self, symbol: str, price: float, current_date: date
    ) -> None:
        """Update position unrealized P&L for both long and short positions."""
        for pos in self._state.positions.values():
            if pos.symbol == symbol:
                if pos.direction == "long":
                    # Long: profit when price goes up
                    pos.unrealized_pnl = (price - pos.avg_price) * pos.quantity
                else:
                    # Short: profit when price goes down
                    pos.unrealized_pnl = (pos.avg_price - price) * pos.quantity

                # Update days held
                if hasattr(pos, 'entry_date') and pos.entry_date:
                    pos.days_held = (current_date - pos.entry_date).days

    def _check_exits(
        self,
        symbol: str,
        price: float,
        current_date: date,
        constraints: dict,
        row: pd.Series,
    ) -> None:
        """Check stop loss and take profit conditions for long and short positions."""
        if symbol not in self._state.positions:
            return

        position = self._state.positions[symbol]
        entry_price = position.avg_price
        is_long = position.direction == "long"

        # Stop loss
        stop_loss = constraints.get("stop_loss", {})
        if stop_loss:
            sl_pct = stop_loss.get("percentage") or stop_loss.get("percent")
            if sl_pct:
                if is_long:
                    # Long: stop loss below entry
                    sl_price = entry_price * (1 - sl_pct / 100)
                    if price <= sl_price:
                        self._close_position(symbol, price, current_date, "stop_loss")
                        return
                else:
                    # Short: stop loss above entry
                    sl_price = entry_price * (1 + sl_pct / 100)
                    if price >= sl_price:
                        self._close_position(symbol, price, current_date, "stop_loss")
                        return

        # Take profit
        take_profit = constraints.get("take_profit", {})
        if take_profit:
            tp_pct = take_profit.get("percentage") or take_profit.get("percent")
            if tp_pct:
                if is_long:
                    # Long: take profit above entry
                    tp_price = entry_price * (1 + tp_pct / 100)
                    if price >= tp_price:
                        self._close_position(symbol, price, current_date, "take_profit")
                        return
                else:
                    # Short: take profit below entry
                    tp_price = entry_price * (1 - tp_pct / 100)
                    if price <= tp_price:
                        self._close_position(symbol, price, current_date, "take_profit")
                        return

        # Trailing stop
        trailing_stop = constraints.get("trailing_stop", {})
        if trailing_stop:
            ts_pct = trailing_stop.get("percentage") or trailing_stop.get("percent")
            if ts_pct and position.unrealized_pnl > 0:
                if is_long:
                    # Long: trail from peak price
                    peak_price = entry_price + (position.unrealized_pnl / position.quantity)
                    ts_price = peak_price * (1 - ts_pct / 100)
                    if price <= ts_price:
                        self._close_position(symbol, price, current_date, "trailing_stop")
                        return
                else:
                    # Short: trail from trough price
                    trough_price = entry_price - (position.unrealized_pnl / position.quantity)
                    ts_price = trough_price * (1 + ts_pct / 100)
                    if price >= ts_price:
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
