"""Portfolio backtester for multi-symbol strategies.

Provides portfolio-level backtesting with shared capital pool and rebalancing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import pandas as pd

from pyutss.portfolio.rebalancer import RebalanceConfig, RebalanceFrequency, Rebalancer
from pyutss.portfolio.result import PortfolioResult
from pyutss.portfolio.weights import EqualWeight, WeightScheme
from pyutss.results.types import BacktestResult, PortfolioSnapshot, Trade

logger = logging.getLogger(__name__)


@dataclass
class PortfolioConfig:
    """Configuration for portfolio backtesting."""

    initial_capital: float = 100000.0
    commission_rate: float = 0.001
    slippage_rate: float = 0.0005
    risk_free_rate: float = 0.0

    # Rebalancing
    rebalance: str = "monthly"  # "daily", "weekly", "monthly", "quarterly", "yearly", "never"
    rebalance_threshold_pct: float | None = None  # Threshold for drift rebalancing

    # Position limits
    max_position_pct: float = 1.0  # Max % of portfolio per symbol (1.0 = 100%)
    min_position_pct: float = 0.0  # Min % if position exists


@dataclass
class PortfolioState:
    """Internal state for portfolio backtesting."""

    cash: float
    positions: dict[str, float] = field(default_factory=dict)  # symbol -> quantity
    position_values: dict[str, float] = field(default_factory=dict)  # symbol -> value
    trades: list[Trade] = field(default_factory=list)
    history: list[PortfolioSnapshot] = field(default_factory=list)
    weights_history: list[dict[str, float]] = field(default_factory=list)
    equity_history: list[tuple[date, float]] = field(default_factory=list)
    peak_equity: float = 0.0
    total_turnover: float = 0.0
    rebalance_count: int = 0


class PortfolioBacktester:
    """Multi-symbol portfolio backtester with shared capital.

    Runs strategy across multiple symbols with shared capital pool,
    supporting various weight schemes and rebalancing frequencies.

    Example:
        from pyutss.portfolio import PortfolioBacktester, PortfolioConfig

        config = PortfolioConfig(
            initial_capital=100000,
            rebalance="monthly",
        )
        backtester = PortfolioBacktester(config)

        result = backtester.run(
            strategy=strategy,
            data={"AAPL": aapl_df, "MSFT": msft_df, "GOOGL": googl_df},
            start_date=date(2020, 1, 1),
            end_date=date(2024, 1, 1),
            weights="equal",
        )
    """

    def __init__(self, config: PortfolioConfig | None = None) -> None:
        """Initialize portfolio backtester.

        Args:
            config: Portfolio configuration
        """
        self.config = config or PortfolioConfig()
        self._state: PortfolioState | None = None
        self._rebalancer: Rebalancer | None = None
        self._weight_scheme: WeightScheme | None = None

    def reset(self) -> None:
        """Reset backtester state."""
        self._state = None
        if self._rebalancer:
            self._rebalancer.reset()

    def run(
        self,
        strategy: dict[str, Any],
        data: dict[str, pd.DataFrame],
        start_date: date | None = None,
        end_date: date | None = None,
        weights: str | WeightScheme | dict[str, float] = "equal",
        parameters: dict[str, float] | None = None,
    ) -> PortfolioResult:
        """Run portfolio backtest across multiple symbols.

        Args:
            strategy: UTSS strategy definition
            data: Dict mapping symbol to OHLCV DataFrame
            start_date: Backtest start date
            end_date: Backtest end date
            weights: Weight scheme - "equal", "inverse_vol", "risk_parity",
                    WeightScheme instance, or dict of fixed weights
            parameters: Strategy parameters

        Returns:
            PortfolioResult with portfolio-level metrics
        """
        self.reset()

        symbols = list(data.keys())
        if not symbols:
            raise ValueError("No data provided")

        # Setup weight scheme
        self._weight_scheme = self._get_weight_scheme(weights)

        # Setup rebalancer
        freq = RebalanceFrequency(self.config.rebalance)
        rebal_config = RebalanceConfig(
            frequency=freq,
            threshold_pct=self.config.rebalance_threshold_pct,
        )
        self._rebalancer = Rebalancer(rebal_config)

        # Filter and align data
        aligned_data = self._align_data(data, start_date, end_date)
        if not aligned_data:
            raise ValueError("No overlapping data across symbols")

        # Get common date range
        all_dates = set()
        for df in aligned_data.values():
            all_dates.update(df.index.tolist())
        all_dates = sorted(all_dates)

        if not all_dates:
            raise ValueError("No trading dates in data")

        # Initialize state
        self._state = PortfolioState(
            cash=self.config.initial_capital,
            peak_equity=self.config.initial_capital,
        )

        # Pre-compute signals for each symbol
        symbol_signals = {}
        for symbol, df in aligned_data.items():
            try:
                from pyutss.engine.evaluator import ConditionEvaluator, EvaluationContext, SignalEvaluator

                context = EvaluationContext(
                    primary_data=df,
                    signal_library=strategy.get("signals", {}),
                    condition_library=strategy.get("conditions", {}),
                    parameters=parameters or strategy.get("parameters", {}).get("defaults", {}),
                )

                signal_eval = SignalEvaluator()
                cond_eval = ConditionEvaluator(signal_eval)

                rules = strategy.get("rules", [])
                rule_signals = []
                for rule in rules:
                    condition = rule.get("when", {"type": "always"})
                    try:
                        signal = cond_eval.evaluate_condition(condition, context)
                        rule_signals.append(signal)
                    except Exception:
                        rule_signals.append(pd.Series(False, index=df.index))

                symbol_signals[symbol] = {
                    "rules": rules,
                    "signals": rule_signals,
                    "data": df,
                }
            except Exception as e:
                logger.warning(f"Failed to compute signals for {symbol}: {e}")

        # Get target weights for initial allocation
        first_date = pd.Timestamp(all_dates[0])
        target_weights = self._weight_scheme.calculate(
            symbols, aligned_data, first_date
        )

        # Simulate day by day
        per_symbol_trades: dict[str, list[Trade]] = {s: [] for s in symbols}
        weights_history = []

        for i, dt in enumerate(all_dates):
            current_date = dt.date() if hasattr(dt, "date") else dt
            ts = pd.Timestamp(dt)

            # Get current prices
            prices = {}
            for symbol, df in aligned_data.items():
                if ts in df.index:
                    prices[symbol] = df.loc[ts, "close"]

            if not prices:
                continue

            # Update position values
            self._update_positions(prices)

            # Check for rebalancing
            current_weights = self._get_current_weights()
            if self._rebalancer.should_rebalance(current_date, current_weights, target_weights):
                target_weights = self._weight_scheme.calculate(
                    symbols, aligned_data, ts
                )
                turnover = self._rebalance(symbols, prices, target_weights, current_date)
                self._state.total_turnover += turnover
                self._state.rebalance_count += 1

            # Process strategy signals for each symbol
            constraints = strategy.get("constraints", {})
            for symbol, sig_data in symbol_signals.items():
                if ts not in sig_data["data"].index:
                    continue

                idx = sig_data["data"].index.get_loc(ts)
                price = prices.get(symbol, 0)

                for rule_idx, rule in enumerate(sig_data["rules"]):
                    if sig_data["signals"][rule_idx].iloc[idx]:
                        trade = self._process_signal(
                            rule=rule,
                            symbol=symbol,
                            price=price,
                            current_date=current_date,
                            target_weight=target_weights.get(symbol, 0),
                            constraints=constraints,
                        )
                        if trade:
                            per_symbol_trades[symbol].append(trade)

            # Check stop loss / take profit
            self._check_exits(prices, current_date, constraints, per_symbol_trades)

            # Record snapshot
            self._record_snapshot(current_date, prices, target_weights)
            weights_history.append({"date": current_date, **current_weights})

        # Close remaining positions
        final_prices = {}
        for symbol, df in aligned_data.items():
            if len(df) > 0:
                final_prices[symbol] = df.iloc[-1]["close"]

        final_date = all_dates[-1].date() if hasattr(all_dates[-1], "date") else all_dates[-1]
        for symbol in list(self._state.positions.keys()):
            if symbol in final_prices:
                trade = self._close_position(symbol, final_prices[symbol], final_date, "end_of_backtest")
                if trade:
                    per_symbol_trades[symbol].append(trade)

        # Build per-symbol results
        per_symbol_results = {}
        for symbol in symbols:
            symbol_df = aligned_data.get(symbol)
            if symbol_df is None or symbol_df.empty:
                continue

            # Build equity curve for this symbol from trades
            symbol_trades = per_symbol_trades.get(symbol, [])
            initial = self.config.initial_capital / len(symbols)

            # Simple equity calculation from trades
            symbol_equity = []
            equity = initial
            trade_pnl = {}
            for trade in symbol_trades:
                if not trade.is_open:
                    trade_pnl[trade.exit_date] = trade.pnl

            for dt in symbol_df.index:
                d = dt.date() if hasattr(dt, "date") else dt
                if d in trade_pnl:
                    equity += trade_pnl[d]
                symbol_equity.append((dt, equity))

            equity_series = pd.Series(
                {d: eq for d, eq in symbol_equity},
                name="equity",
            )

            actual_start = symbol_df.index[0].date() if hasattr(symbol_df.index[0], "date") else symbol_df.index[0]
            actual_end = symbol_df.index[-1].date() if hasattr(symbol_df.index[-1], "date") else symbol_df.index[-1]

            per_symbol_results[symbol] = BacktestResult(
                strategy_id=strategy.get("info", {}).get("id", "unknown"),
                symbol=symbol,
                start_date=actual_start,
                end_date=actual_end,
                initial_capital=initial,
                final_equity=equity,
                trades=symbol_trades,
                equity_curve=equity_series,
                parameters=parameters,
            )

        # Build weights DataFrame
        weights_df = pd.DataFrame(weights_history)
        if not weights_df.empty and "date" in weights_df.columns:
            weights_df = weights_df.set_index("date")

        # Build portfolio equity curve
        equity_series = pd.Series(
            {d: eq for d, eq in self._state.equity_history},
            name="equity",
        )

        # Calculate average turnover
        avg_turnover = (
            self._state.total_turnover / self._state.rebalance_count
            if self._state.rebalance_count > 0
            else 0
        )

        actual_start = all_dates[0].date() if hasattr(all_dates[0], "date") else all_dates[0]
        actual_end = all_dates[-1].date() if hasattr(all_dates[-1], "date") else all_dates[-1]

        return PortfolioResult(
            strategy_id=strategy.get("info", {}).get("id", "unknown"),
            symbols=symbols,
            start_date=actual_start,
            end_date=actual_end,
            initial_capital=self.config.initial_capital,
            final_equity=self._get_equity(final_prices),
            equity_curve=equity_series,
            portfolio_weights=weights_df,
            per_symbol_results=per_symbol_results,
            rebalance_count=self._state.rebalance_count,
            turnover=avg_turnover,
            parameters=parameters,
            weight_scheme=self._get_weight_scheme_name(weights),
            rebalance_frequency=self.config.rebalance,
        )

    def _get_weight_scheme(
        self,
        weights: str | WeightScheme | dict[str, float],
    ) -> WeightScheme:
        """Get weight scheme from specification."""
        if isinstance(weights, WeightScheme):
            return weights

        if isinstance(weights, dict):
            from pyutss.portfolio.weights import TargetWeights
            return TargetWeights(weights)

        if weights == "equal":
            return EqualWeight()

        if weights == "inverse_vol":
            from pyutss.portfolio.weights import InverseVolatility
            return InverseVolatility()

        if weights == "risk_parity":
            from pyutss.portfolio.weights import RiskParity
            return RiskParity()

        # Default to equal weight
        return EqualWeight()

    def _get_weight_scheme_name(
        self,
        weights: str | WeightScheme | dict[str, float],
    ) -> str:
        """Get name of weight scheme."""
        if isinstance(weights, str):
            return weights
        if isinstance(weights, dict):
            return "custom"
        return weights.__class__.__name__

    def _align_data(
        self,
        data: dict[str, pd.DataFrame],
        start_date: date | None,
        end_date: date | None,
    ) -> dict[str, pd.DataFrame]:
        """Filter and align data across symbols."""
        result = {}

        for symbol, df in data.items():
            df = df.copy()

            # Ensure datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            # Lowercase columns
            df.columns = df.columns.str.lower()

            # Filter by date
            if start_date:
                df = df[df.index >= pd.Timestamp(start_date)]
            if end_date:
                df = df[df.index <= pd.Timestamp(end_date)]

            if not df.empty:
                result[symbol] = df

        return result

    def _update_positions(self, prices: dict[str, float]) -> None:
        """Update position values based on current prices."""
        for symbol, qty in self._state.positions.items():
            if symbol in prices:
                self._state.position_values[symbol] = qty * prices[symbol]

    def _get_equity(self, prices: dict[str, float] | None = None) -> float:
        """Calculate current portfolio equity."""
        equity = self._state.cash

        for symbol, qty in self._state.positions.items():
            if prices and symbol in prices:
                equity += qty * prices[symbol]
            elif symbol in self._state.position_values:
                equity += self._state.position_values[symbol]

        return equity

    def _get_current_weights(self) -> dict[str, float]:
        """Get current portfolio weights."""
        equity = self._get_equity()
        if equity <= 0:
            return {}

        weights = {}
        for symbol, value in self._state.position_values.items():
            weights[symbol] = value / equity

        return weights

    def _rebalance(
        self,
        symbols: list[str],
        prices: dict[str, float],
        target_weights: dict[str, float],
        current_date: date,
    ) -> float:
        """Rebalance portfolio to target weights.

        Returns turnover as percentage.
        """
        equity = self._get_equity(prices)
        turnover = 0.0

        for symbol in symbols:
            target_weight = target_weights.get(symbol, 0)
            target_value = equity * target_weight
            target_qty = target_value / prices[symbol] if prices.get(symbol, 0) > 0 else 0

            current_qty = self._state.positions.get(symbol, 0)
            delta_qty = target_qty - current_qty

            if abs(delta_qty) < 0.01:
                continue

            price = prices[symbol]
            trade_value = abs(delta_qty * price)

            # Apply commission and slippage
            commission = trade_value * self.config.commission_rate
            slippage = trade_value * self.config.slippage_rate

            if delta_qty > 0:
                # Buy
                cost = delta_qty * price + commission + slippage
                if cost <= self._state.cash:
                    self._state.cash -= cost
                    self._state.positions[symbol] = current_qty + delta_qty
                    self._state.position_values[symbol] = self._state.positions[symbol] * price
            else:
                # Sell
                proceeds = abs(delta_qty) * price - commission - slippage
                self._state.cash += proceeds
                self._state.positions[symbol] = current_qty + delta_qty
                if self._state.positions[symbol] <= 0:
                    del self._state.positions[symbol]
                    if symbol in self._state.position_values:
                        del self._state.position_values[symbol]
                else:
                    self._state.position_values[symbol] = self._state.positions[symbol] * price

            turnover += trade_value / equity if equity > 0 else 0

        return turnover * 100

    def _process_signal(
        self,
        rule: dict,
        symbol: str,
        price: float,
        current_date: date,
        target_weight: float,
        constraints: dict,
    ) -> Trade | None:
        """Process a strategy signal for a symbol."""
        action = rule.get("then", {})
        direction = action.get("direction", "buy")

        # Only handle explicit close/sell signals
        # Position sizing is handled by rebalancing
        if direction in ["sell", "close"]:
            return self._close_position(symbol, price, current_date, "sell_signal")

        return None

    def _close_position(
        self,
        symbol: str,
        price: float,
        current_date: date,
        reason: str,
    ) -> Trade | None:
        """Close position for a symbol."""
        if symbol not in self._state.positions:
            return None

        qty = self._state.positions.pop(symbol)
        if symbol in self._state.position_values:
            del self._state.position_values[symbol]

        proceeds = qty * price
        commission = proceeds * self.config.commission_rate
        slippage = proceeds * self.config.slippage_rate
        self._state.cash += proceeds - commission - slippage

        # Find entry trade
        entry_price = price  # Default
        entry_date = current_date

        for trade in reversed(self._state.trades):
            if trade.symbol == symbol and trade.is_open:
                entry_price = trade.entry_price
                entry_date = trade.entry_date
                trade.close(
                    exit_date=current_date,
                    exit_price=price,
                    reason=reason,
                    commission=commission,
                    slippage=slippage,
                )
                return trade

        # Create synthetic trade if no open trade found
        trade = Trade(
            symbol=symbol,
            direction="long",
            entry_date=entry_date,
            entry_price=entry_price,
            quantity=qty,
            exit_date=current_date,
            exit_price=price,
            commission=commission,
            slippage=slippage,
            is_open=False,
            exit_reason=reason,
        )
        trade.pnl = (price - entry_price) * qty - commission - slippage
        return trade

    def _check_exits(
        self,
        prices: dict[str, float],
        current_date: date,
        constraints: dict,
        per_symbol_trades: dict[str, list[Trade]],
    ) -> None:
        """Check stop loss / take profit for all positions."""
        stop_loss = constraints.get("stop_loss", {})
        take_profit = constraints.get("take_profit", {})

        sl_pct = stop_loss.get("percentage") or stop_loss.get("percent")
        tp_pct = take_profit.get("percentage") or take_profit.get("percent")

        for symbol in list(self._state.positions.keys()):
            if symbol not in prices:
                continue

            price = prices[symbol]

            # Find entry price from trades
            entry_price = price
            for trade in reversed(self._state.trades):
                if trade.symbol == symbol and trade.is_open:
                    entry_price = trade.entry_price
                    break

            should_exit = False
            reason = ""

            if sl_pct:
                sl_price = entry_price * (1 - sl_pct / 100)
                if price <= sl_price:
                    should_exit = True
                    reason = "stop_loss"

            if tp_pct and not should_exit:
                tp_price = entry_price * (1 + tp_pct / 100)
                if price >= tp_price:
                    should_exit = True
                    reason = "take_profit"

            if should_exit:
                trade = self._close_position(symbol, price, current_date, reason)
                if trade:
                    per_symbol_trades[symbol].append(trade)

    def _record_snapshot(
        self,
        current_date: date,
        prices: dict[str, float],
        weights: dict[str, float],
    ) -> None:
        """Record portfolio snapshot."""
        equity = self._get_equity(prices)
        positions_value = sum(self._state.position_values.values())

        if equity > self._state.peak_equity:
            self._state.peak_equity = equity

        drawdown = self._state.peak_equity - equity
        drawdown_pct = (drawdown / self._state.peak_equity * 100) if self._state.peak_equity > 0 else 0

        snapshot = PortfolioSnapshot(
            date=current_date,
            cash=self._state.cash,
            positions_value=positions_value,
            equity=equity,
            drawdown=drawdown,
            drawdown_pct=drawdown_pct,
        )
        self._state.history.append(snapshot)
        self._state.equity_history.append((current_date, equity))
