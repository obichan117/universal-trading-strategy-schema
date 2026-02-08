"""Signal evaluator for UTSS strategies."""

import logging
from typing import Any

import pandas as pd

from pyutss.engine.evaluator.context import (
    EvaluationContext,
    EvaluationError,
)
from pyutss.engine.evaluator.signals.data import (
    eval_external_signal,
    eval_fundamental_signal,
    eval_portfolio_signal,
)
from pyutss.engine.evaluator.signals.market import (
    eval_constant_signal,
    eval_indicator_signal,
    eval_price_signal,
)
from pyutss.engine.evaluator.signals.reference import eval_ref_signal
from pyutss.engine.evaluator.signals.temporal import (
    eval_calendar_signal,
    eval_event_signal,
)

logger = logging.getLogger(__name__)


class SignalEvaluator:
    """Evaluates UTSS signals against OHLCV data.

    Supports all UTSS signal types:
    - price: OHLCV price fields
    - indicator: Technical indicators (SMA, EMA, RSI, MACD, etc.)
    - fundamental: Fundamental metrics (PE_RATIO, ROE, etc.)
    - calendar: Date patterns (day_of_week, is_month_end, etc.)
    - event: Market events (EARNINGS_RELEASE, etc.)
    - portfolio: Portfolio state
    - constant: Fixed values
    - external: External data sources (webhook, file, provider)
    - expr: Custom expressions (limited support)

    Example:
        evaluator = SignalEvaluator()
        context = EvaluationContext(primary_data=ohlcv_df)

        # Evaluate a signal
        signal = {"type": "indicator", "indicator": "RSI", "params": {"period": 14}}
        values = evaluator.evaluate_signal(signal, context)
    """

    def __init__(self) -> None:
        """Initialize signal evaluator."""
        self._cache: dict[str, pd.Series] = {}
        self._dispatch = {
            "price": lambda s, c: eval_price_signal(s, c),
            "indicator": lambda s, c: eval_indicator_signal(
                s, c, self._resolve_params, self._get_source
            ),
            "constant": lambda s, c: eval_constant_signal(s, c),
            "calendar": lambda s, c: eval_calendar_signal(s, c),
            "fundamental": lambda s, c: eval_fundamental_signal(s, c),
            "external": lambda s, c: eval_external_signal(s, c),
            "event": lambda s, c: eval_event_signal(s, c),
            "portfolio": lambda s, c: eval_portfolio_signal(s, c),
            "$ref": lambda s, c: eval_ref_signal(s, c, self),
        }

    def clear_cache(self) -> None:
        """Clear calculation cache."""
        self._cache.clear()

    def evaluate_signal(
        self,
        signal: dict[str, Any],
        context: EvaluationContext,
    ) -> pd.Series:
        """Evaluate a signal definition to get a numeric series.

        Args:
            signal: Signal definition from UTSS strategy
            context: Evaluation context with data

        Returns:
            Series of signal values
        """
        # Check for $ref first (can appear without explicit type)
        if "$ref" in signal:
            return eval_ref_signal(signal, context, self)

        signal_type = signal.get("type", "price")

        handler = self._dispatch.get(signal_type)
        if handler:
            return handler(signal, context)

        raise EvaluationError(f"Unsupported signal type: {signal_type}")

    def _resolve_params(
        self, params: dict[str, Any], context: EvaluationContext
    ) -> dict[str, Any]:
        """Resolve parameter references in params dict."""
        resolved = {}
        for key, val in params.items():
            if isinstance(val, str) and val.startswith("$param."):
                param_name = val[7:]
                if context.parameters and param_name in context.parameters:
                    resolved[key] = context.parameters[param_name]
                else:
                    raise EvaluationError(f"Parameter not found: {param_name}")
            else:
                resolved[key] = val
        return resolved

    def _get_source(self, data: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
        """Get source price series."""
        source = params.get("source", "close")
        if source == "close":
            return data["close"]
        elif source == "open":
            return data["open"]
        elif source == "high":
            return data["high"]
        elif source == "low":
            return data["low"]
        elif source == "hl2":
            return (data["high"] + data["low"]) / 2
        elif source == "hlc3":
            return (data["high"] + data["low"] + data["close"]) / 3
        elif source == "ohlc4":
            return (data["open"] + data["high"] + data["low"] + data["close"]) / 4
        return data["close"]
