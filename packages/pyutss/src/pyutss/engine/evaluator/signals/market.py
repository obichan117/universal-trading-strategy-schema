"""Market signal evaluators: price, indicator, constant."""

from typing import Any

import pandas as pd

from pyutss.engine.evaluator.context import EvaluationContext, EvaluationError


def eval_price_signal(
    signal: dict[str, Any], context: EvaluationContext
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


def eval_indicator_signal(
    signal: dict[str, Any],
    context: EvaluationContext,
    resolve_params: Any,
    get_source: Any,
) -> pd.Series:
    """Evaluate indicator signal using the dispatch registry."""
    from pyutss.engine.indicators.dispatcher import dispatch_indicator

    data = context.get_data()
    indicator = signal.get("indicator", "").upper()
    params = signal.get("params", {})

    resolved_params = resolve_params(params, context)
    source = get_source(data, resolved_params)

    result = dispatch_indicator(indicator, data, source, resolved_params)
    if result is not None:
        return result

    raise EvaluationError(f"Unsupported indicator: {indicator}")


def eval_constant_signal(
    signal: dict[str, Any], context: EvaluationContext
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
