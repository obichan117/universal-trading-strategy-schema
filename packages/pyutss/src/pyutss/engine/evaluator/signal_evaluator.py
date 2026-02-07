"""Signal evaluator for UTSS strategies."""

import logging
from typing import Any

import pandas as pd

from pyutss.engine.evaluator.context import (
    EvaluationContext,
    EvaluationError,
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
            return self._eval_ref_signal(signal, context)

        signal_type = signal.get("type", "price")

        if signal_type == "price":
            return self._eval_price_signal(signal, context)
        elif signal_type == "indicator":
            return self._eval_indicator_signal(signal, context)
        elif signal_type == "constant":
            return self._eval_constant_signal(signal, context)
        elif signal_type == "calendar":
            return self._eval_calendar_signal(signal, context)
        elif signal_type == "fundamental":
            return self._eval_fundamental_signal(signal, context)
        elif signal_type == "external":
            return self._eval_external_signal(signal, context)
        elif signal_type == "event":
            return self._eval_event_signal(signal, context)
        elif signal_type == "portfolio":
            return self._eval_portfolio_signal(signal, context)
        elif signal_type == "$ref":
            return self._eval_ref_signal(signal, context)
        else:
            raise EvaluationError(f"Unsupported signal type: {signal_type}")

    def _eval_price_signal(
        self, signal: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate price signal."""
        data = context.get_data()
        field = signal.get("field", "close")

        field_map = {
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
            "hl2": None,
            "hlc3": None,
            "ohlc4": None,
        }

        if field in ["hl2", "hlc3", "ohlc4"]:
            if field == "hl2":
                return (data["high"] + data["low"]) / 2
            elif field == "hlc3":
                return (data["high"] + data["low"] + data["close"]) / 3
            else:
                return (data["open"] + data["high"] + data["low"] + data["close"]) / 4

        col = field_map.get(field, "close")
        if col and col in data.columns:
            return data[col]

        raise EvaluationError(f"Unknown price field: {field}")

    def _eval_indicator_signal(
        self, signal: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate indicator signal using the dispatch registry."""
        from pyutss.engine.indicators.dispatcher import dispatch_indicator

        data = context.get_data()
        indicator = signal.get("indicator", "").upper()
        params = signal.get("params", {})

        # Resolve parameter references
        resolved_params = self._resolve_params(params, context)

        # Get source series
        source = self._get_source(data, resolved_params)

        result = dispatch_indicator(indicator, data, source, resolved_params)
        if result is not None:
            return result

        raise EvaluationError(f"Unsupported indicator: {indicator}")

    def _eval_constant_signal(
        self, signal: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate constant signal."""
        value = signal.get("value", 0)
        if isinstance(value, str) and value.startswith("$param."):
            param_name = value[7:]
            if context.parameters and param_name in context.parameters:
                value = context.parameters[param_name]
            else:
                raise EvaluationError(f"Parameter not found: {param_name}")

        data = context.get_data()
        return pd.Series(float(value), index=data.index)

    def _eval_calendar_signal(
        self, signal: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate calendar signal (returns boolean-like 0/1)."""
        data = context.get_data()
        field = signal.get("field", "day_of_week")
        index = data.index

        if field == "day_of_week":
            return pd.Series(index.dayofweek, index=index)
        elif field == "day_of_month":
            return pd.Series(index.day, index=index)
        elif field == "month":
            return pd.Series(index.month, index=index)
        elif field == "week_of_year":
            return pd.Series(index.isocalendar().week.values, index=index)
        elif field == "is_month_start":
            return self._is_first_trading_day(index).astype(int)
        elif field == "is_month_end":
            return self._is_last_trading_day(index).astype(int)
        elif field == "is_quarter_end":
            return pd.Series((index.month % 3 == 0) & (self._is_last_trading_day(index)), index=index).astype(int)
        else:
            raise EvaluationError(f"Unknown calendar field: {field}")

    def _eval_fundamental_signal(
        self, signal: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate fundamental signal.

        Looks up a fundamental metric (e.g. PE_RATIO) from context.fundamental_data.
        Returns a constant series (fundamentals are point-in-time snapshots).
        """
        metric = signal.get("metric", "PE_RATIO")
        symbol = signal.get("symbol")
        data = context.get_data()

        if context.fundamental_data is None:
            return pd.Series(float("nan"), index=data.index)

        # Look up by explicit symbol or use first available
        key = symbol or next(iter(context.fundamental_data), None)
        fund = context.fundamental_data.get(key) if key else None
        if fund is None:
            return pd.Series(float("nan"), index=data.index)

        # Map UPPER_CASE metric to snake_case attribute
        attr = metric.lower()
        value = getattr(fund, attr, None) if not isinstance(fund, dict) else fund.get(attr)
        return pd.Series(
            float(value) if value is not None else float("nan"),
            index=data.index,
        )

    def _eval_external_signal(
        self, signal: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate external signal.

        Looks up a pre-loaded Series from context.external_data by key.
        Aligns to primary data index and fills gaps with default value.
        """
        source = signal.get("source", "file")
        default = signal.get("default", 0.0)
        data = context.get_data()

        if context.external_data is None:
            return pd.Series(default, index=data.index)

        # Build key from signal definition
        key = signal.get("url") or signal.get("path") or signal.get("provider") or source
        series = context.external_data.get(key)

        if series is None:
            return pd.Series(default, index=data.index)

        # Align to primary data index, fill gaps with default
        return series.reindex(data.index).fillna(default)

    def _eval_event_signal(
        self, signal: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate event signal.

        Returns 1 for dates within the event window, 0 otherwise.
        The window is defined by days_before and days_after the event date.
        """
        event_type = signal.get("event", "EARNINGS_RELEASE")
        days_before = signal.get("days_before", 0)
        days_after = signal.get("days_after", 0)
        data = context.get_data()

        if context.event_data is None:
            return pd.Series(0, index=data.index, dtype=int)

        event_dates = context.event_data.get(event_type, [])
        if not event_dates:
            return pd.Series(0, index=data.index, dtype=int)

        result = pd.Series(0, index=data.index, dtype=int)
        for event_date in event_dates:
            for i, idx in enumerate(data.index):
                current = idx.date() if hasattr(idx, "date") else idx
                diff = (event_date - current).days
                if -days_after <= diff <= days_before:
                    result.iloc[i] = 1
        return result

    def _eval_portfolio_signal(
        self, signal: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate portfolio signal."""
        data = context.get_data()
        field = signal.get("field", "unrealized_pnl")
        symbol = signal.get("symbol")

        if context.portfolio_state is None:
            return pd.Series(0.0, index=data.index)

        ps = context.portfolio_state

        if field == "unrealized_pnl":
            value = ps.unrealized_pnl
        elif field == "realized_pnl":
            value = ps.realized_pnl
        elif field == "cash":
            value = ps.cash
        elif field == "equity":
            value = ps.equity
        elif field == "position_size":
            if symbol and symbol in ps.positions:
                value = ps.positions[symbol].quantity
            elif ps.positions:
                value = sum(p.quantity for p in ps.positions.values())
            else:
                value = 0.0
        elif field == "position_value":
            if symbol and symbol in ps.positions:
                pos = ps.positions[symbol]
                value = pos.quantity * pos.avg_price
            elif ps.positions:
                value = sum(p.quantity * p.avg_price for p in ps.positions.values())
            else:
                value = 0.0
        elif field == "days_in_position":
            if symbol and symbol in ps.positions:
                pos = ps.positions[symbol]
                value = pos.days_held if hasattr(pos, 'days_held') else 0
            elif ps.positions:
                value = max(
                    (p.days_held if hasattr(p, 'days_held') else 0)
                    for p in ps.positions.values()
                )
            else:
                value = 0
        elif field == "exposure":
            if ps.equity > 0:
                position_value = sum(
                    p.quantity * p.avg_price for p in ps.positions.values()
                )
                value = (position_value / ps.equity) * 100
            else:
                value = 0.0
        elif field == "win_rate":
            if ps.total_trades > 0:
                value = (ps.winning_trades / ps.total_trades) * 100
            else:
                value = 0.0
        elif field == "total_trades":
            value = ps.total_trades
        elif field == "has_position":
            if symbol:
                value = 1.0 if symbol in ps.positions else 0.0
            else:
                value = 1.0 if ps.positions else 0.0
        else:
            raise EvaluationError(f"Unknown portfolio field: {field}")

        return pd.Series(float(value), index=data.index)

    def _eval_ref_signal(
        self, signal: dict[str, Any], context: EvaluationContext
    ) -> pd.Series:
        """Evaluate reference signal."""
        ref = signal.get("$ref", "")
        if ref.startswith("#/signals/"):
            ref_name = ref[10:]
            if context.signal_library and ref_name in context.signal_library:
                return self.evaluate_signal(context.signal_library[ref_name], context)
        raise EvaluationError(f"Signal reference not found: {ref}")

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

    def _is_first_trading_day(self, index: pd.DatetimeIndex) -> pd.Series:
        """Check if each date is first trading day of month."""
        year_month = index.to_period("M")
        first_days = index.to_series().groupby(year_month).transform("min")
        return pd.Series(index == first_days.values, index=index)

    def _is_last_trading_day(self, index: pd.DatetimeIndex) -> pd.Series:
        """Check if each date is last trading day of month."""
        year_month = index.to_period("M")
        last_days = index.to_series().groupby(year_month).transform("max")
        return pd.Series(index == last_days.values, index=index)
