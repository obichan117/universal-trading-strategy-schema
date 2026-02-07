"""Unified backtesting engine for UTSS strategies.

Single `Engine` class that handles both single-symbol and multi-symbol
strategies with a unified API. Replaces `BacktestEngine` and
`PortfolioBacktester` with a single entry point.

Usage:
    from pyutss import Engine

    engine = Engine(initial_capital=100000)

    # Single symbol
    result = engine.backtest(strategy, data=df, symbol="AAPL")

    # Multi-symbol (determined by strategy universe or data dict)
    result = engine.backtest(strategy, data={"AAPL": df1, "MSFT": df2})

    # Auto-fetch from strategy universe
    result = engine.backtest(strategy, start_date="2020-01-01", end_date="2024-01-01")
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import pandas as pd
import yaml

from pyutss.engine.evaluator import (
    ConditionEvaluator,
    EvaluationContext,
    SignalEvaluator,
)
from pyutss.engine.executor import BacktestExecutor, OrderRequest
from pyutss.engine.portfolio import PortfolioManager
from pyutss.engine.sizing import calculate_size
from pyutss.portfolio.result import PortfolioResult
from pyutss.portfolio.weights import EqualWeight, WeightScheme
from pyutss.results.types import (
    BacktestConfig,
    BacktestResult,
)

logger = logging.getLogger(__name__)


class Engine:
    """Unified backtesting engine for UTSS strategies.

    Handles 1..N symbols with the same API. The number of symbols
    is determined by the strategy's universe or the provided data.

    Single-symbol strategies return BacktestResult.
    Multi-symbol strategies return PortfolioResult.
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        risk_free_rate: float = 0.0,
        lot_size: int = 1,
        config: BacktestConfig | None = None,
        executor: BacktestExecutor | None = None,
    ) -> None:
        """Initialize engine.

        Args:
            initial_capital: Starting capital
            commission_rate: Commission as fraction of trade value
            slippage_rate: Slippage as fraction of trade value
            risk_free_rate: Annual risk-free rate
            lot_size: Default lot size (1 for US, 100 for Japan)
            config: Legacy BacktestConfig (overrides other params if provided)
            executor: Custom executor for trade fills. If not provided,
                     a BacktestExecutor is created from the other params.
        """
        if config is not None:
            self.initial_capital = config.initial_capital
            self.commission_rate = config.commission_rate
            self.slippage_rate = config.slippage_rate
            self.risk_free_rate = config.risk_free_rate
            self.lot_size = lot_size
        else:
            self.initial_capital = initial_capital
            self.commission_rate = commission_rate
            self.slippage_rate = slippage_rate
            self.risk_free_rate = risk_free_rate
            self.lot_size = lot_size

        if executor is not None:
            self.executor = executor
        else:
            self.executor = BacktestExecutor(
                commission_rate=self.commission_rate,
                slippage_rate=self.slippage_rate,
                lot_size=self.lot_size,
            )

        self.signal_evaluator = SignalEvaluator()
        self.condition_evaluator = ConditionEvaluator(self.signal_evaluator)

    def backtest(
        self,
        strategy: dict[str, Any] | str,
        data: pd.DataFrame | dict[str, pd.DataFrame] | None = None,
        symbol: str | None = None,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        parameters: dict[str, float] | None = None,
        weights: str | WeightScheme | dict[str, float] = "equal",
        config: Any | None = None,
    ) -> BacktestResult | PortfolioResult:
        """Run a backtest.

        Args:
            strategy: UTSS strategy dict or path to YAML file
            data: OHLCV DataFrame (single) or dict of DataFrames (multi)
            symbol: Symbol name (for single-symbol with DataFrame)
            start_date: Backtest start date
            end_date: Backtest end date
            parameters: Strategy parameter overrides
            weights: Weight scheme for multi-symbol ("equal", "inverse_vol", etc.)
            config: BacktestSpec or path to backtest config YAML

        Returns:
            BacktestResult for single symbol, PortfolioResult for multiple
        """
        # Load strategy if path
        if isinstance(strategy, str):
            strategy = self._load_yaml(strategy)

        # Load backtest config if provided
        if isinstance(config, str):
            config = self._load_yaml(config)

        # Apply backtest config overrides
        if config and isinstance(config, dict):
            if start_date is None:
                start_date = config.get("start_date", start_date)
            if end_date is None:
                end_date = config.get("end_date", end_date)

        # Resolve symbols and data
        symbols, data_dict = self._resolve_data(strategy, data, symbol, start_date, end_date)

        if len(symbols) == 1 and symbol is not None:
            return self._run_single(
                strategy, data_dict[symbols[0]], symbols[0],
                start_date, end_date, parameters,
            )
        elif len(symbols) == 1:
            return self._run_single(
                strategy, data_dict[symbols[0]], symbols[0],
                start_date, end_date, parameters,
            )
        else:
            return self._run_multi(
                strategy, data_dict, symbols,
                start_date, end_date, parameters, weights,
            )

    # ─── Runners ─────────────────────────────────────────────

    def _run_single(
        self,
        strategy: dict,
        data: pd.DataFrame,
        symbol: str,
        start_date: date | str | None,
        end_date: date | str | None,
        parameters: dict[str, float] | None,
    ) -> BacktestResult:
        """Run single-symbol backtest (delegates to single_runner)."""
        from pyutss.engine.single_runner import run_single
        return run_single(self, strategy, data, symbol, start_date, end_date, parameters)

    def _run_multi(
        self,
        strategy: dict,
        data: dict[str, pd.DataFrame],
        symbols: list[str],
        start_date: date | str | None,
        end_date: date | str | None,
        parameters: dict[str, float] | None,
        weights: str | WeightScheme | dict[str, float],
    ) -> PortfolioResult:
        """Run multi-symbol portfolio backtest (delegates to portfolio_runner)."""
        from pyutss.engine.portfolio_runner import run_multi
        return run_multi(self, strategy, data, symbols, start_date, end_date, parameters, weights)

    # ─── Shared Logic ────────────────────────────────────────

    def _execute_rule(
        self,
        rule: dict,
        symbol: str,
        price: float,
        current_date: date,
        context: EvaluationContext,
        constraints: dict,
        pm: PortfolioManager,
        data: pd.DataFrame,
    ) -> None:
        """Execute a triggered rule."""
        action = rule.get("then", {})
        action_type = action.get("type", "trade")

        if action_type == "trade":
            self._execute_trade(action, symbol, price, current_date, context, constraints, pm, data)
        elif action_type == "alert":
            logger.info(f"Alert: {action.get('message', 'Signal triggered')}")
        elif action_type == "hold":
            pass

    def _execute_trade(
        self,
        action: dict,
        symbol: str,
        price: float,
        current_date: date,
        context: EvaluationContext,
        constraints: dict,
        pm: PortfolioManager,
        data: pd.DataFrame,
    ) -> None:
        """Execute a trade action via the Executor."""
        direction = action.get("direction", "buy")

        # Check constraints
        if direction in ("buy", "long", "short"):
            max_positions = constraints.get("max_positions")
            if max_positions and len(pm.positions) >= max_positions:
                return

            if direction == "short" and constraints.get("no_shorting", False):
                return

        # Handle sell/cover via executor
        if direction in ("sell", "close"):
            if symbol in pm.positions:
                qty = pm.positions[symbol].quantity
                order = OrderRequest(symbol=symbol, direction="sell", quantity=qty, price=price)
                fill = self.executor.execute(order)
                if fill:
                    pm.close_position(symbol, price, current_date, "sell_signal", fill.commission, fill.slippage)
            return

        if direction == "cover":
            if symbol in pm.positions and pm.positions[symbol].direction == "short":
                qty = pm.positions[symbol].quantity
                order = OrderRequest(symbol=symbol, direction="cover", quantity=qty, price=price)
                fill = self.executor.execute(order)
                if fill:
                    pm.close_position(symbol, price, current_date, "cover_signal", fill.commission, fill.slippage)
            return

        # Calculate size
        sizing = action.get("sizing", {"type": "percent_of_equity", "percent": 10})
        equity = pm.get_equity({symbol: price})

        quantity = calculate_size(
            sizing, price, equity, pm.cash,
            positions=pm.positions, trades=pm.trades, data=data,
        )

        if quantity <= 0:
            return

        # Execute through executor (handles lot rounding, commission, slippage)
        trade_direction = "buy" if direction in ("buy", "long") else "short"
        order = OrderRequest(
            symbol=symbol, direction=trade_direction, quantity=quantity, price=price,
        )
        fill = self.executor.execute(order)
        if fill is None:
            return

        pm_direction = "long" if direction in ("buy", "long") else "short"
        pm.open_position(
            symbol, fill.quantity, price, pm_direction, current_date,
            commission=fill.commission, slippage=fill.slippage,
            reason=action.get("reason", "rule_triggered"),
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

    def _build_context(
        self,
        strategy: dict,
        data: pd.DataFrame,
        parameters: dict[str, float] | None,
    ) -> EvaluationContext:
        """Build evaluation context from strategy and data."""
        return EvaluationContext(
            primary_data=data,
            signal_library=strategy.get("signals", {}),
            condition_library=strategy.get("conditions", {}),
            parameters=parameters or strategy.get("parameters", {}).get("defaults", {}),
        )

    # ─── Data Resolution ─────────────────────────────────────

    def _resolve_data(
        self,
        strategy: dict,
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
        symbols = self._resolve_universe_symbols(strategy)
        if not symbols:
            raise ValueError("No data provided and could not resolve symbols from strategy universe")

        data_dict = self._fetch_data(symbols, start_date, end_date)
        return symbols, data_dict

    def _resolve_universe_symbols(self, strategy: dict) -> list[str]:
        """Extract symbols from strategy universe."""
        from pyutss.engine.universe import UniverseResolver
        resolver = UniverseResolver()
        universe = strategy.get("universe", {})
        try:
            return resolver.resolve(universe)
        except (ValueError, Exception) as e:
            logger.warning(f"Failed to resolve universe: {e}")
            return []

    def _fetch_data(
        self,
        symbols: list[str],
        start_date: date | str | None,
        end_date: date | str | None,
    ) -> dict[str, pd.DataFrame]:
        """Fetch data for symbols using pyutss data sources."""
        if start_date is None or end_date is None:
            raise ValueError("start_date and end_date required when auto-fetching data")

        from pyutss.data.sources import download
        return download(symbols, start_date, end_date)

    # ─── Helpers ─────────────────────────────────────────────

    def _prepare_data(
        self,
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

    def _get_weight_scheme(
        self, weights: str | WeightScheme | dict[str, float]
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
        return EqualWeight()

    def _get_weight_scheme_name(
        self, weights: str | WeightScheme | dict[str, float]
    ) -> str:
        """Get name of weight scheme."""
        if isinstance(weights, str):
            return weights
        if isinstance(weights, dict):
            return "custom"
        return weights.__class__.__name__

    def _get_current_weights(
        self, pm: PortfolioManager, prices: dict[str, float]
    ) -> dict[str, float]:
        """Get current portfolio weights."""
        equity = pm.get_equity(prices)
        if equity <= 0:
            return {}
        weights = {}
        for symbol, pos in pm.positions.items():
            p = prices.get(symbol, pos.avg_price)
            weights[symbol] = (pos.quantity * p) / equity
        return weights

    def _rebalance(
        self,
        pm: PortfolioManager,
        symbols: list[str],
        prices: dict[str, float],
        target_weights: dict[str, float],
    ) -> float:
        """Rebalance portfolio to target weights. Returns turnover %."""
        equity = pm.get_equity(prices)
        turnover = 0.0

        for symbol in symbols:
            target_weight = target_weights.get(symbol, 0)
            target_value = equity * target_weight
            price = prices.get(symbol, 0)
            if price <= 0:
                continue

            target_qty = target_value / price
            current_qty = pm.positions[symbol].quantity if symbol in pm.positions else 0
            delta_qty = target_qty - current_qty

            if abs(delta_qty) < 0.01:
                continue

            if delta_qty > 0:
                # Buy more via executor
                order = OrderRequest(symbol=symbol, direction="buy", quantity=delta_qty, price=price)
                fill = self.executor.execute(order)
                if fill is None:
                    continue

                cost = fill.quantity * price + fill.commission + fill.slippage
                if cost <= pm.cash:
                    if symbol in pm.positions:
                        pos = pm.positions[symbol]
                        new_qty = pos.quantity + fill.quantity
                        pos.avg_price = (pos.avg_price * pos.quantity + price * fill.quantity) / new_qty
                        pos.quantity = new_qty
                        pm.cash -= cost
                    else:
                        pm.open_position(
                            symbol, fill.quantity, price, "long",
                            pm.portfolio_history[-1].date if pm.portfolio_history else date.today(),
                            commission=fill.commission, slippage=fill.slippage,
                            reason="rebalance",
                        )
                trade_value = fill.quantity * price
            else:
                # Sell some via executor
                abs_delta = abs(delta_qty)
                order = OrderRequest(symbol=symbol, direction="sell", quantity=abs_delta, price=price)
                fill = self.executor.execute(order)
                if fill is None:
                    continue

                if symbol in pm.positions:
                    pos = pm.positions[symbol]
                    if fill.quantity >= pos.quantity - 0.01:
                        d = pm.portfolio_history[-1].date if pm.portfolio_history else date.today()
                        pm.close_position(symbol, price, d, "rebalance", fill.commission, fill.slippage)
                    else:
                        proceeds = fill.quantity * price - fill.commission - fill.slippage
                        pm.cash += proceeds
                        pos.quantity -= fill.quantity
                trade_value = fill.quantity * price

            turnover += trade_value / equity if equity > 0 else 0

        return turnover * 100

    @staticmethod
    def _load_yaml(path: str) -> dict:
        """Load a YAML file."""
        with open(path) as f:
            return yaml.safe_load(f)
