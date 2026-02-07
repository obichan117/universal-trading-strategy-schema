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

from datetime import date
from typing import Any

import pandas as pd
import yaml

from pyutss.engine.data_resolver import prepare_data, resolve_data
from pyutss.engine.evaluator import (
    ConditionEvaluator,
    EvaluationContext,
    SignalEvaluator,
)
from pyutss.engine.executor import BacktestExecutor
from pyutss.engine.portfolio import PortfolioManager
from pyutss.engine.rule_executor import (
    build_context,
    execute_rule,
    precompute_rules,
)
from pyutss.engine.weight_manager import (
    get_current_weights,
    get_weight_scheme,
    get_weight_scheme_name,
    rebalance,
)
from pyutss.portfolio.result import PortfolioResult
from pyutss.portfolio.weights import WeightScheme
from pyutss.results.types import (
    BacktestConfig,
    BacktestResult,
)


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

    # ─── Thin wrappers (backward compatibility) ──────────────

    def _execute_rule(
        self, rule: dict, symbol: str, price: float, current_date: date,
        context: EvaluationContext, constraints: dict,
        pm: PortfolioManager, data: pd.DataFrame,
    ) -> None:
        """Execute a triggered rule (delegates to rule_executor)."""
        execute_rule(self.executor, rule, symbol, price, current_date, context, constraints, pm, data)

    def _execute_trade(
        self, action: dict, symbol: str, price: float, current_date: date,
        context: EvaluationContext, constraints: dict,
        pm: PortfolioManager, data: pd.DataFrame,
    ) -> None:
        """Execute a trade action (delegates to rule_executor)."""
        from pyutss.engine.rule_executor import execute_trade
        execute_trade(self.executor, action, symbol, price, current_date, context, constraints, pm, data)

    def _precompute_rules(
        self, rules: list[dict], context: EvaluationContext,
    ) -> list[pd.Series]:
        """Pre-compute rule conditions (delegates to rule_executor)."""
        return precompute_rules(self.condition_evaluator, rules, context)

    def _build_context(
        self, strategy: dict, data: pd.DataFrame,
        parameters: dict[str, float] | None,
    ) -> EvaluationContext:
        """Build evaluation context (delegates to rule_executor)."""
        return build_context(strategy, data, parameters)

    def _resolve_data(
        self, strategy: dict,
        data: pd.DataFrame | dict[str, pd.DataFrame] | None,
        symbol: str | None,
        start_date: date | str | None,
        end_date: date | str | None,
    ) -> tuple[list[str], dict[str, pd.DataFrame]]:
        """Resolve symbols and data (delegates to data_resolver)."""
        return resolve_data(strategy, data, symbol, start_date, end_date)

    def _prepare_data(
        self, data: pd.DataFrame,
        start_date: date | str | None,
        end_date: date | str | None,
    ) -> pd.DataFrame:
        """Prepare data (delegates to data_resolver)."""
        return prepare_data(data, start_date, end_date)

    def _get_weight_scheme(
        self, weights: str | WeightScheme | dict[str, float],
    ) -> WeightScheme:
        """Get weight scheme (delegates to weight_manager)."""
        return get_weight_scheme(weights)

    def _get_weight_scheme_name(
        self, weights: str | WeightScheme | dict[str, float],
    ) -> str:
        """Get weight scheme name (delegates to weight_manager)."""
        return get_weight_scheme_name(weights)

    def _get_current_weights(
        self, pm: PortfolioManager, prices: dict[str, float],
    ) -> dict[str, float]:
        """Get current weights (delegates to weight_manager)."""
        return get_current_weights(pm, prices)

    def _rebalance(
        self, pm: PortfolioManager, symbols: list[str],
        prices: dict[str, float], target_weights: dict[str, float],
    ) -> float:
        """Rebalance portfolio (delegates to weight_manager)."""
        return rebalance(self.executor, pm, symbols, prices, target_weights)

    @staticmethod
    def _load_yaml(path: str) -> dict:
        """Load a YAML file."""
        with open(path) as f:
            return yaml.safe_load(f)
