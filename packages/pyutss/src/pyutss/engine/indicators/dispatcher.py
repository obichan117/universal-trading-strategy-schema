"""Unified indicator dispatch registry.

Single source of truth for mapping indicator names to IndicatorService calls.
Used by both evaluator.py and expr_parser.py to eliminate duplication.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from pyutss.engine.indicators.service import IndicatorService


@dataclass
class ParamDef:
    """Definition of an indicator parameter."""

    name: str
    type: type  # int or float
    default: Any


@dataclass
class IndicatorSpec:
    """Specification for an indicator dispatch.

    Attributes:
        method: Name of the IndicatorService static method.
        params: Ordered list of parameter definitions.
        inputs: What OHLCV inputs the indicator needs:
            "source"  -> single price series (default: close)
            "hlc"     -> high, low, close
            "hlcv"    -> high, low, close, volume
            "hl"      -> high, low
            "cv"      -> close, volume
            "none"    -> no data inputs (handled specially)
        components: For multi-output indicators, maps component name
            to the attribute name on the result object.
            If None, method returns a pd.Series directly.
        component_param: Which param name selects the component (default: "line").
        default_component: Default component to return if none specified.
        aliases: Alternative names for this indicator.
    """

    method: str
    params: list[ParamDef] = field(default_factory=list)
    inputs: str = "source"
    components: dict[str, str] | None = None
    component_param: str = "line"
    default_component: str | None = None
    aliases: list[str] = field(default_factory=list)

    def resolve_params(self, raw_params: dict[str, Any]) -> dict[str, Any]:
        """Resolve params dict, applying defaults and type coercion."""
        resolved = {}
        for pdef in self.params:
            val = raw_params.get(pdef.name, pdef.default)
            if val is not None:
                resolved[pdef.name] = pdef.type(val)
        return resolved

    def positional_to_dict(self, positional: list[Any]) -> dict[str, Any]:
        """Convert positional args (from expr parser) to a params dict.

        If a positional arg is a string, it's treated as a "source" param.
        """
        result: dict[str, Any] = {}
        param_idx = 0
        for arg in positional:
            if isinstance(arg, str):
                result["source"] = arg
            elif param_idx < len(self.params):
                pdef = self.params[param_idx]
                result[pdef.name] = pdef.type(arg)
                param_idx += 1
            else:
                break
        return result

    def call(
        self,
        data: pd.DataFrame,
        source: pd.Series,
        resolved_params: dict[str, Any],
    ) -> pd.Series:
        """Call the indicator method and return the appropriate series.

        Args:
            data: Full OHLCV DataFrame.
            source: Pre-resolved source price series (for "source" input indicators).
            resolved_params: Already-resolved params dict (type-coerced, defaults applied).

        Returns:
            The indicator series.
        """
        method = getattr(IndicatorService, self.method)

        # Build positional args based on input type
        if self.inputs == "source":
            args = [source]
        elif self.inputs == "hlc":
            args = [data["high"], data["low"], data["close"]]
        elif self.inputs == "hlcv":
            args = [data["high"], data["low"], data["close"], data["volume"]]
        elif self.inputs == "hl":
            args = [data["high"], data["low"]]
        elif self.inputs == "cv":
            args = [data["close"], data["volume"]]
        elif self.inputs == "none":
            args = []
        else:
            args = [source]

        # Build kwargs from params (excluding component_param and source)
        kwargs = {
            k: v for k, v in resolved_params.items()
            if k != self.component_param and k != "source"
        }

        result = method(*args, **kwargs)

        # Handle multi-output indicators
        if self.components is not None:
            component_name = resolved_params.get(
                self.component_param, self.default_component
            )
            if component_name and component_name in self.components:
                return getattr(result, self.components[component_name])
            # Return default component
            if self.default_component and self.default_component in self.components:
                return getattr(result, self.components[self.default_component])
            # Fallback: return first component
            first_attr = next(iter(self.components.values()))
            return getattr(result, first_attr)

        return result


# =============================================================================
# Registry: maps indicator name (uppercase) -> IndicatorSpec
# =============================================================================

_SPECS: list[IndicatorSpec] = [
    # --- Moving Averages ---
    IndicatorSpec("sma", [ParamDef("period", int, 20)]),
    IndicatorSpec("ema", [ParamDef("period", int, 20)]),
    IndicatorSpec("wma", [ParamDef("period", int, 20)]),
    IndicatorSpec("dema", [ParamDef("period", int, 20)]),
    IndicatorSpec("tema", [ParamDef("period", int, 20)]),
    IndicatorSpec("kama", [
        ParamDef("period", int, 10),
        ParamDef("fast_period", int, 2),
        ParamDef("slow_period", int, 30),
    ]),
    IndicatorSpec("hull", [ParamDef("period", int, 9)]),
    IndicatorSpec("vwma", [ParamDef("period", int, 20)], inputs="cv"),

    # --- Momentum ---
    IndicatorSpec("rsi", [ParamDef("period", int, 14)]),
    IndicatorSpec("macd", [
        ParamDef("fast_period", int, 12),
        ParamDef("slow_period", int, 26),
        ParamDef("signal_period", int, 9),
    ], components={
        "macd": "macd_line",
        "signal": "signal_line",
        "histogram": "histogram",
    }, default_component="macd", aliases=["MACD"]),
    IndicatorSpec("stochastic", [
        ParamDef("k_period", int, 14),
        ParamDef("d_period", int, 3),
    ], inputs="hlc", components={
        "k": "k",
        "d": "d",
    }, default_component="k", aliases=["STOCH", "STOCHASTIC"]),
    IndicatorSpec("williams_r", [ParamDef("period", int, 14)], inputs="hlc",
                  aliases=["WILLIAMS_R", "WILLR"]),
    IndicatorSpec("cci", [ParamDef("period", int, 20)], inputs="hlc"),
    IndicatorSpec("mfi", [ParamDef("period", int, 14)], inputs="hlcv"),
    IndicatorSpec("cmo", [ParamDef("period", int, 14)]),
    IndicatorSpec("tsi", [
        ParamDef("long_period", int, 25),
        ParamDef("short_period", int, 13),
    ]),
    IndicatorSpec("stoch_rsi", [
        ParamDef("rsi_period", int, 14),
        ParamDef("stoch_period", int, 14),
        ParamDef("k_period", int, 3),
    ]),
    IndicatorSpec("roc", [ParamDef("period", int, 12)]),
    IndicatorSpec("momentum", [ParamDef("period", int, 10)]),

    # --- Volatility ---
    IndicatorSpec("atr", [ParamDef("period", int, 14)], inputs="hlc"),
    IndicatorSpec("stddev", [ParamDef("period", int, 20)]),
    IndicatorSpec("variance", [ParamDef("period", int, 20)]),
    IndicatorSpec("bollinger_bands", [
        ParamDef("period", int, 20),
        ParamDef("std_dev", float, 2.0),
    ], components={
        "upper": "upper",
        "lower": "lower",
        "middle": "middle",
        "bandwidth": "bandwidth",
        "percent_b": "percent_b",
    }, component_param="band", default_component="percent_b",
        aliases=["BB", "BOLLINGER"]),

    # --- Trend ---
    IndicatorSpec("adx", [ParamDef("period", int, 14)], inputs="hlc"),
    IndicatorSpec("plus_di", [ParamDef("period", int, 14)], inputs="hlc"),
    IndicatorSpec("minus_di", [ParamDef("period", int, 14)], inputs="hlc"),
    IndicatorSpec("supertrend", [
        ParamDef("period", int, 10),
        ParamDef("multiplier", float, 3.0),
    ], inputs="hlc"),
    IndicatorSpec("psar", [
        ParamDef("af_start", float, 0.02),
        ParamDef("af_increment", float, 0.02),
        ParamDef("af_max", float, 0.2),
    ], inputs="hlc"),
    IndicatorSpec("aroon", [ParamDef("period", int, 25)], inputs="hl",
                  components={
                      "up": "aroon_up",
                      "down": "aroon_down",
                      "oscillator": "oscillator",
                  }, component_param="line", default_component="up"),
    IndicatorSpec("ichimoku_tenkan", [ParamDef("period", int, 9)], inputs="hl"),
    IndicatorSpec("ichimoku_kijun", [ParamDef("period", int, 26)], inputs="hl"),
    IndicatorSpec("ichimoku_senkou_a", [
        ParamDef("tenkan_period", int, 9),
        ParamDef("kijun_period", int, 26),
    ], inputs="hl"),
    IndicatorSpec("ichimoku_senkou_b", [ParamDef("period", int, 52)], inputs="hl"),
    IndicatorSpec("ichimoku_chikou", [ParamDef("period", int, 26)], inputs="source"),
    IndicatorSpec("donchian_channel", [ParamDef("period", int, 20)], inputs="hl",
                  components={
                      "upper": "upper",
                      "middle": "middle",
                      "lower": "lower",
                  }, default_component="upper"),
    IndicatorSpec("keltner_channel", [
        ParamDef("ema_period", int, 20),
        ParamDef("atr_period", int, 10),
        ParamDef("multiplier", float, 2.0),
    ], inputs="hlc", components={
        "upper": "upper",
        "middle": "middle",
        "lower": "lower",
    }, default_component="upper"),

    # --- Volume ---
    IndicatorSpec("obv", [], inputs="cv"),
    IndicatorSpec("vwap", [], inputs="hlcv"),
    IndicatorSpec("cmf", [ParamDef("period", int, 20)], inputs="hlcv"),
    IndicatorSpec("ad", [], inputs="hlcv"),
    IndicatorSpec("klinger", [
        ParamDef("fast_period", int, 34),
        ParamDef("slow_period", int, 55),
    ], inputs="hlcv"),

    # --- Statistical ---
    IndicatorSpec("highest", [ParamDef("period", int, 20)]),
    IndicatorSpec("lowest", [ParamDef("period", int, 20)]),
    IndicatorSpec("simple_return", [ParamDef("period", int, 1)],
                  aliases=["RETURN"]),
    IndicatorSpec("drawdown", []),
    IndicatorSpec("zscore", [ParamDef("period", int, 20)]),
    IndicatorSpec("percentile", [ParamDef("period", int, 252)]),
    IndicatorSpec("rank", [ParamDef("period", int, 252)]),
    IndicatorSpec("beta", [ParamDef("period", int, 252)]),
    IndicatorSpec("correlation", [ParamDef("period", int, 252)]),
]


def _build_registry() -> dict[str, IndicatorSpec]:
    """Build the indicator registry from specs."""
    registry: dict[str, IndicatorSpec] = {}
    for spec in _SPECS:
        # Register by method name (uppercase)
        registry[spec.method.upper()] = spec
        # Register aliases
        for alias in spec.aliases:
            registry[alias.upper()] = spec
    return registry


INDICATOR_REGISTRY: dict[str, IndicatorSpec] = _build_registry()

# --- Shortcut registrations for component indicators ---
# These are indicators that are really a specific component of a multi-output indicator.
# E.g. MACD_SIGNAL is MACD with line=signal, BB_UPPER is bollinger_bands with band=upper.

_COMPONENT_SHORTCUTS: dict[str, tuple[str, str, str]] = {
    # name -> (base_indicator, component_param, component_value)
    "MACD_SIGNAL": ("MACD", "line", "signal"),
    "MACD_HIST": ("MACD", "line", "histogram"),
    "STOCH_K": ("STOCHASTIC", "line", "k"),
    "STOCH_D": ("STOCHASTIC", "line", "d"),
    "BB_UPPER": ("BOLLINGER_BANDS", "band", "upper"),
    "BB_LOWER": ("BOLLINGER_BANDS", "band", "lower"),
    "BB_MIDDLE": ("BOLLINGER_BANDS", "band", "middle"),
    "BB_WIDTH": ("BOLLINGER_BANDS", "band", "bandwidth"),
    "BB_PERCENT": ("BOLLINGER_BANDS", "band", "percent_b"),
    "DC_UPPER": ("DONCHIAN_CHANNEL", "line", "upper"),
    "DC_MIDDLE": ("DONCHIAN_CHANNEL", "line", "middle"),
    "DC_LOWER": ("DONCHIAN_CHANNEL", "line", "lower"),
    "KC_UPPER": ("KELTNER_CHANNEL", "line", "upper"),
    "KC_MIDDLE": ("KELTNER_CHANNEL", "line", "middle"),
    "KC_LOWER": ("KELTNER_CHANNEL", "line", "lower"),
    "AROON_UP": ("AROON", "line", "up"),
    "AROON_DOWN": ("AROON", "line", "down"),
    "AROON_OSC": ("AROON", "line", "oscillator"),
}


def dispatch_indicator(
    indicator: str,
    data: pd.DataFrame,
    source: pd.Series,
    resolved_params: dict[str, Any],
) -> pd.Series | None:
    """Dispatch an indicator call through the registry.

    Args:
        indicator: Uppercase indicator name (e.g., "SMA", "MACD", "BB_UPPER").
        data: Full OHLCV DataFrame.
        source: Pre-resolved source series.
        resolved_params: Params dict with $param refs already resolved.

    Returns:
        The indicator series, or None if the indicator is not in the registry.
    """
    # Check component shortcuts first
    if indicator in _COMPONENT_SHORTCUTS:
        base_name, comp_param, comp_value = _COMPONENT_SHORTCUTS[indicator]
        spec = INDICATOR_REGISTRY.get(base_name)
        if spec:
            params = spec.resolve_params(resolved_params)
            params[comp_param] = comp_value
            return spec.call(data, source, params)

    # Check main registry
    spec = INDICATOR_REGISTRY.get(indicator)
    if spec is None:
        return None

    params = spec.resolve_params(resolved_params)
    return spec.call(data, source, params)


def build_indicator_signal(indicator: str, positional_params: list[Any]) -> dict[str, Any]:
    """Build a signal dict from an indicator name and positional params.

    Used by expr_parser to convert e.g. SMA(20) -> {"type": "indicator", ...}.

    Args:
        indicator: Uppercase indicator name.
        positional_params: Positional args from expression parse.

    Returns:
        Signal dict ready for SignalEvaluator.
    """
    signal: dict[str, Any] = {"type": "indicator", "indicator": indicator}

    # Check component shortcuts — normalize to base indicator
    if indicator in _COMPONENT_SHORTCUTS:
        base_name, comp_param, comp_value = _COMPONENT_SHORTCUTS[indicator]
        spec = INDICATOR_REGISTRY.get(base_name)
        if spec:
            params = spec.positional_to_dict(positional_params)
            params[comp_param] = comp_value
            signal["params"] = params
            return signal

    # Check main registry
    spec = INDICATOR_REGISTRY.get(indicator)
    if spec:
        # Normalize aliases: WILLR -> WILLIAMS_R, etc.
        if indicator in ("WILLR",):
            signal["indicator"] = "WILLIAMS_R"
        params = spec.positional_to_dict(positional_params)
        signal["params"] = params
    else:
        # Generic fallback: assume first param is period
        if positional_params:
            signal["params"] = {"period": int(positional_params[0])}

    return signal
